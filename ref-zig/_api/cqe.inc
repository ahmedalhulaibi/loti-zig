.. code-block:: zig

   pub const io_uring_cqe = extern struct {
       /// io_uring_sqe.data submission passed back
       user_data: u64,

       /// result code for this event
       res: i32,
       flags: u32,

       // Followed by 16 bytes of padding if initialized with IORING_SETUP_CQE32, doubling cqe size

       pub fn err(self: io_uring_cqe) E {
           if (self.res > -4096 and self.res < 0) {
               return @as(E, @fromBackingInt(@intCast(-self.res)));
           }
           return .SUCCESS;
       }

       // On successful completion of the provided buffers IO request, the CQE flags field
       // will have IORING_CQE_F_BUFFER set and the selected buffer ID will be indicated by
       // the upper 16-bits of the flags field.
       pub fn buffer_id(self: io_uring_cqe) !u16 {
           if (self.flags & IORING_CQE_F_BUFFER != IORING_CQE_F_BUFFER) {
               return error.NoBufferSelected;
           }
           return @as(u16, @intCast(self.flags >> IORING_CQE_BUFFER_SHIFT));
       }
   };
