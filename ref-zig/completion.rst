.. _completion:

Completion
==========

Submitting successfully is not the same as completing successfully. Inspect
the CQE's tag, result and operation-specific flags. Handle short results using
the actual count, not the requested length. Retain request state until the
dependent completion is processed.

Copy and consume
----------------

``copy_cqe()`` waits for one completion if needed, returns a value and advances
CQ head. ``copy_cqes(destination, wait_nr)`` copies up to the destination capacity
and consumes the copied entries, returning the actual count. ``wait_nr = 0`` is
nonblocking. A one-element destination provides a nonblocking single-CQE check;
the result can be zero. A positive wait threshold is not a strict guarantee that
every call returns exactly that many entries: available CQEs may be copied first.
Loop using the returned count when assembling a batch.

There is no extra ``cqe_seen`` call after either copy method. Copying a CQE
does not complete some other operation or release unrelated request operands.

Borrow and acknowledge
----------------------

``cq_ready`` acquires the producer state and reports available CQEs without
consuming them. With a single CQ consumer, snapshot head and readiness, then
index ``cq.cqes`` with wrapping counter arithmetic and the ring mask. Process
only the observed available range. ``cqe_seen`` acknowledges one borrowed entry;
``cq_advance(count)`` acknowledges exactly that many processed entries.
Do not advance twice, skip unread entries or keep borrowed pointers after reuse.

This manual access is lower-level than copy methods. The executable uses a
separate batch for borrowed entries so its acknowledgement demonstration cannot
accidentally consume the copied batch twice. Shared consumers need external
synchronisation; these examples do not make arbitrary concurrent ring access safe.

Waiting with a deadline
-----------------------

``raw_ops.wait_with_timeout`` uses ``IORING_ENTER_EXT_ARG`` (Linux 5.11+) with a
relative ``kernel_timespec`` and optional ``linux.sigset_t``. It waits for CQ
availability but neither submits queued SQEs nor consumes CQEs. Submit first;
after a successful wait copy/process available entries. Timeout reports
``error.WaitTimedOut``; interruption reports ``error.WaitInterrupted``.
The caller must decide whether/how to retry. The helper's full source is in
:ref:`submission`.

Unlike historical timeout convenience wrappers, this helper creates no hidden
SQE, reserves no special user-data tag and performs no implicit submission.
A submitted ``ring.timeout`` is different: it produces a CQE whose ``res``
reports timer expiration. An enter deadline limits the wait itself. A signal
mask is installed atomically for the wait and restored afterwards; setting it
with separate calls would leave a signal race.

Delivered signals and mask restoration
--------------------------------------

``reference-signals`` starts with a private blocked ``SIGUSR1`` and sends it to
the calling thread with ``tgkill``. The pending bit is observed before entering
the wait: no sleep or concurrent sender is needed. A temporary mask that unblocks
``SIGUSR1`` produces a real handler invocation and ``error.WaitInterrupted``.
The handler records its active mask using a native syscall and lock-free atomics;
it performs no allocation or I/O. The signal itself produces **no CQE**.

The caller mask contains ``SIGUSR1``/``SIGUSR2``. Wait masks use ``SIGWINCH`` as
an extra sentinel, so exact before/after masks detect incomplete restoration.
The handler sees the temporary mask plus its automatically blocked signal;
the caller's mask is restored after the handler returns. Another pending signal
stays blocked across a deadline with a different non-null mask and then a null
mask. **Null is not an empty mask**: it leaves the caller mask in force.

A prepared NOP remains in SQ throughout both expired waits, proving the helper
does not submit it. Explicit unblocking delivers the pending signal; only an
explicit submit produces the correlated NOP CQE. The example restores the saved
kernel action and complete original mask and checks both. It uses the raw kernel
action for exact restoration because the SDK installer adds a restorer flag.
This owns ``SIGUSR1`` in a fresh process, not arbitrary application-wide handlers;
it does not establish sender races, every signal or restart policy.

.. code-block:: console

   zig build
   zig-out/bin/reference-signals
   zig-out/bin/reference-signals --ordinary

