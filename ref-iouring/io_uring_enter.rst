.. _io_uring_enter:

``linux.io_uring_enter``
========================

Submit published SQ entries, wait for CQ availability, or do both. The native
Zig 0.17.0 entry point is:

.. include:: _api/io_uring_enter.inc

``fd`` identifies the ring; ``to_submit`` limits SQ entries to consume.
``min_complete`` requests a wait threshold with ``IORING_ENTER_GETEVENTS``.
The successful return counts consumed submissions, not successful operations or
CQEs copied by the application. The syscall does not advance application CQ head.
Raw errors are errno-encoded ``usize`` values decoded with ``linux.errno``.
Operation-specific failures normally arrive separately in CQE ``res``.

Flags, waits and signals
------------------------

``IORING_ENTER_GETEVENTS`` drives/waits for completion availability. Without a
blocking wait, ordinary interrupt-driven CQ entries can be inspected without
entering the kernel. On IOPOLL rings the call drives storage completion polling;
do not assume its wait threshold is an exact returned batch size.
``IORING_ENTER_SQ_WAKEUP`` wakes a sleeping SQ poller. Publish before checking
``IORING_SQ_NEED_WAKEUP`` with the required ordering. Prefer ``IoUring.submit``
for its built-in publication and wakeup rules.

``sig`` is an optional pointer to ``linux.sigset_t``. The kernel atomically
installs that mask for the wait and restores the old one. Separately changing
the mask, entering and restoring it leaves a signal race. ``linux.io_uring_enter``
supplies the ordinary mask ABI size; the EXT_ARG form has a different argument
layout. Repository ``raw_ops.wait_with_timeout`` uses ``linux.syscall6`` and
``linux.io_uring_getevents_arg`` for EXT_ARG, not an incompatible cast of ``sig``.

The :ref:`signal reference <completion>` queues a blocked ``SIGUSR1`` before
EXT_ARG entry, then temporarily unmasks it. Actual handler delivery yields
``WaitInterrupted``; the saved caller mask returns after the handler. Blocked
and null-mask waits expire with the signal still pending, and neither submits
a queued NOP. Complete masks, handler state and later recovery CQE are checked.
This is a bounded pending-signal example, not a concurrent-sender/restart-policy
attestation. Ordinary non-EXT_ARG delivered-signal behaviour remains untested.
See :ref:`completion` for its compiled use and Linux 5.11+ deadline requirement.

Publication and lifetimes
-------------------------

Fill an SQE, place its index in the SQ array, then release-publish the new tail.
The kernel acquire-observes it, consumes the request and updates head. Consumption
makes the SQE slot reusable; it does not complete I/O or release buffer ownership.
For CQ processing, acquire-observe tail before reading entries and release-publish
head only after processing. The :ref:`low_level` source implements these steps
for an ordinary single-producer/single-consumer ring.

See :ref:`sqe` and :ref:`cqe` for native layouts. ``user_data`` is an opaque u64
tag; correlate completion to stable application state. CQE flags are **not**
reserved: buffer selection and multishot/notification features use them.

Operation coverage
------------------

The historical opcode set is represented by ``linux.IORING_OP``. This table
points to native interfaces; :ref:`submission` gives signatures, operand rules
and complete constructor/raw-operation programs.

