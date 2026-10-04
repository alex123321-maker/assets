"""Measure continuous frozen death paths during build; never author trajectories."""
import json
from pathlib import Path
from author_death_motion import validate_linear_segments
from death_rubble import supported_by_floor
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
asset=ROOT/'assets/characters/bosses/cairn'
motion=json.loads((asset/'source/death_motion.json').read_text())
measurements=validate_linear_segments(motion)
final=np.asarray(motion['frames'][-1]['centers'])
previous=np.asarray(motion['frames'][-2]['centers'])
sizes=np.asarray(motion['sizes'])
supported=supported_by_floor(final,sizes)
speed=np.linalg.norm(final-previous,axis=1)/(motion['frames'][-1]['time']-motion['frames'][-2]['time'])
measurements.update({'fragments':len(sizes),'unsupported_fragments':int(np.count_nonzero(~supported)),
                     'max_final_speed_m_s':float(speed.max())})
if not np.all(supported) or speed.max()>1e-7: raise ValueError('Unsupported or moving final rubble')
(asset/'review/death_validation.json').write_text(json.dumps(measurements,indent=2)+'\n',encoding='utf-8')
print(json.dumps(measurements))
