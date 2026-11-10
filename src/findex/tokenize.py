"""NFC → casefold → finditer; внутрішній апостроф лишається, дефіс розділяє."""

import re
import unicodedata
from collections.abc import Iterator

WORD = re.compile(r"[^\W_]+(?:['’ʼ][^\W_]+)*", re.UNICODE)


def tokenize(text: str) -> Iterator[str]:
    """Цифри зберігаються; варіанти апострофа зводяться до ASCII; '_' розділяє."""
    normalized = unicodedata.normalize("NFC", text).casefold()
    normalized = normalized.replace("’", "'").replace("ʼ", "'")
    for match in WORD.finditer(normalized):
        yield match.group()
