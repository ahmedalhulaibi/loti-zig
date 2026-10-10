.. _submission:

Submission
==========

Prepare one or more SQEs, set correlation tags/extra flags, then submit. Native
``IoUring`` constructors combine acquisition and operand preparation. The
:ref:`cat source <cat_zig>` shows a vectored read; the :ref:`copy <cp_zig>`
shows repeated batches. Constructing a request does not execute it.

Queue and publication
---------------------

``get_sqe`` returns a vacant slot or ``error.SubmissionQueueFull``. It does not
return a nullable pointer. If you use a low-level SQE preparer, set ``user_data``
after it. Constructors already take a u64 tag. ``sq_ready`` counts outstanding
SQ entries; free capacity is ``ring.sq.sqes.len - ring.sq_ready()`` under the
wrapper's single-producer discipline. Neither count describes completed I/O.

The :ref:`completion reference <completion>` fills all eight slots, checks that
a ninth NOP returns ``SubmissionQueueFull`` without changing pending count or
local tail, then submits and consumes all eight. This is an executed capacity
failure, not merely a constructor signature. It uses one producer without SQPOLL.

``submit`` publishes queued entries and returns a submission count through a
Zig error union. ``submit_and_wait(wait_nr)`` also requests a completion wait,
but its returned number still counts submissions. SQPOLL can consume entries
concurrently; do not treat these return counts as completion counts or assume
every ``submit`` performs an enter syscall. See :ref:`sq_poll`.

File data and durability
------------------------

``read`` takes ``IoUring.ReadBuffer``: ``.buffer`` prepares ``READ``;
``.iovecs`` prepares ``READV``. ``write`` takes a const byte slice; ``writev``
takes ``[]const posix.iovec_const``. The slice carries length, replacing a
separate pointer/count pair. Offsets are absolute ``u64`` values. The all-ones
offset selects current-position semantics where supported; explicit offsets
avoid shared-descriptor position races.

Per-I/O read/write flags from ``linux.RWF`` belong in ``sqe.rw_flags`` after
preparation, not in the u8 ``sqe.flags`` dependency bitmap. See :man:`preadv2(2)`
for their meanings. Kernel, filesystem and opcode support still apply; setting a
flag is not proof that the operation supports it.

``read_fixed`` and ``write_fixed`` take an iovec pointer and registered-buffer
index. The requested range must fit that registered buffer. They do not register
memory implicitly. See :ref:`fixed_buffers`.

``fsync`` uses zero flags for full file integrity or ``IORING_FSYNC_DATASYNC``
for data-only sync. A write submitted before an fsync can still run concurrently
with it. Wait for dependent writes or establish a link/drain dependency before
claiming durability. ``raw_ops.sync_file_range`` prepares the distinct Linux
``SYNC_FILE_RANGE`` opcode: descriptor, u64 offset, u32 length and range flags.
Length zero selects the remainder of the file. Use ``raw_ops.sync_wait_before``,
``sync_write`` and ``sync_wait_after`` for the three supported bits. They occupy
SQE ``rw_flags``, not the SQE's u8 dependency flags.

This range operation does not sync metadata or flush volatile disk caches; it
is **not** a substitute for fsync or proof of crash durability. Flags zero are
a permitted no-op. The reference uses all three bits (value 7), then separately
executes invalid-flags and invalid-descriptor requests. Each failure arrives in
its own correlated CQE, not as a constructor error. See :man:`sync_file_range(2)`.

Files, paths and advice
-----------------------

``openat`` takes a sentinel-terminated path, native ``linux.O`` flags and
permission mode; a successful CQE contains the new descriptor. ``statx`` takes
a sentinel slice, native ``linux.STATX`` mask and stable output ``linux.Statx``.
Directory descriptor, path and lookup flags determine resolution. ``close``
closes a process descriptor on successful completion; do not close it a second
time or close it while other unsequenced requests still need it.

``fallocate`` passes a mode, offset and 64-bit length for allocation or other
filesystem space operations. Filesystem support is operation-specific.
``sqe.prep_files_update`` asynchronously updates a registered-file table; acquire
the SQE and set its tag separately. This differs from synchronous
``ring.register_files_update``. Keep the supplied descriptor array alive through
the CQE.
The :ref:`registration reference <advanced_usage>` submits this request separately,
checks its updated-entry count and then reads through the changed fixed-file slot.

