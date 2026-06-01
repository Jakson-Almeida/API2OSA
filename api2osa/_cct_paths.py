"""Localiza as DLLs .NET do Compact Spectrograph (CCT11)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SDK_DIR = _REPO_ROOT / "sdk"
_BUNDLED_NET48 = _SDK_DIR / "net48"

_DEFAULT_INSTALL = Path(
    r"C:\Program Files\Thorlabs\Compact Spectrograph"
)


def _net48_has_driver_dll(folder: Path) -> bool:
    return (folder / "Thorlabs.ManagedDevice.CompactSpectrographDriver.dll").is_file()


def resolve_net48_dir() -> Path:
    """
    Devolve a pasta net48 com as DLLs do SDK CCT.

    Raises:
        FileNotFoundError: Se nenhuma pasta válida for encontrada.
    """
    candidates: list[Path] = []

    env = os.environ.get("CCT_SDK_PATH")
    if env:
        candidates.append(Path(env))

    if _BUNDLED_NET48.is_dir():
        candidates.append(_BUNDLED_NET48)

    if _DEFAULT_INSTALL.is_dir():
        for sub in ("net48", "NET48", "bin", "Bin"):
            p = _DEFAULT_INSTALL / sub
            if p.is_dir():
                candidates.append(p)
        candidates.append(_DEFAULT_INSTALL)

    for folder in candidates:
        if _net48_has_driver_dll(folder):
            return folder.resolve()

    raise FileNotFoundError(
        "DLLs do Compact Spectrograph não encontradas. Instale o software Thorlabs "
        "do CCT11, copie as DLLs para sdk/net48/, ou defina CCT_SDK_PATH. Veja README.md."
    )


def configure_cct_sdk() -> Path:
    """Garante que `sdk` está no path para importar pyCCT."""
    if str(_SDK_DIR) not in sys.path:
        sys.path.insert(0, str(_SDK_DIR))
    return resolve_net48_dir()
