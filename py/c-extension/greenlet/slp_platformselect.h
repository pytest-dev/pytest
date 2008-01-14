/*
 * Platform Selection for Stackless Python
 */

#if   defined(MS_WIN32) && !defined(MS_WIN64) && defined(_M_IX86)
#include "switch_x86_msvc.h" /* MS Visual Studio on X86 */
#elif defined(__GNUC__) && defined(__amd64__)
#include "switch_amd64_unix.h" /* gcc on amd64 */
#elif defined(__GNUC__) && defined(__i386__)
#include "switch_x86_unix.h" /* gcc on X86 */
#elif defined(__GNUC__) && defined(__PPC__) && defined(__linux__)
#include "switch_ppc_unix.h" /* gcc on PowerPC */
#elif defined(__GNUC__) && defined(__ppc__) && defined(__APPLE__)
#include "switch_ppc_macosx.h" /* Apple MacOS X on PowerPC */
#elif defined(__GNUC__) && defined(sparc) && defined(sun)
#include "switch_sparc_sun_gcc.h" /* SunOS sparc with gcc */
#elif defined(__GNUC__) && defined(__s390__) && defined(__linux__)
#include "switch_s390_unix.h"	/* Linux/S390 */
#elif defined(__GNUC__) && defined(__s390x__) && defined(__linux__)
#include "switch_s390_unix.h"	/* Linux/S390 zSeries (identical) */
#elif defined(__GNUC__) && defined(__mips__) && defined(__linux__)
#include "switch_mips_unix.h"	/* Linux/MIPS */
#endif
