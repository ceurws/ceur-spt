"""
Created on 2023-03-17

@author: wf
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse,Response,RedirectResponse
from fastapi.staticfiles import StaticFiles
from ceurspt.ceurws import Volume,VolumeManager, Paper,PaperManager

class WebServer:
    """
    the webserver
    """

    def __init__(self,vm:VolumeManager,pm:PaperManager,static_directory:str="static"):
        """
        constructor
        
        Args:
            vm(VolumeManager): the volume manager to use
            pm(PaperManager): the paper manager to use
            static_directory(str): the directory for static html files to use
        """
        self.app = FastAPI()
        #https://fastapi.tiangolo.com/tutorial/static-files/
        self.app.mount("/static", StaticFiles(directory=static_directory), name="static")
        self.vm=vm
        self.pm=pm
    
        @self.app.get("/Vol-{number:int}/{pdf_name:str}.pdf")
        async def paperPdf(number:int,pdf_name:str):
            """
            get the PDF for the given paper
            """
            paper=self.getPaper(number,pdf_name)
            pdf=paper.getPdf()
            return FileResponse(pdf)
        
        @self.app.get("/Vol-{number:int}/{pdf_name}.json")
        async def paperJson(number:int,pdf_name:str):
            """
            get the json response for the given paper
            """
            paper=self.getPaper(number,pdf_name)
            paper_dict=paper.getMergedDict()
            return paper_dict
        
        @self.app.get("/Vol-{number:int}/{pdf_name}.html")
        async def paperHtml(number:int,pdf_name:str):
            """
            get the html response for the given paper
            """
            paper=self.getPaper(number,pdf_name)
            content=paper.asHtml()
            return HTMLResponse(content=content)
        
        @self.app.get("/Vol-{number:int}/{pdf_name}.txt")
        async def paperText(number:int,pdf_name:str):
            """
            get the text for the given paper
            """
            paper=self.getPaper(number,pdf_name)
            text=paper.getText()
            return PlainTextResponse(text)
        
        @self.app.get("/Vol-{number:int}/{pdf_name}.grobid")
        async def paperGrobidXml(number:int,pdf_name:str):
            """
            get the grobid XML for the given paper
            """
            paper=self.getPaper(number,pdf_name)
            xml=paper.getContentByPostfix(".tei.xml")
            return Response(content=xml, media_type="application/xml")
      
        @self.app.get("/Vol-{number:int}/{pdf_name}.cermine")
        async def paperCermineXml(number:int,pdf_name:str):
            """
            get the grobid XML for the given paper
            """
            paper=self.getPaper(number,pdf_name)
            xml=paper.getContentByPostfix(".cermine.xml")
            return Response(content=xml, media_type="application/xml")
    
        @self.app.get("/Vol-{number:int}.json")
        async def volumeJson(number: int):
            """
            Get metadata of volume by given id
            """
            vol=self.getVolume(number)
            if vol:
                return vol.getMergedDict()
            else:
                return { "error": f"unknown volume number {number}"}
            
        @self.app.get("/Vol-{number:int}")
        async def volumeHtmlWithPdf(number:int):
            """
            get html Response for the given volume by number
            displaying pdfs directly
            """
            return self.volumeHtml(number,ext=".pdf")
            
        @self.app.get("/Vol-{number:int}.html")
        async def volumeHtmlWithHtml(number:int):
            """
            get html Response for the given volume by number
            displaying pdfs embedded in html
            """
            return self.volumeHtml(number,ext=".html")
            
        @self.app.get("/")
        async def home():
            """
            Return the home 
            """
            url = "https://github.com/ceurws/ceur-spt"
            response = RedirectResponse(url=url,status_code=302)
            return response
        
    def volumeHtml(self,number:int,ext:str=".pdf"):
            """
            get html Response for the given volume by number
            """
            vol=self.getVolume(number)
            if vol:
                content=vol.getHtml(ext=ext,fixLinks=True)
                return HTMLResponse(content=content, status_code=200)
            else:
                return HTMLResponse(content=f"unknown volume number {number}",status_code=404)
        
    def getVolume(self,number:int)->Volume:
        """
        get the volume for the given number
        
        Args:
            number(int): the number of the volume to fetch
            
        Returns:
            Volume: the volume or None if the volume number is not known
        """
        vol=self.vm.getVolume(number)
        return vol
            
    def getPaper(self,number:int,pdf_name:str,exceptionOnFail:bool=True)->Paper:
        """
        get the paper for the given volume number and pdf_name
        
        Args:
            number(int): the number of the volume the paper is part of
            pdf_name(str): the pdf name of the paper
            exceptionOnFail(bool): if True raise an exception on failure
        
        Returns:
            Paper: the paper or None if the paper is not found
        """
        paper=self.pm.getPaper(number, pdf_name)
        if paper is None and exceptionOnFail:
            raise HTTPException(status_code=404, detail=f"paper Vol-{number}/{pdf_name}.pdf not found")    
        return paper

