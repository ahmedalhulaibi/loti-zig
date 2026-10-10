.. _link_zig:

Linking requests
================

Queue order alone does not establish an execution dependency. Set
``linux.IOSQE_IO_LINK`` on an SQE to link it to the next SQE. Leave this flag
clear on the chain's last request. This example links a write, a read and a
close; the read must observe the write before the descriptor is closed.

.. code-block:: console

   zig build
   zig-out/bin/link /tmp/loti-link.txt
   zig-out/bin/link /tmp/loti-link-failure.txt --fail-read

Success produces the complete JSON record:

.. code-block:: json

   {"results":[15,15,0],"data":"Hello, io_uring!"}

The failure run opens the file without read permission. Its write succeeds,
the read reports ``-EBADF`` and the unstarted linked close reports
``-ECANCELED``:

.. code-block:: json

   {"results":[15,-9,-125],"data":""}

The application records results by tags 1, 2 and 3 rather than assuming CQ
arrival order. A successful asynchronous close transfers closure responsibility;
if it is cancelled, deferred application cleanup still closes the descriptor.

.. literalinclude:: ../examples/link.zig
   :language: zig
   :caption: Successful and cancelled write/read/close chains

A soft link breaks on an unsuccessful result, including an unexpected short
read or write. It is not a transaction: earlier writes are not rolled back.
``IOSQE_IO_HARDLINK`` preserves a submitted chain across operation-result
failures, but cannot protect against all submission failures. Independent chains
can run concurrently. Do not confuse linking with ``IOSQE_IO_DRAIN``.

``tests/test_examples.py`` checks both complete result arrays, the returned text
and actual file bytes. The read/write/close opcodes require Linux 5.6 or later;
setup and each result remain the authoritative capability checks.
