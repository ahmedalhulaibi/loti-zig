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

``submit`` publishes queued entries; outside SQPOLL its Zig error-union result
counts submissions, not completed operations. ``submit_and_wait(wait_nr)`` also
requests a completion threshold. With SQPOLL, a successful count from **either**
method may be higher or lower, including zero, than requests actually submitted
during that call. The SDK's ``submit`` delegates to ``submit_and_wait(0)``; the
non-exact SQPOLL rule applies to both. Correlate operation results through CQEs.
Do not assume every ``submit`` enters the kernel; see :ref:`sq_poll`.

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

Executed per-I/O append flags
-----------------------------

``zig-out/bin/reference-rwf INPUT`` accepts a stable regular file of 1–4097
bytes and creates only a private CLOEXEC memfd. It writes a two-byte marker,
then uses ``linux.RWF.APPEND`` with explicit offset zero. The payload goes to
EOF, but the descriptor cursor stays at one. An ordinary zero-flag write next
overwrites the prefix: APPEND did not become persistent ``O_APPEND``. A final
APPEND with the all-ones current-position offset appends again and advances the
cursor to the completed end. Positional reads and stat queries observe exact
bytes, size and cursor after each CQE without changing the cursor.

SQE metadata records ``rw_flags`` separately from the u8 dependency flags. Two
unknown-bit READ/WRITE requests produce ``-EOPNOTSUPP``; an invalid-FD APPEND
produces ``-EBADF``. Failures preserve memfd bytes/cursor and the failed-read
poison buffer. Input stays unchanged. Memory/source descriptors close and are
queried before exit; the caller ring remains open. No external output path.

``tests/test_rwf.py`` compares whole reports with a generated binary/byte-cursor
model and a separately pinned literal. Eight invalid input plans preserve files;
an actual syscall oracle checks seven submissions, five non-append status
queries, CLOEXEC/queried closure and no synchronous memfd-write substitute.
Eight damaged traces must fail. This covers current sequential memfd APPEND,
not regular-filesystem atomicity/durability, partial-write/race/cancellation or
other RWF flags. Zig 0.17.0's ``linux.RWF`` namespace has HIPRI/DSYNC/SYNC/NOWAIT/
APPEND, not the newer NOAPPEND/ATOMIC/DONTCACHE constants. Do not invent SDK names.

.. literalinclude:: ../examples/reference_rwf.zig
   :language: zig
   :caption: Per-request APPEND bytes, explicit/current cursors and flag failures

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

Executed messages and descriptor passing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``reference-messages INPUT CAPACITY`` uses an owned UNIX datagram socketpair,
not a network listener or externally visible socket path. INPUT must be a
regular, final-component nonsymlink file of at most 4097 bytes; receive CAPACITY
is a decimal value from 0 to 4097. The input is unchanged; there is no output
file. Two stable vectors gather the send payload and scatter its receive prefix.
Operation flags are in ``sqe.rw_flags``, not u8 ``sqe.flags`` or the send header's
ignored input ``flags``. Header, vectors and nested control storage remain live
through the CQE. Empty vectors still use valid userspace base addresses: Linux
checks iovec address ranges even when lengths are zero.

The payload RECVMSG requests DONTWAIT/TRUNC/CMSG_CLOEXEC. For datagrams, input
MSG_TRUNC returns the full record length even when receive capacity is smaller;
only ``min(capacity, length)`` bytes are initialized. Output ``msg.flags`` reports
TRUNC separately from ordinary CQE flags. The extra 16 poisoned bytes remain
untouched. A zero result can consume an empty datagram: the next DONTWAIT receive
returns -EAGAIN, not another empty record or TCP EOF. Never use a datagram's full
CQE length as a buffer slice length when MSG_TRUNC was requested.

A native cmsghdr encodes SOL_SOCKET/SCM_RIGHTS using aligned header/data/space
sizes derived from the Linux ABI, without foreign macros. This passes an open
file description reference, not an integer usable in another process. The
sender's application FD is closed/queried after send completion and before
receipt. The receiver's FD may reuse that numeric slot; it reads original file
bytes and has FD_CLOEXEC from MSG_CMSG_CLOEXEC. It must be closed independently.
Output control length and header length differ: on this x86_64 ABI they are
24 and 20 bytes, with an 8-byte alignment. Bounds/type checks precede FD access.

