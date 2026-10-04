"""Check actual post-modifier Godot bone matrices against the authored cubes."""
import json
from pathlib import Path
from validate_voxel_motion import validate_asset

ROOT=Path(__file__).resolve().parents[2]
asset=ROOT/'assets/characters/bosses/cairn'
contract=json.loads((asset/'source/rig_contract.json').read_text())
probe=json.loads((asset/'review/godot/runtime_pose_samples.json').read_text())
report=validate_asset(contract['cubes'],probe['samples'],tolerance=2e-5,max_issues=40)
(asset/'review/godot/cube_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='issues'}))
if not report['pass']:
    print(json.dumps(report['issues'][:20],indent=2))
    raise SystemExit(1)
