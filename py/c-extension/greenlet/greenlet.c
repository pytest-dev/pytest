#include "greenlet.h"
#include "structmember.h"


/* XXX major open bugs:
   XXX - no GC.  Unfinished greenlets won't be deallocated if they
   XXX   contain a cycle to themselves from anywhere in their frame stack.
*/

/***********************************************************

A PyGreenlet is a range of C stack addresses that must be
saved and restored in such a way that the full range of the
stack contains valid data when we switch to it.

Stack layout for a greenlet:

               |     ^^^       |
               |  older data   |
               |               |
  stack_stop . |_______________|
        .      |               |
        .      | greenlet data |
        .      |   in stack    |
        .    * |_______________| . .  _____________  stack_copy + stack_saved
        .      |               |     |             |
        .      |     data      |     |greenlet data|
        .      |   unrelated   |     |    saved    |
        .      |      to       |     |   in heap   |
 stack_start . |     this      | . . |_____________| stack_copy
               |   greenlet    |
               |               |
               |  newer data   |
               |     vvv       |


Note that a greenlet's stack data is typically partly at its correct
place in the stack, and partly saved away in the heap, but always in
the above configuration: two blocks, the more recent one in the heap
and the older one still in the stack (either block may be empty).

Greenlets are chained: each points to the previous greenlet, which is
the one that owns the data currently in the C stack above my
stack_stop.  The currently running greenlet is the first element of
this chain.  The main (initial) greenlet is the last one.  Greenlets
whose stack is entirely in the heap can be skipped from the chain.

The chain is not related to execution order, but only to the order
in which bits of C stack happen to belong to greenlets at a particular
point in time.

The main greenlet doesn't have a stack_stop: it is responsible for the
complete rest of the C stack, and we don't know where it begins.  We
use (char*) -1, the largest possible address.

States:
  stack_stop == NULL && stack_start == NULL:  did not start yet
  stack_stop != NULL && stack_start == NULL:  already finished
  stack_stop != NULL && stack_start != NULL:  active

The running greenlet's stack_start is undefined but not NULL.

 ***********************************************************/

/*** global state ***/

/* In the presence of multithreading, this is a bit tricky:

   - ts_current always store a reference to a greenlet, but it is
     not really the current greenlet after a thread switch occurred.

   - each *running* greenlet uses its run_info field to know which
     thread it is attached to.  A greenlet can only run in the thread
     where it was created.  This run_info is a ref to tstate->dict.

   - the thread state dict is used to save and restore ts_current,
     using the dictionary key 'ts_curkey'.
*/

static PyGreenlet* ts_current;
static PyGreenlet* ts_origin;
static PyGreenlet* ts_target;
static PyObject* ts_passaround;

/***********************************************************/
/* Thread-aware routines, switching global variables when needed */

#define STATE_OK    (ts_current->run_info == PyThreadState_GET()->dict \
			|| !green_updatecurrent())

static PyObject* ts_curkey;
static PyObject* ts_delkey;
static PyObject* PyExc_GreenletError;
static PyObject* PyExc_GreenletExit;

static PyGreenlet* green_create_main(void)
{
	PyGreenlet* gmain;
	PyObject* dict = PyThreadState_GetDict();
	if (dict == NULL) {
		if (!PyErr_Occurred())
			PyErr_NoMemory();
		return NULL;
	}

	/* create the main greenlet for this thread */
	gmain = (PyGreenlet*) PyType_GenericAlloc(&PyGreen_Type, 0);
	if (gmain == NULL)
		return NULL;
	gmain->stack_start = (char*) 1;
	gmain->stack_stop = (char*) -1;
	gmain->run_info = dict;
	Py_INCREF(dict);
	return gmain;
}

