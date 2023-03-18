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
        vm=VolumeManager(base_path=base_path)
        self.ws = WebServer(vm)
        self.client = TestClient(self.ws.app)
    
    def test_home(self):
        """
        """
        response = self.client.get(f"/")
        self.assertEqual(404, response.status_code)
        debug=self.debug
        debug=True
        if debug:
            print(response)
    
    def test_read_volume(self):
        """
        test reading a volume
        """
       
        debug=self.debug
        #debug=True
        for ext,expected,equal in [
            (".json",{'number': 3262.0, 'title':None},True),
            ("","CEURVERSION=2020-0",False),
            (".html","CEURVERSION=2020-0",False)
        ]:
            response = self.client.get(f"/Vol-3262{ext}")
            self.assertEqual(200, response.status_code)
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
    