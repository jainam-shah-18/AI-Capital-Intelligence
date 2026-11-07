$ErrorActionPreference = "Stop"
py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
Write-Host "Environment created. Edit .env and set SEC_USER_AGENT before running the pipeline."
Write-Host "Activate with: .\.venv\Scripts\Activate.ps1"
Write-Host "Then run: python -m src.aci.pipeline"
