"""UI data access helpers."""

from app.ui.data_access.gold_loader import (
    DEFAULT_GOLD_BUNDLE_PATH,
    GoldArtifactNotFoundError,
    load_gold_bundle,
)

__all__ = [
    "DEFAULT_GOLD_BUNDLE_PATH",
    "GoldArtifactNotFoundError",
    "load_gold_bundle",
]
