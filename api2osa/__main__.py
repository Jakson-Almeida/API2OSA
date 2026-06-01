"""CLI: python -m api2osa [--device osa|cct] info | read | list."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Protocol

from api2osa.cct import CCT11
from api2osa.osa import OSA203
from api2osa.spectrum import SpectrumResult


class _Spectrometer(Protocol):
    @property
    def model(self) -> str: ...

    @property
    def serial_number(self) -> str: ...

    def read_spectrum(self, **kwargs: object) -> SpectrumResult: ...

    def close(self) -> None: ...

    def __enter__(self) -> "_Spectrometer": ...

    def __exit__(self, *args: object) -> None: ...


def _connect(args: argparse.Namespace) -> _Spectrometer:
    if args.device == "osa":
        return OSA203.connect(
            autogain=args.autogain,
            resolution=args.resolution,
            sensitivity=args.sensitivity,
        )
    return CCT11.connect(device_id=args.device_id)


def _read_kwargs(args: argparse.Namespace) -> dict[str, object]:
    if args.device == "osa":
        return {
            "spectrum_averaging": args.averaging,
            "x_unit": args.x_unit,
            "y_unit": args.y_unit,
            "apodization": args.apodization,
        }
    kwargs: dict[str, object] = {
        "hardware_averaging": args.averaging,
        "x_unit": args.x_unit,
        "y_unit": args.y_unit,
    }
    if args.exposure_ms is not None:
        kwargs["exposure_ms"] = args.exposure_ms
    return kwargs


def _cmd_info(args: argparse.Namespace) -> int:
    with _connect(args) as inst:
        print(f"Instrumento: {args.device}")
        print(f"Modelo:      {inst.model}")
        print(f"ID/Série:    {inst.serial_number}")
    return 0


def _cmd_read(args: argparse.Namespace) -> int:
    with _connect(args) as inst:
        print("A adquirir espectro...", flush=True)
        spec = inst.read_spectrum(**_read_kwargs(args))

    y_label = args.y_unit
    print(f"Pontos: {spec.n_points}")
    print(
        f"wl [{spec.x_unit}]: {spec.wavelength_nm.min():.3f} .. {spec.wavelength_nm.max():.3f}"
    )
    print(f"I [{y_label}]: {spec.intensity.min():.3f} .. {spec.intensity.max():.3f}")
    if spec.warnings:
        print("Avisos:", "; ".join(spec.warnings))

    if args.output:
        out = Path(args.output)
        with out.open("w", encoding="utf-8") as fh:
            fh.write(
                f"# device={args.device}, model={spec.model}, serial={spec.serial_number}, "
                f"x_unit={spec.x_unit}, y_unit={spec.y_unit}\n"
            )
            fh.write(f"wavelength,{y_label}\n")
            for wl, intensity in zip(spec.wavelength_nm, spec.intensity, strict=True):
                fh.write(f"{wl},{intensity}\n")
        print(f"Gravado: {out.resolve()}")

    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    if args.device != "cct":
        print("O comando 'list' só se aplica a --device cct.", file=sys.stderr)
        return 1
    devices = CCT11.list_devices()
    if not devices:
        print("Nenhum dispositivo CCT encontrado.")
        return 1
    for dev_id in devices:
        print(dev_id)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="api2osa",
        description="Leitura de espectros Thorlabs OSA203 e CCT11 (Windows).",
    )
    parser.add_argument(
        "--device",
        choices=("osa", "cct"),
        default="osa",
        help="Tipo de instrumento (padrão: osa).",
    )
    parser.add_argument(
        "--device-id",
        metavar="ID",
        help="ID do CCT (ver 'list'); ignorado para OSA.",
    )
    parser.add_argument(
        "--autogain",
        action="store_true",
        help="[OSA] Ativar autogain na ligação.",
    )
    parser.add_argument(
        "--resolution",
        choices=("low", "high"),
        default="low",
        help="[OSA] Resolução (padrão: low).",
    )
    parser.add_argument(
        "--sensitivity",
        default="low",
        help="[OSA] Sensibilidade (padrão: low).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="Mostrar modelo e ID/série.")
    sub.add_parser("list", help="[CCT] Listar dispositivos disponíveis.")

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
        help="Média de N espectros/frames (padrão: 1).",
    )
    read_p.add_argument(
        "--x-unit",
        default=None,
        help="Rótulo do eixo X (padrão: nm (vac) para OSA, nm para CCT).",
    )
    read_p.add_argument(
        "--y-unit",
        default=None,
        help="Rótulo/unidade do eixo Y (padrão: dBm para OSA, counts para CCT).",
    )
    read_p.add_argument(
        "--apodization",
        default="None",
        help="[OSA] Apodização (padrão: None).",
    )
    read_p.add_argument(
        "--exposure-ms",
        type=float,
        default=None,
        metavar="MS",
        help="[CCT] Tempo de exposição manual em ms.",
    )

    args = parser.parse_args(argv)

    if args.command == "read":
        if args.x_unit is None:
            args.x_unit = "nm (vac)" if args.device == "osa" else "nm"
        if args.y_unit is None:
            args.y_unit = "dBm" if args.device == "osa" else "counts"

    try:
        if args.command == "info":
            return _cmd_info(args)
        if args.command == "read":
            return _cmd_read(args)
        if args.command == "list":
            return _cmd_list(args)
    except FileNotFoundError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
