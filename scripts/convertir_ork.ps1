# =============================================================================
# convertir_ork.ps1
# Script de automatizacion: convierte un archivo de diseno .ork de OpenRocket
# a un Jupyter Notebook listo para analisis con RocketPy.
#
# Proyecto: Club de Ciencias y Tecnologias Espaciales (CCTE)
# Autor:    Equipo de Simulacion CCTE
# Version:  1.0
# =============================================================================

# ---------------------------------------------------------------------------
# CONFIGURACION -- Ajusta estas variables antes de ejecutar el script
# ---------------------------------------------------------------------------

# Nombre del archivo de diseno OpenRocket (debe estar en la carpeta /disenos)
$ARCHIVO_ORK = "cohete.ork"

# Nombre del notebook de salida (se guardara en /notebooks)
$NOTEBOOK_SALIDA = "simulacion_cohete.ipynb"

# Ruta al ejecutable .jar de OpenRocket (dejalo vacio si esta en el PATH del sistema)
# Ejemplo: $JAR_OPENROCKET = ".\OpenRocket-23.09.jar"
$JAR_OPENROCKET = ".\OpenRocket-15.03.jar"

# Ruta raiz del JDK instalado (requerida por JPype para encontrar jvm.dll)
# OpenRocket 15.03 requiere Java 8 -- NO usar Java 11+ con este jar
$JAVA_HOME_PATH = "C:\Program Files\Zulu\zulu-8"

# Codificacion del archivo .ork (por defecto UTF-8)
$ENCODING = "utf-8"

# Mostrar informacion detallada durante la ejecucion
$VERBOSE = "True"

# ---------------------------------------------------------------------------
# RUTAS DEL PROYECTO -- No modificar salvo que cambies la estructura de carpetas
# ---------------------------------------------------------------------------
$RUTA_DISENOS = ".\disenos"
$RUTA_NOTEBOOKS = ".\notebooks"
$RUTA_RESULTADOS = ".\resultados"
$RUTA_ENV_PYTHON = ".\.venv\Scripts\python.exe"
$RUTA_ORK2NOTEBOOK = ".\.venv\Scripts\ork2notebook.exe"

# ---------------------------------------------------------------------------
# VERIFICACION DE PRERREQUISITOS
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   CCTE -- Conversion OpenRocket a Jupyter Notebook  " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que el entorno virtual existe
if (-not (Test-Path $RUTA_ENV_PYTHON)) {
    Write-Host "[ERROR] El entorno virtual no fue encontrado en .venv\" -ForegroundColor Red
    Write-Host "        Ejecuta primero: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Entorno virtual encontrado." -ForegroundColor Green

# 2. Verificar que ork2notebook esta disponible en el entorno
if (-not (Test-Path $RUTA_ORK2NOTEBOOK)) {
    Write-Host "[ERROR] ork2notebook no encontrado. Instala rocketserializer:" -ForegroundColor Red
    Write-Host "        .venv\Scripts\pip.exe install rocketserializer" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] ork2notebook disponible." -ForegroundColor Green

# 3. Verificar que Java esta instalado (requerido por rocketserializer)
try {
    $javaVersion = java -version 2>&1 | Select-String "version"
    Write-Host "[OK] Java detectado: $javaVersion" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Java no esta instalado o no esta en el PATH." -ForegroundColor Red
    Write-Host "        Descarga Java 17+ desde: https://adoptium.net/" -ForegroundColor Yellow
    exit 1
}

# 4. Verificar que el archivo .ork existe en la carpeta de disenos
$RUTA_COMPLETA_ORK = Join-Path $RUTA_DISENOS $ARCHIVO_ORK
if (-not (Test-Path $RUTA_COMPLETA_ORK)) {
    Write-Host "[ERROR] Archivo de diseno no encontrado: $RUTA_COMPLETA_ORK" -ForegroundColor Red
    Write-Host "        Copia tu archivo .ork a la carpeta /disenos antes de continuar." -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Archivo de diseno encontrado: $RUTA_COMPLETA_ORK" -ForegroundColor Green

# ---------------------------------------------------------------------------
# EJECUCION DE LA CONVERSION
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "[INFO] Iniciando conversion de $ARCHIVO_ORK ..." -ForegroundColor Cyan

# Configurar JAVA_HOME para que JPype pueda localizar jvm.dll
$env:JAVA_HOME = $JAVA_HOME_PATH
Write-Host "[INFO] JAVA_HOME configurado: $env:JAVA_HOME" -ForegroundColor Cyan

# Construir la ruta de salida dentro de /notebooks
$RUTA_COMPLETA_SALIDA = Join-Path $RUTA_NOTEBOOKS $NOTEBOOK_SALIDA

# Construir el comando base
$ARGS_CONVERSION = @(
    "--filepath", $RUTA_COMPLETA_ORK,
    "--output", $RUTA_COMPLETA_SALIDA,
    "--encoding", $ENCODING,
    "--verbose", $VERBOSE
)

# Agregar el .jar de OpenRocket si se especifico
if ($JAR_OPENROCKET -ne "") {
    $ARGS_CONVERSION += "--ork_jar", $JAR_OPENROCKET
}

# Ejecutar ork2notebook
& $RUTA_ORK2NOTEBOOK @ARGS_CONVERSION

# ---------------------------------------------------------------------------
# RESULTADO FINAL
# ---------------------------------------------------------------------------

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[EXITO] Notebook generado correctamente:" -ForegroundColor Green
    Write-Host "        $RUTA_COMPLETA_SALIDA" -ForegroundColor White
    Write-Host ""
    Write-Host "[INFO] Guarda los graficos y resultados en: $RUTA_RESULTADOS" -ForegroundColor Cyan
    Write-Host "[INFO] Para abrir el notebook, ejecuta:" -ForegroundColor Cyan
    Write-Host "       .venv\Scripts\jupyter.exe notebook $RUTA_COMPLETA_SALIDA" -ForegroundColor White
    Write-Host ""
}
else {
    Write-Host ""
    Write-Host "[ERROR] La conversion fallo. Revisa los mensajes anteriores." -ForegroundColor Red
    Write-Host "        Asegurate de que la simulacion en OpenRocket fue ejecutada" -ForegroundColor Yellow
    Write-Host "        al menos una vez antes de exportar el archivo .ork." -ForegroundColor Yellow
    exit 1
}
