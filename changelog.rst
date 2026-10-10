.. _changelog:

Edition history
===============

Zig 0.17.0 edition
------------------

The native edition recreates all tutorial programs, replaces foreign-language
API declarations with Zig interfaces and supplies runnable reference examples.
The immutable original-line inventory and conversion audit remain in the
repository. Git history records implementation changes; ``conversion/audit.md``
records verified gates and incomplete requirements.

Original update: 2020-06-15
---------------------------

Shuveb Hussain added the ``IORING_FEAT_SINGLE_MMAP`` explanation: SQ and CQ can
share one mapping; SQEs still require a separate mapping. This reduces the usual
three mappings to two. The explanation remains in :ref:`what_is_io_uring` and
:ref:`low_level` with native Zig code.
