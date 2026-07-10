#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "sources.json"


def load_sources(manifest_path):
    sources = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(sources, list):
        raise ValueError("manifest must contain a list")

    seen = set()
    for source in sources:
        path = Path(source["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe path: {source['path']}")
        if source["path"] in seen:
            raise ValueError(f"duplicate path: {source['path']}")
        if not source["url"].startswith("https://"):
            raise ValueError(f"URL must use HTTPS: {source['path']}")
        seen.add(source["path"])
    return sources


def validate_content(data):
    if len(data) < 8 or b"\x00" in data:
        return False
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False

    prefix = text.lstrip()[:256].lower()
    if prefix.startswith("<!doctype html") or prefix.startswith("<html"):
        return False
    return any(line.strip() and not line.lstrip().startswith(("#", ";")) for line in text.splitlines())


def sync_source(root, source):
    target = Path(root) / source["path"]
    request = Request(source["url"], headers={"User-Agent": "shaoyou11-surge-rule-mirror/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read()
    except (OSError, URLError) as exc:
        return False, f"download failed: {exc}"

    if not validate_content(data):
        return False, "downloaded content failed validation"

    if target.exists() and target.read_bytes() == data:
        return True, "unchanged"

    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
    return True, "updated"


def main():
    sources = load_sources(MANIFEST)
    failures = 0
    for source in sources:
        ok, message = sync_source(ROOT, source)
        status = "OK" if ok else "ERROR"
        print(f"{status} {source['path']}: {message}")
        failures += not ok
    print(f"Synced {len(sources) - failures}/{len(sources)} rule sources")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