static int green_updatecurrent(void)
{
	PyThreadState* tstate;
	PyGreenlet* next;
	PyGreenlet* previous;
	PyObject* deleteme;

	/* save ts_current as the current greenlet of its own thread */
	previous = ts_current;
	if (PyDict_SetItem(previous->run_info, ts_curkey, (PyObject*) previous))
		return -1;

	/* get ts_current from the active tstate */
	tstate = PyThreadState_GET();
	if (tstate->dict && (next =
	    (PyGreenlet*) PyDict_GetItem(tstate->dict, ts_curkey))) {
		/* found -- remove it, to avoid keeping a ref */
		Py_INCREF(next);
		if (PyDict_SetItem(tstate->dict, ts_curkey, Py_None))
			PyErr_Clear();
	}
	else {
		/* first time we see this tstate */
		next = green_create_main();
		if (next == NULL)
			return -1;
	}
	ts_current = next;
	Py_DECREF(previous);
	/* green_dealloc() cannot delete greenlets from other threads, so
	   it stores them in the thread dict; delete them now. */
	deleteme = PyDict_GetItem(tstate->dict, ts_delkey);
	if (deleteme != NULL) {
		PyList_SetSlice(deleteme, 0, INT_MAX, NULL);
	}
	return 0;
}

static PyObject* green_statedict(PyGreenlet* g)
{
	while (!PyGreen_STARTED(g))
		g = g->parent;
	return g->run_info;
}

/***********************************************************/

static int g_save(PyGreenlet* g, char* stop)
{
	/* Save more of g's stack into the heap -- at least up to 'stop'

	   g->stack_stop |________|
	                 |        |
			 |    __ stop       . . . . .
	                 |        |    ==>  .       .
			 |________|          _______
			 |        |         |       |
			 |        |         |       |
	  g->stack_start |        |         |_______| g->stack_copy

	 */
	long sz1 = g->stack_saved;
	long sz2 = stop - g->stack_start;
	assert(g->stack_start != NULL);
	if (sz2 > sz1) {
		char* c = PyMem_Realloc(g->stack_copy, sz2);
		if (!c) {
			PyErr_NoMemory();
			return -1;
		}
		memcpy(c+sz1, g->stack_start+sz1, sz2-sz1);
		g->stack_copy = c;
		g->stack_saved = sz2;
	}
	return 0;
}

static void slp_restore_state(void)
{
	PyGreenlet* g = ts_target;
	
	/* Restore the heap copy back into the C stack */
	if (g->stack_saved != 0) {
		memcpy(g->stack_start, g->stack_copy, g->stack_saved);
		PyMem_Free(g->stack_copy);
		g->stack_copy = NULL;
		g->stack_saved = 0;
	}
	if (ts_current->stack_stop == g->stack_stop)
		g->stack_prev = ts_current->stack_prev;
	else
		g->stack_prev = ts_current;
}

static int slp_save_state(char* stackref)
{
	/* must free all the C stack up to target_stop */
	char* target_stop = ts_target->stack_stop;
	assert(ts_current->stack_saved == 0);
	if (ts_current->stack_start == NULL)
		ts_current = ts_current->stack_prev;  /* not saved if dying */
	else
		ts_current->stack_start = stackref;
	
	while (ts_current->stack_stop < target_stop) {
		/* ts_current is entierely within the area to free */
		if (g_save(ts_current, ts_current->stack_stop))
			return -1;  /* XXX */
		ts_current = ts_current->stack_prev;
	}
	if (ts_current != ts_target) {
		if (g_save(ts_current, target_stop))
			return -1;  /* XXX */
	}
	return 0;
}


/*
 * the following macros are spliced into the OS/compiler
 * specific code, in order to simplify maintenance.
 */

#define SLP_SAVE_STATE(stackref, stsizediff)		\
  stackref += STACK_MAGIC;				\
  if (slp_save_state((char*)stackref)) return -1;	\
  if (!PyGreen_ACTIVE(ts_target)) return 1;		\
  stsizediff = ts_target->stack_start - (char*)stackref

#define SLP_RESTORE_STATE()			\
  slp_restore_state()


