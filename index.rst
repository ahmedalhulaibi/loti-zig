Lord of the io_uring — Zig 0.17.0
========================================

Learn Linux asynchronous I/O with native Zig 0.17.0. The guide covers shared
rings, a raw reader, pipelined file copying, an asynchronous HTTP server, runtime
probing, linked requests, registered resources and the Linux syscall interface.
No libc, foreign-language imports or external ring library is required.

About and attribution
---------------------

Shuveb Hussain wrote the original
`Lord of the io_uring <https://github.com/shuveb/loti>`_ and the Linux-focused
`unixism.net <https://unixism.net>`_ articles. Ahmed Alhulaibi's
`Zig edition <https://github.com/ahmedalhulaibi/loti-zig>`_ recreates the examples
and replaces language-specific explanations. Original illustrations and the
MIT licence remain. Historical screenshots are identified as original material.

Source and build
----------------

Guide, examples and tests live in the Zig-edition repository. Report edition
bugs and contribute there, not to a separate examples repository. Included code
is taken directly from the compiled ``examples/`` files.

.. code-block:: console

   zig version
   zig build
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.lock
   LOTI_TEST_CASES=400 .venv/bin/python -m unittest discover
   make html
   make epub

``zig version`` must print exactly ``0.17.0``; the build enforces this. Run on
Linux with io_uring permitted by host/container policy. The examples use explicit
runtime capability checks rather than infer support only from version numbers.
The timed-wait helper needs Linux 5.11+; the HTTP confined open needs 5.6+.

The code and book have not yet passed the required independent review. See the
repository's ``conversion/audit.md`` for evidence and outstanding gates.

.. toctree::
   :maxdepth: 1
   :caption: Introduction

   async_intro
   what_is_io_uring
   low_level

.. toctree::
   :maxdepth: 2
   :caption: Tutorial

   tutorial/index

.. toctree::
   :maxdepth: 2
   :caption: Native Zig reference

   ref-zig/index

.. toctree::
   :maxdepth: 2
   :caption: Linux syscall reference

   ref-iouring/index

.. toctree::
   :maxdepth: 1
   :caption: Edition history

   changelog
   license
