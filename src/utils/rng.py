import numpy as np


class SeededRNG:
    """
    Thin wrapper around numpy's default_rng for reproducible randomness.
    Provides convenience methods used throughout the game systems.
    """

    def __init__(self, seed: int = None):
        self.seed = seed if seed is not None else int(np.random.randint(0, 2**32))
        self._rng = np.random.default_rng(self.seed)

    # --- Delegation ---
    def random(self) -> float:
        return float(self._rng.random())

    def uniform(self, low: float, high: float) -> float:
        return float(self._rng.uniform(low, high))

    def integers(self, low: int, high: int) -> int:
        return int(self._rng.integers(low, high))

    def choice(self, options):
        return self._rng.choice(options)

    def __repr__(self) -> str:
        return f"SeededRNG(seed={self.seed})"