.. list-table:: Native operation interfaces
   :header-rows: 1
   :widths: 34 66

   * - Opcode
     - Zig interface / contract
   * - NOP
     - ``ring.nop``; completes without data I/O
   * - READ / READV
     - ``ring.read`` with ``.buffer`` / ``.iovecs``
   * - WRITE / WRITEV
     - ``ring.write`` / ``ring.writev``; actual count can be short
   * - READ_FIXED / WRITE_FIXED
     - ``ring.read_fixed`` / ``write_fixed``; registered range/index
   * - FSYNC
     - ``ring.fsync``; dependency ordering required for prior writes
   * - POLL_ADD / POLL_REMOVE
     - ``ring.poll_add`` / ``poll_remove``; one-shot readiness / target tag
   * - EPOLL_CTL
     - ``ring.epoll_ctl``; modifies an epoll interest list
   * - SYNC_FILE_RANGE
     - ``raw_ops.sync_file_range``; descriptor, offset, length and range flags; correlated CQEs, not durable fsync
   * - SENDMSG / RECVMSG
     - ``ring.sendmsg`` / ``recvmsg``; stable native message headers and nested storage
   * - SEND / RECV
     - ``ring.send`` / ``recv``; socket bytes and message flags
   * - TIMEOUT / TIMEOUT_REMOVE
     - ``ring.timeout`` / ``timeout_remove``; timespec/count or target tag
   * - ACCEPT / CONNECT
     - ``ring.accept`` / ``connect``; stable socket addresses; accept returns a descriptor
   * - ASYNC_CANCEL / LINK_TIMEOUT
     - ``ring.cancel`` / ``link_timeout``; separate target/timer completions and races
   * - FALLOCATE
     - ``ring.fallocate``; file space operation, mode, offset and length
   * - FADVISE / MADVISE
     - ``raw_ops.fadvise`` / ``madvise``; explicit Linux SQE encodings
   * - OPENAT / OPENAT2
     - ``ring.openat`` / ``raw_ops.openat2``; relative path and access/resolution rules
   * - CLOSE / STATX
     - ``ring.close`` / ``statx``; descriptor ownership / stable metadata output
   * - SPLICE
     - ``ring.splice``; at least one pipe, value offsets and operation flags
   * - FILES_UPDATE
     - ``sqe.prep_files_update``; asynchronous table replacement
   * - PROVIDE_BUFFERS / REMOVE_BUFFERS
     - ``ring.provide_buffers`` / ``remove_buffers``; selected-buffer group management

Historical minimum kernels range from 5.1 for basic rings to 5.7 for splice and
provided buffers. Use :ref:`probing_zig` and actual CQEs instead of treating that
version range as a universal capability promise. Newer enum members and features
are not automatically covered by the historical tutorial set.

SQE flags
---------

``IOSQE_FIXED_FILE``
   Interpret SQE ``fd`` as a registered-file table index.

``IOSQE_IO_DRAIN``
   Hold this request until prior work completes and order later work behind it,
   subject to the kernel's drain rules. Different from a dependency chain.

``IOSQE_IO_LINK``
   Link to the next SQE; the first entry without the bit ends the chain. An
   unsuccessful/unexpected result can cancel the remaining unstarted members
   with ``-ECANCELED``. Unrelated requests/chains remain independent.

``IOSQE_IO_HARDLINK``
   Preserve a submitted chain across completion-result failures; submission
   failure can still break it. Do not require a separate soft-link bit to use
   the kernel's hard-link semantics.

``IOSQE_ASYNC``
   Request asynchronous issue from the start rather than the inline-first attempt.
   It does not by itself establish dependencies or order CQ arrival.

Add flags after preparation with ``|=`` to preserve constructor-set bits;
assignment deliberately replaces the whole bitmap. See :ref:`link_zig` for real
successful and cancelled chains.

Errors and recovery
-------------------

The enter call can report ``AGAIN``/``BUSY`` for resource pressure; drain available
completions and retry where appropriate. ``INTR`` is an interrupted wait.
``BADF``/``OPNOTSUPP`` can indicate the wrong ring descriptor; ``NXIO`` can
indicate teardown. Invalid arguments/unsupported modes report ``INVAL`` or
other errno according to kernel version. Do not reuse old blanket restrictions
(for example, forbidding ordinary vectored I/O merely because buffers are
registered) as current-kernel rules.

Invalid request descriptors, inaccessible buffers, wrong registered ranges,
unsupported opcodes/flags and other request errors must also be handled through
CQEs. A successful enter is not a successful operation. The wrapper exposes
named Zig enter errors; completed-operation errors remain negative ``cqe.res``.

See :ref:`io_uring_setup` and :ref:`io_uring_register`.
