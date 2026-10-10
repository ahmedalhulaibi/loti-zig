.. _register_eventfd:

Register an eventfd
===================

An ``eventfd`` is a Linux 64-bit counter descriptor. Register it with
``ring.register_eventfd(fd)`` to receive completion notifications. An existing
``poll``/``epoll`` loop can watch that descriptor instead of blocking directly
on the ring. The notification is a wakeup hint, not a CQE or request identity:
multiple completions can contribute to one counter read.

.. code-block:: console

   zig build
   zig-out/bin/register-eventfd input.bin > prefix.bin

This teaching program queues one read of at most 512 bytes. It then starts a
``std.Thread`` listener, which reads exactly eight bytes from the eventfd and
calls ``copy_cqe``. Notification-before-listener-start is safe because eventfd
retains its counter. No timing sleep is needed. The producer no longer touches
the ring while the listener handles completion; ``thread.join()`` synchronises
access to the listener result before the main thread reads it.

.. literalinclude:: ../examples/register_eventfd.zig
   :language: zig
   :caption: Native eventfd notification and listener thread

Only completed file bytes go to stdout. A JSON record on stderr reports
``notifications``, ``user_data`` and ``result``. ``tests/test_examples.py``
checks the complete prefix and those fields. A notification does not imply a
successful read; negative CQE results still need error handling.

The listener uses ``linux.read`` on the counter descriptor, retries ``INTR``
and checks the full eight-byte result. There is no foreign eventfd helper or
thread library. Registration ends before the eventfd is closed. Buffers, file,
ring and listener state stay alive until the thread has joined.

``register_eventfd_async`` notifies only for asynchronous completions, not inline
ones. The separate :ref:`registration example <advanced_usage>` forces an async
NOP to verify that path. A general multi-producer/multi-consumer ring needs more
synchronisation than this one-request demonstration provides.