.. literalinclude:: ../examples/reference_signals.zig
   :language: zig
   :caption: Pending signals, interrupted/expired waits and exact restoration

``tests/test_signals.py`` compares the whole report with a committed symbolic
fixture resolved using Python's independent signal definitions. It checks pending
bits, handler counts/masks, both restored wait masks, original process state,
unchanged queued NOP and actual recovery CQE. It also checks exact argument errors.

Ordinary mask waits and timer CQEs
----------------------------------

``--ordinary`` uses ``linux.io_uring_enter(fd, 0, minimum, GETEVENTS, mask)``
with the basic signal-set pointer and SDK mask size, **not EXT_ARG**. A submitted
one-second timer bounds the first wait. A pending thread-directed ``SIGUSR1``
unmasked during entry invokes the handler and yields raw ``EINTR``; no signal
CQE exists. Explicit ``timeout_remove`` then produces two distinct, tag-correlated
CQEs: the timer's ``-ECANCELED`` and the remover's zero. Arrival order is not
assumed. The timespec remains alive until its timer completes.

Two more timers expire after 20 ms and one second. Both are submitted before a
NOP is prepared locally. A mask that blocks ``SIGUSR1`` waits for the first CQE;
a null mask with threshold two then waits for the second without consuming the
first. Both enters return **zero submitted entries**, not the number of CQEs.
The timer CQEs carry ``-ETIME`` although both enter syscalls succeed. Neither
wait submits the queued NOP or releases its ownership. Explicit unblocking
produces the second handler invocation; only later explicit submission produces
the NOP CQE. Original mask/action restoration remains common to both modes.

``tests/test_ordinary_signals.py`` compares five fresh-process whole reports with
an independent symbolic fixture. A syscall oracle checks all seven basic enters,
actual masks/ABI sizes/thresholds/submission counts, two self-thread signals,
handler mask queries and signal-return masks; ten damaged traces must fail.
This is a bounded current-kernel sequential contract, not concurrent sender,
SA_RESTART policy, IOPOLL, timer-cancellation races, arbitrary handlers or every
kernel/architecture assurance. Preemption past a timer deadline can invalidate
the stated intermediate-CQ plan; the test then fails, it does not silently skip.

Exact native declarations
-------------------------

.. include:: _api/completion.inc

Executable reference
--------------------

.. code-block:: console

   zig build
   zig-out/bin/reference-completion
   zig-out/bin/reference-completion 0 1 3 8 1

Optional operands are nonblocking destination capacities: at most 32 values,
each 0–8, with enough total capacity to drain eight completions. With no operands
the sequence is ``0, 1, 3, 8, 1``. The reference first fills all eight SQ slots;
a ninth NOP must return ``SubmissionQueueFull`` without changing pending count
or local SQ tail. After submission/wait makes all eight CQEs available, each
copy uses ``wait_nr = 0``. A zero-capacity copy must preserve a populated CQ.
The singleton and batch copies consume only their returned counts.

The JSON records actual readiness/head transitions and sorted copied tags
10–17, not an assumed CQ completion order. The first nine CQEs were already
consumed by earlier phases. The new phase therefore crosses the physical end
of the 16-entry CQ (head 9 to 17). This is **physical ring wrap**, not a proof
of u32 counter overflow. No producer remains active during the drain model.

.. literalinclude:: ../examples/reference_completion.zig
   :language: zig
   :caption: Copied/borrowed CQEs, both timeout models and nonblocking drain

``tests/test_reference.py`` checks the complete default report against literal
values: copied tags 1–4, separately acknowledged tags 5–8, expired enter deadline,
and timer CQE ``-62``. Model-based Hypothesis commands then vary the nonblocking
capacity sequence: ``count = min(capacity, remaining)``, readiness falls by that
count, and CQ head rises exactly once. Full-SQ rejection preserves pending/tail
state; all tags 10–17 are consumed exactly once. Invalid plans have exact errors.
The separate signal reference above covers pending delivery and mask restoration.
Neither reference establishes u32 counter wrap, multishot, CQ overflow,
SQPOLL interleavings or concurrent-consumer safety.
