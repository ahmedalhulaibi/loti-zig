Native Zig examples
===================

``std.os.linux.IoUring`` manages ring setup, mappings, publication and completion
consumption. Your application owns operands and request state. Each chapter
includes the exact repository source compiled by ``zig build`` and exercised
through its CLI or TCP boundary. The :ref:`low_level` chapter remains useful
for understanding what the native wrapper does.

.. toctree::
   :maxdepth: 1

   cat
   cp
   webserver
   probe
   link
   fixed_buffers
   sq_poll
   register_eventfd
