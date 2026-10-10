.. _cat_zig:

``cat`` with Zig's native ring
==============================

The :ref:`raw reader <low_level>` exposes setup, mappings and queue publication.
``std.os.linux.IoUring`` owns that machinery. The application still owns its
descriptors, buffers and completion handling. This example needs neither libc
nor an external ring library.

Run it
------

.. code-block:: console

   zig build
   zig-out/bin/cat first.txt second.txt > combined.txt

Files are processed in argument order. Empty files contribute no bytes. Output
is binary-safe: no zero terminator or character encoding is required.

Submission and completion
-------------------------

Two 2048-byte arrays form a scatter-read destination. ``std.posix.iovec`` uses
``base`` and ``len`` fields. Call ``ring.read`` with the ``.iovecs`` variant of
``IoUring.ReadBuffer`` to prepare a ``READV`` request. There is no ``ring.readv``
method in Zig 0.17.0. The constructor returns an SQE and sets its ``user_data``
tag; ``ring.submit()`` publishes it.

``ring.copy_cqe()`` waits if necessary, returns a value and advances the CQ.
Do not call ``cqe_seen`` on that value. Verify the tag, decode a negative result,
and print only the completed byte count. A short read advances the file offset
by its actual count. A zero result ends the file. Interrupted or temporarily
unavailable operations are resubmitted at the same offset.

This bounded reader avoids the original whole-file allocation and block-device
size query. It reads seekable inputs until EOF. It is not a pipe/stdin reader;
explicit file offsets are used. It queues one operation at a time, so it teaches
the ring interface rather than throughput optimisation.

Complete source
---------------

.. literalinclude:: ../examples/cat.zig
   :language: zig
   :caption: Vectored reader, compiled with Zig 0.17.0

The shared ``support.completedBytes`` rejects operation errors;
``support.output`` handles short synchronous stdout writes. See
:ref:`native submission <submission>` and :ref:`native completion <completion>`.

Verification
------------

``tests/test_examples.py`` compares whole output bytes for all three readers
(``readv``, ``raw-cat`` and ``cat``), including generated binary inputs and
multiple-file argument order. The compiled source above is the tested source.
