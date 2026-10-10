.. _low_level:

The low-level io_uring interface
========================================

This chapter uses native Zig 0.17.0 Linux declarations and explicit shared-ring
operations. It submits one read at a time to make ownership and memory ordering
visible. It is a teaching implementation, not a replacement for the standard
``IoUring`` wrapper.

Build the repository with ``zig build``. Run these programs on Linux:

.. code-block:: console

   zig version
   zig build
   zig-out/bin/readv input.bin
   zig-out/bin/raw-cat input.bin second.bin

The compiler version must be exactly ``0.17.0``. The complete build graph also
compiles the reference programs. Restricted io_uring setup is an execution
blocker, not a successful example run.

Scatter reads first
-------------------

``readv`` fills an array of ``std.posix.iovec`` ranges in sequence. Each range
has a mutable byte pointer and a length. A successful call can fill only part of
the combined capacity; zero bytes means end of input. Never print every allocated
byte merely because a buffer exists.

The synchronous program establishes the byte-preservation contract before
introducing ring publication. It streams through two 2048-byte ranges, retries
interrupted calls and writes exactly the returned count.

.. literalinclude:: examples/readv.zig
   :language: zig
   :caption: Complete synchronous scatter-read program

``std.posix`` here supplies native ABI declarations. It does not import foreign
headers or require a system runtime library. Output uses Zig 0.17.0's
``std.Io.File`` writer and explicitly flushes its buffered interface.

Submission and completion types
-------------------------------

Use ``std.os.linux.io_uring_sqe`` and ``std.os.linux.io_uring_cqe``. Do not copy an
old handwritten layout. In this edition's ordinary ring configuration an SQE is
64 bytes and a CQE is 16 bytes; ``reference-setup`` verifies those sizes.

For ``.READV``, the SQE records a descriptor, the vector-array address, vector
count and absolute file offset. ``prep_readv`` initializes the native structure.
The application supplies ``user_data`` as a ``u64`` tag.

A CQE returns that tag, ``res: i32`` and ``flags: u32``. A read result is a byte
count, not a buffer capacity. Negative results encode Linux errors;
``cqe.err()`` decodes them. Independent requests need independent tags because
completion order is not guaranteed.

Setup and mappings
------------------

``RawRing.init`` zeroes ``linux.io_uring_params`` and calls
``linux.io_uring_setup``. Raw syscall results use errno-encoded ``usize``;
``linux.errno`` distinguishes a descriptor from failure. Check before casting.

The kernel returns SQ/CQ sizes and byte offsets. ``RawRing.map`` computes the
larger ring-control size, maps it at ``IORING_OFF_SQ_RING``, and maps the separate
SQE array at ``IORING_OFF_SQES``. It derives aligned pointers from the returned
offsets, not assumed offsets. The SQ index array and CQ entry array are different
objects.

This implementation explicitly requires ``IORING_FEAT_SINGLE_MMAP``. It does
not claim support for the separate-mapping fallback on earlier kernels. Ring
creation success transfers descriptor ownership; failed construction closes the
unowned descriptor. ``deinit`` releases both mappings and the descriptor.

``reference-setup input.bin`` also maps an existing setup descriptor, applies
``MADV_DONTFORK`` to both ranges and completes an actual read. Preventing mapping
inheritance does not make sharing a live ring across fork boundaries safe.

Publishing an SQE
-----------------

The application owns SQ tail; the kernel owns SQ head. Read the kernel's head
with acquire ordering before reusing a slot. Use wrapping ``u32`` subtraction
to check capacity and ``tail & mask`` to select a slot. Counters are monotonically
advancing modulo their integer width; they are not reset at the ring boundary.

Prepare the SQE and write its index into ``sq_array`` **before** publishing the
new tail with ``@atomicStore(..., .release)``. The kernel must not observe a
new tail and then an incompletely initialized request. A compiler-only barrier
or a CPU-specific assembly macro is not a portable substitute.

Reading a CQE
-------------

The kernel owns CQ tail; the application owns CQ head. Acquire-load tail before
reading the corresponding entry. If head equals tail, no result is available.
Otherwise copy the entry at ``head & mask`` and release-store the advanced head.
That final update returns the slot to the kernel.

A copied result remains usable after acknowledgement because it is an ordinary
Zig value. A pointer into the shared ring does not: the kernel may overwrite its
slot. The raw program copies and consumes exactly once.

When no completion is ready, ``linux.io_uring_enter`` submits pending entries and
waits with ``IORING_ENTER_GETEVENTS``. An interrupted wait is retried. The request
buffer and vector array stay in scope throughout the operation.

Complete raw reader
-------------------

.. literalinclude:: examples/raw_cat.zig
   :language: zig
   :caption: Setup, mapping, atomic publication and completed-byte output

The fixed working buffers remove whole-file allocation and size-query logic.
The program increments its offset by the **actual** completed count and reads
until EOF. Regular-file byte preservation, empty inputs, binary inputs and
ring-slot reuse are exercised at the CLI boundary. Block-device behaviour is
not independently verified by that regular-file test corpus.

The ring has eight SQ slots but this example has only one outstanding operation.
A deeper queue alone does not create concurrent I/O. The copy tutorial shows
multiple independently correlated requests; the linked tutorial shows dependency
ordering rather than assuming FIFO completion.

Source: `this repository <https://github.com/ahmedalhulaibi/loti-zig/tree/master/examples>`_.
