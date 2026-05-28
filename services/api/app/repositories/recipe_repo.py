from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.recipe import Recipe


class RecipeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Recipe)) or 0

    def upsert(self, values: dict) -> None:
        """Insert a recipe, or refresh embedding/payload if content_hash exists."""
        stmt = insert(Recipe).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Recipe.content_hash],
            set_={
                "title": stmt.excluded.title,
                "ingredients": stmt.excluded.ingredients,
                "steps": stmt.excluded.steps,
                "macros": stmt.excluded.macros,
                "tags": stmt.excluded.tags,
                "source_url": stmt.excluded.source_url,
                "embedding": stmt.excluded.embedding,
            },
        )
        self.session.execute(stmt)

    def search(self, query_vector: list[float], k: int) -> Sequence[Recipe]:
        return self.session.scalars(
            select(Recipe).order_by(Recipe.embedding.cosine_distance(query_vector)).limit(k)
        ).all()