Zig 0.17.0 has no corresponding ring methods for ``openat2``, ``fadvise``,
``madvise`` or ``sync_file_range``. Repository ``raw_ops`` helpers encode actual
Linux SQEs. ``OpenHow``
contains three u64 fields: flags, mode and resolution constraints. File advice
specifies a descriptor/range/access pattern; memory advice specifies an address
range/advice value and needs suitable page alignment where Linux requires it.
The helpers do not silently call synchronous substitutes.
In the submitted reference below, FADVISE uses NORMAL advice and checks its
success CQE only; no cache or performance outcome is measured. The separate
MADVISE request checks DONTNEED zeroing on owned anonymous pages. OPENAT2 returns
the descriptor used for the independently checked file prefix. Do not attribute
one operation's byte or memory effects to another operation's success CQE.

``splice`` transfers between descriptors, at least one of which must be a pipe.
Its Zig offsets are **values**, not pointer arguments. Use the all-ones sentinel
for a pipe/current-position case; flags go in ``sqe.rw_flags`` after preparation.
The original preparer already accepted values; its pointer/NULL prose mixed in
the synchronous syscall interface. An explicit regular-file offset leaves that
FD's current position unchanged; the sentinel advances it by completed bytes.
The same rule applies to the output descriptor. See :man:`splice(2)`.

Executed SPLICE transfers
~~~~~~~~~~~~~~~~~~~~~~~~~

``reference-splice INPUT`` reads an unchanged regular file (at most 1 MiB) through
two owned nonblocking pipes. Each pipe is resized to exactly 4096 bytes; larger
requests produce actual short completions. The loop advances by the **completed**
count, not the request length. A final READ copies drained bytes into user memory
for independent observation; it is not part of the two SPLICE legs.

The reference checks file/pipe/pipe bytes, input EOF, explicit/current source
cursors, and both output-offset modes on an owned memfd. Positional observation
checks exact overlap/zero-gap bytes without changing the memfd cursor. It also
checks six separate correlated negative CQEs: bad FD, empty nonblocking pipe,
non-sentinel pipe input/output offsets, same pipe and no pipe. ``SPLICE_F_NONBLOCK``
is value 2 in operation flags, not ``sqe.flags``; ordinary file I/O can still block.

Pipe FD closure is queried before process exit; the input FD remains caller-owned.
This example needs 4096-byte pipe support. It does not attest every filesystem,
socket, registered descriptor, concurrency/cancellation path, physical copy
avoidance or performance. It has no externally visible output file.

.. literalinclude:: ../examples/reference_splice.zig
   :language: zig
   :caption: Owned SPLICE pipeline and both value-offset modes

Sockets and readiness
---------------------

``accept`` takes a listener, optional address pointer/length pointer and accept
flags; if supplied, initialise the input address capacity and retain both
outputs. A successful CQE returns the new descriptor. ``connect`` takes a stable
peer address and its value length. ``recv`` accepts ``RecvBuffer``; ``send``
takes const bytes. TCP results can be partial; zero reception means peer EOF.
Use ``MSG.NOSIGNAL`` when appropriate to avoid SIGPIPE on abandoned sends.

``recvmsg`` uses ``linux.msghdr`` and ``sendmsg`` uses ``linux.msghdr_const``.
Keep the header and all nested vectors, address and control storage valid.
These operations also support datagram sockets; consult their flags and result
semantics rather than apply TCP's EOF rule to zero-length datagrams.

``epoll_ctl`` modifies an epoll interest list with an operation and optional
event pointer. It is not a wait for an epoll event. ``poll_add`` requests one-shot
readiness for a descriptor/mask; submit again to observe later events.
``poll_remove`` identifies an outstanding poll by its submission tag. Removal
and the target request have distinct completions; races can yield ``NOENT``.

Executed poll ownership
~~~~~~~~~~~~~~~~~~~~~~~

``reference-poll`` uses an owned nonblocking pipe; operands are optional command
names: ``arm write wait cancel drain missing quiet``. The full plan (at most 64
commands) is validated before setup. ``arm`` submits a one-shot ``POLL.IN``;
``write`` creates input with one byte; ``wait`` consumes that poll's CQE but not
the pipe data. ``drain`` reads the bytes. Each emitted step records the original
tag, unconsumed poll ownership, byte count, actual request/CQEs and FIFO data.

