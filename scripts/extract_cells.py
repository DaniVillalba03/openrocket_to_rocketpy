import json

nb = json.load(open(r'notebooks\simulacion_cohete.ipynb\simulation.ipynb', 'r', encoding='utf-8'))
keywords = ['Rocket(', 'add_trapezoidal', 'center_of_mass', 'NoseCone(', 'add_motor', 'SolidMotor(', 'TrapezoidalFins(']

for i, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    if any(k in src for k in keywords):
        ctype = cell['cell_type']
        print(f'--- Cell {i} (type={ctype}) ---')
        print(src[:4000])
        print()
