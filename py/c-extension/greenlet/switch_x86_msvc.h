/*
 * this is the internal transfer function.
 *
 * HISTORY
 * 24-Nov-02  Christian Tismer  <tismer@tismer.com>
 *      needed to add another magic constant to insure
 *      that f in slp_eval_frame(PyFrameObject *f)
 *      STACK_REFPLUS will probably be 1 in most cases.
 *      gets included into the saved stack area.
 * 26-Sep-02  Christian Tismer  <tismer@tismer.com>
 *      again as a result of virtualized stack access,
 *      the compiler used less registers. Needed to
 *      explicit mention registers in order to get them saved.
 *      Thanks to Jeff Senn for pointing this out and help.
 * 17-Sep-02  Christian Tismer  <tismer@tismer.com>
 *      after virtualizing stack save/restore, the
 *      stack size shrunk a bit. Needed to introduce
 *      an adjustment STACK_MAGIC per platform.
 * 15-Sep-02  Gerd Woetzel       <gerd.woetzel@GMD.DE>
 *      slightly changed framework for sparc
 * 01-Mar-02  Christian Tismer  <tismer@tismer.com>
 *      Initial final version after lots of iterations for i386.
 */

#define alloca _alloca

#define STACK_REFPLUS 1

#ifdef SLP_EVAL

#define STACK_MAGIC 0

static int
slp_switch(void)
{
    register int *stackref, stsizediff;
    __asm mov stackref, esp;
	/* modify EBX, ESI and EDI in order to get them preserved */
	__asm mov ebx, ebx;
	__asm xchg esi, edi;
    {
        SLP_SAVE_STATE(stackref, stsizediff);
        __asm {
            mov     eax, stsizediff
            add     esp, eax
            add     ebp, eax
        }
        SLP_RESTORE_STATE();
        return 0;
    }
}

#endif

/*
 * further self-processing support
 */

/* we have IsBadReadPtr available, so we can peek at objects */
#define STACKLESS_SPY

#ifdef IMPLEMENT_STACKLESSMODULE
#include "Windows.h"
#define CANNOT_READ_MEM(p, bytes) IsBadReadPtr(p, bytes)

static int IS_ON_STACK(void*p)
{
    int stackref;
    int stackbase = ((int)&stackref) & 0xfffff000;
    return (int)p >= stackbase && (int)p < stackbase + 0x00100000;
} 

#endif
