"""
Created on 2023-03-17

@author: wf
"""
from fastapi import FastAPI
import os

class WebServer:
    """
    the webserver
    """

    def __init__(self,base_path:str):
        """
        constructor
        """
        self.app = FastAPI()
        self.base_path=base_path

        @self.app.get("/Vol-{number}/")
        async def volume(number: int):
            """
            Get metadata of volume by given id
            """
            vol_dir=f"{self.base_path}/Vol-{number}"
            if os.path.isdir(vol_dir):
                return { "number":number }
            else:
                return { "error": f"unknown volume number {number}"}