Completed one-shot requests produce no more notifications. A new ``arm`` while
the bytes remain unread completes again; a later write without rearm does not.
An empty pending poll can be cancelled: the target receives ``-ECANCELED`` and
the separate remover receives zero. Both CQEs must be consumed. Output sorts
these two by tag, not arrival order. ``missing`` removes a nonexistent numeric
tag and receives ``-ENOENT``. Removal after readiness is a race, not this
example's deterministic cancellation path.

The final checks submit an invalid-FD poll, then close the pipe's write end.
``POLL.HUP`` is delivered although only ``POLL.IN`` was requested; a subsequent
positive-length READ returns zero for EOF. Pipe closure is queried before exit.
``quiet`` and empty-arm/HUP guards use real bounded EXT_ARG waits (Linux 5.11+).
An independent syscall trace checks the waits, since a reported timeout boolean
alone cannot prove them. No sleeps or concurrent sender are used.

Scope: ordinary one-shot pipes, IN/HUP and sequential ownership. Other masks,
descriptors, multishot, readiness/cancel races, SQPOLL and concurrent consumers
are not verified. The helper accepts a u32 mask and encodes it little-endian;
poll event results are bitmasks, not transferred byte counts.

.. literalinclude:: ../examples/reference_poll.zig
   :language: zig
   :caption: One-shot readiness, rearm, cancellation and HUP/EOF

Timers, cancellation and selected buffers
-----------------------------------------

``timeout`` borrows ``linux.kernel_timespec``. With count zero it expires by
time; a positive count also permits completion after that many events. Relative
timeouts use the monotonic clock by default; ``IORING_TIMEOUT_ABS`` selects an
absolute deadline. Expiration reports ``-ETIME``, count satisfaction zero and
cancellation ``-ECANCELED``. ``timeout_remove`` targets a timeout tag; its own
result can be zero, ``-ENOENT`` or ``-EBUSY`` as the race dictates.

``cancel`` identifies a request by tag (with additional matching modes controlled
by flags). A successful cancellation request does not mean the target CQE has
already been consumed. Retain target operands until its completion; not-found
or already-running results are possible. ``link_timeout`` is attached to a
linked request, not a general CQ wait. Expiration can attempt to cancel that
request; normal target completion cancels the link timer. See :ref:`link_zig`.

``provide_buffers`` supplies a contiguous allocation, per-buffer size/count,
group and first ID. ``remove_buffers`` removes a count from a group. Selected
receive/read requests set ``IOSQE_BUFFER_SELECT``; decode the selected ID from
CQE flags and do not reuse its storage while still owned by an operation.
Provided buffers and fixed registered buffers are different mechanisms.

.. _provided_buffers:

Provided-buffer ownership
-------------------------

``reference-buffers INPUT [COMMAND ...]`` submits real provide/remove requests
and selected reads. Input must be a nonempty regular file; each read requests
its first 64 bytes. Up to 32 ``read``, ``provide`` or ``remove`` commands are
accepted. Invalid ownership transitions are rejected before any SQE is issued.
With no commands, the default plan consumes, exhausts, recycles and removes.

A selected read consumes the one available buffer in group 7. Its CQE carries
``IORING_CQE_F_BUFFER`` and ID 257 in the upper 16 bits. Only after that CQE may
the application reset/re-provide the same storage. Exhaustion returns
``-ENOBUFS`` without a selected ID or memory change. ``provide`` restores an
application-owned buffer, while ``remove`` returns its available storage.

Separate requests prove group isolation with group 9/ID 513. A two-buffer group
is supplied and then removed with a request for three: the CQE returns **two**,
the actual removed count, not zero success or the requested count. The read
following removal returns ``-ENOBUFS``. Non-selected CQEs exercise
``buffer_id()``'s ``error.NoBufferSelected`` path; see :ref:`cqe`.

Storage snapshots distinguish kernel-written prefixes from untouched 0xa5 tails.
Snapshots are owned copies, not slices into subsequently recycled memory. All
requests are drained before reuse; an available final buffer is explicitly
removed before pool lifetime ends. These are provided buffers, **not fixed
registered buffers**. The selected groups each hold one buffer, so no kernel
multi-buffer selection order is assumed. EOF/zero-result ownership, concurrent
or multishot receive and cancellation races remain unverified.

