"""
Created on 2023-03-17

@author: wf
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from ceurspt.ceurws import VolumeManager
import dataclasses

class WebServer:
    """
    the webserver
    """

    def __init__(self,vm:VolumeManager):
        """
        constructor
        """
        self.app = FastAPI()
        self.vm=vm
        
    
        @self.app.get("/Vol-{number:int}.json")
        async def volumeJson(number: int):
            """
            Get metadata of volume by given id
            """
            vol=self.vm.getVolume(number)
            if vol:
                return dataclasses.asdict(vol)
            else:
                return { "error": f"unknown volume number {number}"}
            
        @self.app.get("/Vol-{number:int}")
        @self.app.get("/Vol-{number:int}.html")
        async def volumeHtml(number:int):
            """
            get html Response for the given volume by number
            """
            vol=self.vm.getVolume(number)
            if vol:
                content=vol.getHtml()
                return HTMLResponse(content=content, status_code=200)
            else:
                return HTMLResponse(content=f"unknown volume number {number}",status_code=404)
            
        @self.app.get("/")
        async def home():
            """
            Return the home 
            """
            url = "https://github.com/ceurws/ceur-spt"
            response = RedirectResponse(url=url)
            return response

