"""
=============================================================================
CCTE - Rocket U2: Parser Corregido de OpenRocket -> RocketPy
=============================================================================
Este script corrige el bug crítico de traducción geométrica del rocketserializer.

PROBLEMA IDENTIFICADO:
El rocketserializer leyó la posición de las aletas como 0.179m desde la nariz,
cuando el valor correcto es ~1.979m. Esto pone las aletas virtualmente EN LA NARIZ,
causando margen de estabilidad = -10.2c.

CAUSA RAÍZ:
- OR almacena la posición de las aletas como type='bottom', value=-0.121
  (es decir, el borde trasero de la aleta está a 0.121m del fondo del Body Tube)
- El serializer no convirtió correctamente las coordenadas:
  Posición absoluta correcta = BT_END + pos_val - root_chord
  = 2.1 + (-0.121) - 0.22 = 1.759m (leading edge)
  ó simplemente: BT_END + pos_val = 1.979m (trailing edge)

ESTE SCRIPT:
Lee directamente el .ork, calcula todas las posiciones absolutas correctas,
e instancia RocketPy con los datos geométricos reales.
=============================================================================
"""
import zipfile
import xml.etree.ElementTree as ET
import numpy as np


ORK_FILE_PATH = "disenos/cohete.ork"


# =============================================================================
# SECCIÓN 1: PARSER DEL ARCHIVO .ORK
# =============================================================================

