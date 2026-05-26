"""Load app-facing Gold artifacts for the Streamlit UI."""

import json
from pathlib import Path

from app.domain.contracts import GoldArtifactBundle

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GOLD_BUNDLE_PATH = PROJECT_ROOT / "app" / "storage" / "gold" / "gold_artifact_bundle.json"


class GoldArtifactNotFoundError(FileNotFoundError):
    """Raised when the published Gold artifact bundle is unavailable."""


def load_gold_bundle(path: Path = DEFAULT_GOLD_BUNDLE_PATH) -> GoldArtifactBundle:
    """Load and validate the published Gold artifact bundle."""

    if not path.exists():
        raise GoldArtifactNotFoundError(f"Gold artifact bundle not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    return GoldArtifactBundle.model_validate(payload)
