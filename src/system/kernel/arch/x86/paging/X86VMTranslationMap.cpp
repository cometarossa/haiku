/*
 * Copyright 2008-2011, Ingo Weinhold, ingo_weinhold@gmx.de.
 * Copyright 2002-2007, Axel Dörfler, axeld@pinc-software.de. All rights reserved.
 * Distributed under the terms of the MIT License.
 *
 * Copyright 2001-2002, Travis Geiselbrecht. All rights reserved.
 * Distributed under the terms of the NewOS License.
 */


#include "paging/X86VMTranslationMap.h"

#include <KernelExport.h>
#include <string.h>

#include <thread.h>
#include <smp.h>

#include "paging/X86PagingStructures.h"


//#define TRACE_X86_VM_TRANSLATION_MAP
#ifdef TRACE_X86_VM_TRANSLATION_MAP
#	define TRACE(x...) dprintf(x)
#else
#	define TRACE(x...) ;
#endif


// AI-assisted independent research fork: opt-in cumulative diagnostics.
// Keep invalidation semantics unchanged. No logging on the hot path.
namespace {
int32 sLabEnabled = 0;
int64 sLabLocks = 0;
int64 sLabLockWaitUs = 0;
int64 sLabEmptyFlushes = 0;
int64 sLabFlushes = 0;
int64 sLabFlushUs = 0;
int64 sLabInvalidPages = 0;
int64 sLabRemoteCandidates = 0;
int64 sLabOuterLocks = 0;
int64 sLabOuterWaitUs = 0;
int64 sLabSlowWaits = 0;
int64 sLabLongWaits = 0;
int64 sLabHolds = 0;
int64 sLabHoldUs = 0;
int64 sLabSlowHolds = 0;
int64 sLabLongHolds = 0;

int
lab_vmstats(int argc, char** argv)
{
	if (argc == 2 && strcmp(argv[1], "on") == 0)
		atomic_set(&sLabEnabled, 1);
	else if (argc == 2 && strcmp(argv[1], "off") == 0)
		atomic_set(&sLabEnabled, 0);
	else if (argc != 1) {
		kprintf("usage: lab_vmstats [on|off]\n");
		return 0;
	}
	kprintf("LAB_VM enabled=%" B_PRId32 " locks=%" B_PRId64
		" lock_wait_us=%" B_PRId64 " empty_flushes=%" B_PRId64 "\n",
		atomic_get(&sLabEnabled), atomic_get64(&sLabLocks),
		atomic_get64(&sLabLockWaitUs), atomic_get64(&sLabEmptyFlushes));
	kprintf("LAB_VM flushes=%" B_PRId64 " flush_us=%" B_PRId64
		" invalid_pages=%" B_PRId64 " remote_candidates=%" B_PRId64 "\n",
		atomic_get64(&sLabFlushes), atomic_get64(&sLabFlushUs),
		atomic_get64(&sLabInvalidPages),
		atomic_get64(&sLabRemoteCandidates));
	kprintf("LAB_VM_WAIT outer=%" B_PRId64 " wait_us=%" B_PRId64
		" ge50us=%" B_PRId64 " ge1ms=%" B_PRId64 "\n",
		atomic_get64(&sLabOuterLocks), atomic_get64(&sLabOuterWaitUs),
		atomic_get64(&sLabSlowWaits), atomic_get64(&sLabLongWaits));
	kprintf("LAB_VM_HOLD samples=%" B_PRId64 " hold_us=%" B_PRId64
		" ge50us=%" B_PRId64 " ge1ms=%" B_PRId64 "\n",
		atomic_get64(&sLabHolds), atomic_get64(&sLabHoldUs),
		atomic_get64(&sLabSlowHolds), atomic_get64(&sLabLongHolds));
	return 0;
}
} // namespace


void
x86_vm_lab_stats_init()
{
	add_debugger_command("lab_vmstats", &lab_vmstats,
		"Show or enable/disable experimental user translation-map counters");
}


X86VMTranslationMap::X86VMTranslationMap()
	:
	fPageMapper(NULL),
	fInvalidPagesCount(0),
	fLabHoldStart(-1)
{
}


X86VMTranslationMap::~X86VMTranslationMap()
{
}


status_t
X86VMTranslationMap::Init(bool kernel)
{
	fIsKernelMap = kernel;
	return B_OK;
}


