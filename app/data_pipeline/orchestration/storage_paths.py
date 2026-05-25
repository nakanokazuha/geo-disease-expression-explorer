"""Local storage paths for pipeline artifacts."""

from dataclasses import dataclass
from pathlib import Path

from app.data_pipeline.orchestration.manifest import PipelineStage


@dataclass(frozen=True)
class PipelineStoragePaths:
    """Resolved local paths for generated pipeline outputs."""

    root: Path = Path("app/storage")

    @property
    def bronze_studies(self) -> Path:
        return self.root / "bronze" / "studies.json"

    @property
    def silver_studies(self) -> Path:
        return self.root / "silver" / "studies.json"

    @property
    def gold_bundle(self) -> Path:
        return self.root / "gold" / "gold_artifact_bundle.json"

    def manifest_path(self, stage: PipelineStage) -> Path:
        return self.root / "manifests" / f"{stage.value}_manifest.json"

    def ensure_directories(self) -> None:
        for directory in ["bronze", "silver", "gold", "manifests"]:
            (self.root / directory).mkdir(parents=True, exist_ok=True)
