.. _link_zig:

Linking requests
================

Queue order alone does not establish an execution dependency. Set
``linux.IOSQE_IO_LINK`` to link to the next SQE within one submission. Leave the
flag clear on the last request and submit the whole chain in one batch. This
example links a write, a read and a close; the read observes the write before close.

.. code-block:: console

   zig build
   zig-out/bin/link /tmp/loti-link.txt
   zig-out/bin/link /tmp/loti-link-failure.txt --fail-read

Success produces the complete JSON record:

.. code-block:: json

   {"results":[16,16,0],"data":"Hello, io_uring!"}

The failure run opens the file without read permission. Its write succeeds,
the read reports ``-EBADF`` and the unstarted linked close reports
``-ECANCELED``:

.. code-block:: json

   {"results":[16,-9,-125],"data":""}

The application records results by tags 1, 2 and 3 rather than assuming CQ
arrival order. A successful asynchronous close transfers closure responsibility;
if it is cancelled, deferred application cleanup still closes the descriptor.

.. literalinclude:: ../examples/link.zig
   :language: zig
   :caption: Successful and cancelled write/read/close chains

A soft link breaks on an unsuccessful result, including an unexpected short
read or write. It is not a transaction: earlier writes are not rolled back.
``IOSQE_IO_HARDLINK`` preserves a chain across operation-result failures. SQE
validation/initialization failures can still break it, even after a positive
submit return. Independent chains can run concurrently; ``IOSQE_IO_DRAIN`` differs.

``tests/test_examples.py`` checks both complete result arrays, the returned text
and actual file bytes. The read/write/close opcodes require Linux 5.6 or later;
setup and each result remain the authoritative capability checks.
``tests/test_link_ownership.py`` checks descriptor state before report publication
using an owned full stdout pipe; syscall traces check application cleanup after
a cancelled close. ``tests/test_link_prose.py`` checks complete publisher/archive
JSON records against the original and native 16-byte message contract.
