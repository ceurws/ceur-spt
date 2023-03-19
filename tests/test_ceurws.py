'''
Created on 2023-03-18

@author: wf
'''
from ceurspt.ceurws import Volume,VolumeManager
from tests.basetest import Basetest
from pathlib import Path

class Test_CEURWS(Basetest):
    """
    Test the ceur-ws concepts
    """
    
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        script_path=Path(__file__)
        base_path=f"{script_path.parent.parent}/ceur-ws"
        self.vm=VolumeManager(base_path=base_path)
    
    def test_volume(self):
        """
        test instantiating a volume
        """
        vol=Volume()
        debug=self.debug
        if debug:
            print(vol)
        
    def test_fix_links(self):
        """
        test fixing the links
        """
        vol=self.vm.getVolume(3262)
        html=vol.getHtml()
        debug=self.debug
        debug=True
        if debug:
            print(html)
        
