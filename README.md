# API2OSA

API mínima em Python para **ler espectros** de instrumentos Thorlabs em **Windows**, a partir do terminal:

| Instrumento | Flag CLI | SDK |
|-------------|----------|-----|
| **OSA203** (série OSA 20x) | `--device osa` (padrão) | pyOSA + `FTSLib.dll` (ThorSpectra) |
| **CCT11** (Compact Spectrograph) | `--device cct` | pyCCT + DLLs .NET (`net48`) |

Sem interface gráfica — apenas conectar, medir e exportar dados.

---

## Requisitos

| Item | OSA203 | CCT11 |
|------|--------|-------|
| SO | Windows 10/11 (64-bit) | Idem |
| Python | 3.10+ | 3.10+ |
| Ligação | USB | USB ou Ethernet (conforme modelo) |
| Software Thorlabs | **ThorSpectra** | **Compact Spectrograph** SDK / app CCT |

Dependências Python: `numpy`, `pythonnet` (só necessário para CCT).

O código Python (`sdk/pyOSA`, `sdk/pyCCT.py`) já vem no repositório. As **DLLs do fabricante** instalam-se à parte.

---

## 1. Instalar SDKs Thorlabs

### OSA203 — ThorSpectra (FTSLib)

1. Instale ThorSpectra (instalador Thorlabs do OSA).
2. DLL habitual: `C:\Program Files\Thorlabs\ThorSpectra\FTSLib.dll`
3. Ou copie para `sdk\FTSLib\FTSLib.dll` (pasta no `.gitignore`).

```powershell
$env:FTSLIB_PATH = "D:\caminho\para\FTSLib.dll"   # opcional
```

### CCT11 — Compact Spectrograph (.NET)

Com **ThorSpectra** instalado, a API deteta automaticamente as DLLs em:

`C:\Program Files\Thorlabs\ThorSpectra\Examples\CompactSpectrometer\Python\pyCCT\net48`

Alternativas:

1. Copie essa pasta **net48** para `sdk\net48\` neste repositório.
2. Ou defina (pasta **net48** completa — não use só `ThorSpectra\`, faltam DLLs `Microsoft.Extensions.*`):

```powershell
$env:CCT_SDK_PATH = "C:\Program Files\Thorlabs\ThorSpectra\Examples\CompactSpectrometer\Python\pyCCT\net48"
```

---

## 2. Ambiente Python

```powershell
cd C:\Users\DELL\Documents\GitHub\API2OSA
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 3. Uso no terminal

Forma geral:

```text
python -m api2osa [--device osa|cct] [opções globais] <comando> [opções do comando]
```

Ative o ambiente antes: `.\.venv\Scripts\activate`

### Comandos disponíveis

| Comando | OSA203 | CCT11 | Descrição |
|---------|:------:|:-----:|-----------|
| `info` | sim | sim | Modelo e ID/série; liga e desliga o instrumento |
| `read` | sim | sim | Mede um espectro e mostra **resumo** no terminal |
| `echo` | sim | sim | Mede e imprime **todos os pontos** em stdout (pipe/ficheiro) |
| `list` | — | sim | Lista IDs dos CCT ligados (sem medição) |

### Opções globais

| Opção | Padrão | Descrição |
|-------|--------|-----------|
| `--device osa` \| `cct` | `osa` | Tipo de instrumento |
| `--device-id ID` | primeiro CCT | ID exato do CCT (`list` mostra os IDs) |
| `--autogain` | desligado | [OSA] Autogain na ligação |
| `--resolution low` \| `high` | `low` | [OSA] Resolução |
| `--sensitivity TEXTO` | `low` | [OSA] Sensibilidade |

### Opções de medição (`read` e `echo`)

| Opção | Padrão | Descrição |
|-------|--------|-----------|
| `-n`, `--averaging N` | `1` | Média de N espectros (OSA) ou frames (CCT) |
| `--x-unit` | `nm (vac)` / `nm` | Rótulo do eixo X |
| `--y-unit` | `dBm` / `counts` | Rótulo do eixo Y |
| `--apodization` | `None` | [OSA] Apodização |
| `--exposure-ms MS` | atual | [CCT] Exposição manual em ms |

### Opções só do `read`

