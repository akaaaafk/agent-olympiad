"""Artifact loading, validation, and normalization."""

from .assets import Asset, AssetError, load_assets
from .slides import (
    ArtifactValidation,
    NormalizedSubmission,
    normalize_submission,
    validate_html_slides,
    validate_pdf_slides,
)

__all__ = [
    "ArtifactValidation",
    "Asset",
    "AssetError",
    "NormalizedSubmission",
    "load_assets",
    "normalize_submission",
    "validate_html_slides",
    "validate_pdf_slides",
]
