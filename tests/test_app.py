from fastapi.testclient import TestClient
from tests.basetest import Basetest
from ceurspt.webserver import WebServer
from pathlib import Path
import json
from ceurspt.ceurws import VolumeManager

class Test_app(Basetest):
    """
    Test the application
    """
    
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        script_path=Path(__file__)
        base_path=f"{script_path.parent.parent}/ceur-ws"
        static_directory=f"{script_path.parent.parent}/static"
        vm=VolumeManager(base_path=base_path)
        self.ws = WebServer(vm,static_directory=static_directory)
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
    
    def test_read_volume(self):
        """
        test reading a volume
        """
       
        debug=self.debug
        #debug=True
        for ext,expected,equal in [
            (".json",{'number': 3262, 'title':None},True),
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
            if equal:
                self.assertEqual(expected,result)
            else:
                self.assertTrue(expected in result)
                
    def test_read_paper(self):
        """
        test reading the pdf for a paper
        """
        response = self.checkResponse(f"/Vol-3262/paper1.pdf",200)
        self.assertEqual(2509257,response.num_bytes_downloaded)
        pass
    