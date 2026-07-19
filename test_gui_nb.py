import json
import subprocess
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
notebook_dir = os.path.join(root_dir, 'notebooks', 'simulacion_cohete.ipynb')
notebook_path = os.path.join(notebook_dir, 'simulation.ipynb')
temp_nb_path = os.path.join(notebook_dir, 'temp_simulation.ipynb')

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Insert cell
nb['cells'].insert(1, {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": ["print('test')\n"]
})

with open(temp_nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f)

venv_python = os.path.join(root_dir, '.venv', 'Scripts', 'python.exe')
cmd = [venv_python, "-m", "jupyter", "nbconvert", "--to", "html", "--execute", temp_nb_path]

result = subprocess.run(cmd, cwd=notebook_dir, capture_output=True, text=True)
print("Return code:", result.returncode)
with open('test_gui_nb_stderr.txt', 'w') as f:
    f.write(result.stderr)
