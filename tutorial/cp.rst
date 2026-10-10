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

The input can be a regular file or a block device, opened read-only. For a
regular file, metadata supplies its size. For a block device, the native
``BLKGETSIZE64`` ioctl returns a u64 byte count. Its request is generated with
``linux.IOCTL.IOR(0x12, 114, usize)``: Linux encodes ``size_t`` in the request
but writes a u64 result. Decode errno and retry interrupted queries. This size
query is synchronous; data transfers still use io_uring.

The initial size bounds the copy. The destination must be a regular file,
never a device. The output is opened without truncation; descriptor metadata is
checked for identical
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

``tools/check_block_devices.py`` boots an isolated x86_64 KVM guest with four
disposable, read-only virtio disks (0, 512, 33,280 and 131,584 bytes). It checks
the readers and copy against independent byte fixtures using ``cmp``. No host
storage device is passed to the VM. Use only owned test devices for experiments.
This verifies one kernel/architecture, not every device or ioctl compatibility ABI.
