/*
 * this is the internal transfer function.
 *
 * HISTORY
 * 24-Nov-02  Christian Tismer  <tismer@tismer.com>
 *      needed to add another magic constant to insure
 *      that f in slp_eval_frame(PyFrameObject *f)
 *      STACK_REFPLUS will probably be 1 in most cases.
 *      gets included into the saved stack area.
 * 06-Oct-02  Gustavo Niemeyer <niemeyer@conectiva.com>
 *      Ported to Linux/S390.
 */

#define STACK_REFPLUS 1

#ifdef SLP_EVAL

#define STACK_MAGIC 0

#define REGS_TO_SAVE "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r14", \
		     "f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", \
		     "f8", "f9", "f10", "f11", "f12", "f13", "f14", "f15"

static int
slp_switch(void)
{
    register int *stackref, stsizediff;
    __asm__ volatile ("" : : : REGS_TO_SAVE);
    __asm__ ("lr %0, 15" : "=g" (stackref) : );
    {
        SLP_SAVE_STATE(stackref, stsizediff);
        __asm__ volatile (
            "ar 15, %0"
            : /* no outputs */
            : "g" (stsizediff)
            );
        SLP_RESTORE_STATE();
    }
    __asm__ volatile ("" : : : REGS_TO_SAVE);
    return 0;
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
