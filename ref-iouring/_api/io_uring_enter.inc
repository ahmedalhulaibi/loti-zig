.. code-block:: zig

   pub fn io_uring_enter(fd: fd_t, to_submit: u32, min_complete: u32, flags: u32, sig: ?*sigset_t) usize
