class FakeEmbedder:
    """Deterministic keyword-based embedder for tests (no torch, no network)."""

    dim = 384
    VOCAB = ["курица", "рыба", "овсянка", "говядина", "салат", "творог"]

    def encode(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            lowered = text.lower()
            for i, word in enumerate(self.VOCAB):
                if word in lowered:
                    vec[i] = 1.0
            if not any(vec):
                vec[len(self.VOCAB)] = 1.0  # stable "no keyword" bucket
            out.append(vec)
        return out
