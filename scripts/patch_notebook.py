"""
Patcher del notebook simulation.ipynb:
Reemplaza las celdas críticas con las versiones corregidas.

El bug del rocketserializer colocaba las aletas en 0.179m desde la nariz
en lugar de los correctos 1.759m (posición del leading edge calculada
directamente del .ork).

Ejecutar este script desde la raíz del proyecto CCTE.
"""
import json
import zipfile
import xml.etree.ElementTree as ET
import sys

NOTEBOOK_PATH = 'notebooks/simulacion_cohete.ipynb/simulation.ipynb'
ORK_PATH = 'disenos/cohete.ork'

# ---- Calcular posición correcta de aletas desde el .ork ----
def get_correct_fin_position(ork_path):
    with zipfile.ZipFile(ork_path) as z:
        root = ET.fromstring(z.read('rocket.ork').decode('utf-8'))
    
    stage_sc = root.find('rocket').find('subcomponents').find('stage').find('subcomponents')
    nc_len = float(stage_sc.find('nosecone').find('length').text)
    bt_len = float(stage_sc.find('bodytube').find('length').text)
    BT_END = nc_len + bt_len  # 2.1m
    
    fins_el = stage_sc.find('bodytube').find('subcomponents').find('trapezoidfinset')
    pos_el = fins_el.find('position')
    pos_val = float(pos_el.text)     # -0.121
    root_chord = float(fins_el.find('rootchord').text)  # 0.22m
    
    fin_trailing = BT_END + pos_val        # 1.979m
    fin_leading = fin_trailing - root_chord  # 1.759m
    return fin_leading

FIN_POS_CORRECTED = get_correct_fin_position(ORK_PATH)
print(f"Posición correcta de aletas: {FIN_POS_CORRECTED:.4f}m desde la nariz")
print(f"Posición del serializer: 0.179m (ERROR: {FIN_POS_CORRECTED - 0.179:.4f}m de diferencia)")

# ---- Cargar notebook ----
with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# ---- Definir celdas de reemplazo ----

# Celda de DIAGNÓSTICO (insertar como primera celda de código después de imports)
DIAG_CELL_SOURCE = [
    "# ============================================================\n",
    "# CORRECCIÓN APLICADA: Bug de posición de aletas del rocketserializer\n",
    "# ============================================================\n",
    "# El rocketserializer colocó las aletas en 0.179m desde la nariz (INCORRECTO)\n",
    "# El valor correcto calculado del .ork es 1.759m (leading edge del root chord)\n",
    "# Este error causaba: CP ≈ CG ≈ nariz → estabilidad = -10.2c → cohete incontrolable\n",
    "# ============================================================\n",
    "\n",
    "import zipfile\n",
    "import xml.etree.ElementTree as ET\n",
    "import os\n",
    "\n",
    "# Calcular posición correcta de aletas directamente del .ork\n",
    "_ork_path = os.path.join('..', '..', 'disenos', 'cohete.ork')\n",
    "with zipfile.ZipFile(_ork_path) as _z:\n",
    "    _root = ET.fromstring(_z.read('rocket.ork').decode('utf-8'))\n",
    "\n",
    "_stage_sc = _root.find('rocket').find('subcomponents').find('stage').find('subcomponents')\n",
    "_nc_len = float(_stage_sc.find('nosecone').find('length').text)   # 0.3m\n",
    "_bt_len = float(_stage_sc.find('bodytube').find('length').text)   # 1.8m\n",
    "_BT_END = _nc_len + _bt_len                                        # 2.1m\n",
    "\n",
    "_fins_el = _stage_sc.find('bodytube').find('subcomponents').find('trapezoidfinset')\n",
    "_pos_el = _fins_el.find('position')\n",
    "_pos_val = float(_pos_el.text)                                     # -0.121\n",
    "_root_chord = float(_fins_el.find('rootchord').text)               # 0.22m\n",
    "\n",
    "# OR type='bottom': trailing_edge = BT_END + pos_val → leading_edge = trailing - root_chord\n",
    "_fin_trailing = _BT_END + _pos_val                                 # 1.979m\n",
    "FIN_POSITION_CORRECTED = _fin_trailing - _root_chord               # 1.759m\n",
    "\n",
    "print(f'[CORRECCIÓN] Posición real de aletas (del .ork): {FIN_POSITION_CORRECTED:.4f}m')\n",
    "print(f'             (serializer usaba 0.179m — error de {FIN_POSITION_CORRECTED - 0.179:.4f}m)')\n",
    "print(f'             Body Tube: {_nc_len:.3f}m → {_BT_END:.3f}m')\n",
    "print(f'             Fins TE: {_fin_trailing:.4f}m | Fins LE: {FIN_POSITION_CORRECTED:.4f}m')\n",
]

