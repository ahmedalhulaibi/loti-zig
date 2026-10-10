.. _sqe:

SQE: submission queue entry
===========================

``linux.io_uring_sqe`` is an ``extern struct`` with the Linux ABI layout.
The ordinary SQE occupies 64 bytes; do not assume this stride for an SQE128 ring.
The native definition below shows fields, without its preparation methods.
Use the installed type rather than redeclaring it in application code.

.. include:: _api/sqe.inc

``opcode`` is a ``linux.IORING_OP`` enum; ``flags`` is the u8 SQE flag bitmap.
``ioprio`` selects I/O priority where supported. ``fd`` normally holds a process
descriptor; with ``IOSQE_FIXED_FILE`` it holds a registered-table index.
``user_data`` is an application u64 tag copied back unchanged in the CQE.

``off``, ``addr``, ``len`` and ``rw_flags`` are operation-dependent ABI storage,
not universal read/write parameters. Zig uses these fields for the overlapping
Linux unions. For example, ``rw_flags`` holds fsync, socket, timeout or advice
flags according to the opcode. ``buf_index`` also carries a provided-buffer
group when buffer selection is enabled. ``personality`` selects registered
credentials; zero uses the normal credentials. ``splice_fd_in`` is splice's
input descriptor. The additional fields preserve the current ABI layout.

Prefer ``IoUring`` constructors for supported operations. They acquire a slot,
initialise operands and set the tag. Native SQE preparers initialise fields but
do not acquire a slot, submit, or retain your application storage. Preparation
can clear fields, so set extra flags and personality **after** preparation.
Assigning ``sqe.flags`` replaces all bits; ``|=`` preserves constructor-set bits.

Pointers encoded in an SQE do not transfer ownership. Keep buffers, vectors,
paths, socket addresses, message headers and output structures valid until the
dependent operation completes. The submitted SQE slot itself becomes reusable
when the kernel consumes it; that does not release its referenced storage.

See :ref:`submission` for every converted operation constructor and the executed
32-constructor reference. See :ref:`io_uring_enter` for queue publication and
flag semantics. ``reference-setup`` verifies the ordinary SQE size at runtime.
