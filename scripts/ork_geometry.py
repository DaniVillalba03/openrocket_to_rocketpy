"""
=============================================================================
ork_geometry.py  —  Parser dinámico de geometría OpenRocket → RocketPy
=============================================================================
Convierte CUALQUIER archivo .ork a posiciones absolutas correctas.

Reglas de transformación implementadas (spec OpenRocket):
──────────────────────────────────────────────────────────
  type="top"      → abs_start = parent_fore + offset
                    abs_end   = abs_start + length

  type="bottom"   → abs_end   = parent_aft + offset
                    abs_start = abs_end − length

  type="middle"   → abs_start = parent_mid + offset − length/2
                    abs_end   = abs_start + length

  type="absolute" → abs_start = offset  (desde la punta de la nariz)
                    abs_end   = abs_start + length

  Sin etiqueta    → hermanos secuenciales: el componente empieza donde
                    termina el anterior dentro del mismo padre.

Para aletas (trapezoidfinset / freeformfinset / ellipticalfinset):
  RocketPy.add_surfaces necesita el LEADING EDGE del root chord.
  abs_leading = abs_trailing − root_chord
  abs_trailing = abs_end  (resultado de la conversión anterior)

Uso como módulo:
  from scripts.ork_geometry import OrkGeometry
  geo = OrkGeometry("disenos/cohete.ork")
  print(geo.fin_sets)          # lista de dicts con 'position_abs'
  print(geo.nosecones)
  print(geo.body_tubes)

Uso como script de diagnóstico:
  python scripts/ork_geometry.py [ruta/al/cohete.ork]
=============================================================================
"""

import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
import sys


# ---------------------------------------------------------------------------
# Tipos de componentes que RocketPy necesita posicionar
# ---------------------------------------------------------------------------
FIN_TAGS = {"trapezoidfinset", "freeformfinset", "ellipticalfinset"}
STRUCTURAL_TAGS = {
    "nosecone", "bodytube", "transition",
    "trapezoidfinset", "freeformfinset", "ellipticalfinset",
    "innertube", "tubecoupler", "engineblock",
    "centeringring", "bulkhead", "launchlug",
    "parachute", "shockcord", "masscomponent",
}


# ---------------------------------------------------------------------------
# Estructuras de datos de resultado
# ---------------------------------------------------------------------------
@dataclass
class ComponentGeometry:
    """Geometría resuelta de un componente con posición absoluta."""
    tag: str
    name: str
    abs_fore: float          # extremo delantero desde punta de nariz [m]
    abs_aft: float           # extremo trasero desde punta de nariz [m]
    length: float            # longitud [m]
    override_mass: Optional[float] = None   # kg si existe <overridemass>
    # Parámetros específicos de aletas
    root_chord: Optional[float] = None
    tip_chord: Optional[float] = None
    span: Optional[float] = None
    sweep_length: Optional[float] = None
    sweep_angle: Optional[float] = None
    cant_angle: float = 0.0
    fin_count: int = 0
    fin_leading_edge: Optional[float] = None  # posición que necesita RocketPy
    # Parámetros de nosecone
    nc_shape: Optional[str] = None
    nc_shape_param: Optional[float] = None
    # Radio del cuerpo
    radius: Optional[float] = None


