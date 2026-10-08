import unittest,sys,json,tempfile,wave,os,types,subprocess
from pathlib import Path
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'scripts'
sys.path.insert(0,str(S))
fake=types.ModuleType('faster_whisper')
class Model:
 def __init__(self,*a,**kw):pass
 def transcribe(self,*a,**kw):
  words=[types.SimpleNamespace(word='Hello',start=.1,end=.3),types.SimpleNamespace(word='world.',start=.3,end=.6)]
  return iter([types.SimpleNamespace(start=.1,end=.6,text='Hello world.',words=words)]),None
fake.WhisperModel=Model
sys.modules['faster_whisper']=fake
import common,align,fill_gaps,transcribe,run_all,merge_translations
PYTHON=sys.executable
ENV=os.environ.copy()
def wav(path,channels=1,dur=1):
 sr=16000;t=np.arange(round(sr*dur))/sr
 mono=(np.sin(2*np.pi*440*t)*7000).astype(np.int16)
 data=mono[None,:] if channels==1 else np.vstack([mono,-mono//2])
 with wave.open(str(path),'wb') as f:
  f.setnchannels(channels);f.setsampwidth(2);f.setframerate(sr);f.writeframes(data.T.copy().tobytes())
 return data,sr
class Regressions(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.w=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def args(self,*extra):return patch.object(sys,'argv',['script','--work',str(self.w),*extra])
 def test_01_pcm_mono_amplitude_is_preserved(self):
  expected,sr=wav(self.w/'a.wav');got,rate,layout=common.load_all(str(self.w/'a.wav'))
  self.assertEqual(layout,'mono');self.assertEqual(rate,sr);np.testing.assert_array_equal(got,expected)
 def test_02_pcm_stereo_channels_are_not_interleaved(self):
  expected,sr=wav(self.w/'a.wav',2);got,rate,layout=common.load_all(str(self.w/'a.wav'))
  self.assertEqual(got.shape,expected.shape);np.testing.assert_array_equal(got,expected)
 def test_03_mp3_encode_decode_is_not_saturated(self):
  expected,sr=wav(self.w/'a.wav');common.encode_clip(expected,sr,'mono',0,1,str(self.w/'a.mp3'))
  got,rate,layout=common.load_all(str(self.w/'a.mp3'));self.assertLess(np.max(np.abs(got)),12000);self.assertGreater(np.max(np.abs(got)),2000)
 def test_04_very_short_rms_and_chunk_tails_are_covered(self):
  rms,_=common.compute_rms(np.ones(8,dtype=np.float32),16000);self.assertEqual(len(rms),1)
  _,hop=common.compute_rms(np.ones(22050,dtype=np.float32),22050);self.assertAlmostEqual(hop,220/22050)
  for duration in [.2,90.2,180.3]:
   pcm=np.ones(round(1000*duration),dtype=np.int16)*4000
   chunks=transcribe.plan_chunks(pcm,1000);self.assertEqual(chunks[0][0],0);self.assertEqual(chunks[-1][1],duration)
   self.assertTrue(all(b>a for a,b in chunks));self.assertTrue(all(a[1]==b[0] for a,b in zip(chunks,chunks[1:])))
 def test_05_translation_check_does_not_write_output(self):
  (self.w/'sentences.json').write_text(json.dumps({'sentences':[{},{}]}))
  (self.w/'_trans_1.json').write_text(json.dumps({'1':'你好'}))
  with self.args('--check'):merge_translations.main()
  self.assertFalse((self.w/'translations.json').exists())
  with self.args():merge_translations.main()
  self.assertEqual(json.loads((self.w/'translations.json').read_text()),{'1':'你好'})
 def test_06_missing_word_timestamps_keep_sentence_order(self):
  segs=[{'start':0,'end':1,'text':'unfinished','words':[{'w':'Hello','s':0,'e':1}]},
        {'start':1,'end':2,'text':'Middle sentence.','words':[]},
        {'start':2,'end':3,'text':'Last words.','words':[{'w':'Last','s':2,'e':2.5},{'w':'words.','s':2.5,'e':3}]}]
  got=align.build_sentences(segs);self.assertEqual([x['text'] for x in got],['Hello','Middle sentence.','Last words.'])
 def test_07_gap_wav_accepts_mono_and_stereo(self):
  for ch in [1,2]:
   data,sr=wav(self.w/f'{ch}.wav',ch);p=self.w/f'gap{ch}.wav'
   fill_gaps.write_wav(data,sr,0,.7,str(p));got,_,_=common.load_all(str(p));self.assertEqual(got.shape[0],ch)
 def test_08_chinese_materials_have_separate_storage(self):
  a=[{'text':'Hello','start':0,'end':1}]
  self.assertNotEqual(common.storage_key('四级第一套',a),common.storage_key('六级第二套',a))
  self.assertEqual(common.storage_key('四级第一套',a),common.storage_key('四级第一套',a))
  self.assertNotEqual(common.storage_key('四级第一套',a),common.storage_key('四级第一套',[{'text':'Changed','start':0,'end':1}]))
 def test_09_restart_clears_completed_steps_before_failure(self):
  wav(self.w/'a.wav');run_all.save_config(str(self.w),{'audio':str(self.w/'a.wav'),'done_steps':run_all.STEPS})
  with self.args('--restart','--only','transcribe.py'),patch.object(run_all,'run',side_effect=SystemExit(9)):
   with self.assertRaises(SystemExit):run_all.main()
  self.assertEqual(run_all.read_done(str(self.w)),set())
 def test_10_resume_rebuilds_missing_final_html(self):
  wav(self.w/'a.wav');cfg={'audio':str(self.w/'a.wav'),'title':'测试','done_steps':['make_single.py']};cfg['pipeline_signature']=run_all.input_signature(cfg);run_all.save_config(str(self.w),cfg)
  with self.args('--resume','--only','make_single.py'),patch.object(run_all,'run',side_effect=lambda *_:(self.w/'测试（单文件版）.html').write_text('<html>ok</html>')) as call:run_all.main()
  self.assertEqual(call.call_count,1)
 def test_11_changed_audio_archives_stale_translations(self):
  wav(self.w/'a.wav');cfg={'audio':str(self.w/'a.wav'),'done_steps':run_all.STEPS};cfg['pipeline_signature']=run_all.input_signature(cfg);run_all.save_config(str(self.w),cfg)
  (self.w/'translations.json').write_text('{"1":"旧译文"}');(self.w/'a.wav').write_bytes(b'new source')
  def run(step,extra):
   self.assertIn('--restart',extra);(self.w/'segments_raw.json').write_text('{}')
  with self.args('--resume','--only','transcribe.py'),patch.object(run_all,'run',side_effect=run):run_all.main()
  self.assertFalse((self.w/'translations.json').exists());self.assertEqual(len(list((self.w/'_previous_inputs').rglob('translations.json'))),1)
 def test_12_partial_transcription_does_not_leave_old_final(self):
  wav(self.w/'a.wav');(self.w/'segments_raw.json').write_text('{"old":true}')
  pcm=np.ones(91000,dtype=np.int16)*5000
  with self.args('--audio',str(self.w/'a.wav'),'--model','small','--jobs','1','--no-batch','--limit','1'),patch.object(transcribe,'decode_16k',return_value=(pcm,1000)):
   transcribe.main()
  self.assertFalse((self.w/'segments_raw.json').exists());progress=json.loads((self.w/'transcribe_progress.json').read_text());self.assertEqual(progress['done'],1)
  # Simulate a crash after writing uncommitted rows; resumed processing must trim them.
  with (self.w/'segments_raw.jsonl').open('a') as f:f.write('{"uncommitted":true}\n')
  with self.args('--model','small','--jobs','1','--no-batch'),patch.object(transcribe,'decode_16k',return_value=(pcm,1000)):
   transcribe.main()
  final=json.loads((self.w/'segments_raw.json').read_text());self.assertEqual(len(final['segments']),2);self.assertTrue(all('uncommitted' not in x for x in final['segments']))
 def test_13_index_escapes_text_and_keeps_audio_extension(self):
  wav(self.w/'a.wav');data={'duration':1,'sentences':[{'start':0,'end':1,'clip_start':0,'clip_end':1,'file':'001.mp3','text':'<img src=x onerror="bad()"> & literal','section':'<unsafe>'}]}
  (self.w/'sentences.json').write_text(json.dumps(data));(self.w/'config.json').write_text(json.dumps({'audio':str(self.w/'a.wav')}))
  subprocess.run([PYTHON,str(S/'build_index.py'),'--work',str(self.w),'--title','<unsafe title>'],env=ENV,check=True,capture_output=True)
  html=(self.w/'index.html').read_text();self.assertNotIn('<img src=x',html);self.assertIn('&lt;img',html);self.assertIn('src="full.wav"',html);self.assertTrue((self.w/'full.wav').exists())
 def test_14_one_word_answers_are_not_merged_with_next_speaker(self):
  words=[{'w':'Yes.','s':0,'e':.3},{'w':'Dr.','s':.5,'e':.7},{'w':'Smith','s':.7,'e':1},{'w':'agrees.','s':1,'e':1.3}]
  got=align.build_sentences([{'words':words}]);self.assertEqual([x['text'] for x in got],['Yes.','Dr. Smith agrees.'])
 def test_15_relative_audio_paths_survive_cwd_change(self):
  wav(self.w/'a.wav')
  previous=os.getcwd()
  try:
   os.chdir(self.w)
   with self.args('--audio','a.wav'):common.get_args()
   os.chdir(previous)
   with self.args():args=common.get_args()
   self.assertTrue(os.path.samefile(args.audio,self.w/'a.wav'))
  finally:os.chdir(previous)
if __name__=='__main__':unittest.main(verbosity=2)