#define SLP_EVAL
#include "slp_platformselect.h"

#ifndef STACK_MAGIC
#error "greenlet needs to be ported to this platform,\
 or teached how to detect your compiler properly."
#endif


/* This is a trick to prevent the compiler from inlining or
   removing the frames */
int (*_PyGreen_slp_switch) (void);
int (*_PyGreen_switchstack) (void);
void (*_PyGreen_initialstub) (void*);

static int g_switchstack(void)
{
	/* perform a stack switch according to some global variables
	   that must be set before:
	   - ts_current: current greenlet (holds a reference)
	   - ts_target: greenlet to switch to
	   - ts_passaround: NULL if PyErr_Occurred(),
	             else a tuple of args sent to ts_target (holds a reference)
	*/
	int err;
	{   /* save state */
		PyThreadState* tstate = PyThreadState_GET();
		ts_current->recursion_depth = tstate->recursion_depth;
		ts_current->top_frame = tstate->frame;
	}
	ts_origin = ts_current;
	err = _PyGreen_slp_switch();
	if (err < 0) {   /* error */
		Py_XDECREF(ts_passaround);
		ts_passaround = NULL;
	}
	else {
		PyThreadState* tstate = PyThreadState_GET();
		tstate->recursion_depth = ts_target->recursion_depth;
		tstate->frame = ts_target->top_frame;
		ts_target->top_frame = NULL;
		ts_current = ts_target;
		Py_INCREF(ts_target);
		Py_DECREF(ts_origin);
	}
	return err;
}

static PyObject* g_switch(PyGreenlet* target, PyObject* args)
{
	/* _consumes_ a reference to the args tuple,
	   and return a new tuple reference */

	/* check ts_current */
	if (!STATE_OK) {
		Py_DECREF(args);
		return NULL;
	}
	if (green_statedict(target) != ts_current->run_info) {
		PyErr_SetString(PyExc_GreenletError,
				"cannot switch to a different thread");
		Py_DECREF(args);
		return NULL;
	}
	ts_passaround = args;

	/* find the real target by ignoring dead greenlets,
	   and if necessary starting a greenlet. */
	while (1) {
		if (PyGreen_ACTIVE(target)) {
			ts_target = target;
			_PyGreen_switchstack();
			return ts_passaround;
		}
		if (!PyGreen_STARTED(target)) {
			void* dummymarker;
			ts_target = target;
			_PyGreen_initialstub(&dummymarker);
			return ts_passaround;
		}
		target = target->parent;
	}
}

static PyObject *g_handle_exit(PyObject *result)
{
	if (result == NULL &&
	    PyErr_ExceptionMatches(PyExc_GreenletExit)) {
		/* catch and ignore GreenletExit */
		PyObject *exc, *val, *tb;
		PyErr_Fetch(&exc, &val, &tb);
		if (val == NULL) {
			Py_INCREF(Py_None);
			val = Py_None;
		}
		result = val;
		Py_DECREF(exc);
		Py_XDECREF(tb);
	}
	if (result != NULL) {
		/* package the result into a 1-tuple */
		PyObject* r = result;
		result = PyTuple_New(1);
		if (result)
			PyTuple_SET_ITEM(result, 0, r);
		else
			Py_DECREF(r);
	}
	return result;
}

