import nbformat as nbf
import os
path = 'notebooks/simulacion_cohete.ipynb/simulation.ipynb'
nb = nbf.read(path, as_version=4)

for cell in nb.cells:
    if 'flight.export_kml' in cell.source or 'exporter.export_kml' in cell.source:
        cell.source = '''flight.info()
flight.plots.linear_kinematics_data()
flight.plots.trajectory_3d()

# ==========================================
# MODULO DE RECUPERACION Y TELEMETRIA
# ==========================================
import os
from rocketpy.simulation.flight_data_exporter import FlightDataExporter

# Asegurar existencia del directorio de resultados en la raiz del proyecto
os.makedirs('../../resultados', exist_ok=True)

# 1. Extraccion de coordenadas de impacto
impact_lat = flight.latitude(flight.t_final)
impact_lon = flight.longitude(flight.t_final)
print(f"\\n[SISTEMA] Coordenada de Impacto Prevista: {impact_lat:.6f}, {impact_lon:.6f}")

# Instanciar exportador (RocketPy v1.12+)
exporter = FlightDataExporter(flight)

# 2. Exportacion KML para Google Earth
exporter.export_kml(
    file_name="../../resultados/trayectoria_operativa.kml",
    extrude=True,
    altitude_mode="relative_to_ground"
)
print("[SISTEMA] Archivo KML generado en /resultados para visualizacion espacial.")

# 3. Exportacion de la matriz balistica a CSV
exporter.export_data(
    "../../resultados/datos_telemetria_simulada.csv",
    "z", "vz", "az", "mach_number"
)
print("[SISTEMA] Matriz de vuelo exportada a CSV en /resultados con exito.")
'''
nbf.write(nb, path)
