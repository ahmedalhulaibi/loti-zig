.. code-block:: zig

   pub const io_sqring_offsets = extern struct {
       /// offset of ring head
       head: u32,

       /// offset of ring tail
       tail: u32,

       /// ring mask value
       ring_mask: u32,

       /// entries in ring
       ring_entries: u32,

       /// ring flags
       flags: u32,

       /// number of sqes not submitted
       dropped: u32,

       /// sqe index array
       array: u32,

       resv1: u32,
       user_addr: u64,
   };

.. code-block:: zig

   pub const io_cqring_offsets = extern struct {
       head: u32,
       tail: u32,
       ring_mask: u32,
       ring_entries: u32,
       overflow: u32,
       cqes: u32,
       flags: u32,
       resv: u32,
       user_addr: u64,
   };
