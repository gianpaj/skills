# Synthetic two-origin regression test. Requires agent-browser and Node 24.
# No personal browser or real website is accessed.
import http.server
import json
import os
import pathlib
import subprocess
import tempfile
import threading

root = pathlib.Path(tempfile.mkdtemp(prefix="teardown-scope-"))
os.chmod(root, 0o700)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.headers.get("Host", "").split(":")[0]
        label = "a" if host == "127.0.0.1" else "b"
        ok = f"synthetic_{label}=session-{label}" in self.headers.get("Cookie", "")
        body = f"<h1>{'Authenticated ' + label if ok else 'Signed out'}</h1>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
port = server.server_port
urls = {"a": f"http://127.0.0.1:{port}/", "b": f"http://localhost:{port}/"}
prefix = f"scope-{os.getpid()}"
source = prefix + "-source"
attached = prefix + "-attached"
restore = prefix + "-restore"
scoped = prefix + "-scoped"
control = prefix + "-control"


def ab(session, *args):
    p = subprocess.run(
        ["agent-browser", "--session", session, *args],
        capture_output=True,
        text=True,
        timeout=40,
    )
    if p.returncode:
        raise RuntimeError(f"{args[0]} failed: {p.stderr[:250]}")
    return p.stdout.strip()


def shape(path):
    s = json.loads(path.read_text())
    return {
        "cookie_domains": sorted(set(c["domain"] for c in s["cookies"])),
        "origins": [o["origin"] for o in s["origins"]],
    }


try:
    for i, label in enumerate(["a", "b"]):
        ab(source, *(["open", urls[label]] if not i else ["tab", "new", urls[label]]))
        ab(
            source,
            "eval",
            f'document.cookie="synthetic_{label}=session-{label}; Path=/"; localStorage.setItem("marker", "local-{label}"); sessionStorage.setItem("marker", "session-{label}"); true',
        )
    urls["a"] += "?capture=1"
    ab(source, "tab", "new", urls["a"])
    ab(source, "eval", 'sessionStorage.setItem("marker","session-a"); true')
    ab(source, "state", "save", str(root / "owned.json"))
    endpoint = ab(source, "get", "cdp-url")
    ab(attached, "connect", endpoint)
    ab(attached, "--pin-tab", "state", "save", str(root / "attached.json"))
    ab(control, "open", urls["a"])
    assert ab(control, "get", "text", "h1") == "Signed out"
    ab(restore, "--state", str(root / "attached.json"), "open", urls["a"])
    results = {
        "version": subprocess.check_output(
            ["agent-browser", "--version"], text=True
        ).strip(),
        "owned_export": shape(root / "owned.json"),
        "attached_export": shape(root / "attached.json"),
    }
    checks = {}
    for label in ["a", "b"]:
        ab(restore, "open", urls[label])
        checks[label] = {
            "heading": ab(restore, "get", "text", "h1"),
            "storage": json.loads(
                ab(
                    restore,
                    "eval",
                    '({local:localStorage.getItem("marker"),session:sessionStorage.getItem("marker")})',
                )
            ),
        }
    results["builtin_restore"] = checks
    assert all(checks[x]["heading"] == f"Authenticated {x}" for x in ["a", "b"])
    assert checks["a"]["storage"] == {"local": "local-a", "session": "session-a"}
    assert checks["b"]["storage"] == {"local": None, "session": None}
    for key in ["owned_export", "attached_export"]:
        assert results[key]["cookie_domains"] == ["127.0.0.1", "localhost"]
        assert results[key]["origins"] == [f"http://127.0.0.1:{port}"]
    script = str(pathlib.Path(__file__).with_name("export-origin-state.mjs"))
    p = subprocess.run(
        ["node", script, endpoint, urls["a"], str(root / "scoped.json")],
        capture_output=True,
        text=True,
        timeout=25,
    )
    if p.returncode:
        raise RuntimeError(p.stderr)
    results["scoped_export"] = shape(root / "scoped.json")
    assert results["scoped_export"]["cookie_domains"] == ["127.0.0.1"]
    ab(scoped, "--state", str(root / "scoped.json"), "open", urls["a"])
    assert ab(scoped, "get", "text", "h1") == "Authenticated a"
    ab(scoped, "open", urls["b"])
    assert ab(scoped, "get", "text", "h1") == "Signed out"
    results["scoped_restore"] = {"a": "Authenticated a", "b": "Signed out"}
    print(json.dumps(results, indent=2))
    (root / "results.json").write_text(json.dumps(results, indent=2))
    print("RESULTS_DIR=" + str(root))
finally:
    for session in [control, restore, scoped, source]:
        try:
            ab(session, "close")
        except Exception:
            pass
    server.shutdown()
    for name in ["owned.json", "attached.json", "scoped.json"]:
        (root / name).unlink(missing_ok=True)
