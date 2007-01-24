
/* Greenlet object interface */

#ifndef Py_GREENLETOBJECT_H
#define Py_GREENLETOBJECT_H
#ifdef __cplusplus
extern "C" {
#endif

#include <Python.h>

typedef struct _greenlet {
	PyObject_HEAD
	char* stack_start;
	char* stack_stop;
	char* stack_copy;
	long stack_saved;
	struct _greenlet* stack_prev;
	struct _greenlet* parent;
	PyObject* run_info;
	struct _frame* top_frame;
	int recursion_depth;
	PyObject* weakreflist;
} PyGreenlet;

extern PyTypeObject PyGreen_Type;

#define PyGreen_Check(op)      PyObject_TypeCheck(op, &PyGreen_Type)
#define PyGreen_STARTED(op)    (((PyGreenlet*)(op))->stack_stop != NULL)
#define PyGreen_ACTIVE(op)     (((PyGreenlet*)(op))->stack_start != NULL)
#define PyGreen_GET_PARENT(op) (((PyGreenlet*)(op))->parent)

PyObject* PyGreen_New(PyObject* run, PyObject* parent);
PyObject* PyGreen_Current(void);
PyObject* PyGreen_Switch(PyObject* g, PyObject* args);  /* g.switch(*args) */
int PyGreen_SetParent(PyObject* g, PyObject* nparent);  /* g.parent = ... */

#ifdef __cplusplus
}
#endif
#endif /* !Py_GREENLETOBJECT_H */