static void g_initialstub(void* mark)
{
	int err;
	PyObject* o;

	/* ts_target.run is the object to call in the new greenlet */
	PyObject* run = PyObject_GetAttrString((PyObject*) ts_target, "run");
	if (run == NULL) {
		Py_XDECREF(ts_passaround);
		ts_passaround = NULL;
		return;
	}
	/* now use run_info to store the statedict */
	o = ts_target->run_info;
	ts_target->run_info = green_statedict(ts_target->parent);
	Py_INCREF(ts_target->run_info);
	Py_XDECREF(o);

	/* start the greenlet */
	ts_target->stack_start = NULL;
	ts_target->stack_stop = (char*) mark;
	if (ts_current->stack_start == NULL)    /* ts_current is dying */
		ts_target->stack_prev = ts_current->stack_prev;
	else
		ts_target->stack_prev = ts_current;
	ts_target->top_frame = NULL;
	ts_target->recursion_depth = PyThreadState_GET()->recursion_depth;
	err = _PyGreen_switchstack();
	/* returns twice!
	   The 1st time with err=1: we are in the new greenlet
	   The 2nd time with err=0: back in the caller's greenlet
	*/
	if (err == 1) {
		/* in the new greenlet */
		PyObject* args;
		PyObject* result;
		PyGreenlet* ts_self = ts_current;
		ts_self->stack_start = (char*) 1;  /* running */

		args = ts_passaround;
		if (args == NULL)    /* pending exception */
			result = NULL;
		else {
			/* call g.run(*args) */
			result = PyEval_CallObject(run, args);
			Py_DECREF(args);
		}
		Py_DECREF(run);
		result = g_handle_exit(result);
		/* jump back to parent */
		ts_self->stack_start = NULL;  /* dead */
		g_switch(ts_self->parent, result);
		/* must not return from here! */
		PyErr_WriteUnraisable((PyObject*) ts_self);
		Py_FatalError("greenlets cannot continue");
	}
	/* back in the parent */
}


/***********************************************************/


static PyObject* green_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PyObject* o;
	if (!STATE_OK)
		return NULL;
	
	o = type->tp_alloc(type, 0);
	if (o != NULL) {
		Py_INCREF(ts_current);
		((PyGreenlet*) o)->parent = ts_current;
	}
	return o;
}

static int green_setrun(PyGreenlet* self, PyObject* nparent, void* c);
static int green_setparent(PyGreenlet* self, PyObject* nparent, void* c);

static int green_init(PyGreenlet *self, PyObject *args, PyObject *kwds)
{
	PyObject *run = NULL;
	PyObject* nparent = NULL;
	static char *kwlist[] = {"run", "parent", 0};
	if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO:green", kwlist,
					 &run, &nparent))
		return -1;

	if (run != NULL) {
		if (green_setrun(self, run, NULL))
			return -1;
	}
	if (nparent != NULL)
		return green_setparent(self, nparent, NULL);
	return 0;
}

static int kill_greenlet(PyGreenlet* self)
{
	/* Cannot raise an exception to kill the greenlet if
	   it is not running in the same thread! */
	if (self->run_info == PyThreadState_GET()->dict) {
		/* The dying greenlet cannot be a parent of ts_current
		   because the 'parent' field chain would hold a
		   reference */
		PyObject* result;
		if (!STATE_OK)
			return -1;
		Py_INCREF(ts_current);
		self->parent = ts_current;
		/* Send the greenlet a GreenletExit exception. */
		PyErr_SetNone(PyExc_GreenletExit);
		result = g_switch(self, NULL);
		if (result == NULL)
			return -1;
		Py_DECREF(result);
		return 0;
	}
	else {
		/* Not the same thread! Temporarily save the greenlet
		   into its thread's ts_delkey list. */
		PyObject* lst;
		lst = PyDict_GetItem(self->run_info, ts_delkey);
		if (lst == NULL) {
			lst = PyList_New(0);
			if (lst == NULL || PyDict_SetItem(self->run_info,
							  ts_delkey, lst) < 0)
				return -1;
		}
		if (PyList_Append(lst, (PyObject*) self) < 0)
			return -1;
		if (!STATE_OK)  /* to force ts_delkey to be reconsidered */
			return -1;
		return 0;
	}
}

