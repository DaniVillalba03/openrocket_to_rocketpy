import sys
import os
import json
import zipfile
import xml.etree.ElementTree as ET
import subprocess
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QCheckBox, 
                             QFileDialog, QMessageBox, QFrame, QSizePolicy)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl

# Intentar importar PyQtWebEngine (dependencia necesaria)
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

# --- HOJAS DE ESTILO GLOBALES (QSS) ---
# Estilo "iOS Light"
QSS_LIGHT = """
/* Global Config */
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 14px;
    color: #1c1c1e;
}

QMainWindow {
    background-color: #f2f2f7;
}

QWidget {
    background-color: #f2f2f7;
}

/* Containers */
#controlPanel, #exportPanel {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #e5e5ea;
}

#webContainer {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #e5e5ea;
}

/* Status Labels */
#statusLabel {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    padding: 6px 12px;
    color: #8e8e93;
    font-weight: 500;
}

#progressLabel {
    font-size: 13px;
    font-weight: 600;
    color: #007aff;
    letter-spacing: 1px;
    margin: 5px 0px;
}

#webPlaceholder {
    background-color: #ffffff;
    color: #8e8e93;
    font-size: 16px;
    border-radius: 12px;
}

/* Buttons */
QPushButton {
    background-color: #e5e5ea;
    color: #007aff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #d1d1d6;
}

QPushButton:pressed {
    background-color: #c7c7cc;
}

QPushButton:disabled {
    background-color: #f2f2f7;
    color: #aeaeb2;
}

/* Main Action Button (Start) */
#startBtn {
    background-color: #007aff;
    color: #ffffff;
    border-radius: 10px;
    font-size: 15px;
    font-weight: bold;
    padding: 10px 24px;
}

#startBtn:hover {
    background-color: #0060cc;
}

#startBtn:pressed {
    background-color: #004c9e;
}

#startBtn:disabled {
    background-color: #a1caff;
    color: #ffffff;
}

/* Checkboxes */
QCheckBox {
    spacing: 10px;
    font-weight: 500;
    color: #1c1c1e;
    background-color: transparent;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 10px;
    border: 1.5px solid #c7c7cc;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border: 1.5px solid #007aff;
}

QCheckBox::indicator:checked {
    background-color: #007aff;
    border: 1.5px solid #007aff;
}
"""

# Estilo "iOS Dark"
QSS_DARK = """
/* Global Config */
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 14px;
    color: #f5f5f7;
}

QMainWindow {
    background-color: #000000;
}

QWidget {
    background-color: #000000;
}

/* Containers */
#controlPanel, #exportPanel {
    background-color: #1c1c1e;
    border-radius: 12px;
    border: 1px solid #2c2c2e;
}

#webContainer {
    background-color: #1c1c1e;
    border-radius: 12px;
    border: 1px solid #2c2c2e;
}

/* Status Labels */
#statusLabel {
    background-color: #1c1c1e;
    border: 1px solid #2c2c2e;
    border-radius: 8px;
    padding: 6px 12px;
    color: #8e8e93;
    font-weight: 500;
}

#progressLabel {
    font-size: 13px;
    font-weight: 600;
    color: #0a84ff;
    letter-spacing: 1px;
    margin: 5px 0px;
}

#webPlaceholder {
    background-color: #1c1c1e;
    color: #8e8e93;
    font-size: 16px;
    border-radius: 12px;
}

/* Buttons */
QPushButton {
    background-color: #2c2c2e;
    color: #0a84ff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #3a3a3c;
}

QPushButton:pressed {
    background-color: #48484a;
}

QPushButton:disabled {
    background-color: #1c1c1e;
    color: #636366;
}

/* Main Action Button (Start) */
#startBtn {
    background-color: #0a84ff;
    color: #ffffff;
    border-radius: 10px;
    font-size: 15px;
    font-weight: bold;
    padding: 10px 24px;
}

#startBtn:hover {
    background-color: #007aff;
}

#startBtn:pressed {
    background-color: #0060cc;
}

#startBtn:disabled {
    background-color: #003a70;
    color: #8e8e93;
}

/* Checkboxes */
QCheckBox {
    spacing: 10px;
    font-weight: 500;
    color: #f5f5f7;
    background-color: transparent;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 10px;
    border: 1.5px solid #48484a;
    background-color: #1c1c1e;
}

QCheckBox::indicator:hover {
    border: 1.5px solid #0a84ff;
}

QCheckBox::indicator:checked {
    background-color: #0a84ff;
    border: 1.5px solid #0a84ff;
}
"""

