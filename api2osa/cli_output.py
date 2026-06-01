"""Formatação de espectros para terminal e ficheiros."""

from __future__ import annotations

import sys
from pathlib import Path

from api2osa.spectrum import SpectrumResult


def print_spectrum_summary(spec: SpectrumResult, *, y_label: str) -> None:
    """Resumo legível (stdout)."""
    print(f"Pontos: {spec.n_points}")
    print(
        f"wl [{spec.x_unit}]: {spec.wavelength_nm.min():.3f} .. {spec.wavelength_nm.max():.3f}"
    )
    print(f"I [{y_label}]: {spec.intensity.min():.3f} .. {spec.intensity.max():.3f}")
    if spec.warnings:
        print("Avisos:", "; ".join(spec.warnings))


def print_spectrum_echo(
    spec: SpectrumResult,
    *,
    y_label: str,
    header: bool = True,
    fmt: str = "csv",
) -> None:
    """
    Imprime o espectro em stdout (estilo echo), para pipes e scripts.

    Formatos:
        csv  — wavelength,intensity por linha
        tsv  — separado por tab
        plain — wavelength intensity (espaço)
    """
    if header:
        if fmt == "tsv":
            print(f"wavelength\t{y_label}")
        elif fmt == "plain":
            print(f"# wavelength({spec.x_unit}) intensity({y_label})")
        else:
            print(f"wavelength,{y_label}")

    if fmt == "tsv":
        for wl, intensity in zip(spec.wavelength_nm, spec.intensity, strict=True):
            print(f"{wl}\t{intensity}")
    elif fmt == "plain":
        for wl, intensity in zip(spec.wavelength_nm, spec.intensity, strict=True):
            print(f"{wl} {intensity}")
    else:
        for wl, intensity in zip(spec.wavelength_nm, spec.intensity, strict=True):
            print(f"{wl},{intensity}")


def write_spectrum_csv(
    path: Path,
    spec: SpectrumResult,
    *,
    device: str,
    y_label: str,
) -> None:
    with path.open("w", encoding="utf-8") as fh:
        fh.write(
            f"# device={device}, model={spec.model}, serial={spec.serial_number}, "
            f"x_unit={spec.x_unit}, y_unit={spec.y_unit}\n"
        )
        fh.write(f"wavelength,{y_label}\n")
        for wl, intensity in zip(spec.wavelength_nm, spec.intensity, strict=True):
            fh.write(f"{wl},{intensity}\n")


def print_warnings_stderr(spec: SpectrumResult) -> None:
    if spec.warnings:
        print("Avisos:", "; ".join(spec.warnings), file=sys.stderr)
