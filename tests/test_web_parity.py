import copy,json,math,shutil,subprocess,unittest
from pathlib import Path
from researchos_rf.records import read_json
from researchos_rf.model import analyze
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('node'),'Node required for web parity')
class WebParityTests(unittest.TestCase):
    def test_complete_result_parity(self):
        base=read_json(ROOT/'examples/synthetic-rf.json');cases=[base]
        r=copy.deepcopy(base);r['link']['distances_m']=[.001,100];r['sensing']['assumed_round_trip_delay_ns']=.5;cases.append(r)
        r=copy.deepcopy(base);r['link']['temperature_K']=300;r['bands'][2]['extra_attenuation_db_km']=10;r['sensing']['assumed_round_trip_delay_ns']=0;cases.append(r)
        js="import fs from 'node:fs';import{analyze}from './web/model.mjs';console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(analyze)))"
        results=json.loads(subprocess.check_output(['node','--input-type=module','-e',js],input=json.dumps(cases),text=True,cwd=ROOT))
        def compare(a,b):
            if isinstance(b,dict):
                self.assertEqual(a.keys(),b.keys())
                for k in b:compare(a[k],b[k])
            elif isinstance(b,list):
                self.assertEqual(len(a),len(b))
                for x,y in zip(a,b):compare(x,y)
            elif type(b) is float:self.assertTrue(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-11),(a,b))
            else:self.assertEqual(a,b)
        for r,w in zip(cases,results):compare(w,analyze(r))
