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
helper and the Zig 0.17.0 wrapper both require ``IORING_FEAT_SINGLE_MMAP``.
``RawRing.dontFork`` applies ``MADV_DONTFORK`` to both ring and SQE
mappings. It does not prevent descriptor inheritance or make shared-ring use
after a fork safe. See :ref:`low_level` for its complete implementation.

Executable reference
--------------------

.. code-block:: console

   zig build
   zig-out/bin/reference-setup input.bin

.. literalinclude:: ../examples/reference_setup.zig
   :language: zig
   :caption: Enlarged CQ, native sizes and separate raw mapping

``tests/test_reference.py`` verifies SQ 8, CQ 32, SQE 64 and CQE 16 on the
verification host, plus the input's actual read count. ``dontFork`` is invoked,
not merely declared; the test does not fork a child to inspect its address map.
Mapping support or permissions can differ on another host.