A second three-byte record offers another right to the same file, but receives
into two data bytes with no ancillary capacity and without input MSG_TRUNC.
Its CQE returns two; output flags contain TRUNC/CTRUNC/CMSG_CLOEXEC. The discarded
tail is not a later datagram. The kernel disposes excess rights; actual procfs FD
counts do not rise, then fall by one after the retained received FD is closed.
Both socket FDs are closed/queried before exit. Final counts leave only the
caller-owned ring above the initial baseline, followed by normal ring teardown.

Six negative CQEs check SENDMSG/RECVMSG invalid/non-socket FDs, a short control
header and an invalid passed FD. Requests submit separately with correlated tags;
no pending external sender or sleep is needed. The independent byte model and
literal also check flags, complete poisoned storage, input bytes and ownership.
A syscall oracle checks 14 submissions, queried closure/CLOEXEC and absence of
synchronous sendmsg/recvmsg substitutes; it is not verifier-agent acceptance.
A separate procfs oracle decodes actual open/getdents/EOF/close snapshots and
checks FD-count deltas 0/4/4/3/1 relative to the initial process, excluding the
enumerating directory FD. It rejects self-reported counts without enumeration.

Scope: sequential bounded UNIX datagrams and one SCM_RIGHTS descriptor. TCP
partial sends/SIGPIPE, UDP/address outputs, credentials/other ancillary types,
multishot, cancellation/concurrency, descriptor limits, architectures/historical
kernels and all failure unwinding are not attested. Procfs is required.

.. literalinclude:: ../examples/reference_messages.zig
   :language: zig
   :caption: Datagram scatter/gather, truncation and owned ancillary descriptors

Executed accepted peer outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``reference-accept CAPACITY FLAGS`` owns a nonblocking/CLOEXEC IPv4 TCP listener
bound only to ``127.0.0.1`` at an allocated port. It prints and flushes one JSON
ready event. The caller then connects an owned client; the executable submits a
one-shot ACCEPT and prints its report. It is not a server or arbitrary-network
probe. The independent client checks both endpoint identities and receives EOF
after the accepted socket closes.

``CAPACITY`` is ``null`` or decimal 0–16. ``null`` passes both output pointers as
null. Otherwise an aligned, poisoned address buffer and an initialized socklen
remain live through completion. The SQE stores the address pointer in ``addr``
and the **length pointer** in ``off``; ``len`` is zero. This is not CONNECT's
address-length value. On success the kernel writes at most the supplied capacity
but returns the full IPv4 address length, 16. Even capacity zero can accept a
connection and return length 16 without writing any bytes. All untouched bytes
and a 16-byte guard remain poisoned. Peer ports are network-endian; the family
field is native-endian. Independent getsockname/getpeername queries observe the
complete addresses; truncated output must not be read as a complete sockaddr.

``FLAGS`` is ``none``, ``nonblock``, ``cloexec`` or ``both``. These accept4 flags
are in ``sqe.rw_flags``, not ``sqe.flags``. A successful CQE contains a new owned
FD, not zero-success metadata. Actual fcntl queries check NONBLOCK/CLOEXEC for
all four modes: Linux does not inherit the listener's NONBLOCK status. The new
socket survives queried listener closure, then closes/queries before exit while
the ring stays open. Invalid FD/non-socket/invalid-flags requests return separate
-EBADF/-ENOTSOCK/-EINVAL CQEs with unchanged output storage and length.

All 72 capacity/flag combinations, a separate whole symbolic literal, ten typed
pre-setup negatives and a syscall oracle/seven damaged traces are checked in
fresh owned client processes. The finite domain is exhaustively table-tested,
not claimed as another generated property or independent-verifier acceptance.

A supplemental flag/order oracle requires six actual successful fcntl queries:
both listener flags, accepted status/descriptor flags, accepted-FD survival after
listener closure and ring survival after accepted closure. Seven damaged traces
challenge those observations. It closes an author-test gap: a compiled
input-derived flag report initially passed the core contracts without querying
the accepted flags. This supplement is post-discovery, not independent review.

Scope: current IPv4 loopback and one-shot outputs/FD flags/ownership. Payload,
IPv6/other protocols, aborted peers/resource limits, descriptor reuse, multishot,
concurrency/cancellation and all failure unwinding are not attested.

.. literalinclude:: ../examples/reference_accept.zig
   :language: zig
   :caption: Owned ACCEPT peer outputs, truncated capacities and new-FD flags