# Celda de MOTOR corregida (con dry_mass real del M1613-P)
MOTOR_CELL_SOURCE = [
    "motor = SolidMotor(\n",
    "    thrust_source='thrust_source.csv',\n",
    "    # CORRECCIÓN: dry_mass real del M1613-P (serializer usaba 0, incorrecto)\n",
    "    dry_mass=4.0,\n",
    "    dry_inertia=[0.5, 0.5, 0.05],\n",
    "    center_of_dry_mass_position=0,\n",
    "    grains_center_of_mass_position=0,\n",
    "    grain_number=1,\n",
    "    grain_density=1292.6590331104403,\n",
    "    grain_outer_radius=0.0508,\n",
    "    grain_initial_inner_radius=0.0254,\n",
    "    grain_initial_height=0.65,\n",
    "    grain_separation=0,\n",
    "    nozzle_radius=0.038099999999999995,\n",
    "    nozzle_position=-0.325,\n",
    "    throat_radius=0.0254,\n",
    "    reshape_thrust_curve=False,\n",
    "    interpolation_method='linear',\n",
    "    coordinate_system_orientation='nozzle_to_combustion_chamber',\n",
    ")\n",
]

# Celda de ALETAS corregida
FINS_CELL_SOURCE = [
    "# ================================================================\n",
    "# CORRECCIÓN CRÍTICA: Aletas con posición calculada del .ork\n",
    "# Bug original: serializer usaba 0.179m (relativo al BT, no absoluto)\n",
    "# Corrección:   usar FIN_POSITION_CORRECTED = 1.759m (calculado arriba)\n",
    "# ================================================================\n",
    "trapezoidal_fins = {}\n",
    "trapezoidal_fins[0] = TrapezoidalFins(\n",
    "    n=4,\n",
    "    root_chord=0.22,\n",
    "    tip_chord=0.12,\n",
    "    span=0.12,\n",
    "    cant_angle=0.0,\n",
    "    sweep_length=0.2078460969082652,\n",
    "    sweep_angle=None,\n",
    "    rocket_radius=0.054,\n",
    "    name='Trapezoidal Fin Set',\n",
    ")\n",
    "print(f'[OK] Aletas creadas, se posicionarán en {FIN_POSITION_CORRECTED:.4f}m desde la nariz')\n",
]

# Celda de ADD_SURFACES corregida (LA MÁS CRÍTICA)
ADD_SURFACES_CELL_SOURCE = [
    "# ================================================================\n",
    "# CRÍTICO: Posición de aletas CORREGIDA (del .ork, no del serializer)\n",
    "# ================================================================\n",
    "# Body Tube: 0.3m → 2.1m | Fin TE: 1.979m | Fin LE: 1.759m\n",
    "# La posición que RocketPy necesita = leading edge del root chord\n",
    "# ================================================================\n",
    "rocket.add_surfaces(\n",
    "    surfaces=[nosecone, trapezoidal_fins[0]],\n",
    "    positions=[\n",
    "        0.0,                    # Nosecone: punta de nariz\n",
    "        FIN_POSITION_CORRECTED  # Aletas: 1.759m (CORRECTO) vs 0.179m (INCORRECTO)\n",
    "    ]\n",
    ")\n",
    "\n",
    "print(f'[OK] Superficies aerodinámicas agregadas:')\n",
    "print(f'     Nosecone en 0.000m (punta de nariz)')\n",
    "print(f'     Aletas en {FIN_POSITION_CORRECTED:.4f}m (leading edge del root chord)')\n",
]

# ---- Reemplazar celdas en el notebook ----
cells_modified = 0

for i, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    
    # Identificar celda de motor (celda 5 en el notebook original)
    if 'SolidMotor(' in src and 'thrust_source' in src and 'dry_mass=0' in src:
        print(f"[PATCH] Celda {i}: Motor (dry_mass=0 → 4.0)")
        cell['source'] = MOTOR_CELL_SOURCE
        cell['outputs'] = []
        cell['execution_count'] = None
        cells_modified += 1
    
    # Identificar celda de aletas
    elif 'TrapezoidalFins(' in src and ('position' not in src or '0.179' in src or 'sweep_length' in src):
        if 'trapezoidal_fins[0] = TrapezoidalFins(' in src:
            print(f"[PATCH] Celda {i}: Aletas trapezoidales (con corrección de FIN_POSITION_CORRECTED)")
            cell['source'] = FINS_CELL_SOURCE
            cell['outputs'] = []
            cell['execution_count'] = None
            cells_modified += 1
    
    # Identificar celda de add_surfaces
    elif 'add_surfaces' in src and 'nosecone' in src:
        print(f"[PATCH] Celda {i}: add_surfaces (posición corregida)")
        cell['source'] = ADD_SURFACES_CELL_SOURCE
        cell['outputs'] = []
        cell['execution_count'] = None
        cells_modified += 1

print(f"\n[PATCH] {cells_modified} celdas modificadas")

# Insertar celda de diagnóstico después de la celda de imports
for i, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    if 'from rocketpy import' in src and 'import datetime' in src:
        diag_cell = {
            "cell_type": "code",
            "execution_count": None,
            "id": "ccte_fix_diagnosis",
            "metadata": {},
            "outputs": [],
            "source": DIAG_CELL_SOURCE
        }
        nb['cells'].insert(i + 1, diag_cell)
        print(f"[PATCH] Celda de diagnóstico insertada después de celda {i} (imports)")
        break

# ---- Guardar notebook ----
with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\n[OK] Notebook guardado en: {NOTEBOOK_PATH}")
print("\nPara verificar la corrección, ejecuta el notebook y comprueba que:")
print(f"  FIN_POSITION_CORRECTED = {FIN_POS_CORRECTED:.4f}m")
print("  El margen de estabilidad inicial debe ser ~1.96c (como en OpenRocket)")
