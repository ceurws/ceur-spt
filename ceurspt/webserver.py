'''
Created on 2023-03-17

@author: wf
'''
from fastapi import FastAPI
import uvicorn
 
class WebServer:
    """
    the webserver
    """ 

    def __init__(self):
        """
        constructor
        """
        self.app = FastAPI()

        @self.app.get("/Vol-{number}/")
        async def volume(number:int):
            return str(number)