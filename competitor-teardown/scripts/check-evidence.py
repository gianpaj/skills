#!/usr/bin/env python3
"""Check local evidence files; this is not a visual or coverage assessment."""

import argparse
import hashlib
import re
import struct
import zlib
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))")
REFERENCE_LINK = re.compile(r"^\s*\[[^\]\n]+\]:\s*(?:<([^>\n]+)>|(\S+))", re.MULTILINE)


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        self.targets.extend(
            value for key, value in attrs if key in {"href", "src"} and value
        )


def markdown_targets(source):
    """Skip code examples; handle ordinary inline links and link definitions."""
    prose = []
    fence = None
    for line in source.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is None:
            prose.append(line)
    text = re.sub(r"(`+).*?\1", "", "\n".join(prose))
    targets = [
        match[1] or match[2]
        for pattern in (INLINE_LINK, REFERENCE_LINK)
        for match in pattern.finditer(text)
    ]
    html = HTMLLinks()
    html.feed(text)
    return targets + html.targets


def local_target(source, target):
    url = urlsplit(target)
    if url.scheme or url.netloc or not url.path:
        return None
    path = Path(unquote(url.path))
    path = path if path.is_absolute() else source.parent / path
    # Local editor links can have a line suffix; anchors are deliberately unchecked.
    if not path.exists() and re.search(r":\d+$", str(path)):
        path = Path(re.sub(r":\d+$", "", str(path)))
    return path


def png_dimensions(data):
    """Validate chunk framing and CRCs without implementing a PNG decoder."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("invalid PNG signature")
    offset = 8
    dimensions = None
    has_data = False
    while offset + 12 <= len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 12 + size
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        chunk = data[offset + 8 : offset + 8 + size]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + chunk) != crc:
            raise ValueError("PNG checksum mismatch")
        if dimensions is None:
            if kind != b"IHDR" or size != 13:
                raise ValueError("missing PNG header")
            dimensions = struct.unpack_from(">II", chunk)
            if 0 in dimensions:
                raise ValueError("zero PNG dimension")
        if kind == b"IDAT":
            has_data = True
        if kind == b"IEND":
            if size or not has_data or end != len(data):
                raise ValueError("invalid PNG end/data")
            return dimensions
        offset = end
    raise ValueError("missing PNG end")


def check(root, expected_widths):
    errors = []
    warnings = []
    hashes = defaultdict(list)
    link_count = 0
    image_count = 0
    for source in sorted(root.rglob("*")):
        if not source.is_file():
            continue
        label = str(source.relative_to(root))
        try:
            if source.suffix.lower() in {".md", ".html", ".htm"}:
                text = source.read_text(encoding="utf-8")
                if source.suffix.lower() == ".md":
                    targets = markdown_targets(text)
                else:
                    html = HTMLLinks()
                    html.feed(text)
                    targets = html.targets
                for target in targets:
                    path = local_target(source, target)
                    if path is not None:
                        link_count += 1
                        if not path.exists():
                            errors.append(
                                f"{label}: missing target {unquote(urlsplit(target).path)}"
                            )
            elif source.suffix.lower() == ".png":
                image_count += 1
                data = source.read_bytes()
                width, height = png_dimensions(data)
                if expected_widths and width not in expected_widths:
                    warnings.append(f"{label}: unexpected dimensions {width}x{height}")
                hashes[hashlib.sha256(data).digest()].append(label)
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"{label}: {error}")
    for names in hashes.values():
        if len(names) > 1:
            warnings.append("byte-identical PNGs: " + ", ".join(names))
    return errors, warnings, link_count, image_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected-width", type=int, action="append", default=[])
    args = parser.parse_args()
    if not args.directory.is_dir():
        parser.error("directory must exist")
    if any(width <= 0 for width in args.expected_width):
        parser.error("expected widths must be positive")
    errors, warnings, links, images = check(
        args.directory.resolve(), set(args.expected_width)
    )
    for message in errors:
        print("ERROR:", message)
    for message in warnings:
        print("WARN:", message)
    print(
        f"Checked {links} local links and {images} PNGs; "
        f"{len(errors)} errors, {len(warnings)} warnings."
    )
    print("PNG structure checked; rendering and coverage require review.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
