'''
Created on 2023-03-18

@author: wf
'''
from ceurspt.ceurws import Volume
from tests.basetest import Basetest

class Test_CEURWS(Basetest):
    """
    Test the ceur-ws concepts
    """
    
    def test_volume(self):
        """
        test instantiating a volume
        """
        vol=Volume()
        print(vol)
