"""Conexão e leitura de espectro no Thorlabs Compact Spectrograph (CCT11)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from api2osa._cct_paths import configure_cct_sdk
from api2osa.spectrum import SpectrumResult


class CCT11:
    """
    Interface simples para o espectrógrafo compacto CCT11 (SDK .NET).

    Exemplo::

        with CCT11.connect() as cct:
            spec = cct.read_spectrum()
            print(cct.device_id, spec.n_points)
    """

    def __init__(self, pycct: Any, device: Any, device_id: str) -> None:
        self._pycct = pycct
        self._device = device
        self._device_id = device_id

    @classmethod
    def connect(
        cls,
        *,
        device_id: str | None = None,
        sdk_path: str | Path | None = None,
    ) -> "CCT11":
        """
        Descobre e liga ao primeiro CCT disponível (ou ao ``device_id`` indicado).

        Args:
            device_id: ID devolvido por ``list_devices()``; omite para o primeiro.
            sdk_path: Pasta ``net48`` com as DLLs (omite para auto-detecção).
        """
        if sdk_path is not None:
            net48 = Path(sdk_path)
            if not (net48 / "Thorlabs.ManagedDevice.CompactSpectrographDriver.dll").is_file():
                raise FileNotFoundError(f"SDK CCT inválido em {net48}")
            configure_cct_sdk()
        else:
            net48 = configure_cct_sdk()

        from pyCCT import PyCCT  # noqa: WPS433

        pycct = PyCCT(str(net48))
        devices = pycct.discover_devices()
        if not devices:
            pycct.stop()
            raise RuntimeError(
                "Nenhum espectrógrafo CCT encontrado. Verifique USB/rede e o software Thorlabs."
            )

        chosen = device_id or devices[0]
        if chosen not in devices:
            pycct.stop()
            raise RuntimeError(
                f"Dispositivo '{chosen}' não encontrado. Disponíveis: {', '.join(devices)}"
            )

        device = pycct.connect_to_device(chosen)
        if device is None:
            pycct.stop()
            raise RuntimeError(f"Falha ao ligar ao dispositivo '{chosen}'.")

        return cls(pycct, device, chosen)

    @classmethod
    def list_devices(cls, *, sdk_path: str | Path | None = None) -> list[str]:
        """Lista IDs de espectrógrafos CCT visíveis pelo SDK."""
        if sdk_path is not None:
            net48 = Path(sdk_path)
            configure_cct_sdk()
        else:
            net48 = configure_cct_sdk()

        from pyCCT import PyCCT  # noqa: WPS433

        pycct = PyCCT(str(net48))
        try:
            return list(pycct.discover_devices())
        finally:
            pycct.stop()

    def __enter__(self) -> "CCT11":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self._device = None
        if self._pycct is not None:
            self._pycct.stop()
            self._pycct = None

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def model(self) -> str:
        return "CCT11"

    @property
    def serial_number(self) -> str:
        return self._device_id

    def read_spectrum(
        self,
        *,
        hardware_averaging: int = 1,
        exposure_ms: float | None = None,
        x_unit: str = "nm",
        y_unit: str = "counts",
    ) -> SpectrumResult:
        """
        Adquire um espectro (uma medição).

        Args:
            hardware_averaging: Média no hardware (frames).
            exposure_ms: Tempo de exposição manual em ms (``None`` = valor atual).
            x_unit: Rótulo do eixo X (o SDK devolve comprimento de onda em nm).
            y_unit: Rótulo do eixo Y (intensidade do detector).
        """
        if hardware_averaging < 1:
            raise ValueError("hardware_averaging deve ser >= 1")

        if hardware_averaging > 1:
            if not self._device.set_hardware_average(hardware_averaging):
                raise RuntimeError("Falha ao definir média no hardware.")

        if exposure_ms is not None:
            if not self._device.set_manual_exposure(float(exposure_ms)):
                raise RuntimeError("Falha ao definir tempo de exposição.")

        wl, intensity, _exp, _ave = self._device.acquire_single_spectrum()
        if wl is None or intensity is None:
            raise RuntimeError("Nenhum dado retornado pelo CCT.")

        warnings: list[str] = []
        if self._device.is_saturated():
            warnings.append("Espectro saturado")

        return SpectrumResult(
            wavelength_nm=np.asarray(wl, dtype=float),
            intensity=np.asarray(intensity, dtype=float),
            x_unit=x_unit,
            y_unit=y_unit,
            model=self.model,
            serial_number=self.serial_number,
            warnings=tuple(warnings),
        )