@dataclass
class OrkGeometry:
    """
    Geometría completa de un cohete OpenRocket, extraída dinámicamente.

    Acceso principal:
        geo.nosecones   → lista[ComponentGeometry]
        geo.body_tubes  → lista[ComponentGeometry]
        geo.fin_sets    → lista[ComponentGeometry]   ← posición lista para RocketPy
        geo.all_components → lista[ComponentGeometry] (orden de punta a cola)
    """
    ork_path: str
    nosecones: list = field(default_factory=list)
    body_tubes: list = field(default_factory=list)
    fin_sets: list = field(default_factory=list)
    all_components: list = field(default_factory=list)
    active_config_id: Optional[str] = None
    total_length: float = 0.0

    def __post_init__(self):
        self._parse()

    # ------------------------------------------------------------------
    # API pública de conveniencia
    # ------------------------------------------------------------------
    @property
    def first_nosecone(self) -> Optional[ComponentGeometry]:
        return self.nosecones[0] if self.nosecones else None

    @property
    def first_fin_set(self) -> Optional[ComponentGeometry]:
        return self.fin_sets[0] if self.fin_sets else None

    def summary(self) -> str:
        """Resumen legible de la geometría para logging."""
        lines = ["", "=" * 64, "  OrkGeometry — Posiciones absolutas desde punta de nariz", "=" * 64]
        for c in self.all_components:
            lead = ""
            if c.tag in FIN_TAGS:
                lead = f"  [leading={c.fin_leading_edge:.4f}m, trailing={c.abs_aft:.4f}m]"
            mass = f"  OVERRIDE={c.override_mass:.3f}kg" if c.override_mass is not None else ""
            lines.append(
                f"  [{c.tag}] {c.name!r:<30}  {c.abs_fore:.4f}m → {c.abs_aft:.4f}m{lead}{mass}"
            )
        lines.append(f"  Longitud total del cohete: {self.total_length:.4f}m")
        lines.append("=" * 64)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Parsing interno
    # ------------------------------------------------------------------
    def _parse(self):
        with zipfile.ZipFile(self.ork_path) as z:
            xml_content = z.read("rocket.ork").decode("utf-8")

        tree = ET.fromstring(xml_content)
        rocket_el = tree.find("rocket")
        if rocket_el is None:
            raise ValueError(f"No se encontró <rocket> en {self.ork_path}")

        # Configuración de motor activa
        self.active_config_id = self._find_active_config(rocket_el)

        # Recorrer subcomponentes del stage principal
        stage = self._get_main_stage(rocket_el)
        stage_children = self._get_subcomponents(stage)

        # Los hermanos del stage se colocan secuencialmente (sin posición explícita)
        self._resolve_sequential(stage_children, parent_fore=0.0, parent_aft=0.0)

        # Calcular longitud total
        if self.all_components:
            self.total_length = max(c.abs_aft for c in self.all_components)

    def _find_active_config(self, rocket_el: ET.Element) -> Optional[str]:
        """Retorna el configid de la configuración de motor marcada como default."""
        for mc in rocket_el.findall("motorconfiguration"):
            if mc.get("default") == "true":
                return mc.get("configid")
        mc = rocket_el.find("motorconfiguration")
        return mc.get("configid") if mc is not None else None

    def _get_main_stage(self, rocket_el: ET.Element) -> ET.Element:
        sc = rocket_el.find("subcomponents")
        if sc is None:
            raise ValueError("El cohete no tiene <subcomponents>")
        stage = sc.find("stage")
        if stage is None:
            raise ValueError("No se encontró <stage>")
        return stage

    def _get_subcomponents(self, elem: ET.Element) -> list:
        sc = elem.find("subcomponents")
        return list(sc) if sc is not None else []

    # ------------------------------------------------------------------
    # Resolución de posiciones
    # ------------------------------------------------------------------
    def _resolve_sequential(self, children: list, parent_fore: float, parent_aft: float):
        """
        Procesa una lista de elementos hermanos.
        En OpenRocket, cuando un componente NO tiene <position> explícito,
        se coloca secuencialmente tras el hermano anterior.
        """
        cursor = parent_fore  # avanza para componentes sin posición explícita

        for elem in children:
            tag = elem.tag.lower()
            if tag not in STRUCTURAL_TAGS:
                continue

            length = _get_float(elem, "length", 0.0)
            pos_val, pos_type = _get_position(elem)

            # ── Calcular posición absoluta ──────────────────────────────
            if pos_type is None:
                # Sin etiqueta <position>: colocación secuencial
                fore = cursor
                aft = fore + length
            else:
                fore, aft = _resolve_position(
                    pos_val, pos_type, length,
                    parent_fore, parent_aft
                )

            # Avanzar cursor solo para componentes sin posición explícita
            # (los que sí la tienen se ubican de forma independiente)
            if pos_type is None:
                cursor = aft

            # ── Crear ComponentGeometry ─────────────────────────────────
            comp = self._build_component(elem, tag, fore, aft, length)

            # ── Clasificar ─────────────────────────────────────────────
            self.all_components.append(comp)
            if tag == "nosecone":
                self.nosecones.append(comp)
            elif tag == "bodytube":
                self.body_tubes.append(comp)
            elif tag in FIN_TAGS:
                self.fin_sets.append(comp)

            # ── Procesar hijos recursivamente ───────────────────────────
            children_of_comp = self._get_subcomponents(elem)
            if children_of_comp:
                self._resolve_children(children_of_comp, fore, aft)

    def _resolve_children(self, children: list, parent_fore: float, parent_aft: float):
        """
        Procesa hijos de un componente.
        Los hijos CON <position> se ubican relativamente al padre.
        Los hijos SIN <position> se colocan secuencialmente dentro del padre.
        """
        cursor = parent_fore

        for elem in children:
            tag = elem.tag.lower()
            if tag not in STRUCTURAL_TAGS:
                continue

            length = _get_float(elem, "length", 0.0)
            pos_val, pos_type = _get_position(elem)

            if pos_type is None:
                fore = cursor
                aft = fore + length
                cursor = aft
            else:
                fore, aft = _resolve_position(
                    pos_val, pos_type, length,
                    parent_fore, parent_aft
                )

            comp = self._build_component(elem, tag, fore, aft, length)
            self.all_components.append(comp)
            if tag == "nosecone":
                self.nosecones.append(comp)
            elif tag == "bodytube":
                self.body_tubes.append(comp)
            elif tag in FIN_TAGS:
                self.fin_sets.append(comp)

            grandchildren = self._get_subcomponents(elem)
            if grandchildren:
                self._resolve_children(grandchildren, fore, aft)

    def _build_component(
        self,
        elem: ET.Element,
        tag: str,
        fore: float,
        aft: float,
        length: float,
    ) -> ComponentGeometry:
        """Construye un ComponentGeometry con todos sus parámetros."""
        name = _get_text(elem, "name", tag)
        override_mass = _get_float(elem, "overridemass", None)
        radius = _get_radius(elem)

        comp = ComponentGeometry(
            tag=tag,
            name=name,
            abs_fore=fore,
            abs_aft=aft,
            length=length,
            override_mass=override_mass,
            radius=radius,
        )

        # ── Parámetros de nosecone ──────────────────────────────────────
        if tag == "nosecone":
            shape_raw = _get_text(elem, "shape", "ogive")
            comp.nc_shape = _map_nosecone_shape(shape_raw)
            comp.nc_shape_param = _get_float(elem, "shapeparameter", 0.0)

        # ── Parámetros de aletas ────────────────────────────────────────
        if tag in FIN_TAGS:
            comp.root_chord = _get_float(elem, "rootchord", 0.0)
            comp.tip_chord = _get_float(elem, "tipchord", 0.0)
            comp.span = _get_float(elem, "height", 0.0)        # OR usa <height> = span
            comp.sweep_length = _get_float(elem, "sweeplength", None)
            comp.sweep_angle = _get_float(elem, "sweepangle", None)
            comp.cant_angle = _get_float(elem, "cant", 0.0)
            comp.fin_count = int(_get_text(elem, "fincount", "3") or "3")

            # ── Posición para RocketPy ──────────────────────────────────
            # aft ya contiene el borde trasero del root chord.
            # RocketPy necesita el LEADING EDGE (borde delantero).
            comp.fin_leading_edge = aft - comp.root_chord

        return comp


