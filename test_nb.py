import json
import subprocess
import os

with open('notebooks/simulacion_cohete.ipynb/simulation.ipynb', 'r', encoding='utf-8') as f: 
    nb = json.load(f)

nb['cells'].insert(1, {
    'id': 'gui_dynamic_injection_cell', 
    'cell_type': 'code', 
    'execution_count': None, 
    'metadata': {}, 
    'outputs': [], 
    'source': ['LATITUD=0\n', 'LONGITUD=0\n', 'ELEVACION=0\n']
})

with open('temp_simulation.ipynb', 'w', encoding='utf-8') as f: 
    json.dump(nb, f)

venv_python = os.path.join(os.path.abspath('.venv'), 'Scripts', 'python.exe')
cmd = [venv_python, "-m", "jupyter", "nbconvert", "--to", "html", "--execute", "temp_simulation.ipynb"]

result = subprocess.run(cmd, cwd='notebooks/simulacion_cohete.ipynb', capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
