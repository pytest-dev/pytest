/*
 * this is the internal transfer function.
 *
 * HISTORY
 * 01-Apr-04  Hye-Shik Chang    <perky@FreeBSD.org>
 *      Ported from i386 to amd64.
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
 *      slightly changed framework for spark
 * 31-Avr-02  Armin Rigo         <arigo@ulb.ac.be>
 *      Added ebx, esi and edi register-saves.
 * 01-Mar-02  Samual M. Rushing  <rushing@ironport.com>
 *      Ported from i386.
 */

#define STACK_REFPLUS 1

#ifdef SLP_EVAL

/* #define STACK_MAGIC 3 */
/* the above works fine with gcc 2.96, but 2.95.3 wants this */
#define STACK_MAGIC 0

#define REGS_TO_SAVE "rdx", "rbx", "r12", "r13", "r14", "r15"


static int
slp_switch(void)
{
    register long *stackref, stsizediff;
    __asm__ volatile ("" : : : REGS_TO_SAVE);
    __asm__ ("movq %%rsp, %0" : "=g" (stackref));
    {
        SLP_SAVE_STATE(stackref, stsizediff);
        __asm__ volatile (
            "addq %0, %%rsp\n"
            "addq %0, %%rbp\n"
            :
            : "r" (stsizediff)
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
