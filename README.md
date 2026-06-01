# API2OSA

API mínima em Python para **ler espectros** do analisador óptico **Thorlabs OSA203** (série OSA 20x), em **Windows**, a partir do terminal.

Não inclui interface gráfica nem processamento de sensores em fibra — apenas conectar, medir e exportar dados.

---

## Requisitos

| Item | Detalhe |
|------|---------|
| SO | Windows 10/11 (64-bit) |
| Python | 3.10 ou superior |
| Hardware | OSA203 ligado por **USB** |
| Software Thorlabs | **ThorSpectra** (instala `FTSLib.dll` e drivers USB) |

O pyOSA já está incluído em `sdk/pyOSA/`. **Não** é preciso instalar pyOSA à parte; só a DLL do Thorlabs.

---

## 1. Instalar ThorSpectra (FTSLib)

1. Descarregue o software do seu instrumento na página Thorlabs (OSA / ThorSpectra), ou use o instalador que veio com o OSA.
2. Instale com as opções por defeito. A DLL costuma ficar em:

   `C:\Program Files\Thorlabs\ThorSpectra\FTSLib.dll`

3. Ligue o OSA203 por USB e confirme no **Gestor de dispositivos** que o Windows reconhece o equipamento (sem instalação, abra o ThorSpectra uma vez para validar).

**Alternativa:** copie `FTSLib.dll` (e ficheiros `.dll` adjacentes do mesmo diretório, se existirem) para:

`sdk\FTSLib\FTSLib.dll`

neste repositório. Essa pasta está no `.gitignore` (licença Thorlabs).

**Variável opcional** se a DLL estiver noutro sítio:

```powershell
$env:FTSLIB_PATH = "D:\caminho\para\FTSLib.dll"
```

---

## 2. Ambiente Python

Na pasta do projeto:

```powershell
cd C:\Users\DELL\Documents\GitHub\API2OSA
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 3. Uso no terminal

**Informação do instrumento** (liga, lê modelo/série, desliga):

```powershell
python -m api2osa info
```

**Um espectro** (imprime resumo no ecrã):

```powershell
python -m api2osa read
```

**Gravar CSV:**

```powershell
python -m api2osa read -o espectro.csv
```

**Opções úteis:**

```powershell
python -m api2osa read -n 5 --y-unit dBm --resolution low --sensitivity low
python -m api2osa read --autogain
```

---

## 4. Uso em código Python

```python
from api2osa import OSA203

with OSA203.connect() as osa:
    spec = osa.read_spectrum(spectrum_averaging=1)
    print(spec.model, spec.n_points)
    print(spec.wavelength_nm[:5], spec.intensity[:5])
```

---

## Estrutura do projeto

```text
API2OSA/
  api2osa/          # API e CLI
  sdk/pyOSA/        # SDK Python Thorlabs (vendored)
  requirements.txt
```

---

## Problemas comuns

| Sintoma | O que fazer |
|---------|-------------|
| `FTSLib.dll não encontrada` | Instalar ThorSpectra ou definir `FTSLIB_PATH` |
| `No OSA found` | USB, cabo, alimentação; fechar ThorSpectra se estiver a usar o OSA |
| `has already been initialized` | Só uma ligação por processo; feche outros scripts ou reinicie o Python |
| `Reference Warmup` | Aguarde aquecimento do laser de referência; a API ignora este aviso por defeito |
| Erro de versão da DLL | ThorSpectra **3.31+** (exigido pelo pyOSA) |

---

## Evolução (ESP32 / Raspberry Pi)

O OSA203 **não** fala UART/SCPI: o host Windows mantém o USB e a `FTSLib.dll`. Microcontroladores podem pedir espectros a um **serviço** neste PC (fase futura), com comandos simples em texto ou JSON.

---

## Licença

Código deste repositório: MIT (ver `LICENSE` se existir). `sdk/pyOSA` e `FTSLib.dll` são da Thorlabs — respeite a licença e redistribuição do fabricante.
