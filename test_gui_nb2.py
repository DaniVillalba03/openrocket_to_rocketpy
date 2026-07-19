import json
import subprocess
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
notebook_dir = os.path.join(root_dir, 'notebooks', 'simulacion_cohete.ipynb')
notebook_path = os.path.join(notebook_dir, 'simulation.ipynb')
temp_nb_path = os.path.join(notebook_dir, 'temp_simulation.ipynb')

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

LATITUD = -25.33
LONGITUD = -57.51
ELEVACION = 125.0
injection_code = [
    "print('[GUI] Clima Dinámico OpenMeteo activado.')\n"
]
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and any('env.set_atmospheric_model' in line for line in cell.get('source', [])):
        cell['source'] = [
            "import requests\n",
            "import datetime\n",
            "import math\n",
            "try:\n",
            f"    print(f'[GUI] Descargando clima de Open-Meteo para Lat: {LATITUD}, Lon: {LONGITUD}...')\n",
            f"    url = f'https://api.open-meteo.com/v1/forecast?latitude={LATITUD}&longitude={LONGITUD}&current_weather=true&windspeed_unit=ms'\n",
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
    "source": [f"LATITUD={LATITUD}\n", f"LONGITUD={LONGITUD}\n", f"ELEVACION={ELEVACION}\n"] + injection_code
}

nb['cells'].insert(1, injection_cell)

with open(temp_nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f)

venv_python = os.path.join(root_dir, '.venv', 'Scripts', 'python.exe')
cmd = [venv_python, "-m", "jupyter", "nbconvert", "--to", "html", "--execute", temp_nb_path]

result = subprocess.run(cmd, cwd=notebook_dir, capture_output=True, text=True)
print("Return code:", result.returncode)
with open('test_gui_nb_stderr2.txt', 'w') as f:
    f.write(result.stderr)
