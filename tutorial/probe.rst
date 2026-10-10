.. _probing_zig:

Probing supported capabilities
==============================

An installed Zig opcode name does not prove kernel support. Create a ring and
call ``ring.get_probe()``. The returned ``linux.io_uring_probe`` is a value;
``probe.is_supported(op)`` checks the kernel's advertised support flag. There is
no allocation to free. Linux introduced opcode probing in 5.6.

.. code-block:: console

   zig build
   zig-out/bin/probe
   zig-out/bin/probe --raw > probe.bin
   zig-out/bin/probe --snapshot probe.bin

The program emits one JSON record for each ``linux.IORING_OP`` enum member,
with the numeric opcode, name and boolean support value. It derives names from
the exact Zig 0.17.0 enum rather than a manually synchronised string array.
Kernel-version-specific sample output would be misleading, so run the program
on the target machine.

``--raw`` uses direct native setup/registration without the SDK probe wrapper or
queue mappings. It writes a zero-initialised 2,064-byte Linux probe ABI response:
a 16-byte header and 256 eight-byte entries. The kernel reports the valid count;
unused entries are not capabilities. Ring ownership still ends with close.

``--snapshot`` reads one exact-size regular file and uses the SDK's same lookup
and listing path without querying a live ring. Snapshots use **native byte order**;
they are not a portable archive format. Synthetic snapshots can exercise absent
support bits and inconsistent bounds; they are not claims about a live kernel.
Always keep both ``last_op`` and ``ops_len`` bounds as well as support bit 0.

.. literalinclude:: ../examples/probe.zig
   :language: zig
   :caption: Runtime opcode probe

``tests/test_examples.py`` checks every SDK-named opcode against an independently
decoded raw kernel response. It pins all 59 Zig 0.17.0 names and checks mixed-flag
fixtures plus generated header/flag snapshots against literal ABI offsets and
bit 0. This matters because all named operations are advertised on the test
kernel: a hardcoded ``true`` would pass a live-only check. Snapshot tests do not
prove operation effects. Neither does a positive kernel probe prove that a
particular descriptor, filesystem, flag combination or security policy permits
the operation. Always inspect the actual request's CQE.

See :ref:`supported_caps` for the native probe types, standalone helper and raw
registration interface. Setup can itself be disabled by a container or host
policy; such a failure is not a negative per-opcode probe result.
