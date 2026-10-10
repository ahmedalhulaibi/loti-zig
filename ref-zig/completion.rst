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

.. literalinclude:: ../examples/reference_completion.zig
   :language: zig
   :caption: Copied CQEs, separately borrowed CQEs and both timeout models

``tests/test_reference.py`` checks an empty nonblocking read, pending SQ count,
tags 1–4 copied/consumed, tags 5–8 manually acknowledged, an empty final CQ, an
expired enter deadline, and the actual timer CQE result ``-62`` (``-ETIME``).
The check does not establish multishot, CQ overflow or concurrent-consumer safety.