Executed client connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``reference-connect PORT`` connects an owned nonblocking/CLOEXEC TCP client to
``127.0.0.1:PORT``. The caller must own a listening socket at that endpoint.
No arguments, nondecimal ports, zero and values above 65535 are rejected before
setup. The example is not a scanner; use a disposable loopback listener only.

CONNECT takes a client FD, an input peer address and a numeric address length,
not the listener/output-address/value-result length used by ACCEPT. The native
preparer places that value in ``sqe.off``; ``sqe.len`` is zero. A correlated CQE
of zero means connection success, not a returned FD. Native getsockname/getpeername
then observe local/remote IPv4 endpoints with actual returned lengths; ports are
converted from network byte order. The independent listener checks its accepted
peer against these observations and receives EOF after queried client closure.

The example keeps the peer bytes unchanged and live through completion.
``IORING_FEAT_SUBMIT_STABLE`` means relevant metadata has been consumed when
the kernel consumes the SQE; see :ref:`io_uring_setup`.
A positive ``submit`` return is not a consumption acknowledgment for SQPOLL.
Keep the peer address until the matching CQE, not merely until that return.
Failed socket state is unspecified: each negative socket probe gets a fresh
owned FD, then closes it. Probes cover invalid FD,
non-socket FD, short address, wrong family, a private bound-but-not-listening
refusal endpoint, and already-connected TCP. The guard holds its port during the
refusal test; no unrelated endpoint is used. Reconnect failure is observed only
after successful endpoint queries, then the client is closed without reuse.

Requests submit separately and check CQ readiness before a one-second EXT_ARG
wait fallback (Linux 5.11+). The recorded loopback trace takes the ready fast
path; it does not attest a delayed CONNECT or actual timeout entry. No sleeps
or sender thread are used. Each CQE retains its original tag.
Before exit, all five created sockets are closed/queried and the caller's ring
remains open until normal deferred teardown. A syscall oracle checks actual
endpoint queries, socket lifetimes, seven ring submissions and absence of a
synchronous connect substitution. A second parser/shape is not agent review.

Scope: sequential IPv4 loopback TCP handshake and selected errors. Payload I/O,
DNS/TLS, IPv6, datagrams, remote network policy, cancellation/interleavings and
accept's supplied peer-address outputs are not attested by this executable.

.. literalinclude:: ../examples/reference_connect.zig
   :language: zig
   :caption: Owned client connection and independent peer endpoint observations

Executed epoll interest-list changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``reference-epoll`` uses one epoll instance and one owned nonblocking pipe.
Optional commands are ``add modify delete write wait drain close``; the entire
plan (at most 64 commands) is validated before setup. ADD monitors IN with an
opaque 64-bit token. MOD switches IN/OUT and replaces that token; unread bytes
stay in the pipe, but OUT does not report their readability. DEL uses a null
event pointer. Duplicate ADD returns ``-EEXIST``; absent MOD/DEL return
``-ENOENT``. Neither changes an existing registration after failure.

An EPOLL_CTL CQE of zero means that the interest-list operation succeeded, not
that a descriptor is ready. Native ``epoll_wait`` (zero timeout, maxevents one)
observes actual readiness separately; io_uring READ drains the actual FIFO bytes.
Repeated waits show level-triggered IN until the bytes are consumed. The event
storage stays alive through the control CQE; the kernel then retains a copy of
its mask/data, not a userspace pointer. Returned opaque tokens are not dereferenced.

Six correlated failures cover invalid epoll/retired-target descriptors, wrong
epoll descriptor type, invalid operation, self-monitoring and null ADD storage.
The Zig 0.17.0 preparer casts the target FD with ``@intCast``: a negative target
would trap. The example retires an owned positive duplicate after ring setup to
obtain a stable invalid target without descriptor reuse. The epoll FD itself can
be negative for its failure case.

``close`` closes the monitored read end; with no duplicates left, the kernel
removes its interest entry. Closing one duplicate does not guarantee removal;
see :man:`epoll(7)`. Remaining entries/bytes are removed/drained during cleanup.
Pipe and epoll closure are checked before exit. An independent syscall trace
checks actual readiness calls and separate ring submissions, and rejects a
synchronous epoll_ctl substitution or fabricated observation.

Scope: sequential, ordinary level-triggered pipe IN/OUT, numeric mask/data,
ADD/MOD/DEL and bounded errors. ET, ONESHOT, EXCLUSIVE, duplicate-FD lifetimes,
concurrent consumers, races and other descriptor types are not verified.

