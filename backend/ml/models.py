"""
PR intelligence scores are computed with statistical and heuristic methods
(see ``services.pr_analytics_v2``, ``services.statistical_scoring``, ``services.risk_heuristics``).

This module deliberately does **not** load serialized estimators. Pickle and joblib loads
remain a code-execution risk; the dashboard does not require persisted ML artifacts.

Backward compatibility:
  ``MLModels`` is retained as a lightweight facade so imports and health checks keep working.

Future: optionally add signed ONNX or sandboxed inference without using arbitrary pickle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

# Reserved for future trusted, non-pickle artifacts only (ONNX, signed bundles, etc.).
# No runtime loading is performed today.
_PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent
ALLOWED_MODEL_DIR: Final[Path] = _PACKAGE_ROOT / "trained_models"


class MLModels:
    """
    Placeholder analytics facade — no disk I/O, no deserialization.

    ``has_trained_models()`` is always False: production analytics never depend on
    loaded pickle/joblib blobs.
    """

    def __init__(self) -> None:
        pass

    def has_trained_models(self) -> bool:
        return False
