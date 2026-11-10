"""Рекурсивний спуск: NOT > явний/неявний AND > OR; фрази і дужки."""

from __future__ import annotations

import re
from dataclasses import dataclass

from findex.boolean import Engine, combine
from findex.index import Index
from findex.tokenize import tokenize


class Node:
    def __and__(self, other: Node) -> And:
        return And(self, other)

    def __or__(self, other: Node) -> Or:
        return Or(self, other)

    def __invert__(self) -> Not:
        return Not(self)

    def evaluate(self, index: Index, engine: Engine = "merge") -> list[int]:
        raise NotImplementedError

    def terms(self, *, positive: bool = True) -> tuple[str, ...]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Term(Node):
    value: str

    def evaluate(self, index: Index, engine: Engine = "merge") -> list[int]:
        return [p.doc_id for p in index.postings.get(self.value, [])]

    def terms(self, *, positive: bool = True) -> tuple[str, ...]:
        return (self.value,) if positive else ()


@dataclass(frozen=True, slots=True)
class Phrase(Node):
    words: tuple[str, ...]

    def evaluate(self, index: Index, engine: Engine = "merge") -> list[int]:
        if not index.positions:
            raise ValueError("Фразовий пошук потребує індексу з --positions")
        maps = [{p.doc_id: p.positions for p in index.postings.get(w, [])} for w in self.words]
        candidates = sorted(maps[0])
        for mapping in maps[1:]:
            candidates = combine(candidates, sorted(mapping), "AND", engine)
        result: list[int] = []
        for doc_id in candidates:
            starts = set(maps[0][doc_id])
            for offset, mapping in enumerate(maps[1:], 1):
                starts.intersection_update(position - offset for position in mapping[doc_id])
            if starts:
                result.append(doc_id)
        return result

    def terms(self, *, positive: bool = True) -> tuple[str, ...]:
        return self.words if positive else ()


@dataclass(frozen=True, slots=True)
class And(Node):
    left: Node
    right: Node

    def evaluate(self, index: Index, engine: Engine = "merge") -> list[int]:
        return combine(
            self.left.evaluate(index, engine), self.right.evaluate(index, engine), "AND", engine
        )

    def terms(self, *, positive: bool = True) -> tuple[str, ...]:
        return self.left.terms(positive=positive) + self.right.terms(positive=positive)


@dataclass(frozen=True, slots=True)
class Or(Node):
    left: Node
    right: Node

    def evaluate(self, index: Index, engine: Engine = "merge") -> list[int]:
        return combine(
            self.left.evaluate(index, engine), self.right.evaluate(index, engine), "OR", engine
        )

    def terms(self, *, positive: bool = True) -> tuple[str, ...]:
        return self.left.terms(positive=positive) + self.right.terms(positive=positive)


@dataclass(frozen=True, slots=True)
class Not(Node):
    operand: Node

    def evaluate(self, index: Index, engine: Engine = "merge") -> list[int]:
        return combine(sorted(index.doc_meta), self.operand.evaluate(index, engine), "NOT", engine)

    def terms(self, *, positive: bool = True) -> tuple[str, ...]:
        return self.operand.terms(positive=not positive)


LEXEME = re.compile(r'"[^"\n]*"|[()]|[^\s()"]+')


class Parser:
    def __init__(self, query: str) -> None:
        self.tokens: list[str] = []
        end = 0
        for match in LEXEME.finditer(query):
            if query[end : match.start()].strip():
                raise ValueError("Незакрита або некоректна фраза")
            self.tokens.append(match.group())
            end = match.end()
        if query[end:].strip():
            raise ValueError("Незакрита фраза")
        self.position = 0

    def peek(self) -> str | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def take(self) -> str:
        value = self.peek()
        if value is None:
            raise ValueError("Неочікуваний кінець запиту")
        self.position += 1
        return value

    def parse_or(self) -> Node:
        node = self.parse_and()
        while self.peek() == "OR":
            self.take()
            node = Or(node, self.parse_and())
        return node

    def parse_and(self) -> Node:
        node = self.parse_unary()
        while self.peek() is not None and self.peek() not in {"OR", ")"}:
            if self.peek() == "AND":
                self.take()
            node = And(node, self.parse_unary())
        return node

    def parse_unary(self) -> Node:
        token = self.take()
        if token == "NOT":
            return Not(self.parse_unary())
        if token == "(":
            node = self.parse_or()
            if self.take() != ")":
                raise ValueError("Очікується закривальна дужка")
            return node
        if token in {"AND", "OR", ")"}:
            raise ValueError(f"Неочікуваний оператор: {token}")
        words = tuple(tokenize(token.strip('"')))
        if not words:
            raise ValueError("Порожній термін або фраза")
        if token.startswith('"'):
            return Phrase(words)
        node: Node = Term(words[0])
        for word in words[1:]:
            node = And(node, Term(word))
        return node


def parse(query: str) -> Node:
    if len(query) > 1000:
        raise ValueError("Запит перевищує 1000 символів")
    parser = Parser(query)
    node = parser.parse_or()
    if parser.peek() is not None:
        raise ValueError("Зайва закривальна дужка")
    return node
