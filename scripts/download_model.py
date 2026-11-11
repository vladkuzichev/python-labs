"""Завантаження зафіксованої MiniLM-моделі для нового середовища/CI."""

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(Path("evaluation/model_manifest.json").read_text())
    destination = Path("models/all-MiniLM-L6-v2")
    destination.mkdir(parents=True, exist_ok=True)
    for name, metadata in manifest["files"].items():
        path = destination / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == metadata["sha256"]:
            continue
        if args.check:
            raise ValueError(f"Немає правильного файла моделі: {path}")
        with urllib.request.urlopen(metadata["url"], timeout=60) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != metadata["sha256"]:
            raise ValueError(f"Невідповідний SHA256: {name}")
        path.write_bytes(content)
    print("MiniLM model verified")


if __name__ == "__main__":
    main()
