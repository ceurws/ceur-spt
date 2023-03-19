"""
Created on 2023-03-17

@author: wf
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse,Response,RedirectResponse
from fastapi.staticfiles import StaticFiles
from ceurspt.ceurws import VolumeManager
import dataclasses

class WebServer:
    """
    the webserver
    """

    def __init__(self,vm:VolumeManager,static_directory:str="static"):
        """
        constructor
        
        Args:
            vm(VolumeManager): the volume manager to use
            static_directory(str): the directory for static html files to use
        """
        self.app = FastAPI()
        #https://fastapi.tiangolo.com/tutorial/static-files/
        self.app.mount("/static", StaticFiles(directory=static_directory), name="static")
        self.vm=vm
        
    
        @self.app.get("/Vol-{number:int}/paper{paper_number:int}.pdf")
        async def paperPdf(number:int,paper_number:int):
            """
            get the PDF for the given paper
            """
            vol=self.vm.getVolume(number)
            paper=vol.getPaper(paper_number)
            pdf=paper.getPdf()
            return FileResponse(pdf)
        
        @self.app.get("/Vol-{number:int}/paper{paper_number:int}.txt")
        async def paperText(number:int,paper_number:int):
            """
            get the text for the given paper
            """
            vol=self.vm.getVolume(number)
            paper=vol.getPaper(paper_number)
            text=paper.getText()
            return PlainTextResponse(text)
        
        @self.app.get("/Vol-{number:int}/paper{paper_number:int}.grobid")
        async def paperGrobidXml(number:int,paper_number:int):
            """
            get the grobid XML for the given paper
            """
            vol=self.vm.getVolume(number)
            paper=vol.getPaper(paper_number)
            xml=paper.getContentByPostfix(".xml")
            return Response(content=xml, media_type="application/xml")
      
        @self.app.get("/Vol-{number:int}/paper{paper_number:int}.cermine")
        async def paperCermineXml(number:int,paper_number:int):
            """
            get the grobid XML for the given paper
            """
            vol=self.vm.getVolume(number)
            paper=vol.getPaper(paper_number)
            xml=paper.getContentByPostfix("-cermine.xml")
            return Response(content=xml, media_type="application/xml")
            
    
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
                content=vol.getHtml(fixLinks=True)
                return HTMLResponse(content=content, status_code=200)
            else:
                return HTMLResponse(content=f"unknown volume number {number}",status_code=404)
            
        @self.app.get("/")
        async def home():
            """
            Return the home 
            """
            url = "https://github.com/ceurws/ceur-spt"
            response = RedirectResponse(url=url,status_code=302)
            return response

