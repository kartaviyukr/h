import hashlib
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

import httpx

from app.core.config import settings


@dataclass
class RecipeData:
    title: str
    ingredients: list[str]
    steps: list[str]
    macros: dict | None
    tags: list[str] = field(default_factory=list)
    source_url: str | None = None

    @property
    def content_hash(self) -> str:
        ingredients = "|".join(i.strip().lower() for i in self.ingredients)
        raw = self.title.strip().lower() + "|" + ingredients
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def embedding_text(self) -> str:
        parts = [self.title]
        if self.ingredients:
            parts.append("Ингредиенты: " + ", ".join(self.ingredients))
        if self.tags:
            parts.append("Теги: " + ", ".join(self.tags))
        return ". ".join(parts)


class _LdJsonExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capturing = False
        self._buffer: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self._capturing = True
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._capturing:
            self._capturing = False
            self.blocks.append("".join(self._buffer))


def _iter_objects(node):
    if isinstance(node, list):
        for item in node:
            yield from _iter_objects(item)
    elif isinstance(node, dict):
        if "@graph" in node:
            yield from _iter_objects(node["@graph"])
        yield node


def _is_recipe(obj: dict) -> bool:
    t = obj.get("@type")
    types = t if isinstance(t, list) else [t]
    return "Recipe" in types


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            text = item.get("text") or item.get("name")
            if text:
                result.append(text)
    return result


def _parse_number(value) -> float | None:
    if value is None:
        return None
    match = re.search(r"\d+(?:[.,]\d+)?", str(value))
    return float(match.group(0).replace(",", ".")) if match else None


def _parse_macros(nutrition) -> dict | None:
    if not isinstance(nutrition, dict):
        return None
    macros = {
        "kcal": _parse_number(nutrition.get("calories")),
        "protein_g": _parse_number(nutrition.get("proteinContent")),
        "fat_g": _parse_number(nutrition.get("fatContent")),
        "carbs_g": _parse_number(nutrition.get("carbohydrateContent")),
    }
    return macros if any(v is not None for v in macros.values()) else None


def _tags(obj: dict) -> list[str]:
    tags: list[str] = []
    for key in ("recipeCuisine", "recipeCategory", "keywords"):
        value = obj.get(key)
        if isinstance(value, str):
            tags.extend(t.strip() for t in value.split(",") if t.strip())
        elif isinstance(value, list):
            tags.extend(str(t).strip() for t in value if str(t).strip())
    return tags


def parse_jsonld_recipes(html: str, source_url: str | None = None) -> list[RecipeData]:
    """Extract schema.org Recipe objects embedded as JSON-LD in an HTML page."""
    extractor = _LdJsonExtractor()
    extractor.feed(html)

    recipes: list[RecipeData] = []
    for block in extractor.blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for obj in _iter_objects(data):
            if not _is_recipe(obj):
                continue
            title = obj.get("name")
            ingredients = _as_str_list(obj.get("recipeIngredient"))
            if not title or not ingredients:
                continue
            recipes.append(
                RecipeData(
                    title=title.strip(),
                    ingredients=ingredients,
                    steps=_as_str_list(obj.get("recipeInstructions")),
                    macros=_parse_macros(obj.get("nutrition")),
                    tags=_tags(obj),
                    source_url=source_url,
                )
            )
    return recipes


def fetch_recipes(url: str, timeout_s: float = 30.0) -> list[RecipeData]:
    """Fetch a page and extract recipes. Requires outbound network access."""
    headers = {"User-Agent": settings.app_name}
    with httpx.Client(timeout=timeout_s, follow_redirects=True, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
    return parse_jsonld_recipes(response.text, source_url=url)
