'''
Created on 2023-03-22

@author: wf
'''
from ceurspt.ceurws import JsonCacheManager
from tests.basetest import Basetest,Profiler

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
            profiler=Profiler(lod_name)
            lod=jcm.load_lod(lod_name)    
            elapsed=profiler.time()
            print(f"read {len(lod)} {lod_name} in {elapsed:5.1f} s")