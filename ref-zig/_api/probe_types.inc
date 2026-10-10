.. code-block:: zig

   pub const io_uring_probe = extern struct {
       /// Last opcode supported
       last_op: IORING_OP,
       /// Length of ops[] array below
       ops_len: u8,
       resv: u16,
       resv2: [3]u32,
       ops: [256]io_uring_probe_op,

       /// Is the operation supported on the running kernel.
       pub fn is_supported(self: @This(), op: IORING_OP) bool {
           const i = @backingInt(op);
           if (i > @backingInt(self.last_op) or i >= self.ops_len)
               return false;
           return self.ops[i].is_supported();
       }
   };

.. code-block:: zig

   pub const io_uring_probe_op = extern struct {
       op: IORING_OP,
       resv: u8,
       /// IO_URING_OP_* flags
       flags: u16,
       resv2: u32,

       pub fn is_supported(self: @This()) bool {
           return self.flags & IO_URING_OP_SUPPORTED != 0;
       }
   };
