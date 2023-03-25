'''
Created on 2023-03-18

@author: wf
'''
from ceurspt.ceurws import Volume,VolumeManager
from tests.base_spt_test import BaseSptTest
from pathlib import Path

class Test_CEURWS(BaseSptTest):
    """
    Test the ceur-ws concepts
    """
    
    def setUp(self, debug=False, profile=True):
        BaseSptTest.setUp(self, debug=debug, profile=profile)
    
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
        #debug=True
        if debug:
            print(html)
        self.assertTrue("""<link href="/static/ceur-ws.css" rel="stylesheet" type="text/css"/>""" in html)
            
    def test_getText(self):
        """
        get the full text of a paper
        """
        paper=self.pm.getPaper(3262,"paper1")
        text=paper.getText()
        debug=self.debug
        #debug=True
        if debug:
            print(text)
        self.assertTrue("Formalizing Property Constraints in Wikidata" in text)
    
        
    def test_asHtml(self):
        """
        test getting html for a paper
        """
        paper=self.pm.getPaper(3262,"paper2")
        prev_paper=paper.prev()
        next_paper=paper.next()
        html=paper.asHtml()
        debug=self.debug
        debug=True
        if debug:
            print(html)
        self.assertTrue("Formalizing Property Constraints in Wikidata" in html)
        
        