static void green_dealloc(PyGreenlet* self)
{
	PyObject *error_type, *error_value, *error_traceback;

	Py_XDECREF(self->parent);
	self->parent = NULL;
	if (PyGreen_ACTIVE(self)) {
		/* Hacks hacks hacks copied from instance_dealloc() */
		/* Temporarily resurrect the greenlet. */
		assert(self->ob_refcnt == 0);
		self->ob_refcnt = 1;
		/* Save the current exception, if any. */
		PyErr_Fetch(&error_type, &error_value, &error_traceback);
		if (kill_greenlet(self) < 0) {
			PyErr_WriteUnraisable((PyObject*) self);
			/* XXX what else should we do? */
		}
		/* Restore the saved exception. */
		PyErr_Restore(error_type, error_value, error_traceback);
		/* Undo the temporary resurrection; can't use DECREF here,
		 * it would cause a recursive call.
		 */
		assert(self->ob_refcnt > 0);
		--self->ob_refcnt;
		if (self->ob_refcnt == 0 && PyGreen_ACTIVE(self)) {
			/* Not resurrected, but still not dead!
			   XXX what else should we do? we complain. */
			PyObject* f = PySys_GetObject("stderr");
			if (f != NULL) {
				PyFile_WriteString("GreenletExit did not kill ",
						   f);
				PyFile_WriteObject((PyObject*) self, f, 0);
				PyFile_WriteString("\n", f);
			}
			Py_INCREF(self);   /* leak! */
		}
		if (self->ob_refcnt != 0) {
			/* Resurrected! */
			int refcnt = self->ob_refcnt;
			_Py_NewReference((PyObject*) self);
			self->ob_refcnt = refcnt;
#ifdef COUNT_ALLOCS
			--self->ob_type->tp_frees;
			--self->ob_type->tp_allocs;
#endif
			return;
		}
	}
	if (self->weakreflist != NULL)
		PyObject_ClearWeakRefs((PyObject *) self);
	Py_XDECREF(self->run_info);
	self->ob_type->tp_free((PyObject*) self);
}

static PyObject* single_result(PyObject* results)
{
	if (results != NULL && PyTuple_Check(results) &&
	    PyTuple_GET_SIZE(results) == 1) {
		PyObject *result = PyTuple_GET_ITEM(results, 0);
		Py_INCREF(result);
		Py_DECREF(results);
		return result;
	}
	else
		return results;
}

static PyObject *
throw_greenlet(PyGreenlet* self, PyObject* typ, PyObject* val, PyObject* tb)
{
	/* Note: _consumes_ a reference to typ, val, tb */
	PyObject *result = NULL;
	PyErr_Restore(typ, val, tb);
	if (PyGreen_STARTED(self) && !PyGreen_ACTIVE(self)) {
		/* dead greenlet: turn GreenletExit into a regular return */
		result = g_handle_exit(result);
	}
	return single_result(g_switch(self, result));
}

PyDoc_STRVAR(switch_doc,
"switch([val]) -> switch execution to greenlet optionally passing a value, "
"return value passed when switching back");

static PyObject* green_switch(PyGreenlet* self, PyObject* args)
{
	Py_INCREF(args);
	return single_result(g_switch(self, args));
}

#ifndef PyExceptionClass_Check      /* Python < 2.5 */
# define PyExceptionClass_Check     PyClass_Check
#endif
#ifndef PyExceptionInstance_Check   /* Python < 2.5 */
# define PyExceptionInstance_Check  PyInstance_Check
#endif
#ifndef PyExceptionInstance_Class   /* Python < 2.5 */
# define PyExceptionInstance_Class(x)				\
		((PyObject*)((PyInstanceObject*)(x))->in_class)
#endif

PyDoc_STRVAR(throw_doc,
"throw(typ[,val[,tb]]) -> raise exception in greenlet, return value passed "
"when switching back");

