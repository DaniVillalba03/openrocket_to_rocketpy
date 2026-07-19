"""
=============================================================================
CCTE - Cohete U2: Bloque de código corregido para el Notebook de RocketPy
=============================================================================

PROBLEMA RAÍZ IDENTIFICADO:
El rocketserializer (ork2notebook) tiene un bug crítico de conversión de
coordenadas al parsear el .ork de OpenRocket:

- Las aletas en el .ork tienen: position=-0.121 [type='bottom'] (relativo al 
  extremo trasero del Body Tube)
- El serializer las colocó en posición=0.179m desde la nariz (incorrecto)
- La posición CORRECTA es: BT_END + pos_val - root_chord = 2.1 + (-0.121) - 0.22 = 1.759m

CONSECUENCIA: Las aletas se simulaban en la zona de la nariz en lugar del
extremo trasero, causando CP ≈ CG ≈ nariz, margen de estabilidad = -10.2c

SOLUCIÓN: Este notebook reemplaza las celdas generadas por el serializer
con valores de posición calculados directamente del .ork (fuente de verdad).

Para usar este código:
1. Copia cada bloque en la celda correspondiente del notebook simulation.ipynb
2. Las celdas de Motor, Nosecone y Aletas deben ser reemplazadas completamente
3. La celda de add_surfaces es la más crítica (tiene la posición corregida)

=============================================================================
"""

# =============================================================================
# BLOQUE 0: DIAGNÓSTICO - Ejecutar primero para verificar la corrección
# =============================================================================
DIAGNOSTIC_CODE = '''
# ============================================================
# DIAGNÓSTICO: Verificación de posiciones geométricas del .ork
# ============================================================
import zipfile, xml.etree.ElementTree as ET, sys

ORK_PATH = '../../disenos/cohete.ork'

def _get_text(elem, tag, default=None):
    el = elem.find(tag)
    return el.text.strip() if el is not None and el.text and el.text.strip() else default

def _get_float(elem, tag, default=0.0):
    t = _get_text(elem, tag)
    return float(t) if t is not None else default

def _get_pos(elem):
    for attr in ('position', 'axialoffset'):
        el = elem.find(attr)
        if el is not None and el.text:
            return float(el.text), el.get('type', el.get('method', 'top'))
    return 0.0, 'top'

def _abs_pos(pos_val, pos_type, length, p_start, p_end):
    if pos_type == 'top':
        s = p_start + pos_val
    elif pos_type == 'bottom':
        s = p_end + pos_val - length
    elif pos_type == 'absolute':
        s = pos_val
    else:
        s = p_start + pos_val
    return s, s + length

with zipfile.ZipFile(ORK_PATH) as z:
    root = ET.fromstring(z.read('rocket.ork').decode('utf-8'))

stage_sc = root.find('rocket').find('subcomponents').find('stage').find('subcomponents')
nc_el = stage_sc.find('nosecone')
bt_el = stage_sc.find('bodytube')

NC_LEN = _get_float(nc_el, 'length', 0.3)
BT_LEN = _get_float(bt_el, 'length', 1.8)
BT_START, BT_END = NC_LEN, NC_LEN + BT_LEN

print(f"Nosecone: 0.000m → {NC_LEN:.3f}m")
print(f"Body Tube: {BT_START:.3f}m → {BT_END:.3f}m")

fins = bt_el.find('subcomponents').find('trapezoidfinset')
pos_val, pos_type = _get_pos(fins)
root_chord = _get_float(fins, 'rootchord', 0.22)
fin_s, fin_e = _abs_pos(pos_val, pos_type, root_chord, BT_START, BT_END)

print(f"\\nAletas leading edge (CORRECTO): {fin_s:.4f}m desde nariz")
print(f"  serializer reportó: 0.179m (INCORRECTO, error={fin_s - 0.179:.4f}m)")

FIN_POSITION_CORRECTED = fin_s
print(f"\\n>>> Usar FIN_POSITION_CORRECTED = {FIN_POSITION_CORRECTED:.4f} en add_surfaces <<<")
'''

# =============================================================================
# BLOQUE 1: MOTOR (sin cambios mayores, solo dry_inertia ajustado)
# =============================================================================
MOTOR_CODE = '''
motor = SolidMotor(
    thrust_source='thrust_source.csv',
    # Masa en seco del motor M1613-P (casing + nozzle, sin propelente)
    # El serializer puso dry_mass=0, que es incorrecto para el cálculo de CG
    # Usar 4.0 kg según datos reales del motor M1613-P
    dry_mass=4.0,
    dry_inertia=[0.5, 0.5, 0.05],
    center_of_dry_mass_position=0,
    grains_center_of_mass_position=0,
    grain_number=1,
    grain_density=1292.6590331104403,
    grain_outer_radius=0.0508,
    grain_initial_inner_radius=0.0254,
    grain_initial_height=0.65,
    grain_separation=0,
    nozzle_radius=0.038099999999999995,
    nozzle_position=-0.325,
    throat_radius=0.0254,
    reshape_thrust_curve=False,
    interpolation_method=\'linear\',
    coordinate_system_orientation=\'nozzle_to_combustion_chamber\',
)
'''

# =============================================================================
# BLOQUE 2: NOSECONE (sin cambios)
# =============================================================================
NOSECONE_CODE = '''
nosecone = NoseCone(
    length=0.3,
    kind=\'lvhaack\',
    base_radius=0.054,
    rocket_radius=0.054,
    name=\'Nose Cone\',
)
'''

