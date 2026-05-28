from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.integrations.embeddings import Embedder, get_embedder
from app.integrations.recipe_source import RecipeData
from app.models.recipe import Recipe
from app.repositories.recipe_repo import RecipeRepository


class RecipeIndexService:
    def __init__(self, session: Session, embedder: Embedder | None = None) -> None:
        self.session = session
        self.repo = RecipeRepository(session)
        self._embedder = embedder

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    def count(self) -> int:
        return self.repo.count()

    def ingest(self, recipes: Sequence[RecipeData]) -> int:
        if not recipes:
            return 0
        vectors = self.embedder.encode([r.embedding_text() for r in recipes])
        for recipe, vector in zip(recipes, vectors, strict=True):
            self.repo.upsert(
                {
                    "title": recipe.title,
                    "ingredients": recipe.ingredients,
                    "steps": recipe.steps,
                    "macros": recipe.macros,
                    "tags": recipe.tags,
                    "source_url": recipe.source_url,
                    "content_hash": recipe.content_hash,
                    "embedding": vector,
                }
            )
        self.session.commit()
        return len(recipes)

    def retrieve(self, query_text: str, k: int) -> Sequence[Recipe]:
        if self.repo.count() == 0:
            return []
        query_vector = self.embedder.encode([query_text])[0]
        return self.repo.search(query_vector, k)
