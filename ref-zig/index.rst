Native Zig reference
====================

This reference targets **exactly Zig 0.17.0**, not a different stable release or
an arbitrary development build. ``linux`` means ``std.os.linux``; ``posix`` means
``std.posix``. ``IoUring`` is ``linux.IoUring``. The generated declarations retain
SDK-local names such as ``ReadBuffer`` and ``RecvBuffer``; they are interface
signatures, not independent runnable programs.

Methods that prepare requests return ``!*linux.io_uring_sqe``. Their success
means preparation, not execution. Methods that copy completions consume them;
methods that borrow queue storage do not. Negative CQE results are operation
errors even when submission and waiting succeeded.

``RawRing`` and ``raw_ops`` are repository helpers, not invented standard-library
methods. Their complete compiled sources are included where used. Signatures
are generated from ``conversion/reference-map.json``, whose SDK source hashes
and declarations are checked against the installed compiler. Runnable examples
provide a separate execution boundary; constructor evidence is identified as such.

.. toctree::
   :maxdepth: 1

   sqe
   cqe
   supported_caps
   setup_teardown
   submission
   completion
   advanced_usage