def parse_ork(ork_path):
    """
    Lee el archivo .ork (ZIP que contiene rocket.ork) y extrae todos los
    parámetros geométricos y de masa con posiciones absolutas correctas.
    
    Returns:
        dict con todos los parámetros del cohete listos para RocketPy
    """
    with zipfile.ZipFile(ork_path) as z:
        with z.open('rocket.ork') as f:
            content = f.read().decode('utf-8')
    
    root = ET.fromstring(content)
    rocket_elem = root.find('rocket')
    
    # ---- Obtener configuración de motor activa ----
    active_config = None
    for mc in rocket_elem.findall('motorconfiguration'):
        if mc.get('default') == 'true':
            active_config = mc.get('configid')
            break
    if active_config is None:
        # Tomar primera configuración
        mc = rocket_elem.find('motorconfiguration')
        if mc is not None:
            active_config = mc.get('configid')
    
    print(f"[ORK Parser] Configuración de motor activa: {active_config}")
    
    # ---- Obtener stage principal ----
    stage_sc = rocket_elem.find('subcomponents')
    if stage_sc is None:
        raise ValueError("No se encontraron subcomponentes en el cohete")
    
    stage = stage_sc.find('stage')
    if stage is None:
        raise ValueError("No se encontró stage")
    
    stage_sc2 = stage.find('subcomponents')
    if stage_sc2 is None:
        raise ValueError("Stage sin subcomponentes")
    
    # ---- Encontrar Nosecone y Body Tube (hermanos secuenciales) ----
    nosecone = None
    bodytube = None
    nosecone_abs = {}  # {start, end}
    bodytube_abs = {}  # {start, end}
    cumulative_pos = 0.0  # posición acumulada para componentes sin posición explícita
    
    for comp in stage_sc2:
        if comp.tag == 'nosecone' and nosecone is None:
            nosecone = comp
            nc_length = float(_get_text(comp, 'length', '0'))
            nosecone_abs['start'] = 0.0
            nosecone_abs['end'] = nc_length
            cumulative_pos = nc_length
        elif comp.tag == 'bodytube' and bodytube is None:
            bodytube = comp
            bt_length = float(_get_text(comp, 'length', '0'))
            bodytube_abs['start'] = cumulative_pos
            bodytube_abs['end'] = cumulative_pos + bt_length
            cumulative_pos += bt_length
    
    if nosecone is None:
        raise ValueError("No se encontró nosecone")
    if bodytube is None:
        raise ValueError("No se encontró body tube")
    
    NC_START = nosecone_abs['start']
    NC_END = nosecone_abs['end']
    NC_LEN = NC_END - NC_START
    
    BT_START = bodytube_abs['start']
    BT_END = bodytube_abs['end']
    BT_LEN = BT_END - BT_START
    
    print(f"[ORK Parser] Nosecone: {NC_START:.4f}m → {NC_END:.4f}m (longitud={NC_LEN:.4f}m)")
    print(f"[ORK Parser] Body Tube: {BT_START:.4f}m → {BT_END:.4f}m (longitud={BT_LEN:.4f}m)")
    
    # ---- Parámetros del nosecone ----
    nc_shape = _get_text(nosecone, 'shape', 'ogive')
    nc_shape_param = float(_get_text(nosecone, 'shapeparameter', '0'))
    # Convertir forma OR -> RocketPy
    shape_map = {
        'ogive': 'ogive',
        'conical': 'conical',
        'ellipsoid': 'ellipsoid',
        'power': 'power',
        'parabolic': 'parabolic',
        'haack': 'lvhaack',  # LD-Haack = LV-Haack en RocketPy
    }
    nc_kind = shape_map.get(nc_shape.lower(), 'ogive')
    
    # Radio del nosecone (base) = radio del body tube
    bt_radius_el = bodytube.find('radius')
    if bt_radius_el is not None and bt_radius_el.text != 'auto':
        bt_radius = float(bt_radius_el.text)
    else:
        bt_radius = 0.054  # fallback
    
    print(f"[ORK Parser] Nosecone: shape={nc_shape}→{nc_kind}, shape_param={nc_shape_param}")
    print(f"[ORK Parser] Radio body tube: {bt_radius}m")
    
    # ---- Procesar subcomponentes del Body Tube ----
    fins_data = None
    mass_components = []
    motor_data = None
    parachutes = []
    
    bt_sc = bodytube.find('subcomponents')
    if bt_sc is not None:
        for comp in bt_sc:
            tag = comp.tag
            name = _get_text(comp, 'name', tag)
            pos_val, pos_type = _get_position(comp)
            length = float(_get_text(comp, 'length', '0'))
            
            # Calcular posición absoluta dentro del Body Tube
            abs_start, abs_end = _compute_abs_pos(pos_val, pos_type, length, BT_START, BT_END)
            
            # Obtener masa override si existe
            override_mass = _get_float(comp, 'overridemass')
            
            if tag == 'trapezoidfinset':
                # Para aletas: abs_end es el borde trasero del root chord
                # abs_start calculado asumiendo que length=root_chord no está en el XML
                # En OR, las aletas no tienen 'length' - su posición es del borde trailing
                root_chord = _get_float(comp, 'rootchord', 0.0)
                tip_chord = _get_float(comp, 'tipchord', 0.0)
                span = _get_float(comp, 'height', 0.0)
                sweep_length_el = comp.find('sweeplength')
                sweep_length = float(sweep_length_el.text) if sweep_length_el is not None else 0.0
                fin_count = int(_get_text(comp, 'fincount', '4'))
                cant = _get_float(comp, 'cant', 0.0)
                
                # La posición en OR para aletas con type='bottom':
                # abs_end (calculado arriba) = borde trailing del root chord absoluto
                # leading edge = abs_end - root_chord
                fin_trailing_abs = abs_end  # borde aft del root chord
                fin_leading_abs = fin_trailing_abs - root_chord  # borde fore del root chord
                
                fins_data = {
                    'name': name,
                    'n': fin_count,
                    'root_chord': root_chord,
                    'tip_chord': tip_chord,
                    'span': span,
                    'sweep_length': sweep_length,
                    'cant_angle': cant,
                    'rocket_radius': bt_radius,
                    # POSICIÓN CORRECTA: leading edge del root chord desde la punta de la nariz
                    'position_abs': fin_leading_abs,
                    'position_trailing': fin_trailing_abs,
                }
                print(f"[ORK Parser] Aletas '{name}': leading_edge={fin_leading_abs:.4f}m, trailing_edge={fin_trailing_abs:.4f}m de la nariz")
                
            elif tag == 'motor':
                # Motor dentro del motormount (puede estar en bodytube directo)
                pass
            
            elif tag == 'innertube':
                mass_components.append({
                    'name': name,
                    'start': abs_start,
                    'end': abs_end,
                    'cg': (abs_start + abs_end) / 2,
                    'mass': override_mass if override_mass is not None else 0.0,
                    'has_override': override_mass is not None,
                })
                
            elif tag == 'bulkhead':
                mass_components.append({
                    'name': name,
                    'start': abs_start,
                    'end': abs_end,
                    'cg': (abs_start + abs_end) / 2,
                    'mass': override_mass if override_mass is not None else 0.0,
                    'has_override': override_mass is not None,
                })
                
            elif tag == 'parachute':
                cd = _get_float(comp, 'cd', 1.5)
                diameter = _get_float(comp, 'diameter', 0.0)
                deploy_event = _get_text(comp, 'deployevent', 'ejection')
                deploy_altitude = _get_float(comp, 'deployaltitude', None)
                deploy_delay = _get_float(comp, 'deploydelay', 0.0)
                
                area = np.pi * (diameter / 2) ** 2 if diameter > 0 else 0.0
                parachutes.append({
                    'name': name,
                    'cd': cd,
                    'area': area,
                    'cds': cd * area,
                    'deploy_event': deploy_event,
                    'deploy_altitude': deploy_altitude,
                    'deploy_delay': deploy_delay,
                    'mass': override_mass,
                })
    
    # ---- Buscar motor en motormount ----
    motormount = bodytube.find('motormount')
    if motormount is not None:
        for motor_el in motormount.findall('motor'):
            if motor_el.get('configid') == active_config:
                motor_data = _parse_motor(motor_el, BT_START, BT_END)
                break
        if motor_data is None and motormount.findall('motor'):
            # Usar primer motor disponible
            motor_el = motormount.findall('motor')[0]
            motor_data = _parse_motor(motor_el, BT_START, BT_END)
    
    # ---- Obtener datos generales del cohete desde la simulación stored ----
    stored = _get_stored_results(root)
    
    # ---- Parámetros globales del cohete ----
    # El CG sin propelente (from stored results or computed from mass overrides)
    total_rocket_mass = stored.get('dry_mass', 15.232)
    cg_without_motor = stored.get('cg_without_motor', 1.272)
    
    result = {
        'nosecone': {
            'length': NC_LEN,
            'kind': nc_kind,
            'base_radius': bt_radius,
            'rocket_radius': bt_radius,
            'name': _get_text(nosecone, 'name', 'Nose Cone'),
            'position_abs': NC_START,
        },
        'body_tube': {
            'start': BT_START,
            'end': BT_END,
            'length': BT_LEN,
            'radius': bt_radius,
        },
        'fins': fins_data,
        'mass_components': mass_components,
        'motor': motor_data,
        'parachutes': parachutes,
        'rocket_params': {
            'radius': bt_radius,
            'mass': total_rocket_mass,
            'center_of_mass_without_motor': cg_without_motor,
        },
        'stored': stored,
        'total_length': BT_END,
    }
    
    return result


