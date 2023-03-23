'''
Created on 2023-03-22

@author: wf
'''
from ceurspt.ceurws import JsonCacheManager,VolumeManager,PaperManager
from tests.basetest import Basetest,Profiler
from pathlib import Path

class TestJsonCache(Basetest):
    """
    Test the ceur-ws Json Cache
    """
    
    def test_json_cache(self):
        """
        test reading list of dicts 
        """
        jcm=JsonCacheManager()
        for lod_name in ["volumes","papers"]:
            profiler=Profiler(f"read {lod_name}")
            lod=jcm.load_lod(lod_name)    
            elapsed=profiler.time()
            print(f"read {len(lod)} {lod_name} in {elapsed:5.1f} s")
            jcm.store(lod_name,lod)
            profiler=Profiler(f"store {lod_name}")
            elapsed=profiler.time()
            print(f"store {len(lod)} {lod_name} in {elapsed:5.1f} s")
            
    def testGetVolumesAndPapers(self):
        """
        get volumes and papers
        """
        script_path=Path(__file__)
        base_path=f"{script_path.parent.parent}/ceur-ws"
        vm=VolumeManager(base_path)
        vm.getVolumes()
        pm=PaperManager()
        pm.getPapers(vm)
    