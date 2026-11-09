"""A stand-in for the R2 bucket during UI tests: serves Documents/CLAUDE/sayback-audio under the bucket's names.

    python tools/testing/audio_server.py [port]      (default 8799; ui_test.py starts and stops it)

GET /en-es/L1/L1-01.mp3 -> sayback-audio/en-es/L1/"L1-01 <title>.mp3", with byte ranges (seeking needs them);
GET /en-es/L1/L1-01.txt -> the lesson's transcript. Admin > Shop & setup's test address points here in the tests.
"""
import http.server
import pathlib
import re
import sys

AUDIO = pathlib.Path(__file__).resolve().parents[3] / "sayback-audio"


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _file(self):
        m = re.fullmatch(r"/(en-es|es-en)/L([1-5])/(L[1-5]-\d\d)\.(mp3|txt)", self.path.split("?")[0])
        if not m:
            return None, None
        course, level, code, ext = m.groups()
        folder = AUDIO / course / ("L" + level)
        if ext == "txt":
            f = folder / (code + ".txt")
            return (f if f.exists() else None), "text/plain; charset=utf-8"
        hits = sorted(folder.glob(code + " *.mp3"))
        return (hits[0] if hits else None), "audio/mpeg"

    def do_HEAD(self):
        self.do_GET(head=True)

    def do_GET(self, head=False):
        f, ctype = self._file()
        if f is None:
            self.send_error(404)
            return
        size = f.stat().st_size
        start, end = 0, size - 1
        rng = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if rng and (rng.group(1) or rng.group(2)):
            if rng.group(1):
                start = int(rng.group(1))
                end = int(rng.group(2)) if rng.group(2) else size - 1
            else:
                start = max(0, size - int(rng.group(2)))
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if head:
            return
        with f.open("rb") as fh:
            fh.seek(start)
            left = end - start + 1
            try:
                while left > 0:
                    chunk = fh.read(min(65536, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8799
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
