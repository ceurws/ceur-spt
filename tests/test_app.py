from fastapi.testclient import TestClient
from tests.basetest import Basetest
from ceurspt.webserver import WebServer
from pathlib import Path
import json

class Test_app(Basetest):
    """
    Test the application
    """
    
    def test_read_volume(self):
        """
        test reading a volume
        """
        script_path=Path(__file__)
        base_path=f"{script_path.parent.parent}/ceur-ws"
        self.ws = WebServer(base_path=base_path)
        client = TestClient(self.ws.app)
        response = client.get("/Vol-3262")
        self.assertEqual(200, response.status_code)
        json_data=response.json()
        debug=self.debug
        #debug=True
        if debug:
            print(json.dumps(json_data,indent=2,default=str))
        self.assertEqual({'number': 3262},json_data)
    