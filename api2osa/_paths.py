"""Configura `FTSLIB_PATH` e o `sys.path` para o pyOSA vendored."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SDK_DIR = _REPO_ROOT / "sdk"
_BUNDLED_DLL = _SDK_DIR / "FTSLib" / "FTSLib.dll"

# Instalação padrão ThorSpectra no Windows
_DEFAULT_THORSPECTRA_DLL = Path(
    r"C:\Program Files\Thorlabs\ThorSpectra\FTSLib.dll"
)


def _first_existing_dll() -> Path | None:
    candidates = [
        os.environ.get("FTSLIB_PATH"),
        str(_BUNDLED_DLL) if _BUNDLED_DLL.is_file() else None,
        str(_DEFAULT_THORSPECTRA_DLL) if _DEFAULT_THORSPECTRA_DLL.is_file() else None,
    ]
    for path in candidates:
        if path and Path(path).is_file():
            return Path(path)
    return None


def configure_sdk() -> Path:
    """
    Prepara o ambiente antes de importar pyOSA.

    Returns:
        Caminho absoluto para FTSLib.dll.

    Raises:
        FileNotFoundError: Se a DLL não for encontrada.
    """
    if str(_SDK_DIR) not in sys.path:
        sys.path.insert(0, str(_SDK_DIR))

    dll = _first_existing_dll()
    if dll is None:
        raise FileNotFoundError(
            "FTSLib.dll não encontrada. Instale ThorSpectra (Thorlabs) ou defina "
            "FTSLIB_PATH com o caminho completo da DLL. Veja README.md."
        )

    os.environ["FTSLIB_PATH"] = str(dll.resolve())
    return dll.resolve()