# ---------------------------------------------------------------------------
# Funciones auxiliares puras (sin estado)
# ---------------------------------------------------------------------------

def _resolve_position(
    pos_val: float,
    pos_type: str,
    length: float,
    parent_fore: float,
    parent_aft: float,
) -> tuple[float, float]:
    """
    Convierte un par (pos_val, pos_type) a (abs_fore, abs_aft).

    Reglas:
        top      → abs_fore = parent_fore + pos_val
        bottom   → abs_aft  = parent_aft  + pos_val   [pos_val suele ser negativo]
        middle   → centro del componente = centro del padre + pos_val
        absolute → abs_fore = pos_val  (desde la punta de la nariz)
    """
    t = pos_type.lower()

    if t == "top":
        fore = parent_fore + pos_val
        aft = fore + length

    elif t == "bottom":
        aft = parent_aft + pos_val
        fore = aft - length

    elif t == "middle":
        parent_mid = (parent_fore + parent_aft) / 2.0
        fore = parent_mid + pos_val - length / 2.0
        aft = fore + length

    elif t == "absolute":
        fore = pos_val
        aft = fore + length

    else:
        # Fallback conservador: igual a "top"
        fore = parent_fore + pos_val
        aft = fore + length

    return fore, aft


def _get_position(elem: ET.Element) -> tuple[float, Optional[str]]:
    """
    Extrae (valor_float, tipo_string) de <position> o <axialoffset>.
    Retorna (0.0, None) si el componente no tiene etiqueta de posición.
    """
    for tag_name, attr_name in [("position", "type"), ("axialoffset", "method")]:
        el = elem.find(tag_name)
        if el is not None and el.text and el.text.strip():
            return float(el.text.strip()), el.get(attr_name, "top")
    return 0.0, None


