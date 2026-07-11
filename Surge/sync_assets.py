#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "assets-sources.json"
VALID_TYPES = {"png", "mmdb", "text"}


def validate_source(source):
    path = Path(source["path"])
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe path: {source['path']}")
    if not source["url"].startswith("https://"):
        raise ValueError(f"URL must use HTTPS: {source['path']}")
    if source["type"] not in VALID_TYPES:
        raise ValueError(f"unsupported type: {source['type']}")


def load_sources(manifest_path=MANIFEST):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    icon_set = manifest["icon_set"]
    sources = [
        {
            "path": f"IconSet/Color/{name}",
            "url": f"{icon_set['upstream_base']}{name}",
            "type": "png",
        }
        for name in icon_set["files"]
    ]
    sources.extend({**source, "type": "mmdb"} for source in manifest["geoip"])
    sources.extend({**source, "type": "text"} for source in manifest["extra_rules"])

    seen = set()
    for source in sources:
        validate_source(source)
        if source["path"] in seen:
            raise ValueError(f"duplicate path: {source['path']}")
        seen.add(source["path"])
    return sources


def validate_content(data, content_type):
    if content_type == "png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "mmdb":
        return b"\xab\xcd\xefMaxMind.com" in data[-131072:]
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
    request = Request(source["url"], headers={"User-Agent": "shaoyou11-surge-asset-mirror/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            data = response.read()
    except (OSError, URLError) as exc:
        return False, f"download failed: {exc}"

    if not validate_content(data, source["type"]):
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
    sources = load_sources()
    failures = 0
    for source in sources:
        ok, message = sync_source(ROOT, source)
        print(f"{'OK' if ok else 'ERROR'} {source['path']}: {message}")
        failures += not ok
    print(f"Synced {len(sources) - failures}/{len(sources)} asset sources")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
