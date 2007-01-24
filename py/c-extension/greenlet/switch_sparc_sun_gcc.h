/*
 * this is the internal transfer function.
 *
 * HISTORY
 * 24-Nov-02  Christian Tismer  <tismer@tismer.com>
 *      needed to add another magic constant to insure
 *      that f in slp_eval_frame(PyFrameObject *f)
 *      STACK_REFPLUS will probably be 1 in most cases.
 *      gets included into the saved stack area.
 * 17-Sep-02  Christian Tismer  <tismer@tismer.com>
 *      after virtualizing stack save/restore, the
 *      stack size shrunk a bit. Needed to introduce
 *      an adjustment STACK_MAGIC per platform.
 * 15-Sep-02  Gerd Woetzel       <gerd.woetzel@GMD.DE>
 *      added support for SunOS sparc with gcc
 */

#define STACK_REFPLUS 1

#ifdef SLP_EVAL

#include <sys/trap.h>

#define STACK_MAGIC 0

static int
slp_switch(void)
{
    register int *stackref, stsizediff;

    /* Put the stack pointer into stackref */

    /* Sparc special: at first, flush register windows
     */
    __asm__ volatile (
        "ta %1\n\t"
        "mov %%sp, %0"
        : "=r" (stackref) :  "i" (ST_FLUSH_WINDOWS));

    {   /* You shalt put SLP_SAVE_STATE into a local block */

        SLP_SAVE_STATE(stackref, stsizediff);

        /* Increment stack and frame pointer by stsizediff */

        /* Sparc special: at first load new return address.
           This cannot be done later, because the stack
           might be overwritten again just after SLP_RESTORE_STATE
           has finished. BTW: All other registers (l0-l7 and i0-i5)
           might be clobbered too. 
         */
        __asm__ volatile (
        "ld [%0+60], %%i7\n\t"
        "add %1, %%sp, %%sp\n\t"
        "add %1, %%fp, %%fp"
        : : "r" (_cst->stack), "r" (stsizediff)
        : "%l0", "%l1", "%l2", "%l3", "%l4", "%l5", "%l6", "%l7",
          "%i0", "%i1", "%i2", "%i3", "%i4", "%i5");

        SLP_RESTORE_STATE();

        /* Run far away as fast as possible, don't look back at the sins.
         * The LORD rained down burning sulfur on Sodom and Gomorra ...
         */

        /* Sparc special: Must make it *very* clear to the CPU that
           it shouldn't look back into the register windows
         */
        __asm__ volatile ( "ta %0" : : "i" (ST_CLEAN_WINDOWS));
        return 0;
    } 
}

#endif

/*
 * further self-processing support
 */

/*
 * if you want to add self-inspection tools, place them
 * here. See the x86_msvc for the necessary defines.
 * These features are highly experimental und not
 * essential yet.
 */
