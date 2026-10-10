.. _io_uring_register:

``linux.io_uring_register``
===========================

Register resources or query capabilities on an existing ring. Native Zig
0.17.0 exposes:

.. include:: _api/io_uring_register.inc

``fd`` is the ring descriptor. ``opcode`` is a ``linux.IORING_REGISTER`` enum,
not an untyped integer macro. ``arg`` is an optional stable pointer to
opcode-specific input/output storage; ``nr_args`` is also opcode-specific.
Decode the raw result with ``linux.errno``. Success is often zero, but
personality registration returns an ID and update operations can report counts.
Do not assume every registration returns zero.

Buffers
-------

``REGISTER_BUFFERS`` takes a ``std.posix.iovec`` array and element count. It pins
or references supplied memory for later fixed operations; memory-lock limits and
kernel resource rules apply. Keep ranges stable. A fixed request's address and
length must fit the selected registered index; using only part of a range is
valid. ``UNREGISTER_BUFFERS`` takes null/zero and releases the registration.

Historical kernels restricted buffers to anonymous memory and imposed a 1-GiB
per-buffer limit; supported backing types and limits evolve. Consult the target
kernel and actual registration result instead of treating those old restrictions
as an unconditional modern ABI promise. Huge-page registration can account for
more memory than the requested subrange. Registration can synchronise with
outstanding work; finish dependencies before changing a table. Ring teardown
releases kernel registration but does not free application allocations.

Files
-----

``REGISTER_FILES`` takes a ``linux.fd_t`` array and count. Fixed-file SQEs set
``IOSQE_FIXED_FILE`` and put a table index in ``fd``. ``-1`` creates a sparse entry
where supported. ``REGISTER_FILES_UPDATE`` takes a native
``linux.io_uring_files_update`` containing a table offset and descriptor pointer;
``nr_args`` counts replacements. ``UNREGISTER_FILES`` takes null/zero.

``IoUring.register_files_update`` handles that ABI structure synchronously.
``sqe.prep_files_update`` instead prepares an asynchronous update request, with
its own CQE. Table references and process descriptor ownership are different;
closing a process descriptor is not the same as unregistering a table entry.
Release resources only after their dependent requests finish.
The :ref:`registration reference <advanced_usage>` demonstrates both update paths,
fixed reads after closing the replacement process descriptor, sparse removal and
table unregistration. Its asynchronous update returns a CQE count of one.

Eventfd
-------

``REGISTER_EVENTFD`` takes a pointer to one eventfd descriptor and ``nr_args=1``.
``REGISTER_EVENTFD_ASYNC`` has the same arguments but omits notifications for
inline completions. ``UNREGISTER_EVENTFD`` takes null/zero. Only one eventfd is
attached at a time. Counter reads can coalesce notifications and do not identify
which request completed. Always reap/check CQEs. See :ref:`register_eventfd` and
the forced-async NOP in :ref:`advanced_usage`.

Probes and credentials
----------------------

``REGISTER_PROBE`` receives ``linux.io_uring_probe`` output storage;
``nr_args`` gives the capacity of its operation array, not bytes. Zero reserved
storage. The kernel fills ``ops_len`` and supported flags. See
:ref:`supported_caps` for exact native types and query helpers.

``REGISTER_PERSONALITY`` takes null/zero, captures current credentials and returns
an ID. Store that u16 ID in a prepared SQE's ``personality`` field.
``UNREGISTER_PERSONALITY`` takes null with the ID in ``nr_args``. Finish dependent
operations before unregistering. Repository ``raw_ops`` implements both helpers;
they are not standard ``IoUring`` methods. The reference executes a NOP with the
registered credential ID, not just registration/unregistration.

Basic buffers/files date to Linux 5.1; eventfd to 5.2; file-table update to 5.5;
async eventfd, probes and personalities to 5.6. These dates are context, not
runtime evidence. Newer registration families are outside the original scope.

Errors and native examples
--------------------------

``BADF`` identifies invalid descriptors; ``BUSY`` can indicate an existing
registration or a conflicting operation. ``FAULT`` identifies inaccessible
storage; ``INVAL`` covers invalid counts/flags/opcode-specific arguments.
``MFILE`` and ``NOMEM`` can identify file-reference or memory/resource limits;
``NXIO`` can identify absent registration or teardown. Unsupported resource
backing/modes may report ``OPNOTSUPP``. Exact limits and privilege exceptions
depend on the kernel. Do not ignore registration failure and then issue a fixed
operation against a table that was never established.

The :ref:`registered-resource reference <advanced_usage>` includes all converted
native methods and its complete executable. ``tests/test_reference.py`` checks
table setup/update, actual async notification, credential NOP and both probes.
:ref:`fixed_buffers` and :ref:`sq_poll` separately verify registered data I/O.

See :ref:`io_uring_setup` and :ref:`io_uring_enter`.
