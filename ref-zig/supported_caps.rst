.. _supported_caps:

Supported capabilities
======================

``IoUring.get_probe`` asks the running kernel which operation codes it supports.
It returns a fixed-capacity ``linux.io_uring_probe`` value, not a heap allocation.
Its ``ops`` array holds 256 ``linux.io_uring_probe_op`` entries; use ``ops_len``
and ``is_supported`` rather than interpret unused entries as capabilities.
The helper checks the reported last opcode, returned array length and
``IO_URING_OP_SUPPORTED`` flag. Linux introduced probing in 5.6.

.. include:: _api/probe_types.inc

Native interfaces
-----------------

.. include:: _api/supported_caps.inc

``ring.get_probe()`` uses an existing ring. ``raw_ops.probe()`` creates and
destroys a temporary ring and returns the probe value. ``raw_ops.register_probe``
zeros caller-owned storage and invokes raw registration on an existing ring;
it is not an ``IoUring.register_probe`` method. Keep the output valid for the
duration of the synchronous call. No foreign allocator or ``free`` is involved.

Use ``probe.is_supported(.READ)`` to test a native opcode. The boolean is not a
promise that all operands, flags, filesystems, credentials or host policies will
work. Check setup errors and actual CQEs. A version string is useful context,
not a substitute for probing and operation results.

Examples and verification
-------------------------

The :ref:`probe tutorial <probing_zig>` includes the complete listing program.
``reference-registration`` also executes the caller-owned and temporary-ring
probe paths and checks NOP support. Their sources are compiled by ``zig build``
and consumed by boundary tests. Probe results vary legitimately by kernel.

The tutorial's ``--raw`` path queries a separate unmapped ring into byte storage,
not ``linux.io_uring_probe``. Boundary tests independently decode its header and
all returned opcode/flag entries, then compare every listed SDK opcode. Snapshot
fixtures/PBT also cover false support bits, unrelated flags, and both header
bounds. These validate the listing/lookup contract, not successful operation
execution or every possible kernel policy.
