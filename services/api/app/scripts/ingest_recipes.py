"""CLI: build the recipe RAG index from a seed list of URLs.

Run where outbound network and the `rag` extra are available:

    pip install -e ".[rag]"
    python -m app.scripts.ingest_recipes --source data/recipe_seeds.txt

Each seed line is a recipe page URL; schema.org Recipe JSON-LD is extracted,
embedded locally and upserted into the `recipes` table (idempotent by content).
"""
import argparse
import sys

from app.db.session import SessionLocal
from app.integrations.recipe_source import RecipeData, fetch_recipes
from app.services.recipe_index import RecipeIndexService


def _read_seeds(path: str) -> list[str]:
    urls: list[str] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest recipes into the RAG index")
    parser.add_argument("--source", required=True, help="path to a file with recipe URLs")
    parser.add_argument("--limit", type=int, default=0, help="max URLs to process (0 = all)")
    args = parser.parse_args(argv)

    urls = _read_seeds(args.source)
    if args.limit:
        urls = urls[: args.limit]
    if not urls:
        print("No URLs to ingest.")
        return 0

    collected: list[RecipeData] = []
    for url in urls:
        try:
            recipes = fetch_recipes(url)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"skip {url}: {exc}", file=sys.stderr)
            continue
        print(f"{url}: {len(recipes)} recipe(s)")
        collected.extend(recipes)

    if not collected:
        print("No recipes extracted.")
        return 0

    session = SessionLocal()
    try:
        count = RecipeIndexService(session).ingest(collected)
    finally:
        session.close()
    print(f"Ingested {count} recipe(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