| Opção | Descrição |
|-------|-----------|
| `-o`, `--output FILE` | Gravar CSV com comentário `#` no topo |

### Opções só do `echo`

| Opção | Descrição |
|-------|-----------|
| `--no-header` | Só dados numéricos (sem linha `wavelength,...`) |
| `--format csv` \| `tsv` \| `plain` | Formato de cada linha (padrão: `csv`) |

`read` mostra resumo (nº de pontos, intervalo de λ e intensidade). **`echo`** envia cada par `(wavelength, intensidade)` para **stdout**; *A adquirir espectro...* e avisos vão para **stderr**, para poder usar `>` ou pipes.

### Exemplos — OSA203

```powershell
python -m api2osa info
python -m api2osa read
python -m api2osa read -o espectro_osa.csv -n 5 --y-unit dBm
python -m api2osa read --autogain --resolution high

# Imprimir espectro no terminal ou guardar
python -m api2osa echo
python -m api2osa echo > espectro_osa.csv
python -m api2osa echo --format plain -n 3 --no-header
```

### Exemplos — CCT11

```powershell
python -m api2osa --device cct list
python -m api2osa --device cct info
python -m api2osa --device cct info --device-id CCT11-M01257363

python -m api2osa --device cct read
python -m api2osa --device cct read -o espectro_cct.csv -n 10 --exposure-ms 50

python -m api2osa --device cct echo
python -m api2osa --device cct echo > espectro_cct.csv
python -m api2osa --device cct echo --no-header | Select-Object -First 5
python -m api2osa --device cct echo --format tsv
```

### Ajuda por comando

```powershell
python -m api2osa --help
python -m api2osa read --help
python -m api2osa echo --help
```

---

## 4. Uso em código Python

**OSA203:**

```python
from api2osa import OSA203

with OSA203.connect() as osa:
    spec = osa.read_spectrum(spectrum_averaging=1)
    print(spec.model, spec.n_points)
```

**CCT11:**

```python
from api2osa import CCT11

for dev_id in CCT11.list_devices():
    print(dev_id)

with CCT11.connect() as cct:
    spec = cct.read_spectrum(hardware_averaging=5, exposure_ms=100.0)
    print(cct.device_id, spec.n_points)
```

Ambos devolvem o mesmo tipo `SpectrumResult` (`wavelength_nm`, `intensity`, `warnings`, …).

---

## Estrutura do projeto

```text
API2OSA/
  api2osa/
    __main__.py     # CLI (info, read, echo, list)
    cli_output.py   # Formato terminal/CSV
    osa.py          # OSA203
    cct.py          # CCT11
    spectrum.py     # SpectrumResult
  sdk/
    pyOSA/          # OSA (vendored)
    pyCCT.py        # CCT (vendored)
    FTSLib/         # FTSLib.dll (local, gitignored)
    net48/          # DLLs .NET CCT (gitignored)
```

---

## Problemas comuns

| Sintoma | O que fazer |
|---------|-------------|
| `FTSLib.dll não encontrada` | Instalar ThorSpectra ou `FTSLIB_PATH` |
| `DLLs do Compact Spectrograph não encontradas` | Instalar SDK CCT, copiar `net48` ou `CCT_SDK_PATH` |
| `No OSA found` | USB OSA; fechar ThorSpectra |
| `Nenhum espectrógrafo CCT encontrado` | USB/rede; app Thorlabs fechada; `python -m api2osa --device cct list` |
| `O acesso à porta 'COMx' foi negado` | [CCT] Fechar ThorSpectra/outra app que use a COM do CCT |
| `CCT_SDK_PATH` / DLL incompleta | Usar pasta `...\pyCCT\net48` completa (ver secção 1) |
| Erro `pythonnet` / `clr` | `pip install pythonnet`; usar Python 64-bit no Windows |
| `has already been initialized` | Uma ligação OSA por processo Python |

---

## Evolução (ESP32 / Raspberry Pi)

OSA e CCT exigem **host Windows** com as DLLs Thorlabs. Microcontroladores podem consumir espectros via um **serviço** neste PC (fase futura).

---

## Licença

Código deste repositório: MIT. `sdk/pyOSA`, `sdk/pyCCT.py` e DLLs Thorlabs — respeitar licença do fabricante.
