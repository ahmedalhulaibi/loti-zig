"""Controlled observer/collector fixtures; no application implementation reuse."""
import json
import os
import signal
import socket
import sys


if sys.argv[1] == "malformed-output":
    os.write(1, b"{\n")
    signal.pause()
elif sys.argv[1] == "fast-close":
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    print(json.dumps({"event": "loti.http.ready", "address": "127.0.0.1",
                      "port": listener.getsockname()[1]}), flush=True)
    peer, _ = listener.accept()
    peer.close()
    listener.close()
    os.writev(2, [b"controlled fast-close fixture\n"])
    sys.exit(1)
else:
    raise ValueError("UnknownLifecycleControl")
