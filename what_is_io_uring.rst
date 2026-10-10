.. _what_is_io_uring:

What is io_uring?
=================

``io_uring`` is Linux's submission/completion interface, introduced in Linux 5.1
by Jens Axboe. Shared rings carry requests and results between the application
and kernel. Files and sockets use the same completion model.

The mental model
----------------

1. Create a ring. Zig 0.17.0's ``std.os.linux.IoUring.init`` performs setup and
   mapping. The low-level path uses ``linux.io_uring_setup`` and mapped offsets.
2. Acquire a submission queue entry (SQE). Store an operation, its operands and
   a ``u64`` correlation tag. Keep every referenced buffer alive.
3. Publish submissions. ``ring.submit()`` can submit a batch. SQ polling lets a
   kernel thread watch the shared submission queue instead.
4. The kernel executes requests. Independent operations can finish out of order.
5. Read completion queue entries (CQEs). ``user_data`` identifies the request;
   ``res`` carries its result. A negative result encodes a Linux error.
6. Consume each completion exactly once, then reuse its request storage.

The submission queue (SQ) contains indices into a separate SQE array. The
completion queue (CQ) directly contains CQEs. With ``SINGLE_MMAP``, one shared
mapping contains both ring-control areas; the SQE array still needs its own
mapping. Do not assume that two queues mean exactly two independent ring mappings.

The examples use single-shot operations without success-CQE suppression. For
these, expect one result per request. Modern multishot operations can produce
several CQEs, and configured success suppression can omit some successful CQEs.
Their flags and lifetimes need additional handling.

Ordering and lifetime
---------------------

Submission order is not completion order. Two devices, or two kernel workers,
can produce results in either order. Numeric tags avoid casting returned integers
back into potentially expired application pointers.

A linked chain orders dependent operations. It does not make the whole batch a
transaction. A failed request can cancel later linked requests, including a
queued close. The application still owns cleanup.

Kernel-visible memory must remain allocated and unmoved until the corresponding
operation finishes. Atomics order ring publication; they do not solve buffer
ownership or synchronize several application producers automatically.

Performance
-----------

Batching reduces submission calls and shared control structures reduce copying
of request metadata. **Ordinary file and socket payloads are not automatically
zero-copy.** Explicit zero-copy operations have separate contracts.

SQ polling spends CPU on a kernel poller. Sleeping pollers still need a wakeup;
completion waits and filesystem work can still need kernel entries. It is not a
promise of a syscall-free application or universally higher throughput.

The `original io_uring paper <https://kernel.dk/io_uring.pdf>`_ reports storage
and NOP measurements on its reference machine. Those historical results are
not measurements of this edition. Benchmark your actual operation mix, storage,
concurrency and latency targets.

Use the native Zig wrapper
--------------------------

Use ``std.os.linux.IoUring`` for normal examples. It owns mappings, exposes native
SQE preparers and returns Zig error unions. No external ring library or foreign
headers are required. The :ref:`low-level chapter <low_level>` explains the
underlying ABI; the tutorials show complete programs.

A kernel version alone does not establish operation support. Probe capabilities
and check actual CQEs. Also check execution policy: seccomp, containers or
``kernel.io_uring_disabled`` can deny setup on an otherwise capable kernel.
