"""
Created on 2023-03-17

@author: wf
"""
from fastapi import FastAPI


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
        async def volume(number: int):
            """
            Get metadata of volume by given id
            """
            return str(number)
