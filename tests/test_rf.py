import copy
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from researchos_rf.model import C,K,analyze
from researchos_rf.records import ValidationError,dumps,read_json,sha,validate
from researchos_rf.workflow import run,verify_bundle,verify_evidence
ROOT=Path(__file__).resolve().parents[1];EXAMPLE=ROOT/'examples/synthetic-rf.json'

class RFTests(unittest.TestCase):
    def setUp(self):self.r=read_json(EXAMPLE)
    def test_known_link_and_noise(self):
        result=analyze(self.r);a=result['link_results'][0]
        self.assertAlmostEqual(a['free_space_loss_db'],68.01080822955625)
        self.assertAlmostEqual(a['received_power_dbm'],28-a['free_space_loss_db'])
        self.assertAlmostEqual(a['noise_power_dbm'],10*math.log10(K*290*100e6/.001)+6)
        self.assertAlmostEqual(a['one_way_delay_ns'],10/C*1e9)
    def test_distance_frequency_and_bandwidth_scaling(self):
        self.r['link']['distances_m']=[10,20];result=analyze(self.r)
        self.assertAlmostEqual(result['link_results'][1]['free_space_loss_db']-result['link_results'][0]['free_space_loss_db'],20*math.log10(2))
        self.r['bands'][1]['frequency_ghz']=12;result=analyze(self.r)
        self.assertAlmostEqual(result['link_results'][2]['free_space_loss_db']-result['link_results'][0]['free_space_loss_db'],20*math.log10(2))
        noise=result['link_results'][0]['noise_power_dbm'];self.r['link']['bandwidth_mhz']*=2
        self.assertAlmostEqual(analyze(self.r)['link_results'][0]['noise_power_dbm']-noise,10*math.log10(2))
    def test_domain_and_declared_attenuation(self):
        self.r['link']['distances_m']=[.001,1000];self.r['bands'][0]['extra_attenuation_db_km']=3
        rows=analyze(self.r)['link_results']
        self.assertEqual(rows[0]['domain_status'],'outside-far-field-model')
        self.assertEqual(rows[0]['threshold_status'],'not-assessed-outside-domain')
        self.assertEqual(rows[1]['extra_loss_db'],3)
    def test_bandwidth_delay_and_half_sample(self):
        s=analyze(self.r)['sensing_results'];self.assertAlmostEqual(s['assumed_range_m'],2.99792458)
        self.assertAlmostEqual(s['bandwidth_results'][1]['ideal_range_resolution_m'],C/(2*100e6))
        self.r['sensing']['assumed_round_trip_delay_ns']=.5
        self.assertEqual(analyze(self.r)['sensing_results']['nearest_sample_index'],1)
        self.r['sensing']['assumed_round_trip_delay_ns']=0
        self.assertEqual(analyze(self.r)['sensing_results']['quantized_range_m'],0)
    def test_invalid_records(self):
        mutations=[lambda r:r.update(schema_version=True),lambda r:r.update(id='../escape'),lambda r:r['link'].update(temperature_K=0),lambda r:r['link'].update(bandwidth_mhz=True),lambda r:r['link'].update(distances_m=[0]),lambda r:r['bands'][0].update(frequency_ghz=301),lambda r:r['bands'].append(copy.deepcopy(r['bands'][0])),lambda r:r['sensing'].update(sample_rate_mhz=0),lambda r:r.update(data_kind='experimental')]
        for mutate in mutations:
            r=copy.deepcopy(self.r);mutate(r)
            with self.subTest(record=r),self.assertRaises(ValidationError):validate(r)
    def test_evidence_and_signed_measurements(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=b'test fixture, not real evidence';(root/'raw').write_bytes(data)
            self.r['data_kind']='experimental';self.r['evidence']=[{'id':'raw','path':'raw','sha256':sha(data),'description':'Fixture'}]
            self.r['measurements']=[{'metric':'received power','unit':'dBm','value':-60,'uncertainty':1,'method':'Fixture','evidence_ids':['raw']}]
            p=root/'record.json';p.write_text(dumps(self.r));run(p,root/'run');(root/'raw').unlink();verify_bundle(root/'run');(root/'run/evidence/0000.bin').write_bytes(b'changed')
            with self.assertRaises(ValidationError):verify_bundle(root/'run')
    def test_integrity_paths_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a,b=root/'a',root/'b';run(EXAMPLE,a);run(EXAMPLE,b);verify_bundle(a)
            self.assertEqual({p.relative_to(a):p.read_bytes() for p in a.rglob('*') if p.is_file()},{p.relative_to(b):p.read_bytes() for p in b.rglob('*') if p.is_file()})
            with self.assertRaises(ValidationError):run(EXAMPLE,a)
            result=read_json(a/'results.json');result['link_results'][0]['snr_db']=999;(a/'results.json').write_text(dumps(result));manifest=read_json(a/'manifest.json');manifest['files']['results.json']=sha((a/'results.json').read_bytes());(a/'manifest.json').write_text(dumps(manifest))
            with self.assertRaises(ValidationError):verify_bundle(a)
            self.r['evidence']=[{'id':'raw','path':'../escape','sha256':sha(b'x'),'description':'Fixture'}]
            with self.assertRaises(ValidationError):validate(self.r)
            (root/'link').symlink_to(root.parent);self.r['evidence'][0]['path']='link/outside'
            with self.assertRaises(ValidationError):verify_evidence(validate(self.r),root)
    def test_strict_json_and_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.json'
            for data in ['{"x":1,"x":2}','{"x":NaN}']:
                p.write_text(data)
                with self.assertRaises(ValidationError):read_json(p)
            output=str(Path(tmp)/'run')
            for args in [['validate',str(EXAMPLE)],['run',str(EXAMPLE),'--output',output],['verify',output],['report',output]]:
                r=subprocess.run([sys.executable,'-m','researchos_rf',*args],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