def _get_text(elem, tag, default=None):
    el = elem.find(tag)
    if el is not None and el.text and el.text.strip():
        return el.text.strip()
    return default


def _get_float(elem, tag, default=None):
    t = _get_text(elem, tag)
    if t is not None:
        try:
            return float(t)
        except ValueError:
            pass
    return default


def _get_position(elem):
    """Retorna (valor, tipo) de la posición del componente."""
    pos_el = elem.find('position')
    axial_el = elem.find('axialoffset')
    
    if pos_el is not None and pos_el.text:
        return float(pos_el.text), pos_el.get('type', 'top')
    elif axial_el is not None and axial_el.text:
        return float(axial_el.text), axial_el.get('method', 'top')
    return 0.0, 'top'


def _compute_abs_pos(pos_val, pos_type, length, parent_start, parent_end):
    """
    Convierte posición relativa OR a posición absoluta (desde punta de nariz).
    
    OR position types:
    - 'top': pos_val medido desde el extremo DELANTERO del padre al extremo DELANTERO del componente
    - 'bottom': pos_val medido desde el extremo TRASERO del padre al extremo TRASERO del componente
    - 'absolute': posición absoluta desde la punta de la nariz
    - 'middle': pos_val desde el centro del padre al centro del componente
    """
    if pos_type == 'top':
        abs_start = parent_start + pos_val
        abs_end = abs_start + length
    elif pos_type == 'bottom':
        abs_end = parent_end + pos_val
        abs_start = abs_end - length
    elif pos_type == 'absolute':
        abs_start = pos_val
        abs_end = abs_start + length
    elif pos_type == 'middle':
        parent_center = (parent_start + parent_end) / 2
        abs_start = parent_center + pos_val - length / 2
        abs_end = abs_start + length
    else:
        # Default to top
        abs_start = parent_start + pos_val
        abs_end = abs_start + length
    
    return abs_start, abs_end


