.. _fixed_buffers:

Fixed buffers
=============

Register stable memory with ``ring.register_buffers(iovecs)`` before preparing
``read_fixed`` or ``write_fixed`` requests. ``std.posix.iovec`` describes each
range by its base address and length. The fixed-operation index selects a range
from this registered table; the submitted address and length must fit inside it.

Registration pins/references memory and reduces repeated mapping overhead. It
does **not** generally eliminate data copies, make buffered I/O zero-copy, or
make an unaligned buffer suitable for direct I/O. Account for memory-lock limits
and the target kernel's registration rules.

.. code-block:: console

   zig build
   zig-out/bin/fixed-buffers /tmp/loti-fixed.txt

The program registers four 512-byte buffers. Indices 0 and 1 supply two writes;
indices 2 and 3 receive the corresponding reads after both writes complete.
Requests use the actual text lengths rather than all 512 bytes. Tags correlate
the two completions in each batch, and duplicate tags or short results fail.
The output is these lines from W. H. Davies's
`Leisure <https://en.wikipedia.org/wiki/Leisure_(poem)>`_:

.. code-block:: text

   What is this life if, full of care,
   We have no time to stand and stare.

Complete source
---------------

.. literalinclude:: ../examples/fixed_buffers.zig
   :language: zig
   :caption: Four registered ranges, two writes and two reads

The buffer storage does not move while registered. Keep it valid through every
dependent completion and unregister before reusing or freeing it. On the normal
path the example explicitly unregisters; ring teardown releases registration on
an error path. ``tests/test_examples.py`` checks both stdout and whole file bytes.

Fixed buffers are not fixed files. The former select memory by ``buf_index``;
the latter select a descriptor by SQE ``fd`` plus ``IOSQE_FIXED_FILE``. See
:ref:`advanced_usage` and :ref:`io_uring_register` for both registration contracts.
