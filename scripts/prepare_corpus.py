"""Відтворюваний корпус справжніх docstring стандартної бібліотеки CPython."""

import ast
import hashlib
import json
import sysconfig
from pathlib import Path


def main() -> None:
    root = Path(sysconfig.get_path("stdlib"))
    output = Path("data/stdlib.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as stream:
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(root)
            if any(
                part in {"site-packages", "test", "tests", "idlelib", "turtledemo", "ensurepip"}
                for part in relative.parts
            ):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            except (SyntaxError, UnicodeError, OSError):
                continue
            module = ".".join(relative.with_suffix("").parts)
            for node in ast.walk(tree):
                if not isinstance(
                    node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
                ):
                    continue
                name = getattr(node, "name", "module")
                if name.startswith("_"):
                    continue
                text = ast.get_docstring(node)
                if not text or len(text) < 100:
                    continue
                title = f"{module}.{name}"
                record = {
                    "title": title,
                    "path": f"stdlib://{relative.as_posix()}#L{getattr(node, 'lineno', 1)}",
                    "text": f"{title}\n\n{text}",
                }
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
    print(
        json.dumps(
            {
                "documents": count,
                "bytes": output.stat().st_size,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "source": "CPython standard-library docstrings; PSF License; local Python runtime",
            }
        )
    )


if __name__ == "__main__":
    main()
