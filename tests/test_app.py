from fastapi.testclient import TestClient
from tests.base_spt_test import BaseSptTest
from ceurspt.webserver import WebServer
import json

class Test_app(BaseSptTest):
    """
    Test the application
    """
    
    def setUp(self, debug=False, profile=True):
        BaseSptTest.setUp(self, debug=debug, profile=profile)
        static_directory=f"{self.script_path.parent.parent}/static"
        self.ws = WebServer(self.vm,self.pm,static_directory=static_directory)
        self.client = TestClient(self.ws.app)
        
    def checkResponse(self,path:str,status_code:int)->'Response':
        """
        check the response for the given path for the given status code
        
        Args:
            path(str): the path for the request
            status_code(int): the expected status code
            
        Returns:
            Response: the response received
        """
        response = self.client.get(path)
        self.assertEqual(status_code,response.status_code)
        return response
        
    def test_docs(self):
        """
        test the documentation handling
        """
        response=self.checkResponse("/docs",200)
        html=response.text
        debug=self.debug
        #debug=True
        if debug:
            print(html)
        self.assertTrue("SwaggerUIBundle" in html)
      
    
    def test_home(self):
        """
        test the home url
        """
        response = self.client.get("/")
        self.assertEqual(404, response.status_code)
        debug=self.debug
        debug=True
        if debug:
            print(response.text)
            
    def test_index(self):
        """
        test the index html file
        """
        response=self.checkResponse("/index.html", 200)
        html=response.text
        debug=True
        if debug:
            print(html)
    
    def test_read_volume(self):
        """
        test reading a volume
        """
       
        debug=self.debug
        #debug=True
        for ext,expected,check_json in [
            (".json",{'spt.number': 3262, "spt.acronym": "Wikidata 2022", "spt.title": "Proceedings of the 3rd Wikidata Workshop 2022"},True),
            ("","CEURVERSION=2020-0",False),
            (".html","CEURVERSION=2020-0",False)
        ]:
            response = self.checkResponse(f"/Vol-3262{ext}",200)
            if ext==".json":
                result=response.json()
                if debug:
                    print(json.dumps(result,indent=2,default=str))
            else:
                result=response.text
                pass
            if check_json:
                for key,value in expected.items():
                    self.assertTrue(key in result)
                    self.assertEqual(value,result[key])
            else:
                self.assertTrue(expected in result)
                
    def test_read_paper(self):
        """
        test reading the pdf for a paper
        """
        response = self.checkResponse(f"/Vol-3262/paper1.pdf",200)
        self.assertEqual(2509257,response.num_bytes_downloaded)
        pass
    