<div align="center">

# 🚀 OpenRocket → RocketPy CCTE

**Herramienta de conversión y simulación avanzada de cohetes**  
*Desarrollada por el Club de Ciencias y Tecnologías Espaciales (CCTE)*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![RocketPy](https://img.shields.io/badge/RocketPy-1.12.1-orange?logo=rocket&logoColor=white)](https://rocketpy.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## ¿Qué es esto?

**OpenRocket → RocketPy CCTE** es una aplicación de escritorio con interfaz gráfica que permite convertir diseños de cohetes creados en [OpenRocket](https://openrocket.info/) (`.ork`) en simulaciones avanzadas ejecutadas con [RocketPy](https://rocketpy.org/), el motor de simulación aeroespacial de código abierto más completo disponible.

La herramienta incluye:

- 🗂️ **Carga de archivos `.ork`** directamente desde la interfaz
- 🌍 **Selección de coordenadas geográficas** de lanzamiento (latitud, longitud, elevación)
- 🌤️ **Modelo atmosférico dinámico** via [Open-Meteo](https://open-meteo.com/) o Atmósfera Estándar ISA
- ⚙️ **Generación automática** de Jupyter Notebooks con todos los parámetros del cohete
- 📊 **Visualización integrada** de resultados de simulación en la misma ventana
- 🌙 **Interfaz Light / Dark Mode** con estética iOS moderna

> **No se requiere instalar Python.** El ejecutable `rocketpy_ccte.exe` incluye todo lo necesario.

---

## Requisitos Previos

Antes de ejecutar la aplicación, asegúrate de tener instalado:

| Requisito  | Versión mínima | Descarga                                    | ¿Para qué se usa?                         |
|------------|----------------|---------------------------------------------|-------------------------------------------|
| **Java**   | 17+            | [adoptium.net](https://adoptium.net/)       | Parsear archivos `.ork` de OpenRocket     |
| **OpenRocket** | 22.02+     | [openrocket.info](https://openrocket.info/) | Diseñar y pre-simular el cohete           |

> ⚠️ **Java es obligatorio.** Sin él, la conversión del archivo `.ork` fallará.  
> Verifica que esté instalado correctamente ejecutando `java -version` en una terminal.

---

## Descarga e Instalación

1. Descarga el archivo `rocketpy_ccte.exe` desde la sección [**Releases**](https://github.com/DaniVillalba03/openrocket_to_rocketpy/releases) del repositorio.
2. Coloca el ejecutable en una carpeta de tu elección (por ejemplo: `C:\Simulaciones\CCTE\`).
3. ¡Listo! No es necesario instalar nada más.

> 💡 La primera vez que lo ejecutes, Windows puede mostrar una advertencia de SmartScreen.  
> Haz clic en **"Más información" → "Ejecutar de todas formas"** para continuar.

---

## Guía de Uso Paso a Paso

### Paso 1 — Diseñar el cohete en OpenRocket

1. Abre **OpenRocket** y diseña tu cohete.
2. Ve al menú **Simulaciones → Ejecutar todas las simulaciones**.
3. Guarda el archivo con `Archivo → Guardar como` con extensión `.ork`.

> 🔴 **Importante:** El archivo `.ork` **debe tener al menos una simulación ejecutada**.  
> Sin esto, el serializador no puede extraer los datos de vuelo del cohete.

---

### Paso 2 — Abrir la aplicación

Haz doble clic en `rocketpy_ccte.exe`.

Se abrirá la ventana principal de la aplicación:

```
┌─────────────────────────────────────────┐
│         OpenRocket → RocketPy           │
│              CCTE  🚀                   │
├─────────────────────────────────────────┤
│  [Seleccionar archivo .ork]             │
│                                         │
│  Latitud:   [ _____ ]                   │
│  Longitud:  [ _____ ]                   │
│  Elevación: [ _____ ] m                 │
│                                         │
│  ☐ Usar Atmósfera Estándar (ISA)        │
│                                         │
│         [ ▶ Iniciar Simulación ]        │
└─────────────────────────────────────────┘
```

---

### Paso 3 — Cargar el archivo `.ork`

Haz clic en el botón **"Seleccionar archivo .ork"** y navega hasta el archivo `.ork` exportado desde OpenRocket.

El nombre del archivo seleccionado aparecerá confirmado en la interfaz.

---

### Paso 4 — Configurar los parámetros de lanzamiento

Ingresa las coordenadas del sitio de lanzamiento:

| Campo       | Descripción                              | Ejemplo         |
|-------------|------------------------------------------|-----------------|
| **Latitud** | Coordenada norte/sur del sitio           | `-34.617`       |
| **Longitud**| Coordenada este/oeste del sitio          | `-58.368`       |
| **Elevación**| Altitud sobre el nivel del mar en metros | `25`            |

> 🗺️ Puedes obtener las coordenadas exactas de tu sitio desde [Google Maps](https://maps.google.com) haciendo clic derecho en el punto deseado.

---

### Paso 5 — Seleccionar el modelo atmosférico

Tienes dos opciones:

| Opción                          | Descripción                                                                 |
|---------------------------------|-----------------------------------------------------------------------------|
| ☐ **Clima Dinámico (por defecto)** | Descarga datos reales de viento y temperatura de Open-Meteo en tiempo real |
| ☑ **Atmósfera Estándar (ISA)**     | Usa el modelo ISA estático. No requiere internet. Ideal para entornos sin conexión |

---

### Paso 6 — Ejecutar la simulación

Haz clic en **"▶ Iniciar Simulación"**.

La aplicación realizará automáticamente:

1. ✅ Extracción de parámetros del archivo `.ork`
2. ✅ Generación del Jupyter Notebook con los datos del cohete
3. ✅ Inyección de coordenadas geográficas y modelo atmosférico
4. ✅ Ejecución de la simulación con RocketPy
5. ✅ Visualización de los resultados en la ventana integrada

El progreso se mostrará en tiempo real en la barra de estado inferior.

---

### Paso 7 — Revisar los resultados

Una vez completada la simulación, los resultados aparecerán directamente en la pestaña de visualización dentro de la aplicación.

Los archivos generados se guardan automáticamente en:

```
<carpeta del .exe>/
├── notebooks/
│   └── simulacion_cohete.ipynb   ← Notebook completo con toda la simulación
├── simulaciones/
│   └── parameters.json           ← Parámetros extraídos del .ork
└── resultados/
    └── *.png / *.pdf             ← Gráficos y reportes exportados
```

---

## Solución de Problemas

| Error / Síntoma                        | Causa probable                             | Solución                                                                 |
|----------------------------------------|---------------------------------------------|--------------------------------------------------------------------------|
| `Java not found`                        | Java no está instalado o no está en PATH    | Instala Java 17+ desde [adoptium.net](https://adoptium.net/) y reinicia   |
| `No simulation data` / sin resultados  | El `.ork` no tiene simulaciones ejecutadas  | Ejecuta al menos una simulación dentro de OpenRocket antes de exportar   |
| La app no abre (SmartScreen)           | Windows bloqueó el ejecutable               | Clic en "Más información" → "Ejecutar de todas formas"                   |
| Error de conexión al descargar clima   | Sin acceso a internet                       | Activa la opción **"Atmósfera Estándar (ISA)"** en la interfaz           |
| El notebook no se genera               | Archivo `.ork` corrupto o inválido          | Vuelve a exportar el `.ork` desde OpenRocket asegurando que el diseño sea válido |
| Pantalla en blanco en resultados       | Falta dependencia de visualización          | Contacta al equipo de soporte de CCTE                                    |

---

## Estructura del Proyecto

> Esta sección es de interés para desarrolladores o colaboradores del proyecto.

```
RocketPy_CCTE/
│
├── gui.py                    ← Aplicación principal (PyQt5)
├── gui.spec                  ← Configuración de PyInstaller para generar el .exe
│
├── disenos/                  ← Archivos de diseño OpenRocket (.ork)
├── simulaciones/             ← Parámetros JSON extraídos por rocketserializer
├── notebooks/                ← Jupyter Notebooks generados automáticamente
├── datos_atmosfericos/       ← Perfiles atmosféricos (NetCDF, CSV)
├── resultados/               ← Gráficos y reportes de simulación
├── motores_CCTE/             ← Base de datos de motores del club
│
├── scripts/
│   ├── convertir_ork.ps1     ← Conversión manual .ork → notebook (PowerShell)
│   └── verificar_entorno.ps1 ← Diagnóstico del entorno de desarrollo
│
└── .venv/                    ← Entorno virtual Python (solo para desarrollo)
```

---

## Stack Tecnológico

| Componente           | Tecnología / Paquete            | Versión  |
|----------------------|---------------------------------|----------|
| Motor de simulación  | `rocketpy`                      | 1.12.1   |
| Conversión `.ork`    | `rocketserializer`              | 0.2.0    |
| Interfaz gráfica     | `PyQt5`                         | 5.x      |
| Notebooks            | `jupyter`                       | 1.1.1    |
| Álgebra numérica     | `numpy`                         | 2.4.6    |
| Métodos científicos  | `scipy`                         | 1.17.1   |
| Visualización        | `matplotlib`                    | 3.11.0   |
| Datos atmosféricos   | `netCDF4`                       | 1.7.4    |
| Empaquetado          | `PyInstaller`                   | 6.x      |

---

## Para Desarrolladores — Compilar desde el código fuente

Si quieres modificar la aplicación y recompilar el ejecutable:

```powershell
# 1. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install "rocketpy[all]" jupyter rocketserializer PyQt5 PyQtWebEngine pyinstaller

# 3. Compilar el ejecutable
pyinstaller gui.spec
```

El ejecutable resultante se encontrará en `dist/rocketpy_ccte.exe`.

---

## Datos Atmosféricos (Uso Avanzado)

Para simulaciones con perfiles atmosféricos históricos o de alta precisión, puedes descargar datos externos:

- **GFS — Global Forecast System:** [nomads.ncep.noaa.gov](https://nomads.ncep.noaa.gov/)
- **Sondeos Argentina:** [weather.uwyo.edu](https://weather.uwyo.edu/upperair/sounding.html)

Guarda los archivos descargados (`.nc` o `.csv`) en la carpeta `/datos_atmosfericos/` y configúralos manualmente en el notebook generado.

---

## Contacto y Soporte

<div align="center">

**Club de Ciencias y Tecnologías Espaciales — CCTE**

Para reportar errores, sugerir mejoras o consultar sobre el proyecto,  
abre un [Issue](https://github.com/DaniVillalba03/openrocket_to_rocketpy/issues) en el repositorio.

</div>

---

<div align="center">

*Documentación — RocketPy CCTE v1.0 · Hecho con ❤️ para la comunidad aeroespacial estudiantil*

</div>
