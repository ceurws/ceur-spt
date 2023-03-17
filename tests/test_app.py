from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.basetest import Basetest
from ceurspt.webserver import WebServer

class Test_app(Basetest):
    
    def test_read_main(self):
        self.ws = WebServer()
        client = TestClient(self.ws.app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"msg": "Hello World"}