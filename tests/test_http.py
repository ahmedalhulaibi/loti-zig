"""Real TCP boundary checks for the asynchronous example."""

import concurrent.futures
import http.client
import json
from pathlib import Path
import select
import socket
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent


class HttpContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name) / "public"
        cls.root.mkdir()
        cls.files = {
            "index.html": b"<h1>Lord of the io_uring</h1>\n",
            "empty.txt": b"",
            "data.bin": bytes(range(256)) * 1025,
            "image.JpG": b"jpeg fixture",
            "script.js": b"console.log('io_uring');\n",
            "style.css": b"body { color: black; }\n",
            "plain.txt": b"plain text\n",
        }
        for name, payload in cls.files.items():
            (cls.root / name).write_bytes(payload)
        (cls.root / "sub").mkdir()
        (cls.root / "sub/index.html").write_bytes(b"nested index\n")
        secret = cls.root.parent / "secret.txt"
        secret.write_bytes(b"must not leave the document root")
        (cls.root / "escape.txt").symlink_to(secret)
        (cls.root / "outside").symlink_to(cls.root.parent, target_is_directory=True)
        cls.process = subprocess.Popen(
            [str(ROOT / "zig-out/bin/webserver"), str(cls.root), "0"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        assert cls.process.stdout is not None
        assert cls.process.stderr is not None
        if not select.select([cls.process.stdout], [], [], 5)[0]:
            cls.process.kill()
            raise AssertionError("Server did not report its listening address")
        line = cls.process.stdout.readline()
        if not line:
            raise AssertionError(cls.process.stderr.read().decode(errors="replace"))
        cls.ready = json.loads(line)
        cls.port = cls.ready["port"]

    @classmethod
    def tearDownClass(cls):
        assert cls.process.stdout is not None
        assert cls.process.stderr is not None
        cls.process.terminate()
        try:
            cls.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.process.kill()
            cls.process.wait(timeout=5)
        cls.process.stdout.close()
        cls.process.stderr.close()
        cls.directory.cleanup()

    def request(self, raw, fragments=None):
        with socket.create_connection(("127.0.0.1", self.port), timeout=5) as client:
            client.settimeout(5)
            if fragments is None:
                client.sendall(raw)
            else:
                for fragment in fragments:
                    client.sendall(fragment)
                    time.sleep(0.005)
            client.shutdown(socket.SHUT_WR)
            response = http.client.HTTPResponse(client)
            response.begin()
            body = response.read()
            headers = {name.lower(): value for name, value in response.getheaders()}
            self.assertEqual(headers["content-length"], str(len(body)))
            self.assertEqual(headers["connection"], "close")
            return response.status, headers["content-type"], body

    def test_get_mime_length_and_binary_body(self):
        cases = [
            ("/", "text/html", self.files["index.html"]),
            ("/empty.txt", "text/plain", b""),
            ("/data.bin", "application/octet-stream", self.files["data.bin"]),
            ("/image.JpG", "image/jpeg", self.files["image.JpG"]),
            ("/script.js", "application/javascript", self.files["script.js"]),
            ("/style.css", "text/css", self.files["style.css"]),
            ("/plain.txt?ignored=query", "text/plain", self.files["plain.txt"]),
            ("/sub/", "text/html", b"nested index\n"),
        ]
        for target, mime, body in cases:
            with self.subTest(target=target):
                request = f"GET {target} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode()
                self.assertEqual(self.request(request), (200, mime, body))

    def test_defined_error_responses_and_root_confinement(self):
        cases = [
            (b"GET /missing HTTP/1.1\r\n\r\n", 404, b"Not Found\n"),
            (b"POST / HTTP/1.1\r\n\r\n", 405, b"Method Not Allowed\n"),
            (b"broken\r\n\r\n", 400, b"Bad Request\n"),
            (b"GET /%xx HTTP/1.1\r\n\r\n", 400, b"Bad Request\n"),
            (b"GET /%00 HTTP/1.1\r\n\r\n", 400, b"Bad Request\n"),
            (b"GET /../secret.txt HTTP/1.1\r\n\r\n", 403, b"Forbidden\n"),
            (b"GET /%2e%2e/secret.txt HTTP/1.1\r\n\r\n", 403, b"Forbidden\n"),
            (b"GET /escape.txt HTTP/1.1\r\n\r\n", 403, b"Forbidden\n"),
            (b"GET /outside/secret.txt HTTP/1.1\r\n\r\n", 403, b"Forbidden\n"),
            (b"GET / HTTP/1.1\r\nX: " + b"x" * 9000 + b"\r\n\r\n", 431, b"Request Header Fields Too Large\n"),
        ]
        for request, status, body in cases:
            with self.subTest(status=status, request=request[:40]):
                self.assertEqual(self.request(request), (status, "text/plain", body))

    def test_fragmented_request_and_concurrent_clients(self):
        raw = b"GET /plain.txt HTTP/1.1\r\nHost: localhost\r\n\r\n"
        self.assertEqual(self.request(raw, [raw[:2], raw[2:17], raw[17:]]), (200, "text/plain", self.files["plain.txt"]))
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: self.request(raw), range(24)))
        self.assertEqual(responses, [(200, "text/plain", self.files["plain.txt"])] * 24)

    def test_one_slow_client_does_not_block_other_clients(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=5) as slow:
            slow.sendall(b"GET /plain")
            response = self.request(b"GET /plain.txt HTTP/1.1\r\n\r\n")
            self.assertEqual(response, (200, "text/plain", self.files["plain.txt"]))


if __name__ == "__main__":
    unittest.main()
