"""
ANALYSIS OF THE COORDINATE SYSTEM TRANSLATION BUG
===================================================
Calculates correct positions for all rocket components
to reproduce OpenRocket's geometry faithfully in RocketPy.
"""
import zipfile
import xml.etree.ElementTree as ET

ORK_PATH = 'disenos/cohete.ork'

with zipfile.ZipFile(ORK_PATH) as z:
    with z.open('rocket.ork') as f:
        content = f.read().decode('utf-8')

root = ET.fromstring(content)

def find_all_tags(elem, tagname):
    results = []
    if elem.tag.lower() == tagname.lower():
        results.append(elem)
    for child in elem:
        results.extend(find_all_tags(child, tagname))
    return results

# Find components
rockets = find_all_tags(root, 'rocket')
rocket = rockets[0] if rockets else None

stages = find_all_tags(rocket, 'stage')
stage = stages[0] if stages else None

nosecones = find_all_tags(stage, 'nosecone')
nosecone = nosecones[0] if nosecones else None

bodytubes = find_all_tags(stage, 'bodytube')
bodytube = bodytubes[0] if bodytubes else None

print("Found:", 
      "rocket" if rocket is not None else "NO ROCKET",
      "stage" if stage is not None else "NO STAGE",
      "nosecone" if nosecone is not None else "NO NOSECONE",
      "bodytube" if bodytube is not None else "NO BODYTUBE")

if bodytube is not None:
    fins_list = find_all_tags(bodytube, 'trapezoidfinset')
    print("Fins found:", len(fins_list))
    
    if fins_list:
        fins = fins_list[0]
        
        # Get all child tags
        print("Fin children:", [c.tag for c in fins])

# Nosecone params
if nosecone is not None:
    pos_el = nosecone.find('position')
    nc_pos_type = pos_el.get('type') if pos_el is not None else 'absolute'
    nc_pos_val = float(pos_el.text) if pos_el is not None else 0.0
    nc_length_el = nosecone.find('length')
    nc_length = float(nc_length_el.text) if nc_length_el is not None else 0.0
    print(f"\nNOSECONE: length={nc_length}m, position={nc_pos_val} [{nc_pos_type}]")

# Body tube
if bodytube is not None:
    pos_el = bodytube.find('position')
    bt_length_el = bodytube.find('length')
    bt_length = float(bt_length_el.text) if bt_length_el is not None else 0.0
    bt_start = nc_length  # starts where nosecone ends
    bt_end = bt_start + bt_length
    print(f"\nBODY TUBE: length={bt_length}m")
    print(f"  Start = {bt_start}m from nose tip")
    print(f"  End (aft) = {bt_end}m from nose tip")

    # Find fins
    fins_list = find_all_tags(bodytube, 'trapezoidfinset')
    if fins_list:
        fins = fins_list[0]
        fin_pos_el = fins.find('position')
        fin_pos_type = fin_pos_el.get('type') if fin_pos_el is not None else 'top'
        fin_pos_val = float(fin_pos_el.text) if fin_pos_el is not None else 0.0
        
        # Find dimensions
        rootchord_el = fins.find('rootchord')
        tipchord_el = fins.find('tipchord')
        height_el = fins.find('height')
        sweep_el = fins.find('sweeplength')
        fincount_el = fins.find('fincount')
        
        fin_root_chord = float(rootchord_el.text) if rootchord_el is not None else 0.0
        fin_tip_chord = float(tipchord_el.text) if tipchord_el is not None else 0.0
        fin_span = float(height_el.text) if height_el is not None else 0.0
        fin_sweep = float(sweep_el.text) if sweep_el is not None else 0.0
        fin_count = int(fincount_el.text) if fincount_el is not None else 4
        
        print(f"\nFINS: count={fin_count}, root_chord={fin_root_chord}m, tip_chord={fin_tip_chord}m")
        print(f"      span={fin_span}m, sweep={fin_sweep}m")
        print(f"      position={fin_pos_val} [{fin_pos_type}]")
        
        # Interpret position
        # 'bottom' = measured from parent's aft end to this component's aft end
        # negative = component aft is FORWARD of parent aft
        if fin_pos_type == 'bottom':
            fin_aft_abs = bt_end + fin_pos_val
            fin_fore_abs = fin_aft_abs - fin_root_chord
            print(f"\n  Interpretation of position type='bottom':")
            print(f"  Fin AFT edge abs = {bt_end} + ({fin_pos_val}) = {fin_aft_abs}m from nose tip")
            print(f"  Fin FORE edge (leading edge root) abs = {fin_aft_abs} - {fin_root_chord} = {fin_fore_abs}m from nose tip")
        elif fin_pos_type == 'top':
            fin_fore_abs = bt_start + fin_pos_val
            fin_aft_abs = fin_fore_abs + fin_root_chord
            print(f"\n  Interpretation of position type='top':")
            print(f"  Fin FORE edge abs = {bt_start} + ({fin_pos_val}) = {fin_fore_abs}m from nose tip")
        
        print(f"\n  ROCKETPY needs: position of fin LEADING EDGE from nose tip = {fin_fore_abs}m")
        print(f"  WHAT SERIALIZER REPORTS: 0.179m (WRONG!)")

print("\n=== WHAT THE SERIALIZER DID WRONG ===")
print("The rocketserializer stored fin position=0.179")
print("This is the position RELATIVE TO THE BODY TUBE START (not absolute from nose)")
print("0.179 = 0.3 (nosecone) + some offset - the serializer had a coordinate origin bug")
print("OR it confused 'bottom' reference type and calculated wrong absolute position")
