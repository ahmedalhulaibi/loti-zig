.. _webserver_zig:

An asynchronous HTTP server in Zig
========================================

This program recreates ZeroHTTPd's teaching purpose: accept a connection, read a
request and write a static-file response through ``io_uring``. It uses native
Zig 0.17.0 ``accept``, ``recv``, ``read`` and ``send`` requests. Socket I/O and
file-data reads share one completion loop; no external ring library is needed.

Shuveb Hussain's original server and
`process-model article <https://unixism.net/2019/04/linux-applications-performance-introduction/>`_
provide the example's origin. This screenshot shows the original demonstration,
not a captured result from the Zig program:

.. image:: ../_static/ZeroHTTPd_static.png
   :align: center
   :alt: Original ZeroHTTPd static-page demonstration

Run it
------

.. code-block:: console

   zig build
   zig-out/bin/webserver public 8080
   curl --fail http://127.0.0.1:8080/

Run ``curl`` from another terminal. ``public/index.html`` is included in the
repository. The first terminal prints a JSON readiness record containing the
actual listening address and port. Port ``0`` asks the kernel to choose a port;
the tests use that returned value. The server binds **only to 127.0.0.1**.
Ctrl-C stops the process through the operating system's normal signal handling.

The confined path open uses ``openat2`` (Linux 5.6+). Check actual setup and
operation results rather than reporting success from a kernel-version string.

State and request identity
--------------------------

The server owns 32 stable ``Client`` slots and a 64-entry ring. Tag ``0`` denotes
the outstanding accept. Client tags are slot index plus one. Each occupied slot
has exactly one outstanding operation, so a completion identifies both its
client and its current phase without returning an application pointer.

The phases are receiving, loading the file, sending headers, sending the body,
and idle. A successful accept starts reception and queues the next accept.
A socket read that is still waiting does not block another client's state
transition. If every slot is occupied, newly accepted connections are closed;
this is a bounded demonstration, not an overload-management design.

Partial I/O
-----------

TCP does not preserve application message boundaries. ``request_len`` accumulates
fragments until the header terminator arrives. File reads advance ``progress``
until the advertised size is available. Header and body sends also advance by
the actual completed count and resubmit the remaining range.

Zero-byte reception closes an unfinished connection. Zero-byte file reception
before the expected size yields an internal-error response. Socket failures
release the client instead of terminating the entire server. ``MSG.NOSIGNAL``
prevents an abandoned response from raising SIGPIPE.

The request ledger records an operation before any later fallible callback and
retires it when its terminal completion is copied. The client keeps its operands
until that retirement. ``ring.copy_cqe()`` already consumes the completion; there
is no additional ``cqe_seen`` call. Fatal cleanup stops the state machine, replaces
only unpublished SQEs with tagged NOPs, submits one cancellation control at a time,
and drains target completions before resources can be released. A cancellation
receipt alone does not retire a target. Successful ACCEPT results are closed even
if they were not dispatched to a client slot; descriptor zero is valid.
``IORING_CQE_F_SOCK_NONEMPTY`` is a socket hint, not ``IORING_CQE_F_MORE``;
it does not prevent a one-shot request from retiring.

Optional ``webserver DOCUMENT_ROOT PORT --observe-send`` reports actual prepared
SEND ranges/flags and tagged CQEs after readiness. It sets ``SO_SNDBUF`` to 4096
on each owned accepted socket and queries Linux's doubled 8192-byte value.
Default mode does not change these socket buffers or emit send observations.

The bounded TCP contract uses a 131072-byte pseudorandom file and a client with
``SO_RCVBUF`` 4096. It requires a positive short body-send CQE before the client
drains data or resets its connection. Independent wire bytes check complete
progress/storage; a later 37-byte GET checks that a reset did not stop the server.

Address-relative SQE offsets and lengths show which retained bytes are queued;
completion counts advance the remaining range. The observer queries socket
retirement before reporting closure. This is sequential current-kernel evidence,
not forced SIGPIPE delivery, partial header sends, every transport/flag/error,
concurrent send races or production assurance.

HTTP and filesystem boundary
----------------------------

Only case-sensitive ``GET`` with an HTTP/1.0 or HTTP/1.1 request line is supported.
A trailing slash selects ``index.html``. Query text does not become a filename.
Percent escapes are decoded once; invalid escapes and control bytes are rejected.

The document root is opened once as a directory descriptor. ``openat2`` uses
``RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS`` to prevent root escape and symlink
following during lookup. The parser also rejects ``..`` components, backslashes
and decoded absolute paths. Concatenating a root string with an untrusted path
would not provide this confinement.

Regular files are limited to 4 MiB; request headers are limited to 8192 bytes.
Metadata lookup and the confined open are synchronous. File content is read
asynchronously into an owned buffer. This is not a streaming, zero-copy, or
atomic-filesystem-snapshot implementation.

Responses always include an exact ``Content-Length`` and ``Connection: close``.
Extension matching is case-insensitive; HTML, JPEG, PNG, GIF, JavaScript, CSS and
text have known MIME types. Other extensions use ``application/octet-stream``.

.. list-table:: Defined response classes
   :header-rows: 1

   * - Status
     - Condition
   * - 200
     - Regular static file, including an empty file
   * - 400
     - Invalid request line, target or percent escape
   * - 403
     - Forbidden path or kernel-rejected confinement/permission check
   * - 404
     - Missing target or nonregular opened target
   * - 405
     - Unsupported method
   * - 413
     - File exceeds the configured limit
   * - 431
     - Header buffer fills without a terminator
   * - 500
     - Other open, metadata or premature file-read failure

Complete source
---------------

.. literalinclude:: ../examples/webserver.zig
   :language: zig
   :caption: Native Zig HTTP state machine

``raw_ops.OpenHow`` supplies the explicit three-u64 Linux ``openat2`` layout;
its shared definition and executable raw-operation example are in this repository.

Verification and limits
-----------------------

``tests/test_http.py`` uses real TCP connections. It checks whole binary bodies,
MIME values and lengths; missing, malformed, method, traversal and symlink cases;
fragmented requests; concurrent clients; and a completing request beside a stalled
client. These checks are not a production HTTP conformance or security audit.

There is no TLS, keep-alive, request-body handling, header-field validation,
per-client deadline or streaming-file transfer. Do not expose this teaching
server as an Internet-facing service. A direct regression now verifies pre-exit
closure for the reproduced late-ACCEPT defect. Broader failure-path and
heap-retirement validation remains in progress. Cleanup retains operands and
waits if submission, cancellation or completion cannot progress; it has no
bounded shutdown guarantee. Do not treat ``defer ring.deinit()`` as an
operand-retirement barrier or this example as a production fatal-cleanup pattern.
