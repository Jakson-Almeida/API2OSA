"""Conexão e leitura de espectro no Thorlabs OSA 20x."""

from __future__ import annotations

from typing import Any

import numpy as np

from api2osa._paths import configure_sdk
from api2osa.spectrum import SpectrumResult


class OSA203:
    """
    Interface simples para o analisador OSA203 (série OSA 20x).

    Exemplo::

        with OSA203.connect() as osa:
            spec = osa.read_spectrum()
            print(spec.n_points, spec.model)
    """

    def __init__(self, instrument: Any) -> None:
        self._instrument = instrument
        self._ignore_errors: list[str] = ["Reference Warmup"]

    @classmethod
    def connect(
        cls,
        *,
        autogain: bool = False,
        resolution: str = "low",
        sensitivity: str = "low",
        ignore_warmup: bool = True,
    ) -> "OSA203":
        """
        Abre o primeiro OSA USB disponível e aplica configuração básica.

        Args:
            autogain: Ativa autogain do instrumento.
            resolution: ``low`` ou ``high`` (OSA 20x).
            sensitivity: ``low``, ``medium low``, ``medium high``, ``high``.
            ignore_warmup: Ignora erro de laser de referência em aquecimento.
        """
        configure_sdk()
        import pyOSA  # noqa: WPS433 — import após configure_sdk

        ignore_errors = ["Reference Warmup"] if ignore_warmup else []
        instrument = pyOSA.initialize()
        instrument.setup(
            autogain=autogain,
            resolution=resolution,
            sensitivity=sensitivity,
        )
        instance = cls(instrument)
        instance._ignore_errors = ignore_errors
        return instance

    def __enter__(self) -> "OSA203":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        if self._instrument is not None:
            self._instrument.close()
            self._instrument = None

    @property
    def model(self) -> str:
        return self._instrument.get_model()

    @property
    def serial_number(self) -> str:
        return self._instrument.get_serial_number()

    def read_spectrum(
        self,
        *,
        spectrum_averaging: int = 1,
        x_unit: str = "nm (vac)",
        y_unit: str = "dBm",
        apodization: str = "None",
    ) -> SpectrumResult:
        """
        Adquire um espectro (uma medição).

        Args:
            spectrum_averaging: Número de espectros a média no hardware.
            x_unit: Unidade do eixo X (ex.: ``nm (vac)``, ``THz``).
            y_unit: Unidade do eixo Y (ex.: ``dBm``, ``mW``).
            apodization: Tipo de apodização (``None``, ``Hann``, etc.).
        """
        batches = self._instrument.acquire(
            spectrum=True,
            interferogram=False,
            number_of_acquisitions=1,
            spectrum_averaging=spectrum_averaging,
            apodization=apodization,
            y_unit=y_unit,
            x_unit=x_unit,
            ignore_errors=self._ignore_errors,
        )
        if not batches:
            raise RuntimeError("Nenhum dado retornado pelo instrumento.")

        spectrum = batches[0]["spectrum"]
        wl = np.asarray(spectrum.get_x(), dtype=float)
        intensity = np.asarray(spectrum.get_y(), dtype=float)

        warnings: list[str] = []
        try:
            validity = spectrum.check_validity()
            if not validity.get("ref_laser_locked", True):
                warnings.append("Laser de referência não bloqueado")
            if not validity.get("interferogram_within_detector_range", True):
                warnings.append("Interferograma clipado")
            if not validity.get("interferogram_is_linear", True):
                warnings.append("Interferograma não linear")
            if not validity.get("autogain_satisfied", True):
                warnings.append("Autogain não satisfeito")
        except Exception:
            pass

        return SpectrumResult(
            wavelength_nm=wl,
            intensity=intensity,
            x_unit=x_unit,
            y_unit=y_unit,
            model=self.model,
            serial_number=self.serial_number,
            warnings=tuple(warnings),
        )
