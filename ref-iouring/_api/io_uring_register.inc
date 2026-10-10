.. code-block:: zig

   pub fn io_uring_register(fd: fd_t, opcode: IORING_REGISTER, arg: ?*const anyopaque, nr_args: u32) usize
