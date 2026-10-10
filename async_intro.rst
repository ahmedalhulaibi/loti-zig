.. _async_intro:

Asynchronous programming under Linux
========================================

A blocking operation stops its calling thread until a result is available.
Other threads can continue, but each thread needs stack space and scheduling.
An asynchronous program retains request state and handles results later. Neither
model removes CPU work or makes slow storage fast.

Processes and threads
---------------------

A process owns an address space. Threads share that address space. A worker pool
limits thread creation and assigns incoming requests to existing workers.
Shared data still needs explicit synchronization. Zig 0.17.0 supplies
``std.Thread`` for explicit threads and ``std.Io`` for I/O through an injected
implementation. The tutorials use ``std.os.linux.IoUring`` directly so that
submission and completion remain visible.

.. image:: _static/Linux_Process_Models.jpg
   :align: center
   :alt: Original illustration of iterative, threaded and asynchronous execution

Process models
--------------

* **Iterative:** handle one request before the next. The listen backlog is finite.
* **Forking:** create a process per request. Process creation and copy-on-write
  memory can add cost; separate processes can use separate CPU cores.
* **Preforked:** retain a process pool. Requests wait when all workers are busy.
* **Threaded:** create a thread per request. Threads share memory, not execution.
* **Prethreaded:** retain a thread pool. This often gives a simple, effective
  design without an application-managed event loop.
* **Poll:** watch descriptor readiness and advance each request's state. Scanning
  many descriptors can become expensive.
* **Epoll:** retain an interest set and receive readiness events. The application
  still performs the subsequent read or write and handles partial progress.

Choose from measured concurrency, latency and resource limits, not a universal
request-rate threshold. A single event-loop thread also cannot execute CPU work
on several cores at once. Use multiple workers or rings when the workload needs it.

Historical comparison
---------------------

Shuveb Hussain's original process-model experiments compare equivalent servers.
These illustrations preserve that evidence; they are **not benchmarks of this
Zig edition**, the current kernel, or the programs in this repository.

.. image:: _static/Linux_Performance_upto_1000_users.png
   :align: center
   :alt: Original server benchmark up to 1000 concurrent users

.. image:: _static/Linux_Performance_more_than_1000_users.png
   :align: center
   :alt: Original server benchmark above 1000 concurrent users

.. image:: _static/Linux_Performance_Fulll_Chart-1.png
   :align: center
   :alt: Original full process-model benchmark

Read the `original experiment <https://unixism.net/2019/04/linux-applications-performance-introduction/>`_
for its workload and interpretation. Its thread pool remains competitive over
much of that workload. Complexity and maintenance cost matter alongside throughput.

Readiness and completion
------------------------

``select``, ``poll`` and ``epoll`` indicate readiness; they do not return the
completed operation. A ready socket can still produce a short read or write.
Ordinary file descriptors do not provide useful asynchronous disk-read readiness:
``poll`` commonly reports them ready, while ``epoll`` cannot monitor regular
files. The subsequent filesystem operation can still wait for storage.

Libraries can hide this difference with worker pools. Keep the operating-system
mechanism separate from the programming interface: a ``std.Io`` implementation
can use threads even when the application expresses sequential operations.

Earlier asynchronous APIs
-------------------------

POSIX AIO and Linux's native ``io_submit``/``io_getevents`` interface are different
APIs. Do not attribute every native-AIO restriction to POSIX AIO. Native Linux
AIO historically worked best with direct storage I/O; buffered I/O, metadata and
resource pressure could introduce blocking. Submission and retrieval also used
separate calls and request structures.

``io_uring`` supplies a completion interface for both files and sockets. A
submitted read yields a completed byte count, not only a readiness indication.
Some work may complete inline; other work can run through kernel workers.
Submission itself is not a guarantee of zero blocking in every configuration.

The HTTP tutorial demonstrates the useful distinction: a stalled socket read
does not prevent another client's request from completing.
