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

The program emits one JSON record for each ``linux.IORING_OP`` enum member,
with the numeric opcode, name and boolean support value. It derives names from
the exact Zig 0.17.0 enum rather than a manually synchronised string array.
Kernel-version-specific sample output would be misleading, so run the program
on the target machine.

.. literalinclude:: ../examples/probe.zig
   :language: zig
   :caption: Runtime opcode probe

``tests/test_examples.py`` parses the complete record stream and checks numeric
identity, uniqueness and known basic operations. A positive probe does not prove
that a particular descriptor, filesystem, flag combination or security policy
permits the operation. Always inspect the actual request's CQE.

See :ref:`supported_caps` for the native probe types, standalone helper and raw
registration interface. Setup can itself be disabled by a container or host
policy; such a failure is not a negative per-opcode probe result.
