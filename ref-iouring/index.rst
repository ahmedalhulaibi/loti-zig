Linux syscall reference
=======================

These Linux ABI entry points are exposed by ``std.os.linux``. Unlike Zig's
``IoUring`` methods, raw syscalls return errno-encoded ``usize`` values. Decode
with ``linux.errno(result)`` before casting a successful descriptor or count.
They do not set a libc ``errno`` variable or return a Zig error union.

.. toctree::
   :maxdepth: 1

   io_uring_setup
   io_uring_enter
   io_uring_register
