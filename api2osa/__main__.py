"""CLI: python -m api2osa info | read."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from api2osa.device import OSA203


def _cmd_info(args: argparse.Namespace) -> int:
    with OSA203.connect(
        autogain=args.autogain,
        resolution=args.resolution,
        sensitivity=args.sensitivity,
    ) as osa:
        print(f"Modelo:  {osa.model}")
        print(f"Serial:  {osa.serial_number}")
    return 0


def _cmd_read(args: argparse.Namespace) -> int:
    with OSA203.connect(
        autogain=args.autogain,
        resolution=args.resolution,
        sensitivity=args.sensitivity,
    ) as osa:
        print("A adquirir espectro...", flush=True)
        spec = osa.read_spectrum(
            spectrum_averaging=args.averaging,
            x_unit=args.x_unit,
            y_unit=args.y_unit,
            apodization=args.apodization,
        )

    print(f"Pontos: {spec.n_points}")
    print(f"λ [{spec.x_unit}]: {spec.wavelength_nm.min():.3f} … {spec.wavelength_nm.max():.3f}")
    print(f"I [{spec.y_unit}]: {spec.intensity.min():.3f} … {spec.intensity.max():.3f}")
    if spec.warnings:
        print("Avisos:", "; ".join(spec.warnings))

    if args.output:
        out = Path(args.output)
        with out.open("w", encoding="utf-8") as fh:
            fh.write(
                f"# model={spec.model}, serial={spec.serial_number}, "
                f"x_unit={spec.x_unit}, y_unit={spec.y_unit}\n"
            )
            fh.write(f"wavelength,{args.y_unit}\n")
            for wl, intensity in zip(spec.wavelength_nm, spec.intensity, strict=True):
                fh.write(f"{wl},{intensity}\n")
        print(f"Gravado: {out.resolve()}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="api2osa",
        description="Leitura de espectros Thorlabs OSA203 (Windows + FTSLib).",
    )
    parser.add_argument(
        "--autogain",
        action="store_true",
        help="Ativar autogain na ligação.",
    )
    parser.add_argument(
        "--resolution",
        choices=("low", "high"),
        default="low",
        help="Resolução (padrão: low).",
    )
    parser.add_argument(
        "--sensitivity",
        default="low",
        help="Sensibilidade (padrão: low).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="Mostrar modelo e número de série.")

    read_p = sub.add_parser("read", help="Adquirir um espectro.")
    read_p.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Gravar CSV (wavelength, intensidade).",
    )
    read_p.add_argument(
        "-n",
        "--averaging",
        type=int,
        default=1,
        metavar="N",
        help="Média de N espectros (padrão: 1).",
    )
    read_p.add_argument(
        "--x-unit",
        default="nm (vac)",
        help='Unidade do eixo X (padrão: "nm (vac)").',
    )
    read_p.add_argument(
        "--y-unit",
        default="dBm",
        help="Unidade do eixo Y (padrão: dBm).",
    )
    read_p.add_argument(
        "--apodization",
        default="None",
        help="Apodização (padrão: None).",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "info":
            return _cmd_info(args)
        if args.command == "read":
            return _cmd_read(args)
    except FileNotFoundError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
