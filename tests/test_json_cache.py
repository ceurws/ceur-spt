"""
Created on 2023-03-22

@author: wf
"""

import unittest
from pathlib import Path

from ceurspt.ceurws import JsonCacheManager, PaperManager, VolumeManager
from tests.basetest import Basetest, Profiler


class TestJsonCache(Basetest):
    """
    Test the ceur-ws Json Cache
    """

    @unittest.skipIf(True, "only manual")
    def test_json_cache(self):
        """
        test reading list of dicts
        """
        jcm = JsonCacheManager()
        for lod_name in ["volumes", "papers", "proceedings", "papers_dblp"]:
            profiler = Profiler(f"read {lod_name}")
            lod = jcm.load_lod(lod_name)
            elapsed = profiler.time()
            print(f"read {len(lod)} {lod_name} in {elapsed:5.1f} s")
            jcm.store(lod_name, lod)
            profiler = Profiler(f"store {lod_name}")
            elapsed = profiler.time()
            print(f"store {len(lod)} {lod_name} in {elapsed:5.1f} s")

    def testGetVolumesAndPapersAndProceedings(self):
        """
        get volumes and papers
        """
        script_path = Path(__file__)
        base_path = f"{script_path.parent.parent}/ceur-ws"
        base_url = "https://cvb.wikidata.dbis.rwth-aachen.de"
        vm = VolumeManager(base_path=base_path, base_url=base_url)
        vm.getVolumes()
        pm = PaperManager(base_url=base_url)
        pm.getPapers(vm)