static PyObject* green_throw(PyGreenlet* self, PyObject* args)
{
	PyObject *typ = PyExc_GreenletExit;
	PyObject *val = NULL;
	PyObject *tb = NULL;
	
	if (!PyArg_ParseTuple(args, "|OOO:throw", &typ, &val, &tb))
		return NULL;

	/* First, check the traceback argument, replacing None with
	   NULL. */
	if (tb == Py_None)
		tb = NULL;
	else if (tb != NULL && !PyTraceBack_Check(tb)) {
		PyErr_SetString(PyExc_TypeError,
			"throw() third argument must be a traceback object");
		return NULL;
	}

	Py_INCREF(typ);
	Py_XINCREF(val);
	Py_XINCREF(tb);

	if (PyExceptionClass_Check(typ)) {
		PyErr_NormalizeException(&typ, &val, &tb);
	}

	else if (PyExceptionInstance_Check(typ)) {
		/* Raising an instance.  The value should be a dummy. */
		if (val && val != Py_None) {
			PyErr_SetString(PyExc_TypeError,
			  "instance exception may not have a separate value");
			goto failed_throw;
		}
		else {
			/* Normalize to raise <class>, <instance> */
			Py_XDECREF(val);
			val = typ;
			typ = PyExceptionInstance_Class(typ);
			Py_INCREF(typ);
		}
	}
	else {
		/* Not something you can raise.  throw() fails. */
		PyErr_Format(PyExc_TypeError,
			     "exceptions must be classes, or instances, not %s",
			     typ->ob_type->tp_name);
		goto failed_throw;
	}

	return throw_greenlet(self, typ, val, tb);

failed_throw:
	/* Didn't use our arguments, so restore their original refcounts */
	Py_DECREF(typ);
	Py_XDECREF(val);
	Py_XDECREF(tb);
	return NULL;
}

static int green_nonzero(PyGreenlet* self)
{
	return PyGreen_ACTIVE(self);
}

static PyObject* green_getdead(PyGreenlet* self, void* c)
{
	PyObject* res;
	if (PyGreen_ACTIVE(self) || !PyGreen_STARTED(self))
		res = Py_False;
	else
		res = Py_True;
	Py_INCREF(res);
	return res;
}

static PyObject* green_getrun(PyGreenlet* self, void* c)
{
	if (PyGreen_STARTED(self) || self->run_info == NULL) {
		PyErr_SetString(PyExc_AttributeError, "run");
		return NULL;
	}
	Py_INCREF(self->run_info);
	return self->run_info;
}

static int green_setrun(PyGreenlet* self, PyObject* nrun, void* c)
{
	PyObject* o;
	if (PyGreen_STARTED(self)) {
		PyErr_SetString(PyExc_AttributeError,
				"run cannot be set "
				"after the start of the greenlet");
		return -1;
	}
	o = self->run_info;
	self->run_info = nrun;
	Py_XINCREF(nrun);
	Py_XDECREF(o);
	return 0;
}

static PyObject* green_getparent(PyGreenlet* self, void* c)
{
	PyObject* result = self->parent ? (PyObject*) self->parent : Py_None;
	Py_INCREF(result);
	return result;
}

static int green_setparent(PyGreenlet* self, PyObject* nparent, void* c)
{
	PyGreenlet* p;
	if (nparent == NULL) {
		PyErr_SetString(PyExc_AttributeError, "can't delete attribute");
		return -1;
	}
	if (!PyGreen_Check(nparent)) {
		PyErr_SetString(PyExc_TypeError, "parent must be a greenlet");
		return -1;
	}
	for (p=(PyGreenlet*) nparent; p; p=p->parent) {
		if (p == self) {
			PyErr_SetString(PyExc_ValueError, "cyclic parent chain");
			return -1;
		}
	}
	p = self->parent;
	self->parent = (PyGreenlet*) nparent;
	Py_INCREF(nparent);
	Py_DECREF(p);
	return 0;
}

static PyObject* green_getframe(PyGreenlet* self, void* c)
{
	PyObject* result = self->top_frame ? (PyObject*) self->top_frame : Py_None;
	Py_INCREF(result);
	return result;
}


/***********************************************************/
/* C interface */

