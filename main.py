#!/usr/bin/env python3
"""Write the entry text to /output/entry.txt.

Reads entry.txt beside this script, checks it against a pinned SHA-256, checks
the gate (UTF-8, 1-1000 code points, not only white space), then copies it out.
Deterministic: the same source bytes always produce the same output bytes.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys

EXPECTED_SHA256 = "3b6358222cce975858140f59077682c23cea31ea7b7d121f9027c4d07cb3bf3f"

SOURCE_NAME = "entry.txt"
DEFAULT_OUTPUT_DIR = "/output"
MIN_CHARS = 1
MAX_CHARS = 1000


def fail(message: str) -> "NoReturn":
    sys.stderr.write("error: " + message + "\n")
    raise SystemExit(1)


def source_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), SOURCE_NAME)


def output_path(argv: list[str]) -> str:
    if len(argv) > 1:
        return os.path.abspath(argv[1])
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR
    return os.path.join(os.path.abspath(out_dir), SOURCE_NAME)


def read_source(path: str) -> tuple[bytes, str]:
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        fail("cannot read %s: %s" % (path, exc))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("%s is not valid UTF-8: %s" % (path, exc))
    return raw, text


def check_gate(text: str) -> None:
    count = len(text)
    if count < MIN_CHARS or count > MAX_CHARS:
        fail("entry is %d characters; the gate allows %d to %d" % (count, MIN_CHARS, MAX_CHARS))
    if not text.strip():
        fail("entry is only white space; the gate needs at least one visible character")


def check_hash(raw: bytes) -> str:
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        fail(
            "entry.txt hash mismatch: expected %s, found %s"
            % (EXPECTED_SHA256, digest)
        )
    return digest


def same_file(source: str, destination: str) -> bool:
    if os.path.abspath(source) == os.path.abspath(destination):
        return True
    if os.path.exists(destination):
        try:
            return os.path.samefile(source, destination)
        except OSError:
            return False
    return False


def main(argv: list[str]) -> int:
    source = source_path()
    destination = output_path(argv)

    if same_file(source, destination):
        fail(
            "source and destination are the same file (%s); refusing to copy onto itself"
            % destination
        )

    raw, text = read_source(source)
    check_gate(text)
    digest = check_hash(raw)

    try:
        parent = os.path.dirname(destination)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(destination, "wb") as handle:
            handle.write(raw)
    except OSError as exc:
        fail("cannot write %s: %s" % (destination, exc))

    sys.stdout.write(
        "wrote %s (%d chars, sha256 %s)\n" % (destination, len(text), digest)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
