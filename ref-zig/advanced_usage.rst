.. _advanced_usage:

Registered resources
====================

Registration reduces per-request resource lookup or mapping work. It does not
transfer ownership of application allocations, remove lifetime requirements or
guarantee faster I/O for every workload. These interfaces use Zig error unions.
Raw registration opcodes and resource limits are described in
:ref:`io_uring_register`.

Buffers and files
-----------------

``register_buffers`` takes ``[]const posix.iovec``. Keep every referenced range
stable until dependent operations finish and registration ends.
``unregister_buffers`` releases the table. Fixed requests select an index plus
an address range inside that entry; see :ref:`fixed_buffers` for actual I/O.

``register_files`` takes ``[]const linux.fd_t``. SQEs using ``IOSQE_FIXED_FILE``
address this table by index instead of process descriptor. A sparse entry is
``-1`` where supported. ``register_files_update(offset, fds)`` replaces a table
range synchronously; ``unregister_files`` releases the table. This is distinct
from an asynchronous SQE ``prep_files_update``. Finish dependent requests before
releasing or repurposing their resources. See :ref:`sq_poll` for fixed-file I/O.

Event notification
------------------

``register_eventfd`` attaches an eventfd counter descriptor for CQ notifications.
``register_eventfd_async`` omits completions performed inline during submission.
Only one eventfd is registered per ring; ``unregister_eventfd`` detaches it.
Notification counts do not identify requests and can be coalesced. Reap the CQ
and inspect results; do not equate a counter read with successful I/O. See
:ref:`register_eventfd` for the threaded read demonstration.

Credentials
-----------

Repository ``raw_ops.register_personality`` calls raw registration and returns
a u16 credential ID. Set the prepared SQE's ``personality`` field to use it.
``raw_ops.unregister_personality`` releases that ID after dependent requests
finish. These are helpers, not ``IoUring`` methods. Registration captures current
credentials; it does not grant privileges the caller did not have. Sharing a
ring across users/processes still needs lifecycle and access-control design.

Exact native declarations
-------------------------

.. include:: _api/advanced_usage.inc

Executable reference
--------------------

.. code-block:: console

   zig build
   zig-out/bin/reference-registration input.bin

.. literalinclude:: ../examples/reference_registration.zig
   :language: zig
   :caption: Registration, table update, async notification, credentials and probes

``tests/test_reference.py`` checks the complete result shape. The reference
registers/unregisters a buffer and file table and updates the table; those steps
do not by themselves prove data I/O. Tutorial programs supply that evidence.
An ``IOSQE_ASYNC`` NOP produces an actual async eventfd notification. A separate
NOP executes with the registered personality. Both probe paths query the kernel.
The complete ``raw_ops`` implementation is included in :ref:`submission`.
