import json

from hypothesis import given, settings
from hypothesis import strategies as st
from typer.testing import CliRunner

from findex.boolean import difference, intersect, union
from findex.cli import app
from findex.corpus import Document
from findex.index import build_index
from findex.store import from_dict, save, to_dict
from findex.tokenize import tokenize


@given(st.lists(st.integers(0, 100)), st.lists(st.integers(0, 100)))
def test_property_merge(a, b):
    a, b = sorted(set(a)), sorted(set(b))
    assert intersect(a, b) == sorted(set(a) & set(b))
    assert union(a, b) == sorted(set(a) | set(b))
    assert difference(a, b) == sorted(set(a) - set(b))


@given(st.lists(st.text(max_size=60), max_size=8))
@settings(max_examples=40)
def test_property_roundtrip(texts):
    index = build_index(Document(i, str(i), t) for i, t in enumerate(texts))
    assert to_dict(from_dict(to_dict(index))) == to_dict(index)
    for values in index.postings.values():
        ids = [p.doc_id for p in values]
        assert ids == sorted(set(ids))


@given(st.text())
def test_property_tokenizer(text):
    assert all(token and token == token.casefold() for token in tokenize(text))


def test_cli_help():
    assert CliRunner().invoke(app, ["--help"]).exit_code == 0


def test_cli_roundtrip(tmp_path):
    corpus = tmp_path / "a.txt"
    corpus.write_text("python event loop", encoding="utf-8")
    path = tmp_path / "index.json"
    runner = CliRunner()
    assert (
        runner.invoke(app, ["index", str(corpus), "--out", str(path), "--positions"]).exit_code == 0
    )
    result = runner.invoke(app, ["search", str(path), "python", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["doc_id"] == 0
    assert runner.invoke(app, ["stats", str(path)]).exit_code == 0


def test_cli_error():
    result = CliRunner().invoke(app, ["search", "missing.bin", "word"])
    assert result.exit_code == 2
    assert "Traceback" not in result.output


def test_cli_parse_error(index, tmp_path):
    path = tmp_path / "x.bin"
    save(index, path)
    result = CliRunner().invoke(app, ["search", str(path), "a OR", "--json"])
    assert result.exit_code == 2
    assert result.stdout == ""