.. literalinclude:: ../examples/reference_epoll.zig
   :language: zig
   :caption: Submitted epoll control and independent readiness observations

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

Optional ``reference-submission --linked-timeout`` executes four private-pipe
cases without an input or output path. An empty one-byte READ has a relative
20-ms linked deadline: its target returns ``-ECANCELED`` and its timer returns
``-ETIME``. A prewritten byte lets the READ return one and cancels its timer.
An invalid-FD READ returns ``-EBADF`` and cancels its timer. A lone linked timer
without a target returns ``-EINVAL``.

Each pair retains its byte storage and timespec until both tagged CQEs have
been consumed. Results are sorted by tag, not arrival order. Only the ready
READ changes the first byte; the seven guard bytes and failed-read storage
remain unchanged. Queue checks precede reuse, and both pipe ends are closed
and queried while the caller still owns the ring.

This is bounded sequential current-kernel pipe evidence, not every deadline
race, operation, clock, flag or cancellation path. One-second EXT_ARG waits
bound missing completions; an external process bound contains native/trace
failures. The mode does not submit the incompatible 33-constructor batch.

Optional ``reference-submission --cancel`` exercises generic ASYNC_CANCEL on
two private pipes without a path. The pending one-byte READ tags have equal
low32 bits but different high32 bits. Default cancellation matches the full
u64 tag, not a descriptor or target pointer. The cancellation CQE returns zero
and its distinct target CQE returns ``-ECANCELED``; both are consumed by tag,
not arrival order.

Repeated, unknown and already-completed tags return ``-ENOENT``. An unsupported
high operation flag returns ``-EINVAL`` without cancelling the other READ.
Only then is a byte written to that second pipe: its original READ returns one
with exact bytes and untouched guards. Storage remains live through target
completion; queues are drained before all four pipe ends are closed and queried
while the ring remains owned.

Scope: sequential default-tag matching on this kernel, not every cancellation
race, flag, descriptor or error/unwind path. One-second completion guards and
10-second externally bounded process groups contain missing completions. This
mode is separate from both linked deadlines and the unsubmitted constructor
batch; successful cancellation does not acknowledge its target CQE for you.

.. literalinclude:: ../examples/async_cancel.zig
   :language: zig
   :caption: Full-u64 cancellation and unrelated request retention

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
multi-buffer selection order is assumed. Concurrent/multishot receive,
ring-based provided buffers and cancellation races remain unverified.

Optional ``--zero-result`` takes a stable nonempty regular input of 1–4097 bytes,
without additional commands or an output file. A positive-length 64-byte READ
at the file's actual size returns zero **with BUFFER/ID 257** on this kernel.
The unchanged 0xa5 storage does not imply pool ownership: a subsequent removal
of one buffer returns zero, and another selected EOF read returns ``-ENOBUFS``.
Inspect CQE flags/ID, not just ``res > 0``, before deciding whether to re-provide.

After re-provision, the reference submits a selected READ with requested length
zero at offset zero. On this legacy 64-byte pool, that request reads up to the
provided buffer's capacity and consumes it; it is **not** an ordinary zero-byte
read or an EOF test. Actual prefix bytes, untouched tails and a second removal
returning zero distinguish this case from the zero-result EOF completion.

All 13 requests have actual SQE snapshots and correlated CQEs. Re-provision is
after completion; final removal returns one, then EOF selection is exhausted.
The input cursor is queried before/after and remains zero because offsets are
absolute. The new test compares whole reports against independent binary/literal
oracles and checks real submission/wait/cursor syscalls. These bounded sequential
legacy-buffer observations do not establish other descriptor classes, pbuf-ring
semantics, multishot/cancellation races or independent review.

Each CQE is validated before further pool operations or a storage reset. Optional
``--zero-result --fail-eof`` deliberately uses an invalid descriptor for the EOF
READ. After provide/READ only, ``UnexpectedBufferZeroSelection`` aborts without a
report or further re-provision/removal. The trace observes exactly two submits,
then ring closure before source closure; input bytes remain unchanged. This
checks one real error/unwind path, not all completion errors or cancellations.

.. code-block:: console

   zig build
   zig-out/bin/reference-buffers input.bin
   zig-out/bin/reference-buffers input.bin read read provide read
   zig-out/bin/reference-buffers input.bin --zero-result
   zig-out/bin/reference-buffers input.bin --zero-result --fail-eof

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
   :caption: 33 unsubmitted constructors; separate deadline/cancellation modes

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
