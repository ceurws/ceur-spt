'''
Created on 2023-03-18

@author: wf
'''
from ceurspt.ceurws import Volume
from tests.base_spt_test import BaseSptTest
import json

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
        
    def test_volume_record(self):
        """
        test json
        """
        vol_record=self.vm.getVolumeRecord(3262)
        debug=True
        if debug:
            print(json.dumps(vol_record,indent=2))
            
    def test_volume_as_smw_markup(self):
        """
        https://github.com/ceurws/ceur-spt/issues/21
        """
        volume=self.vm.getVolume(3262)
        markup=volume.as_smw_markup()
        debug=self.debug
        #debug=True
        if debug:
            print(markup)
        self.assertTrue("|wikidataid=Q115053286" in markup)
    
    def test_volume_as_html(self):
        """
        test getting html for a volume
        """
        volume=self.vm.getVolume(3262)
        html=volume.getHtml()
        debug=self.debug
        debug=True
        if debug:
            print(html)
        self.assertTrue("Vol-3261⫷" in html)
        self.assertTrue("⫸Vol-3263" in html)
        
    def test_volume_as_merged_dict(self):
        """
        test getting merged dict for a volume
        """
        volume=self.vm.getVolume(3262)
        m_dict=volume.getMergedDict()
        debug=self.debug
        debug=True
        if debug:
            print(json.dumps(m_dict,indent=2))        

    def test_paper_as_html(self):
        """
        test getting html for a paper
        """
        paper=self.pm.getPaper(3262,"paper2")
        prev_paper=paper.prev()
        self.assertEqual(1,prev_paper.paper_index)
        next_paper=paper.next()
        self.assertEqual(3,next_paper.paper_index)
        html=paper.asHtml()
        debug=self.debug
        debug=True
        if debug:
            print(html)
        scroll_link="""<a href="/Vol-3262/paper1.html">Vol-3262/paper1⫷</a><a href="/Vol-3262/paper2.html">Vol-3262/paper2</a><a href="/Vol-3262/paper3.html">⫸Vol-3262/paper3</a>"""
        self.assertTrue("Towards improving Wikidata reuse with emerging patterns" in html)
        self.assertTrue(scroll_link in html)
        
    def test_author_bar(self):
        """
        test getting author bar html for a paper
        """
        paper=self.pm.getPaper(3262,"paper2")
        author_bar=paper.getAuthorBar()
        debug=self.debug
        debug=True
        if debug:
            print(author_bar)
        self.assertTrue("Paul Groth" in author_bar)
        self.assertTrue("0000-0003-0183-6910" in author_bar)
    
        
    def test_paper_as_merged_json(self):
        """
        test getting merged json for a paper
        """
        paper=self.pm.getPaper(3262, "paper1")
        paper_dict=paper.getMergedDict()
        debug=True
        if debug:
            print(json.dumps(paper_dict,indent=2))
            
    def test_paper_as_quickstatements(self):
        """
        https://github.com/ceurws/ceur-spt/issues/20
        """
        paper=self.pm.getPaper(3262, "paper1")
        qs=paper.as_quickstatements()
        debug=self.debug
        debug=True
        if debug:
            print(qs)
            
    def test_paper_as_smw_markup(self):
        """
        https://github.com/ceurws/ceur-spt/issues/22
        """
        paper=self.pm.getPaper(3262, "paper1")
        markup=paper.as_smw_markup()
        debug=self.debug
        debug=True
        if debug:
            print(markup)
        self.assertTrue("|dblpUrl=https://dblp.org/rec/conf/semweb/FerrantiPSA22" in markup)
        

    def test_get_empty_volume_page(self):
        """
        tests get_empty_volume_page
        """
        vol = self.vm.getVolume(3262)
        content = vol.get_empty_volume_page()
        self.assertIn("Vol-3261", content)
        self.assertIn("Vol-3262", content)
        self.assertIn("Vol-3263", content)
