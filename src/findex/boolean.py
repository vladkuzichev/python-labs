"""Двовказівникові операції над відсортованими унікальними doc_id."""

from collections.abc import Sequence
from typing import Literal

Engine = Literal["merge", "set"]


def intersect(a: Sequence[int], b: Sequence[int]) -> list[int]:
    i = j = 0
    result: list[int] = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            result.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return result


def union(a: Sequence[int], b: Sequence[int]) -> list[int]:
    i = j = 0
    result: list[int] = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            result.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result


def difference(a: Sequence[int], b: Sequence[int]) -> list[int]:
    i = j = 0
    result: list[int] = []
    while i < len(a):
        while j < len(b) and b[j] < a[i]:
            j += 1
        if j == len(b) or b[j] != a[i]:
            result.append(a[i])
        i += 1
    return result


def combine(a: Sequence[int], b: Sequence[int], operation: str, engine: Engine) -> list[int]:
    if engine == "set":
        left, right = set(a), set(b)
        return sorted(
            left & right
            if operation == "AND"
            else left | right
            if operation == "OR"
            else left - right
        )
    if operation == "AND":
        return intersect(a, b)
    if operation == "OR":
        return union(a, b)
    return difference(a, b)
