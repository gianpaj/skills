#!/usr/bin/env python3
"""Exercise evidence-file checks using synthetic local artifacts only."""

import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPT = Path(__file__).with_name("check-evidence.py")


def png(width=16, height=2):
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    pixels = (b"\0" + b"\xff\xff\xff" * width) * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


class EvidenceChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_check(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_local_links_and_images_pass_without_changing_files(self):
        (self.root / "screen one.png").write_bytes(png())
        (self.root / "coverage.md").write_text("# Coverage\n")
        (self.root / "assessment.md").write_text("""
[Coverage](coverage.md#unchecked-anchor)
[Editor location](coverage.md:1)
![Screen](<screen one.png> "Caption")
![Encoded screen](screen%20one.png)
[Reference][coverage]
[coverage]: coverage.md
[Official source](https://example.com/not-fetched)
[Email](mailto:synthetic@example.com)
[Section](#local-anchor)
`[Code example](not-a-file)`
```markdown
[Another example](not-a-file)
```
""")
        (self.root / "gallery.html").write_text(
            '<img src="screen%20one.png"><a href="coverage.md">Coverage</a>'
        )
        before = {
            path.name: hashlib.sha256(path.read_bytes()).digest()
            for path in self.root.iterdir()
        }
        result = self.run_check("--expected-width", "16")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 errors, 0 warnings", result.stdout)
        after = {
            path.name: hashlib.sha256(path.read_bytes()).digest()
            for path in self.root.iterdir()
        }
        self.assertEqual(before, after)

    def test_missing_markdown_and_html_targets_fail(self):
        (self.root / "assessment.md").write_text("![Screen](missing.png)\n")
        (self.root / "gallery.html").write_text('<a href="missing.md">Report</a>')
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing target missing.png", result.stdout)
        self.assertIn("missing target missing.md", result.stdout)

    def test_missing_link_queries_are_not_printed(self):
        (self.root / "assessment.md").write_text(
            "![Screen](missing.png?token=synthetic-private-value#section)\n"
        )
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing target missing.png", result.stdout)
        self.assertNotIn("synthetic-private-value", result.stdout + result.stderr)

    def test_corrupt_and_truncated_pngs_fail(self):
        corrupt = bytearray(png())
        corrupt[20] ^= 1
        (self.root / "corrupt.png").write_bytes(corrupt)
        (self.root / "truncated.png").write_bytes(png()[:-12])
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("PNG checksum mismatch", result.stdout)
        self.assertIn("missing PNG end", result.stdout)

    def test_duplicate_and_unexpected_width_are_review_warnings(self):
        (self.root / "baseline.png").write_bytes(png())
        (self.root / "restored.png").write_bytes(png())
        (self.root / "popup.png").write_bytes(png(8))
        result = self.run_check("--expected-width", "16")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("byte-identical PNGs: baseline.png, restored.png", result.stdout)
        self.assertIn("popup.png: unexpected dimensions 8x2", result.stdout)
        mixed = self.run_check("--expected-width", "16", "--expected-width", "8")
        self.assertNotIn("unexpected dimensions", mixed.stdout)

    def test_invalid_directory_and_width_are_usage_errors(self):
        result = self.run_check("--expected-width", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("expected widths must be positive", result.stderr)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root / "missing")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("directory must exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
