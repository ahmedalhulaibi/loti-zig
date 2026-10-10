.. code-block:: zig

   pub const io_uring_params = extern struct {
       sq_entries: u32,
       cq_entries: u32,
       flags: u32,
       sq_thread_cpu: u32,
       sq_thread_idle: u32,
       features: u32,
       wq_fd: u32,
       resv: [3]u32,
       sq_off: io_sqring_offsets,
       cq_off: io_cqring_offsets,
   };
