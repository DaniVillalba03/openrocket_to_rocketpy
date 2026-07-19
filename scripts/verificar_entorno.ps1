# =============================================================================
# verificar_entorno.ps1
# Script de diagnostico: verifica que todos los componentes del entorno
# de simulacion esten correctamente instalados y configurados.
#
# Proyecto: Club de Ciencias y Tecnologias Espaciales (CCTE)
# =============================================================================

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   CCTE --- Verificacion del Entorno        " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# --- Verificar Python en el entorno virtual ---
Write-Host ">>> Python" -ForegroundColor Yellow
if (Test-Path ".\.venv\Scripts\python.exe") {
    $v = & ".\.venv\Scripts\python.exe" --version 2>&1
    Write-Host "    [OK] $v" -ForegroundColor Green
} else {
    Write-Host "    [FALLO] Python no encontrado en .venv\" -ForegroundColor Red
}

# --- Verificar Java (requerido por rocketserializer) ---
Write-Host ">>> Java" -ForegroundColor Yellow
try {
    $j = & java -version 2>&1 | Select-Object -First 1
    Write-Host "    [OK] $j" -ForegroundColor Green
}
catch {
    Write-Host "    [FALLO] Java no instalado o no esta en el PATH" -ForegroundColor Red
}

# --- Verificar paquetes Python clave ---
Write-Host ">>> Paquetes instalados" -ForegroundColor Yellow
$paquetes = @("rocketpy", "rocketserializer", "jupyter", "numpy", "scipy", "matplotlib")
foreach ($pkg in $paquetes) {
    $resultado = & ".\.venv\Scripts\pip.exe" show $pkg 2>&1 | Select-String "^Version:" | Select-Object -First 1
    if ($resultado) {
        Write-Host "    [OK] $pkg --- $resultado" -ForegroundColor Green
    }
    else {
        Write-Host "    [FALTA] $pkg no esta instalado" -ForegroundColor Red
    }
}

# --- Verificar CLI ork2notebook ---
Write-Host ">>> CLI ork2notebook" -ForegroundColor Yellow
if (Test-Path ".\.venv\Scripts\ork2notebook.exe") {
    Write-Host "    [OK] Disponible en .venv\Scripts\ork2notebook.exe" -ForegroundColor Green
}
else {
    Write-Host "    [FALLO] No encontrado. Instala rocketserializer." -ForegroundColor Red
}

# --- Verificar estructura de carpetas del proyecto ---
Write-Host ">>> Estructura de carpetas" -ForegroundColor Yellow
$carpetas = @("disenos", "simulaciones", "notebooks", "datos_atmosfericos", "resultados", "scripts")
foreach ($carpeta in $carpetas) {
    if (Test-Path ".\$carpeta") {
        Write-Host "    [OK] /$carpeta" -ForegroundColor Green
    }
    else {
        Write-Host "    [FALTA] /$carpeta no existe" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Verificacion completada." -ForegroundColor Cyan
Write-Host ""
