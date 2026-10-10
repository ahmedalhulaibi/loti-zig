.. _io_uring_setup:

``linux.io_uring_setup``
========================

Create a Linux asynchronous I/O context. Prefer ``IoUring.init`` or
``init_params`` unless you deliberately manage mappings and publication.
The raw entry point has this Zig 0.17.0 declaration:

.. include:: _api/io_uring_setup.inc

``entries`` requests SQ capacity. The kernel returns actual SQ/CQ capacities and
offsets through ``params``. Decode the raw ``usize`` with ``linux.errno``; on
success it is a newly owned descriptor. On failure it is errno-encoded, not
``-1`` with a separate thread-local errno. No queues are mapped by this call.

Native parameters
-----------------

.. include:: _api/params.inc

Zero parameters and then set supported input fields. ``flags`` selects setup
mode; ``sq_thread_cpu`` and ``sq_thread_idle`` configure an SQ poller.
``cq_entries`` requests a CQ size with ``IORING_SETUP_CQSIZE``. ``wq_fd`` is used
only with an attached worker-pool setup. Reserved fields must remain zero.
``sq_entries``, actual ``cq_entries``, ``features``, ``sq_off`` and ``cq_off`` are
kernel outputs. Zig's wrapper takes a nonzero power-of-two u16 entry count;
the raw syscall accepts u32 and applies kernel sizing rules.

Setup flags
-----------

``IORING_SETUP_IOPOLL``
   Poll for storage completion rather than rely on interrupt delivery. The
   descriptor, direct-I/O alignment, filesystem and device must support it.
   ``IORING_ENTER_GETEVENTS`` drives completion polling. Do not mix unsupported
   non-polled operations into that ring. This is not SQ thread polling.

``IORING_SETUP_SQPOLL``
   Start an SQ poller thread. Publishing SQEs can avoid an enter call while it
   is awake. On idle sleep the kernel sets ``IORING_SQ_NEED_WAKEUP``; publish the
   tail before checking that flag and use ``IORING_ENTER_SQ_WAKEUP`` when needed.
   Correct barriers are essential. See :ref:`sq_poll` for Zig's wrapper handling,
   fixed-file addressing and kernel-dependent privilege requirements.

``IORING_SETUP_SQ_AFF``
   Bind the SQ poller to ``sq_thread_cpu``. Requires SQPOLL.

``IORING_SETUP_CQSIZE``
   Request a CQ capacity at least as large as the SQ, subject to kernel limits
   and rounding. The reference requests SQ 8/CQ 32 and checks returned sizes.

With no flags, use ordinary submission and interrupt-driven completion. Linux
has additional setup flags beyond this guide's historical scope; their presence
in ``linux`` does not establish compatibility with this wrapper or teaching raw
mapper. These examples use ordinary 64-byte SQEs and 16-byte CQEs. Do not enable
SQE128/CQE32 or alternate-layout modes without adapting the mapping/stride code.

Feature bits
------------

``IORING_FEAT_SINGLE_MMAP``
   SQ and CQ share a mapping at ``IORING_OFF_SQ_RING`` sized to the larger ring
   region. SQEs still need a separate ``IORING_OFF_SQES`` mapping. Zig 0.17.0's
   ``IoUring`` requires this feature. The teaching ``RawRing`` also supports
   separate SQ/CQ mappings when the bit is absent.

``IORING_FEAT_NODROP``
   The kernel can retain completions when CQ space is exhausted. Reap regularly
   and drive overflow flushing; do not treat it as unlimited queue capacity.
   Resource/backpressure errors can still require draining and retrying.

``IORING_FEAT_SUBMIT_STABLE``
   Relevant submission metadata has been consumed when the SQE is consumed.
   It does **not** permit freeing I/O data buffers before their operations
   finish. The examples conservatively retain all operands through completion.

``IORING_FEAT_RW_CUR_POS``
   Supported read/write operations accept the all-ones offset for shared current
   position. Concurrent requests sharing that position can race; explicit
   offsets are used in the file examples.

``IORING_FEAT_CUR_PERSONALITY``
   Normal requests use the submitting task's credentials rather than only the
   original setup task's credentials. An explicit registered personality can
   override the per-request selection. It does not confer extra privilege.

Mapping and queue indices
-------------------------

``sq_off`` and ``cq_off`` are byte offsets within their mapped regions, not
process pointers. For ordinary layouts the SQ region extends through
``sq_off.array + sq_entries * @sizeOf(u32)``; the CQ region extends through
``cq_off.cqes + cq_entries * @sizeOf(linux.io_uring_cqe)``. SQE mapping size is
``sq_entries * @sizeOf(linux.io_uring_sqe)``. Without SINGLE_MMAP, ``RawRing``
maps SQ at ``IORING_OFF_SQ_RING`` and CQ at ``IORING_OFF_CQ_RING`` using their
individual sizes. Each queue's offsets are relative to its own mapping.

.. include:: _api/offsets.inc

Add each byte offset to the mapped base, then apply alignment-checked pointer
casts. Mask monotonically wrapping u32 head/tail counters to obtain slot indices;
use Zig wrapping arithmetic (``+%``/``-%``), not overflowing ordinary arithmetic.
The application produces SQ indices and consumes CQ entries; the kernel does
the inverse. Shared publication/observation needs release/acquire ordering.
``dropped`` and ``overflow`` are diagnostics, not free-slot counts.

The complete :ref:`raw reader <low_level>` implements setup, mapping, atomic
publication and cleanup. :ref:`setup_and_tear_down` includes the separate native
setup/mapping reference. Ring teardown closes the descriptor and unmaps regions;
application descriptors and outstanding operand lifetimes remain separate.

Errors
------

``FAULT`` means inaccessible parameters. ``INVAL`` covers unsupported flags,
nonzero reserved data, invalid sizing or inconsistent options. ``MFILE`` and
``NFILE`` identify descriptor limits; ``NOMEM`` identifies unavailable kernel
resources. ``PERM`` can mean insufficient privileges **or host/container policy**;
``NOSYS`` can mean an unavailable syscall. Inspect the actual result. The native
wrapper translates expected errno values into named Zig errors such as
``error.ArgumentsInvalid``, ``error.PermissionDenied`` and ``error.SystemOutdated``.

See :ref:`io_uring_enter` and :ref:`io_uring_register`.
