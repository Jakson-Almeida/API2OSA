"""Tipos partilhados entre instrumentos."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpectrumResult:
    """Um espectro medido (comprimento de onda + intensidade)."""

    wavelength_nm: np.ndarray
    intensity: np.ndarray
    x_unit: str
    y_unit: str
    model: str
    serial_number: str
    warnings: tuple[str, ...]

    @property
    def n_points(self) -> int:
        return int(self.wavelength_nm.size)