.. code-block:: console

   zig build
   zig-out/bin/reference-buffers input.bin
   zig-out/bin/reference-buffers input.bin read read provide read

.. literalinclude:: ../examples/reference_buffers.zig
   :language: zig
   :caption: Provided-buffer selection, IDs, exhaustion, recycling and removal

``tests/test_provided_buffers.py`` compares every command/CQE/state/storage with
an independent model over generated binary inputs and valid command sequences.
A separate literal whole-report fixture pins flags/IDs/counts without that model.
Plan/input failures have exact error contracts. These author checks do not
replace independent review.

``nop`` performs no data I/O and is useful for queue/completion experiments.

Exact native declarations
-------------------------

.. include:: _api/submission.inc

Submitted file-operation reference
----------------------------------

``reference-files INPUT NEW_OUTPUT`` executes ``OPENAT``, ``READV``, ``WRITEV``,
``FALLOCATE``, ``STATX``, both ``FSYNC`` flag modes and ``CLOSE``. Input must be
regular; output is created with ``CREAT | EXCL`` and must not exist. ``NOFOLLOW``
rejects final-component symlinks; this is not directory confinement. Existing
files, same-path output and symlink output are rejected without byte changes.

Two stable vectors span 1,024 and 3,072 bytes. Each read CQE bounds initialized
bytes; writes use only those bytes and advance offset/progress. The final read
really returns zero, and an empty input also executes a zero-length ``WRITEV``.
Vector count is two, **not** 4,096. Storage remains alive through each CQE.

After writes complete, mode-zero allocation adds a 4,096-byte zero-filled tail.
Actual ``STATX`` on ``AT.EMPTY_PATH`` checks returned TYPE/SIZE mask bits and
new size. Full/data-only fsyncs follow those completed operations, with observed
opcode/flags and correlated zero CQEs. Output and input close asynchronously;
``fcntl(GETFD)`` then returns ``EBADF``. A new async open reads the whole output
again and hashes actual bytes, before its own close. This proves observable
content/ownership and successful sync requests, **not crash or physical-media
durability**, metadata copying or atomic replacement. Allocation mode/filesystem
support is specific to the execution environment.

Seven separate invalid-descriptor requests return correlated ``-EBADF`` CQEs.
A negative CQE is an operation error, not a constructor failure. Requests are
submitted/drained separately, not as the incompatible mixed batch below.
The source detects size changes, but it is not a concurrent-input snapshot.
A later failure can leave its newly created partial output; it never overwrites
an existing destination. Forced short writes remain unverified.

.. code-block:: console

   zig build
   zig-out/bin/reference-files input.bin new-output.bin

.. literalinclude:: ../examples/reference_files.zig
   :language: zig
   :caption: Submitted file operations, exact metadata and descriptor ownership

``tests/test_file_operations.py`` generates binary inputs across vector/buffer
boundaries. It compares the whole report, unchanged source, exact output plus
zero tail and independent full SHA-256. A committed 4,097-byte fixture has a
literal report with GNU ``sha256sum`` digest; path/argument matrices check
exact errors and retained files. These author checks are not independent review.

Runnable constructor reference
------------------------------

.. code-block:: console

   zig build
   zig-out/bin/reference-submission input.bin
   zig-out/bin/reference-raw input.bin

.. literalinclude:: ../examples/reference_submission.zig
   :language: zig
   :caption: 33 executed constructors; requests deliberately not submitted

``tests/test_reference.py`` verifies prepared opcode/tag/flags and selected
length/group fields. The deliberately incompatible mixed descriptor operands
above are **not submitted**. This tests API preparation, not all filesystem and
network operation effects. Tutorial programs separately execute their actual
operations. The raw reference submits the four missing-wrapper operations and
checks an opened file's exact prefix, unchanged input, ``MADV_DONTNEED`` page
zeroing and range CQEs (success, ``-EINVAL``, ``-EBADF``). Its successful range
result is not evidence of physical write-out or crash durability:

.. literalinclude:: ../examples/reference_raw.zig
   :language: zig
   :caption: Submitted OPENAT2, FADVISE, MADVISE and SYNC_FILE_RANGE requests

Shared native helper implementation:

.. literalinclude:: ../examples/raw_ops.zig
   :language: zig
   :caption: Explicit Linux SQE/registration/deadline helpers
