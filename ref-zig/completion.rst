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
These checks do not establish delivered signals/mask restoration, u32 counter
wrap, multishot, CQ overflow, SQPOLL interleavings or concurrent-consumer safety.
