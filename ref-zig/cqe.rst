.. _cqe:

CQE: completion queue entry
===========================

``linux.io_uring_cqe`` is an ``extern struct``. Ordinary CQEs occupy 16 bytes;
CQE32 rings use a larger stride. The SDK definition includes result decoding
and provided-buffer identity helpers:

.. include:: _api/cqe.inc

``user_data`` is the submission's u64 tag, not a kernel-generated request ID.
``res`` is the operation result: byte count for successful data I/O, descriptor
for a successful open/accept, or negative Linux errno for a failed request.
``cqe.err()`` decodes errno; success alone does not prove the requested count
was transferred. Zero bytes can mean EOF, peer shutdown or no progress, depending
on the operation.

``flags`` is meaningful. ``IORING_CQE_F_BUFFER`` indicates a selected provided
buffer; ``buffer_id()`` returns its upper-bit ID or ``error.NoBufferSelected``.
The :ref:`provided-buffer example <provided_buffers>` executes those paths:
IDs 257/513 are decoded from actual flags, plain/exhausted CQEs have no selected
ID, and exact storage snapshots track consumption/recycling/removal.
``IORING_CQE_F_MORE`` can indicate further completions from a multishot request.
The simple tutorial operations are one-shot, but **one SQE does not universally
mean one CQE**: multishot, notification and skipped-success features differ.
Do not apply the tutorial's one-shot lifetime rule to those features unchanged.

``copy_cqe`` and ``copy_cqes`` return owned values and advance CQ head. A pointer
borrowed directly from CQ storage is valid only until that slot is acknowledged
and reused. The application must acknowledge a borrowed entry exactly once,
but must not acknowledge a copied entry again. See :ref:`completion`.

The kernel does not execute unrelated operations in application completion
order. Correlate by tag. Linked dependencies control execution within a chain;
they do not remove the need for request identity. ``reference-setup`` checks CQE
size; ``reference-completion`` exercises both copied and borrowed batches.