PyObject* PyGreen_New(PyObject* run, PyObject* parent)
{
	PyGreenlet* o;
	if (!PyGreen_Check(parent)) {
		PyErr_SetString(PyExc_TypeError, "parent must be a greenlet");
		return NULL;
	}
	o = (PyGreenlet*) PyType_GenericAlloc(&PyGreen_Type, 0);
	if (o == NULL)
		return NULL;
	Py_INCREF(run);
	o->run_info = run;
	Py_INCREF(parent);
	o->parent = (PyGreenlet*) parent;
	return (PyObject*) o;
}

PyObject* PyGreen_Current(void)
{
	if (!STATE_OK)
		return NULL;
	return (PyObject*) ts_current;
}

PyObject* PyGreen_Switch(PyObject* g, PyObject* value)
{
	PyGreenlet *self;
	if (!PyGreen_Check(g)) {
		PyErr_BadInternalCall();
		return NULL;
	}
	self = (PyGreenlet*) g;
	Py_XINCREF(value);
	if (PyGreen_STARTED(self) && !PyGreen_ACTIVE(self))
		value = g_handle_exit(value);
	return single_result(g_switch(self, value));
}

int PyGreen_SetParent(PyObject* g, PyObject* nparent)
{
	if (!PyGreen_Check(g)) {
		PyErr_BadInternalCall();
		return -1;
	}
	return green_setparent((PyGreenlet*) g, nparent, NULL);
}

/***********************************************************/


static PyMethodDef green_methods[] = {
	{"switch", (PyCFunction)green_switch, METH_VARARGS, switch_doc},
	{"throw",  (PyCFunction)green_throw,  METH_VARARGS, throw_doc},
	{NULL,     NULL}		/* sentinel */
};

static PyGetSetDef green_getsets[] = {
	{"run",    (getter)green_getrun,
		   (setter)green_setrun, /*XXX*/ NULL},
	{"parent", (getter)green_getparent,
		   (setter)green_setparent, /*XXX*/ NULL},
	{"gr_frame", (getter)green_getframe,
	             NULL, /*XXX*/ NULL},
	{"dead",   (getter)green_getdead,
	             NULL, /*XXX*/ NULL},
	{NULL}
};

static PyNumberMethods green_as_number = {
	NULL,		/* nb_add */
	NULL,		/* nb_subtract */
	NULL,		/* nb_multiply */
	NULL,		/* nb_divide */
	NULL,		/* nb_remainder */
	NULL,		/* nb_divmod */
	NULL,		/* nb_power */
	NULL,		/* nb_negative */
	NULL,		/* nb_positive */
	NULL,		/* nb_absolute */
	(inquiry)green_nonzero,	/* nb_nonzero */
};

PyTypeObject PyGreen_Type = {
	PyObject_HEAD_INIT(NULL)
	0,
	"greenlet.greenlet",
	sizeof(PyGreenlet),
	0,
	(destructor)green_dealloc,		/* tp_dealloc */
	0,					/* tp_print */
	0,					/* tp_getattr */
	0,					/* tp_setattr */
	0,					/* tp_compare */
	0,					/* tp_repr */
	&green_as_number,			/* tp_as _number*/
	0,					/* tp_as _sequence*/
	0,					/* tp_as _mapping*/
	0, 					/* tp_hash */
	0,					/* tp_call */
	0,					/* tp_str */
	0,					/* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer*/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  /* tp_flags */
	"greenlet(run=None, parent=None)\n\
Create a new greenlet object (without running it).  \"run\" is the\n\
callable to invoke, and \"parent\" is the parent greenlet, which\n\
defaults to the current greenlet.",		/* tp_doc */
 	0,					/* tp_traverse */
	0,					/* tp_clear */
	0,					/* tp_richcompare */
	offsetof(PyGreenlet, weakreflist),	/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	green_methods,				/* tp_methods */
	0,					/* tp_members */
	green_getsets,				/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	(initproc)green_init,			/* tp_init */
	0,					/* tp_alloc */
	green_new,				/* tp_new */
};
/* XXX need GC support */


