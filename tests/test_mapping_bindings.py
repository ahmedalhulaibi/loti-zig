"""The published binding manifest must describe current mapping ownership."""
import json
import unittest

from tests.test_examples import ROOT


class MappingBindingContracts(unittest.TestCase):
    def test_mapping_and_fork_bindings_describe_all_owned_regions(self):
        bindings = {row["original"]: row for row in json.loads((ROOT / "conversion/reference-map.json").read_text())["entries"]}
        for original, native, scope, difference, signature in [
            ("io_uring_queue_mmap", "RawRing.map",
             "compiled; both mapping strategies execute; five private-descriptor x86_64 seccomp mmap failures verify partial unwind and caller FD ownership",
             "Accepts an existing setup descriptor; owns it only on success. Selects shared SQ/CQ or separate SQ/CQ plus SQEs by SINGLE_MMAP; failure unmaps partial regions but leaves the FD to the caller.",
             "pub fn map(fd: linux.fd_t, params: linux.io_uring_params) !RawRing"),
            ("io_uring_ring_dontfork", "RawRing.dontFork",
             "compiled; per-page mincore in child verifies all owned regions excluded, while fcntl verifies FD inheritance",
             "Applies MADV_DONTFORK to every owned SQ/CQ/SQE region; excludes memory, not descriptor inheritance.",
             "pub fn dontFork(self: *RawRing) !void"),
        ]:
            with self.subTest(original=original):
                self.assertEqual(bindings[original], {
                    "original": original, "zig": native, "example": "examples/reference_setup.zig",
                    "verification_scope": scope, "semantic_difference": difference,
                    "declaration_source": "examples/raw_cat.zig", "zig_signature": signature,
                })


if __name__ == "__main__":
    unittest.main()