def _parse_motor(motor_el, bt_start, bt_end):
    """Extrae datos del motor desde el elemento XML."""
    designation = _get_text(motor_el, 'designation', 'M1613-P')
    length = _get_float(motor_el, 'length', 0.65)
    diameter = _get_float(motor_el, 'diameter', 0.1016)
    
    # Posición del motor en el motormount
    # En OR, el motor generalmente está en el extremo trasero del body tube
    # El overhang es cuánto sobresale el motor por detrás del BT
    overhang = _get_float(motor_el, 'overhang', 0.0)
    
    # Motor position: trailing edge at BT_END - overhang + overhang = BT_END
    # Actually in OR, the motor is flush with or slightly behind the BT
    motor_end = bt_end + overhang if overhang else bt_end
    motor_start = motor_end - length
    
    return {
        'designation': designation,
        'length': length,
        'radius': diameter / 2,
        'start': motor_start,
        'end': motor_end,
        'cg_position': (motor_start + motor_end) / 2,
    }


def _get_stored_results(root):
    """Extrae resultados almacenados en las simulaciones del .ork."""
    results = {}
    
    simulations = root.find('simulations')
    if simulations is None:
        return results
    
    for sim in simulations.findall('simulation'):
        fd = sim.find('flightdata')
        if fd is None:
            continue
        
        # En OR, flightdata contiene databranches con datapoints
        # Los valores de CG, CP etc. están en la primera datapoint
        # Columnas típicas (OR 15.03):
        # time, altitude, velocity, acceleration, stability, cg, cp, mach, ...
        
        dbs = fd.findall('databranch')
        for db in dbs:
            dps = db.findall('datapoint')
            if dps:
                # Obtener nombres de variables del databranch
                # (no siempre disponibles, depende de la versión de OR)
                break
        
        # Buscar flightdata attributes
        # OR stores: maxaltitude, maxvelocity, etc.
        for key, attr in [
            ('max_altitude', 'maxaltitude'),
            ('max_velocity', 'maxvelocity'),
            ('max_acceleration', 'maxacceleration'),
        ]:
            val = fd.get(attr)
            if val:
                results[key] = float(val)
    
    return results


# =============================================================================
# FUNCIÓN PRINCIPAL: Instanciar cohete en RocketPy con datos correctos
# =============================================================================

