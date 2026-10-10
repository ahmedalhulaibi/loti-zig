.. _sq_poll:

Submission queue polling
========================

``linux.IORING_SETUP_SQPOLL`` starts a kernel thread that polls the SQ. A producer
can publish requests without an enter syscall while the poller remains awake.
After ``sq_thread_idle`` milliseconds without work, the thread sleeps; it does
not exit. ``IORING_SQ_NEED_WAKEUP`` requires an enter call with
``IORING_ENTER_SQ_WAKEUP``. Zig's ``IoUring.submit`` performs this wakeup handling.

A poller consumes CPU while looking for work. Measure the workload rather than
assuming that polling improves throughput or latency. Setup can fail under
host policy or insufficient privilege. Modern kernels do not universally require
root: unprivileged SQPOLL support was added in Linux 5.13. Older kernels require
privilege and registered files; ``IORING_FEAT_SQPOLL_NONFIXED`` permits ordinary
descriptors on supporting kernels. This example registers its descriptor so the
fixed-file addressing rule is explicit.

.. code-block:: console

   zig build
   zig-out/bin/sq-poll /tmp/loti-poll.txt

The parameters set a 10-ms idle threshold. A first write completes, the process
sleeps for 50 ms, and a second write is submitted. A read checks the combined
contents. Every SQE uses table index 0 and ``IOSQE_FIXED_FILE``, not the process
file descriptor. Tags and actual completed byte counts prove operation success.
A ``submit`` return count alone cannot prove execution in polling mode.

.. literalinclude:: ../examples/sq_poll.zig
   :language: zig
   :caption: Registered-file I/O before and after an idle interval

``tests/test_examples.py`` checks complete stdout and file bytes. The idle
interval exercises the wakeup path when the poller sleeps, but timing alone does
not prove that it slept on every run. No thread-name search or syscall-free
claim is used as a substitute for completion evidence.

Observe it
----------

A kernel trace can distinguish the submitting task from the polling task. The
tracepoint's exact fields and availability depend on the kernel. In one terminal:

.. code-block:: console

   sudo bpftrace -e 'tracepoint:io_uring:io_uring_submit_sqe { printf("%s(%d)\n", comm, pid); }'

Run ``fixed-buffers`` and then ``sq-poll`` in another terminal. Inspect the task
names/PIDs locally; they are not fixed output. Submission tracing does not prove
that **no** enter calls occur: completion waits and wakeups can still enter the
kernel. Use syscall tracing too if that is the property being measured. These
optional observation commands are not part of the automated verification gate.