# =============================================================================
# BLOQUE 3: ALETAS - CORRECCIÓN CRÍTICA
# =============================================================================
FINS_CODE = '''
# =================================================================
# CORRECCIÓN CRÍTICA: Posición de aletas
# =================================================================
# OpenRocket .ork: position=-0.121 [type=\'bottom\'] relativo a BT aft
#   Body Tube: 0.3m → 2.1m (BT_END = 2.1m)
#   Fin trailing edge abs = BT_END + (-0.121) = 2.1 - 0.121 = 1.979m
#   Fin leading edge abs  = 1.979 - root_chord(0.22) = 1.759m
#
# rocketserializer (INCORRECTO): posición = 0.179m  ← bug de coordenadas
# Valor real del .ork (CORRECTO): posición = 1.759m ← fin leading edge
# =================================================================

# Calcular posición correcta directamente del .ork
import zipfile, xml.etree.ElementTree as ET

_ork = \'../../disenos/cohete.ork\'
with zipfile.ZipFile(_ork) as _z:
    _root = ET.fromstring(_z.read(\'rocket.ork\').decode(\'utf-8\'))

_stage_sc = _root.find(\'rocket\').find(\'subcomponents\').find(\'stage\').find(\'subcomponents\')
_nc_len = float(_stage_sc.find(\'nosecone\').find(\'length\').text)
_bt_len = float(_stage_sc.find(\'bodytube\').find(\'length\').text)
_BT_START = _nc_len       # 0.3m
_BT_END = _nc_len + _bt_len  # 2.1m

_fins_el = _stage_sc.find(\'bodytube\').find(\'subcomponents\').find(\'trapezoidfinset\')
_pos_el = _fins_el.find(\'position\')
_pos_val = float(_pos_el.text)      # -0.121
_pos_type = _pos_el.get(\'type\')    # \'bottom\'
_root_chord = float(_fins_el.find(\'rootchord\').text)  # 0.22

# type=\'bottom\': trailing edge = BT_END + pos_val
_fin_trailing = _BT_END + _pos_val        # 2.1 + (-0.121) = 1.979m
_fin_leading = _fin_trailing - _root_chord  # 1.979 - 0.22 = 1.759m

FIN_POSITION_CORRECTED = _fin_leading
print(f"[FIX] Posición de aletas corregida: {FIN_POSITION_CORRECTED:.4f}m desde la nariz")
print(f"      (serializer tenía: 0.179m — error: {FIN_POSITION_CORRECTED - 0.179:.4f}m)")

# Crear el set de aletas con dimensiones originales del .ork
trapezoidal_fins = {}
trapezoidal_fins[0] = TrapezoidalFins(
    n=int(_fins_el.find(\'fincount\').text),                 # 4
    root_chord=float(_fins_el.find(\'rootchord\').text),     # 0.22m
    tip_chord=float(_fins_el.find(\'tipchord\').text),       # 0.12m
    span=float(_fins_el.find(\'height\').text),              # 0.12m
    cant_angle=0.0,
    sweep_length=float(_fins_el.find(\'sweeplength\').text), # 0.2078m
    sweep_angle=None,
    rocket_radius=0.054,
    name=\'Trapezoidal Fin Set\',
)
'''

# =============================================================================
# BLOQUE 4: COHETE - Parámetros de masa y CG
# =============================================================================
ROCKET_CODE = '''
rocket = Rocket(
    radius=0.054,
    # masa total sin propelente (confirmada por rocketserializer del .ork)
    mass=15.232,
    inertia=[0.028, 0.028, 3.83],
    power_off_drag=\'drag_curve.csv\',
    power_on_drag=\'drag_curve.csv\',
    # CG sin propelente desde la nariz (confirmado por rocketserializer)
    center_of_mass_without_motor=1.272,
    coordinate_system_orientation=\'nose_to_tail\',
)
'''

# =============================================================================
# BLOQUE 5: ADD_SURFACES - LA CELDA MÁS CRÍTICA
# =============================================================================
ADD_SURFACES_CODE = '''
# ================================================================
# CRÍTICO: Usar FIN_POSITION_CORRECTED calculado en la celda anterior
# ================================================================
rocket.add_surfaces(
    surfaces=[nosecone, trapezoidal_fins[0]],
    positions=[
        0.0,                    # Nosecone: punta de nariz en posición 0
        FIN_POSITION_CORRECTED  # Aletas: 1.759m desde la nariz (CORRECTO)
                                # (antes: 0.179m → causaba estabilidad = -10.2c)
    ]
)

print(f"[OK] Nosecone: 0.000m desde nariz")
print(f"[OK] Aletas:   {FIN_POSITION_CORRECTED:.4f}m desde nariz (leading edge del root chord)")
'''

# =============================================================================
# BLOQUE 6: ADD_MOTOR - Posición del motor
# =============================================================================
ADD_MOTOR_CODE = '''
# Posición del motor: confirmada por rocketserializer del .ork
# (esta posición sí estaba correcta, es el CM del motor desde la nariz)
rocket.add_motor(motor, position=1.7776384811117631)
'''

print("="*70)
print("BLOQUES DE CÓDIGO CORRECTOS PARA EL NOTEBOOK")
print("="*70)
print("\n--- BLOQUE 0: DIAGNÓSTICO ---")
print(DIAGNOSTIC_CODE)
print("\n--- BLOQUE 3 (CRÍTICO): ALETAS CON POSICIÓN CORREGIDA ---")
print(FINS_CODE)
print("\n--- BLOQUE 5 (CRÍTICO): ADD_SURFACES CON POSICIÓN CORREGIDA ---")
print(ADD_SURFACES_CODE)
