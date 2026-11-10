import inspect

import pytest

from findex.tokenize import tokenize


@pytest.mark.parametrize("text,expected", [
    ("PyTHON Hello", ["python", "hello"]),
    ("Програмування Київ", ["програмування", "київ"]),
    ("cafe\u0301", ["café"]),
    ("Hello, world!", ["hello", "world"]),
    ("", []),
    ("п’ять пʼять п'ять", ["п'ять", "п'ять", "п'ять"]),
    ("well-known", ["well", "known"]),
    ("3.13 abc_123", ["3", "13", "abc", "123"]),
    ("Straße", ["strasse"]),
    ("___...", []),
])
def test_tokenize(text, expected):
    assert list(tokenize(text)) == expected


def test_generator():
    assert inspect.isgeneratorfunction(tokenize)