def _get_text(elem: ET.Element, tag: str, default: Optional[str] = None) -> Optional[str]:
    el = elem.find(tag)
    if el is not None and el.text and el.text.strip():
        return el.text.strip()
    return default


def _get_float(elem: ET.Element, tag: str, default=None) -> Optional[float]:
    t = _get_text(elem, tag)
    try:
        return float(t) if t is not None else default
    except (ValueError, TypeError):
        return default


def _get_radius(elem: ET.Element) -> Optional[float]:
    """
    Intenta extraer el radio del componente.
    OR usa <radius>, <outerradius>, o <aftradius> según el tipo.
    """
    for tag in ("radius", "outerradius", "aftradius"):
        el = elem.find(tag)
        if el is not None and el.text and el.text.strip():
            val = el.text.strip()
            # OR puede escribir "auto 0.054" → tomar el número
            if val.startswith("auto"):
                parts = val.split()
                if len(parts) > 1:
                    try:
                        return float(parts[1])
                    except ValueError:
                        pass
            else:
                try:
                    return float(val)
                except ValueError:
                    pass
    return None


OR_SHAPE_MAP = {
    "ogive": "ogive",
    "conical": "conical",
    "ellipsoid": "ellipsoid",
    "power": "power",
    "parabolic": "parabolic",
    "haack": "lvhaack",        # LD-Haack ↔ LV-Haack en RocketPy
    "lvhaack": "lvhaack",
}

def _map_nosecone_shape(shape: str) -> str:
    return OR_SHAPE_MAP.get(shape.lower(), "ogive")


# ---------------------------------------------------------------------------
# Punto de entrada para diagnóstico
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ork_path = sys.argv[1] if len(sys.argv) > 1 else "disenos/cohete.ork"
    print(f"\nParsing: {ork_path}")
    geo = OrkGeometry(ork_path)
    print(geo.summary())

    if geo.first_nosecone:
        nc = geo.first_nosecone
        print(f"\nNosecone para RocketPy:")
        print(f"  kind       = {nc.nc_shape}")
        print(f"  length     = {nc.length} m")
        print(f"  base_radius= {nc.radius} m")
        print(f"  position   = {nc.abs_fore} m  (punta de nariz)")

    if geo.first_fin_set:
        f = geo.first_fin_set
        print(f"\nAletas para RocketPy (add_surfaces):")
        print(f"  n          = {f.fin_count}")
        print(f"  root_chord = {f.root_chord} m")
        print(f"  tip_chord  = {f.tip_chord} m")
        print(f"  span       = {f.span} m")
        print(f"  sweep_len  = {f.sweep_length} m")
        print(f"  cant_angle = {f.cant_angle} deg")
        print(f"  FIN_POSITION_ABSOLUTE = {f.fin_leading_edge:.6f} m  ← usar en add_surfaces")

    if geo.body_tubes:
        for bt in geo.body_tubes:
            print(f"\nBody Tube {bt.name!r}: {bt.abs_fore:.4f}m → {bt.abs_aft:.4f}m  (r={bt.radius}m)")
