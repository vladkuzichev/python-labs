import json

import pytest

from findex.corpus import iter_documents
from findex.index import build_index
from findex.parallel import Work, build_parallel, build_partial, merge
from findex.store import to_dict


@pytest.mark.parametrize("executor", ["serial", "threads", "processes"])
@pytest.mark.slow
def test_executors(tmp_path, executor):
    path = tmp_path / "docs.jsonl"
    path.write_text(
        "\n".join(
            json.dumps({"text": t, "title": str(i), "path": str(i)})
            for i, t in enumerate(["a b", "b c", "a a", ""])
        ),
        encoding="utf-8",
    )
    expected = build_index(iter_documents(path), positions=True)
    actual, _ = build_parallel(path, workers=2, executor=executor, positions=True)
    assert to_dict(actual) == to_dict(expected)


def test_merge_collision(index):
    from findex.parallel import PartialIndex

    with pytest.raises(ValueError):
        merge([PartialIndex(index, 0), PartialIndex(index, 0)])


def test_worker_error():
    with pytest.raises(FileNotFoundError):
        build_partial(Work([__import__("pathlib").Path("missing")], 0, False))
