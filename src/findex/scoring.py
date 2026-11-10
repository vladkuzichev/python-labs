"""Взаємозамінні скалярні TF-IDF та BM25; еталон для NumPy-реалізації."""

import math
from dataclasses import dataclass
from typing import Protocol

from findex.index import Index, Posting


class Scorer(Protocol):
    def score(self, term: str, posting: Posting, index: Index) -> float: ...


@dataclass(frozen=True, slots=True)
class TfIdf:
    def score(self, term: str, posting: Posting, index: Index) -> float:
        return (1.0 + math.log(posting.tf)) * math.log(1.0 + index.num_docs / index.df(term))


@dataclass(frozen=True, slots=True)
class BM25:
    k1: float = 1.5
    b: float = 0.75

    def __post_init__(self) -> None:
        if self.k1 <= 0 or not 0 <= self.b <= 1:
            raise ValueError("BM25: k1 > 0 та 0 ≤ b ≤ 1")

    def score(self, term: str, posting: Posting, index: Index) -> float:
        df = index.df(term)
        idf = math.log(1.0 + (index.num_docs - df + 0.5) / (df + 0.5))
        norm = 1 - self.b + self.b * index.doc_length(posting.doc_id) / (index.avg_doc_length or 1)
        return idf * posting.tf * (self.k1 + 1) / (posting.tf + self.k1 * norm)