/*!	Acquires the map's recursive lock, and resets the invalidate pages counter
	in case it's the first locking recursion.
*/
bool
X86VMTranslationMap::Lock()
{
	TRACE("%p->X86VMTranslationMap::Lock()\n", this);

	const bool measure = atomic_get(&sLabEnabled) != 0 && !fIsKernelMap;
	const bigtime_t start = measure ? system_time() : 0;
	recursive_lock_lock(&fLock);
	const bigtime_t acquired = measure ? system_time() : 0;
	const bool outer = recursive_lock_get_recursion(&fLock) == 1;
	if (outer)
		fLabHoldStart = measure ? acquired : -1;
	if (measure) {
		const bigtime_t wait = acquired - start;
		atomic_add64(&sLabLockWaitUs, wait);
		atomic_add64(&sLabLocks, 1);
		if (outer) {
			atomic_add64(&sLabOuterLocks, 1);
			atomic_add64(&sLabOuterWaitUs, wait);
			if (wait >= 50)
				atomic_add64(&sLabSlowWaits, 1);
			if (wait >= 1000)
				atomic_add64(&sLabLongWaits, 1);
		}
	}
	if (outer) {
		// we were the first one to grab the lock
		TRACE("clearing invalidated page count\n");
		fInvalidPagesCount = 0;
	}

	return true;
}


/*!	Unlocks the map, and, if we are actually losing the recursive lock,
	flush all pending changes of this map (ie. flush TLB caches as
	needed).
*/
void
X86VMTranslationMap::Unlock()
{
	TRACE("%p->X86VMTranslationMap::Unlock()\n", this);

	if (recursive_lock_get_recursion(&fLock) == 1) {
		// we're about to release it for the last time
		Flush();
		// Only the owning thread accesses the per-map timestamp. Sample
		// through the flush, but before the underlying mutex handoff.
		if (fLabHoldStart >= 0) {
			const bigtime_t hold = system_time() - fLabHoldStart;
			fLabHoldStart = -1;
			if (atomic_get(&sLabEnabled) != 0) {
				atomic_add64(&sLabHolds, 1);
				atomic_add64(&sLabHoldUs, hold);
				if (hold >= 50)
					atomic_add64(&sLabSlowHolds, 1);
				if (hold >= 1000)
					atomic_add64(&sLabLongHolds, 1);
			}
		}
	}

	recursive_lock_unlock(&fLock);
}


addr_t
X86VMTranslationMap::MappedSize() const
{
	return fMapCount;
}


void
X86VMTranslationMap::Flush()
{
	const bool measure = atomic_get(&sLabEnabled) != 0 && !fIsKernelMap;
	if (fInvalidPagesCount <= 0) {
		if (measure)
			atomic_add64(&sLabEmptyFlushes, 1);
		return;
	}

	Thread* thread = thread_get_current_thread();
	thread_pin_to_current_cpu(thread);

	const bigtime_t start = measure ? system_time() : 0;
	const int invalidPages = fInvalidPagesCount;
	if (measure) {
		// Snapshot only; the actual invalidation path reads its own mask.
		CPUSet cpus = PagingStructures()->active_on_cpus;
		cpus.ClearBit(smp_get_current_cpu());
		if (!cpus.IsEmpty())
			atomic_add64(&sLabRemoteCandidates, 1);
	}

	if (fInvalidPagesCount > PAGE_INVALIDATE_CACHE_SIZE) {
		// invalidate all pages
		TRACE("flush_tmap: %d pages to invalidate, invalidate all\n",
			fInvalidPagesCount);

		if (fIsKernelMap) {
			smp_broadcast_ici(SMP_MSG_GLOBAL_INVALIDATE_PAGES, 0, 0, 0,
				NULL, SMP_MSG_FLAG_SYNC);
		} else {
			InvalidateUserTLB(PagingStructures()->active_on_cpus, x86_read_cr3());
		}
	} else {
		TRACE("flush_tmap: %d pages to invalidate, invalidate list\n",
			fInvalidPagesCount);

		if (fIsKernelMap) {
			smp_broadcast_ici(SMP_MSG_INVALIDATE_PAGE_LIST,
				0, (addr_t)fInvalidPages, fInvalidPagesCount, NULL,
				SMP_MSG_FLAG_SYNC);
		} else {
			InvalidateTLBList(PagingStructures()->active_on_cpus, x86_read_cr3(),
				fInvalidPages, fInvalidPagesCount);
		}
	}
	fInvalidPagesCount = 0;

	if (measure) {
		atomic_add64(&sLabFlushUs, system_time() - start);
		atomic_add64(&sLabInvalidPages, invalidPages);
		atomic_add64(&sLabFlushes, 1);
	}
	thread_unpin_from_current_cpu(thread);
}
