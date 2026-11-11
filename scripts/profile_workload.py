import argparse
from pathlib import Path

from findex.corpus import iter_documents
from findex.index import build_index
from findex.search import search
from findex.store import load


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["index", "search", "load"])
    parser.add_argument("--repeat", type=int, default=500)
    args = parser.parse_args()
    if args.operation == "index":
        for _ in range(max(1, args.repeat // 100)):
            build_index(iter_documents(Path("data/stdlib.jsonl")), positions=True)
    elif args.operation == "load":
        for _ in range(args.repeat):
            load(Path("data/index.bin"))
    else:
        index = load(Path("data/index.bin"))
        for _ in range(args.repeat):
            search(index, "the file return", with_snippets=False)


if __name__ == "__main__":
    main()
