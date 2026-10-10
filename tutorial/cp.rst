.. _cp_zig:

Pipelined copying
=================

The :ref:`reader <cat_zig>` has one outstanding request. A copy can overlap a
read for one range with a write for another. This example keeps two stable
16-KiB slots and submits a batch when work is available. Its origin is Shuveb
Hussain's tutorial, based on the
`fio copying example <https://github.com/axboe/fio/blob/master/t/io_uring.c>`_.
The implementation here is native Zig 0.17.0.

.. code-block:: console

   zig build
   zig-out/bin/cp source.bin destination.bin
   cmp source.bin destination.bin

State machine
-------------

Each ``Slot`` moves through ``idle -> reading -> writing -> idle``. Its offset,
length and completed count describe one file range. Tag ``id + 1`` maps a CQE
back to the stable slot; no heap-allocated application pointer is returned.
Completions can arrive in any order. Never associate them by arrival position.

A read fills the slot before a write starts. Partial operations update ``done``
and queue only the remaining bytes at ``offset + done``. ``INTR`` and ``AGAIN``
retry without advancing. Zero progress before the range is complete is an error,
not an invitation to loop forever. A slot is reusable only after its entire
write completes. ``copy_cqe`` consumes every processed completion automatically.

The input must be a regular file. Its initial size bounds the copy. The output
is opened without truncation; descriptor metadata is checked for identical
device/inode identity before its length is set to zero. This rejects the same
pathname and hard-link aliases without destroying the source. An empty source
still truncates a distinct destination.

Complete source
---------------

.. literalinclude:: ../examples/cp.zig
   :language: zig
   :caption: Two-slot asynchronous copy

Limits and verification
-----------------------

``tests/test_examples.py`` checks whole destination bytes with generated binary
inputs and rejects same-file aliases while verifying that the source remains
unchanged. This is not a metadata-preserving copy, crash-safe replacement or
atomic snapshot. Concurrent source changes can cause a failure or mixed content.
There is no final ``fsync``; completion of writes does not prove durable storage.
See :ref:`submission` for ordering a durability request after dependent writes.