# --- WORKER THREAD PARA EJECUCION EN SEGUNDO PLANO ---
class SimulationWorker(QThread):
    finished = pyqtSignal(str, str) # HTML Path, KML Path
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, ork_path, lat, lon, elev, use_standard_atmosphere, use_dark_mode):
        super().__init__()
        self.ork_path = ork_path
        self.lat = lat
        self.lon = lon
        self.elev = elev
        self.use_standard_atmosphere = use_standard_atmosphere
        self.use_dark_mode = use_dark_mode

    def run(self):
        try:
            self.progress.emit("PREPARANDO ENTORNO Y PARÁMETROS...")
            # Rutas
            if getattr(sys, 'frozen', False):
                root_dir = os.path.dirname(sys.executable)
            else:
                root_dir = os.path.dirname(os.path.abspath(__file__))
            notebook_dir = os.path.join(root_dir, 'notebooks', 'simulacion_cohete.ipynb')
            notebook_path = os.path.join(notebook_dir, 'simulation.ipynb')
            temp_nb_path = os.path.join(notebook_dir, 'temp_simulation.ipynb')
            
            # Verificamos si existe el notebook base. Si no, ejecutamos convertir_ork.ps1 para generarlo.
            if not os.path.exists(notebook_path):
                self.progress.emit("NOTEBOOK BASE NO ENCONTRADO. GENERANDO DESDE .ORK...")
                # Copiar ORK a disenos/cohete.ork
                dest_ork = os.path.join(root_dir, 'disenos', 'cohete.ork')
                if os.path.abspath(self.ork_path) != os.path.abspath(dest_ork):
                    os.makedirs(os.path.dirname(dest_ork), exist_ok=True)
                    shutil.copy2(self.ork_path, dest_ork)
                
                ps1_path = os.path.join(root_dir, 'scripts', 'convertir_ork.ps1')
                subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps1_path], cwd=root_dir, check=True)
            
            if not os.path.exists(notebook_path):
                raise FileNotFoundError(f"No se pudo encontrar ni generar {notebook_path}")

            self.progress.emit("INYECTANDO PARÁMETROS GEOGRÁFICOS Y ATMOSFÉRICOS...")
            
            # Crear copia en memoria del notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = json.load(f)
                
            # Celda de inyección (Bypass de Lat/Lon y OpenMeteo)
            lat_str = str(self.lat) if self.lat is not None else "None"
            lon_str = str(self.lon) if self.lon is not None else "None"
            elev_str = str(self.elev) if self.elev is not None else "None"
            
            injection_code = [
                "# --- INYECCIÓN DINÁMICA DE LA GUI (NO ALTERA EL SCRIPT ORIGINAL) ---\n",
                f"LATITUD = {lat_str}\n",
                f"LONGITUD = {lon_str}\n",
                f"ELEVACION = {elev_str}\n",
            ]
            
            if self.use_standard_atmosphere:
                injection_code.extend([
                    "print('[GUI] Modo Atmósfera Estándar activado (Mantiene condiciones del .ork).')\n"
                ])
                # Buscar la celda de entorno y comentar sus coordenadas hardcodeadas
                for cell in nb['cells']:
                    if cell['cell_type'] == 'code' and any('env.set_atmospheric_model' in line for line in cell.get('source', [])):
                        new_source = []
                        for line in cell.get('source', []):
                            if line.startswith('LATITUD =') or line.startswith('LONGITUD =') or line.startswith('ELEVACION ='):
                                new_source.append('# GUI OVERRIDE: ' + line)
                            else:
                                new_source.append(line)
                        cell['source'] = new_source
                        break
            else:
                injection_code.extend([
                    "print('[GUI] Clima Dinámico OpenMeteo activado.')\n"
                ])
                # Buscar y reemplazar la celda de entorno en el notebook para inyectar OpenMeteo
                for cell in nb['cells']:
                    if cell['cell_type'] == 'code' and any('env.set_atmospheric_model' in line for line in cell.get('source', [])):
                        cell['source'] = [
                            "from rocketpy import Environment\n",
                            "import requests\n",
                            "import datetime\n",
                            "import math\n",
                            "env = Environment()\n",
                            "env.set_location(LATITUD, LONGITUD)\n",
                            "env.set_elevation(ELEVACION)\n",
                            "try:\n",
                            "    print(f'[GUI] Descargando clima de Open-Meteo para Lat: {LATITUD}, Lon: {LONGITUD}...')\n",
                            "    url = f'https://api.open-meteo.com/v1/forecast?latitude={LATITUD}&longitude={LONGITUD}&current_weather=true&windspeed_unit=ms'\n",
                            "    resp = requests.get(url, timeout=10)\n",
                            "    resp.raise_for_status()\n",
                            "    data = resp.json()['current_weather']\n",
                            "    wind_speed = data['windspeed']\n",
                            "    wind_dir_deg = data['winddirection']\n",
                            "    temp_c = data['temperature']\n",
                            "    wind_dir_rad = math.radians(wind_dir_deg)\n",
                            "    wind_u = -wind_speed * math.sin(wind_dir_rad)\n",
                            "    wind_v = -wind_speed * math.cos(wind_dir_rad)\n",
                            "    env.set_atmospheric_model(\n",
                            "        type='custom_atmosphere',\n",
                            "        wind_u=wind_u,\n",
                            "        wind_v=wind_v,\n",
                            "        temperature=temp_c + 273.15\n",
                            "    )\n",
                            "    print(f'[OK] Open-Meteo: Temp={temp_c}°C, Viento={wind_speed} m/s @ {wind_dir_deg}°')\n",
                            "except Exception as e:\n",
                            "    print(f'[ADVERTENCIA] Falló Open-Meteo. Usando ISA. Error: {e}')\n",
                            "    env.set_atmospheric_model(type='standard_atmosphere')\n",
                            "\n",
                            "env.all_info()\n"
                        ]
                        break
                
            injection_cell = {
                "id": "gui_dynamic_injection_cell",
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": injection_code
            }
            
            # Insertar como segunda celda
            nb['cells'].insert(1, injection_cell)
            
            # Guardar notebook temporal
            with open(temp_nb_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, ensure_ascii=False, indent=1)
                
            self.progress.emit("EJECUTANDO SIMULACIÓN HEADLESS (ESTO PUEDE TARDAR UNOS MINUTOS)...")
            
            # Ejecutar nbconvert
            # Cuando corre como .exe (PyInstaller), sys.executable ES el Python embebido.
            # Esto evita usar rutas hardcodeadas de la máquina de desarrollo.
            if getattr(sys, 'frozen', False):
                python_exe = sys.executable
            else:
                venv_python = os.path.join(root_dir, '.venv', 'Scripts', 'python.exe')
                python_exe = venv_python if os.path.exists(venv_python) else sys.executable
                
            cmd = [
                python_exe, "-m", "jupyter", "nbconvert",
                "--to", "html",
                "--execute",
                "--ExecutePreprocessor.timeout=600",
                "--ExecutePreprocessor.kernel_name=python3",
                temp_nb_path
            ]
            
            result = subprocess.run(cmd, cwd=notebook_dir, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Error en nbconvert:\n{result.stderr}")
                
            html_path = os.path.join(notebook_dir, 'temp_simulation.html')
            kml_path = os.path.join(root_dir, 'resultados', 'trayectoria_operativa.kml')
            
            self.progress.emit("¡SIMULACIÓN COMPLETADA CON ÉXITO!")
            self.finished.emit(html_path, kml_path)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Limpiar notebook temporal si existe
            if os.path.exists(temp_nb_path):
                try:
                    os.remove(temp_nb_path)
                except:
                    pass

# --- MODELO ---
class RocketModel:
    def __init__(self):
        self.ork_path = None
        self.latitude = None
        self.longitude = None
        self.elevation = None
        
    def load_ork(self, filepath):
        try:
            with zipfile.ZipFile(filepath, 'r') as z:
                xml_content = z.read('rocket.ork').decode('utf-8')
            root = ET.fromstring(xml_content)
            
            sim = root.find('.//simulation')
            if sim is not None:
                conditions = sim.find('.//conditions')
                if conditions is not None:
                    try:
                        self.latitude = float(conditions.find('launchlatitude').text)
                    except: self.latitude = 0.0
                    
                    try:
                        self.longitude = float(conditions.find('launchlongitude').text)
                    except: self.longitude = 0.0
                    
                    try:
                        self.elevation = float(conditions.find('launchaltitude').text)
                    except: self.elevation = 0.0
                    
                    self.ork_path = filepath
                    return True
            raise ValueError("No se encontraron condiciones de simulación en el archivo ORK.")
        except Exception as e:
            raise Exception(f"Error parseando archivo ORK: {e}")

# --- VISTA / CONTROLADOR ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = RocketModel()
        self.current_kml_path = None
        self.current_html_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Urutaú III - Panel de Control de Simulación")
        self.setGeometry(100, 100, 1200, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Panel Superior (Controles) ---
        control_panel = QFrame()
        control_panel.setObjectName("controlPanel")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(20)
        
        self.btn_load_ork = QPushButton("Subir ORK")
        self.btn_load_ork.setCursor(Qt.PointingHandCursor)
        self.btn_load_ork.clicked.connect(self.action_load_ork)
        control_layout.addWidget(self.btn_load_ork)
        
        self.lbl_ork_status = QLabel("Ningún archivo .ork cargado")
        self.lbl_ork_status.setObjectName("statusLabel")
        self.lbl_ork_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        control_layout.addWidget(self.lbl_ork_status)
        
        self.chk_standard_atm = QCheckBox("Condiciones climaticas del ORK")
        self.chk_standard_atm.setCursor(Qt.PointingHandCursor)
        self.chk_standard_atm.setToolTip("Omite clima en tiempo real y usa parámetros estándar.")
        control_layout.addWidget(self.chk_standard_atm)
        
        self.chk_dark_mode = QCheckBox("Modo Oscuro")
        self.chk_dark_mode.setCursor(Qt.PointingHandCursor)
        self.chk_dark_mode.toggled.connect(self.action_toggle_dark_mode)
        control_layout.addWidget(self.chk_dark_mode)
        
        self.btn_start = QPushButton("INICIAR SIMULACIÓN")
        self.btn_start.setObjectName("startBtn")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.action_start_simulation)
        control_layout.addWidget(self.btn_start)

        main_layout.addWidget(control_panel)

        # --- Panel de Estado ---
        self.lbl_progress = QLabel("SISTEMA EN ESPERA")
        self.lbl_progress.setObjectName("progressLabel")
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_progress)

        # --- Visor Web Nativo (QWebEngineView) ---
        web_container = QFrame()
        web_container.setObjectName("webContainer")
        web_layout = QVBoxLayout(web_container)
        web_layout.setContentsMargins(0, 0, 0, 0)
        
        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
            # Forzar fondo transparente/oscuro en el visor si el HTML lo soporta
            self.web_view.page().setBackgroundColor(Qt.transparent)
            self.web_view.loadFinished.connect(self.apply_theme_to_webview)
            web_layout.addWidget(self.web_view)
        else:
            self.web_view = QLabel("QWebEngineView no está disponible.\nInstale PyQtWebEngine para ver los gráficos interactivos.")
            self.web_view.setObjectName("webPlaceholder")
            self.web_view.setAlignment(Qt.AlignCenter)
            web_layout.addWidget(self.web_view)
            
        main_layout.addWidget(web_container, stretch=1)

        # --- Panel Inferior (Exportación) ---
        export_panel = QFrame()
        export_panel.setObjectName("exportPanel")
        export_layout = QHBoxLayout(export_panel)
        export_layout.setContentsMargins(15, 15, 15, 15)
        export_layout.setSpacing(20)
        
        export_layout.addStretch() # Empujar botones a la derecha
        
        self.btn_export_pdf = QPushButton("Exportar Reporte a PDF")
        self.btn_export_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_export_pdf.setEnabled(False)
        self.btn_export_pdf.clicked.connect(self.action_export_pdf)
        export_layout.addWidget(self.btn_export_pdf)
        
        self.btn_export_kml = QPushButton("Guardar KML de Google Earth")
        self.btn_export_kml.setCursor(Qt.PointingHandCursor)
        self.btn_export_kml.setEnabled(False)
        self.btn_export_kml.clicked.connect(self.action_export_kml)
        export_layout.addWidget(self.btn_export_kml)
        
        main_layout.addWidget(export_panel)

    def action_load_ork(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ORK", "", "OpenRocket Files (*.ork)")
        if filepath:
            try:
                self.model.load_ork(filepath)
                self.lbl_ork_status.setText(f"Cargado: {os.path.basename(filepath)} | Lat: {self.model.latitude:.4f}, Lon: {self.model.longitude:.4f}")
                self.lbl_ork_status.setStyleSheet("color: #007aff; font-weight: 600; border-color: #007aff;")
                self.btn_start.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                self.lbl_ork_status.setText("Error al cargar ORK")
                self.lbl_ork_status.setStyleSheet("color: #ff3b30; border-color: #ff3b30;")
                self.btn_start.setEnabled(False)

    def action_start_simulation(self):
        if not self.model.ork_path:
            return
            
        self.btn_start.setEnabled(False)
        self.btn_load_ork.setEnabled(False)
        self.chk_standard_atm.setEnabled(False)
        self.btn_export_pdf.setEnabled(False)
        self.btn_export_kml.setEnabled(False)
        
        use_std_atm = self.chk_standard_atm.isChecked()
        use_dark_mode = self.chk_dark_mode.isChecked()
        
        self.worker = SimulationWorker(
            self.model.ork_path,
            self.model.latitude,
            self.model.longitude,
            self.model.elevation,
            use_std_atm,
            use_dark_mode
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.simulation_finished)
        self.worker.error.connect(self.simulation_error)
        self.worker.start()

    def action_toggle_dark_mode(self, checked):
        if checked:
            QApplication.instance().setStyleSheet(QSS_DARK)
        else:
            QApplication.instance().setStyleSheet(QSS_LIGHT)
        self.apply_theme_to_webview()

    def apply_theme_to_webview(self):
        if not HAS_WEBENGINE or not hasattr(self, 'web_view') or not self.web_view.url().isValid():
            return
            
        checked = self.chk_dark_mode.isChecked()
        if checked:
            js = """
            var style = document.getElementById('dynamic-dark-mode');
            if (!style) {
                style = document.createElement('style');
                style.id = 'dynamic-dark-mode';
                style.innerHTML = `
                    body, .jp-Notebook { background-color: #000000 !important; color: #f5f5f7 !important; padding: 20px !important; }
                    .jp-Cell { background-color: #1c1c1e !important; border-radius: 12px !important; margin-bottom: 16px !important; padding: 16px !important; border: 1px solid #2c2c2e !important; box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important; }
                    .jp-RenderedHTMLCommon, .jp-RenderedText, .jp-OutputArea-output, .jp-Cell-outputWrapper { background-color: transparent !important; color: #f5f5f7 !important; }
                    .jp-RenderedText pre { color: #f5f5f7 !important; }
                    .jp-InputArea-editor, .jp-CodeMirrorEditor, .cm-editor, .cm-s-jupyter, .highlight, .highlight pre, .jp-InputArea { background-color: #2c2c2e !important; color: #f5f5f7 !important; border: none !important; border-radius: 8px !important; }
                    .jp-OutputPrompt, .jp-InputPrompt { color: #0a84ff !important; font-weight: bold !important; }
                    table.dataframe, table.dataframe th, table.dataframe td { border: 1px solid #48484a !important; color: #f5f5f7 !important; background-color: #1c1c1e !important; }
                    .jp-RenderedHTMLCommon tbody tr:nth-child(even) { background: #2c2c2e !important; }
                    .jp-RenderedHTMLCommon tbody tr:nth-child(odd) { background: #1c1c1e !important; }
                    
                    /* Pygments Syntax Highlighting for Dark Mode */
                    .highlight .c, .highlight .c1, .highlight .cm { color: #8e8e93 !important; font-style: italic; }
                    .highlight .k, .highlight .kn, .highlight .ow { color: #ff375f !important; font-weight: bold; }
                    .highlight .n, .highlight .nn, .highlight .nc { color: #f5f5f7 !important; }
                    .highlight .s, .highlight .s1, .highlight .s2 { color: #32d74b !important; }
                    .highlight .p { color: #f5f5f7 !important; }
                    .highlight .mf, .highlight .mi, .highlight .mb { color: #ff9f0a !important; }
                    .highlight .nb, .highlight .bp { color: #64d2ff !important; }
                    .highlight .o { color: #ff2d55 !important; }
                    .highlight .fm, .highlight .nf { color: #0a84ff !important; }
                `;
                document.head.appendChild(style);
            }
            """
        else:
            js = """
            var style = document.getElementById('dynamic-dark-mode');
            if (style) {
                style.remove();
            }
            """
        self.web_view.page().runJavaScript(js)

    def update_progress(self, msg):
        self.lbl_progress.setText(msg)

    def simulation_finished(self, html_path, kml_path):
        self.lbl_progress.setText("SIMULACIÓN FINALIZADA. RENDERIZANDO REPORTE...")
        self.lbl_progress.setStyleSheet("color: #34c759;") # Verde exito
        self.current_html_path = html_path
        self.current_kml_path = kml_path
        
        # Cargar HTML nativamente si tenemos WebEngine
        if HAS_WEBENGINE and os.path.exists(html_path):
            file_url = f"file:///{os.path.abspath(html_path).replace(chr(92), '/')}"
            self.web_view.load(QUrl(file_url))
            self.btn_export_pdf.setEnabled(True)
        elif not HAS_WEBENGINE:
            self.lbl_progress.setText("SIMULACIÓN FINALIZADA. (WebEngine no disponible)")
            self.web_view.setText(f"Reporte generado en:\n{html_path}")
        
        self.btn_export_kml.setEnabled(os.path.exists(kml_path))
        
        self.btn_start.setEnabled(True)
        self.btn_load_ork.setEnabled(True)
        self.chk_standard_atm.setEnabled(True)

    def simulation_error(self, error_msg):
        self.lbl_progress.setText("ERROR EN SIMULACIÓN")
        self.lbl_progress.setStyleSheet("color: #ff3b30;")
        QMessageBox.critical(self, "Error de Simulación", error_msg)
        self.btn_start.setEnabled(True)
        self.btn_load_ork.setEnabled(True)
        self.chk_standard_atm.setEnabled(True)

    def action_export_pdf(self):
        if not self.current_html_path or not HAS_WEBENGINE:
            return
        dest_path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "reporte_simulacion.pdf", "PDF Files (*.pdf)")
        if dest_path:
            # QWebEngineView nativo printToPdf
            self.web_view.page().printToPdf(dest_path)
            self.lbl_progress.setText(f"PDF EXPORTADO A: {dest_path}")
            self.lbl_progress.setStyleSheet("color: #007aff;")

    def action_export_kml(self):
        if not self.current_kml_path or not os.path.exists(self.current_kml_path):
            QMessageBox.warning(self, "Error", "El archivo KML no fue generado por el backend.")
            return
            
        dest_path, _ = QFileDialog.getSaveFileName(self, "Guardar KML", "trayectoria_operativa.kml", "KML Files (*.kml)")
        if dest_path:
            try:
                shutil.copy2(self.current_kml_path, dest_path)
                self.lbl_progress.setText(f"KML GUARDADO EN: {dest_path}")
                self.lbl_progress.setStyleSheet("color: #007aff;")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo copiar el archivo KML:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS_LIGHT)  # Iniciar en modo claro
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
