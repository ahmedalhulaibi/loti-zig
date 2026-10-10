.. code-block:: zig

   pub const io_uring_sqe = extern struct {
       opcode: linux.IORING_OP,
       flags: u8,
       ioprio: u16,
       fd: i32,
       off: u64,
       addr: u64,
       len: u32,
       rw_flags: u32,
       user_data: u64,
       buf_index: u16,
       personality: u16,
       splice_fd_in: i32,
       addr3: u64,
       resv: u64,
   };
