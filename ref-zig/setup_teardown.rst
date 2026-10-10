.. _setup_and_tear_down:

Setup and teardown
==================

``IoUring`` owns its ring descriptor and mappings. ``ring.sq`` is a native
``IoUring.SubmissionQueue`` and ``ring.cq`` a native
``IoUring.CompletionQueue``. They hold mapped entries, pointers to shared queue
indices/masks/flags and wrapper-local state. They are not kernel parameter
structures and should not be recreated from historical wrapper layouts.
Keep one explicit owner; copying the Zig value does not duplicate the resources.

Native interfaces
-----------------

.. include:: _api/setup_teardown.inc

``IoUring.init(entries, flags)`` returns an owned value or a Zig error. The
wrapper takes a nonzero power-of-two ``u16`` queue size. ``init_params`` accepts
caller-owned ``linux.io_uring_params`` so flags, SQ thread configuration and
CQ sizing can be supplied. Zero reserved fields. The kernel fills actual queue
sizes, features and mapping offsets. See :ref:`io_uring_setup` for those fields.

Use ``defer ring.deinit()`` after successful setup. Teardown unmaps queues and
closes the ring descriptor. It does not release your application-owned files or
buffers for you. Finish dependent operations, or cancel and drain them, before
destroying referenced application memory. Do not infer safe operand release
merely from scope exit while requests remain in flight.

Separate setup and mapping
--------------------------

There is no public ``IoUring.queue_mmap`` method. The repository's
``RawRing.map(fd, params)`` maps an already-created ring and takes descriptor
ownership on success. The caller must close it on mapping failure. This teaching
helper selects two or three mappings from ``IORING_FEAT_SINGLE_MMAP``; the SDK
wrapper still requires the bit. ``RawRing.dontFork`` applies ``MADV_DONTFORK`` to
every owned ring and SQE
mappings. It does not prevent descriptor inheritance or make shared-ring use
after a fork safe. See :ref:`low_level` for its complete implementation.

Executable reference
--------------------

.. code-block:: console

   zig build
   zig-out/bin/reference-setup input.bin
   zig-out/bin/reference-setup input.bin --separate-mappings

.. literalinclude:: ../examples/reference_setup.zig
   :language: zig
   :caption: Enlarged CQ, native sizes and separate raw mapping

The reference uses SDK SQ 8/CQ 32 and raw SQ 8/CQ 512, with ordinary SQE 64/CQE
16 sizes. Both mapping modes complete 1,025 alternating reads: 64 bytes at offset
0, then 31 bytes at offset 64. Output is one JSON line (counts, SHA-256 and checks)
followed by the final offset-zero prefix. The test checks the whole report and
prefix against an independent byte/hash oracle; variable lengths expose stale
CQ slot reads that a constant-length test can miss.

``mincore`` checks every owned page before fork, in the child after DONTFORK,
and after teardown. The child uses only raw syscalls; it also verifies that the
ring descriptor is inherited, then exits without using the ring. The parent
waits for it and verifies descriptor closure after teardown.

Forced separate mode changes only local feature metadata; all mappings and I/O
are real. Current kernels can share physical backing between these distinct
virtual regions, so CQ pointer-origin checks also reject accidental SQ-base
aliases. This tests the strategy, not historical-kernel compatibility or injected
partial-construction failures. Mapping/fork permissions can differ by host.