static PyObject* mod_getcurrent(PyObject* self)
{
	if (!STATE_OK)
		return NULL;
	Py_INCREF(ts_current);
	return (PyObject*) ts_current;
}

static PyMethodDef GreenMethods[] = {
	{"getcurrent", (PyCFunction)mod_getcurrent, METH_NOARGS,
	"greenlet.getcurrent()\n\
Returns the current greenlet (i.e. the one which called this\n\
function)."},
	{NULL,     NULL}	/* Sentinel */
};

static char* copy_on_greentype[] = {
	"getcurrent", "error", "GreenletExit", NULL
};

void initgreenlet(void)
{
	PyObject* m;
	PyObject* greenletexit_doc;
	PyObject* greenletexit_dict;
	PyObject* greenleterror_doc;
	PyObject* greenleterror_dict;
	int error;
	char** p;
	_PyGreen_switchstack = g_switchstack;
	_PyGreen_slp_switch = slp_switch;
	_PyGreen_initialstub = g_initialstub;
	m = Py_InitModule("greenlet", GreenMethods);

	ts_curkey = PyString_InternFromString("__greenlet_ts_curkey");
	ts_delkey = PyString_InternFromString("__greenlet_ts_delkey");
	if (ts_curkey == NULL || ts_delkey == NULL)
		return;
	if (PyType_Ready(&PyGreen_Type) < 0)
		return;

        greenleterror_dict = PyDict_New();
	if (greenleterror_dict == NULL)
		return;
	greenleterror_doc = PyString_FromString("internal greenlet error");
	if (greenleterror_doc == NULL) {
                Py_DECREF(greenleterror_dict);
		return;
        }

        error = PyDict_SetItemString(greenleterror_dict, "__doc__", greenleterror_doc);
	Py_DECREF(greenleterror_doc);
	if (error == -1) {
                Py_DECREF(greenleterror_dict);
		return;
        }

	PyExc_GreenletError = PyErr_NewException("py.magic.greenlet.error", NULL, greenleterror_dict);
        Py_DECREF(greenleterror_dict);
	if (PyExc_GreenletError == NULL)
		return;

        greenletexit_dict = PyDict_New();
	if (greenletexit_dict == NULL)
		return;
	greenletexit_doc = PyString_FromString("greenlet.GreenletExit\n\
This special exception does not propagate to the parent greenlet; it\n\
can be used to kill a single greenlet.\n");
	if (greenletexit_doc == NULL) {
                Py_DECREF(greenletexit_dict);
		return;
        }

        error = PyDict_SetItemString(greenletexit_dict, "__doc__", greenletexit_doc);
	Py_DECREF(greenletexit_doc);
	if (error == -1) {
                Py_DECREF(greenletexit_dict);
		return;
        }

	PyExc_GreenletExit = PyErr_NewException("py.magic.greenlet.GreenletExit",
						NULL, greenletexit_dict);
        Py_DECREF(greenletexit_dict);
	if (PyExc_GreenletExit == NULL)
		return;

	ts_current = green_create_main();
	if (ts_current == NULL)
		return;

	Py_INCREF(&PyGreen_Type);
	PyModule_AddObject(m, "greenlet", (PyObject*) &PyGreen_Type);
	Py_INCREF(PyExc_GreenletError);
	PyModule_AddObject(m, "error", PyExc_GreenletError);
	Py_INCREF(PyExc_GreenletExit);
	PyModule_AddObject(m, "GreenletExit", PyExc_GreenletExit);

	/* also publish module-level data as attributes of the greentype. */
	for (p=copy_on_greentype; *p; p++) {
		PyObject* o = PyObject_GetAttrString(m, *p);
		if (!o) continue;
		PyDict_SetItemString(PyGreen_Type.tp_dict, *p, o);
		Py_DECREF(o);
	}
}