def build_rocketpy_rocket(ork_path, 
                           thrust_csv_path,
                           drag_csv_path,
                           rocket_mass,
                           rocket_inertia,
                           cg_without_motor,
                           motor_dry_mass,
                           motor_position_rocketpy):
    """
    Instancia el cohete RocketPy con la geometría correctamente parseada del .ork.
    
    Esta función ES EL REEMPLAZO de la secuencia de celdas generada por rocketserializer.
    
    Args:
        ork_path: ruta al archivo .ork
        thrust_csv_path: ruta al CSV de empuje
        drag_csv_path: ruta al CSV de arrastre
        rocket_mass: masa total del cohete sin propelente [kg]
        rocket_inertia: [Ixx, Iyy, Izz] momentos de inercia [kg·m²]
        cg_without_motor: CG sin propelente ni motor desde la nariz [m]
        motor_dry_mass: masa en seco del motor [kg]
        motor_position_rocketpy: posición del motor en RocketPy [m]
    
    Returns:
        tuple: (rocket, motor, params_dict)
    """
    from rocketpy import Rocket, SolidMotor, TrapezoidalFins, NoseCone, Parachute
    
    # --- Parsear el ORK ---
    params = parse_ork(ork_path)
    
    fins = params['fins']
    nc = params['nosecone']
    
    print("\n" + "="*60)
    print("INSTANCIANDO MOTOR")
    print("="*60)
    
    # --- Motor ---
    motor = SolidMotor(
        thrust_source=thrust_csv_path,
        dry_mass=motor_dry_mass,
        dry_inertia=[0.001, 0.001, 0.001],
        center_of_dry_mass_position=0,
        grains_center_of_mass_position=0,
        grain_number=1,
        grain_density=1292.659,
        grain_outer_radius=0.0508,
        grain_initial_inner_radius=0.0254,
        grain_initial_height=0.65,
        grain_separation=0,
        nozzle_radius=0.0381,
        nozzle_position=-0.325,
        throat_radius=0.0254,
        reshape_thrust_curve=False,
        interpolation_method='linear',
        coordinate_system_orientation='nozzle_to_combustion_chamber',
    )
    
    print("\n" + "="*60)
    print("INSTANCIANDO COHETE")
    print("="*60)
    
    # --- Rocket ---
    rocket = Rocket(
        radius=params['body_tube']['radius'],
        mass=rocket_mass,
        inertia=rocket_inertia,
        power_off_drag=drag_csv_path,
        power_on_drag=drag_csv_path,
        center_of_mass_without_motor=cg_without_motor,
        coordinate_system_orientation='nose_to_tail',
    )
    
    print("\n" + "="*60)
    print("AGREGANDO SUPERFICIES AERODINÁMICAS")
    print("="*60)
    
    # --- Nosecone ---
    nosecone_rp = NoseCone(
        length=nc['length'],
        kind=nc['kind'],
        base_radius=nc['base_radius'],
        rocket_radius=nc['rocket_radius'],
        name=nc['name'],
    )
    
    # --- Aletas trapezoidales con POSICIÓN CORREGIDA ---
    if fins is not None:
        fins_rp = TrapezoidalFins(
            n=fins['n'],
            root_chord=fins['root_chord'],
            tip_chord=fins['tip_chord'],
            span=fins['span'],
            cant_angle=fins['cant_angle'],
            sweep_length=fins['sweep_length'],
            sweep_angle=None,
            rocket_radius=fins['rocket_radius'],
            name=fins['name'],
        )
        
        # Posición CORREGIDA del leading edge de las aletas desde la nariz
        fin_pos_corrected = fins['position_abs']
        
        print(f"✓ Aletas: posición leading edge = {fin_pos_corrected:.4f}m desde la nariz")
        print(f"  (El serializer reportaba 0.179m - ERROR de {fin_pos_corrected - 0.179:.4f}m)")
        
        rocket.add_surfaces(
            surfaces=[nosecone_rp, fins_rp],
            positions=[nc['position_abs'], fin_pos_corrected]
        )
    else:
        rocket.add_surfaces(
            surfaces=[nosecone_rp],
            positions=[nc['position_abs']]
        )
    
    # --- Motor ---
    print(f"\n✓ Motor posición en RocketPy: {motor_position_rocketpy:.4f}m desde la nariz")
    rocket.add_motor(motor, position=motor_position_rocketpy)
    
    print("\n" + "="*60)
    print("RESUMEN DE GEOMETRÍA CORREGIDA")
    print("="*60)
    print(f"  Longitud total del cohete: {params['total_length']:.4f}m")
    print(f"  Nosecone: 0.0000m → {nc['length']:.4f}m (forma: {nc['kind']})")
    print(f"  Body Tube: {params['body_tube']['start']:.4f}m → {params['body_tube']['end']:.4f}m")
    if fins:
        print(f"  Aletas: leading edge en {fins['position_abs']:.4f}m, trailing edge en {fins['position_trailing']:.4f}m")
    print(f"  CG sin propelente: {cg_without_motor:.4f}m desde la nariz")
    
    return rocket, motor, params


if __name__ == '__main__':
    # Test del parser
    print("="*60)
    print("TEST: Parsing cohete.ork")
    print("="*60)
    params = parse_ork(ORK_FILE_PATH)
    
    print("\n=== POSICIONES ABSOLUTAS CORRECTAS (desde punta de nariz) ===")
    print(f"Nosecone:")
    nc = params['nosecone']
    print(f"  Posición: {nc['position_abs']:.4f}m → {nc['position_abs'] + nc['length']:.4f}m")
    print(f"  Tipo: {nc['kind']}, Longitud: {nc['length']}m, Radio base: {nc['base_radius']}m")
    
    print(f"\nAletas trapezoidales:")
    fins = params['fins']
    if fins:
        print(f"  Leading edge (borde de ataque): {fins['position_abs']:.4f}m ← POSICIÓN CORRECTA PARA ROCKETPY")
        print(f"  Trailing edge (borde de fuga):  {fins['position_trailing']:.4f}m")
        print(f"  Root chord: {fins['root_chord']}m, Tip chord: {fins['tip_chord']}m")
        print(f"  Span: {fins['span']}m, Sweep: {fins['sweep_length']:.4f}m")
        print(f"  Número de aletas: {fins['n']}")
        print(f"\n  COMPARACIÓN:")
        print(f"  ✗ rocketserializer (INCORRECTO): 0.179m")
        print(f"  ✓ Valor real del .ork:           {fins['position_abs']:.4f}m")
        print(f"  Error: {fins['position_abs'] - 0.179:.4f}m ({(fins['position_abs']/0.179 - 1)*100:.1f}% más lejos de la nariz)")
    
    print(f"\nComponentes de masa:")
    for mc in params['mass_components']:
        status = "OVERRIDE" if mc['has_override'] else "sin override"
        print(f"  {mc['name']}: CG={mc['cg']:.4f}m, masa={mc['mass']}kg [{status}]")
