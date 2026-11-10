"""Ліниве читання UTF-8 текстів та JSON Lines."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Document:
    doc_id: int
    path: str
    text: str
    title: str = ""


def iter_documents(root: Path) -> Iterator[Document]:
    """Тримати лише поточний документ; пошкоджені записи пропускати з логом."""
    if not root.exists():
        raise FileNotFoundError(f"Корпус не знайдено: {root}")
    if root.is_dir():
        paths = root.rglob("*.txt")
    else:
        paths = iter((root,))
    doc_id = 0
    for path in paths:
        try:
            if path.suffix.lower() == ".jsonl":
                with path.open(encoding="utf-8", errors="replace") as stream:
                    for line_number, line in enumerate(stream, 1):
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                            text = record["text"]
                            if not isinstance(text, str):
                                raise ValueError("text має бути рядком")
                            yield Document(doc_id, str(record.get("url", record.get("path", path))),
                                           text, str(record.get("title", "")))
                            doc_id += 1
                        except (ValueError, KeyError, TypeError) as error:
                            logger.warning("%s:%d: %s", path, line_number, error)
            else:
                yield Document(doc_id, str(path), path.read_text(encoding="utf-8", errors="replace"),
                               path.stem)
                doc_id += 1
        except OSError as error:
            logger.warning("Пропущено %s: %s", path, error)
