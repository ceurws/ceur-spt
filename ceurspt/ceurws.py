'''
Created on 2023-03-18

@author: wf
'''
import ceurspt.ceurws_base
from datetime import datetime
import os
from bs4 import BeautifulSoup
import urllib.request
import json
from pathlib import Path

class Paper(ceurspt.ceurws_base.Paper):
    """
    a CEUR-WS Paper with it's behavior
    """
    
    def getBasePath(self)->str:
        """
        get the base path to my files
        """
        if self.pdfUrl:
            base_path=self.pdfUrl.replace("https://ceur-ws.org/","")
            base_path=base_path.replace(".pdf","")
            base_path=f"{self.volume.vm.base_path}/{base_path}"
            if os.path.isfile(f"{base_path}.pdf"):
                return base_path
        return None
    
    def getContentByPostfix(self,postfix:str)->str:
        """
        get the content for the given postfix
        
        Args:
            postfix(str): the postfix to read
        """
        base_path=self.getBasePath()
        if base_path is None:
            return None
        text_path=f"{base_path}{postfix}"
        with open(text_path, 'r') as text_file:
            content = text_file.read()
        return content
    
    def getText(self)->str:
        """
        get the plain text content of this paper
        """
        text=self.getContentByPostfix("-content.txt")
        return text
        
    def getPdf(self):
        """
        get the PDF file for this paper
        """
        base_path=self.getBasePath()
        pdf=f"{base_path}.pdf"
        return pdf

class Volume(ceurspt.ceurws_base.Volume):
    """
    a CEUR-WS Volume with it's behavior
    """
    
    def getHtml(self,fixLinks:bool=True)->str:
        """
        get my HTML content
        
        Args:
            fixLinks(bool): if True fix the links
        """
        index_path=f"{self.vol_dir}/index.html"
        with open(index_path, 'r') as index_html:
            content = index_html.read()
            if fixLinks:
                soup = BeautifulSoup(content, 'html.parser')
                for a in soup.findAll(['link','a']):
                    ohref=a['href'] 
                    # .replace("google", "mysite")
                    href=ohref.replace("http://ceur-ws.org/","/")
                    href=href.replace("../ceur-ws.css","/static/ceur-ws.css")
                    if ".pdf" in href:
                        href=f"/Vol-{self.number}/{href}"
                    pass
                    a['href']=href
                content=soup.prettify( formatter="html" )
            return content
    
class JsonCacheManager():
    """
    a json based cache manager
    """
    def __init__(self,base_url:str="http://cvb.bitplan.com"):
        """
        constructor
        
        base_url(str): the base url to use for the json provider
        """
        self.base_url=base_url
        
    def json_path(self,lod_name:str):
        root_path=f"{Path.home()}/.ceurws"
        os.makedirs(root_path, exist_ok=True)
        json_path=f"{root_path}/{lod_name}.json"
        return  json_path
        
    def load_lod(self,lod_name:str)->list:
        """
        load my list of dicts
        """
        json_path=self.json_path(lod_name)
        if os.path.isfile(json_path):
            with open(json_path) as json_file:
                lod = json.load(json_file)
        else:
            url=f"{self.base_url}/{lod_name}.json"
            with urllib.request.urlopen(url) as source:
                lod = json.load(source)
        return lod
    
    def store(self,lod_name:str,lod:list):
        """
        store my list of dicts
        """
        with open(self.json_path(lod_name), 'w') as json_file:
            json.dump(lod, json_file)
    

            pass

class VolumeManager(JsonCacheManager):
    """
    manage all volumes
    """
    def __init__(self,base_path:str,base_url=str):
        """
        initialize me with the given base_path
    
        Args:
            base_path(str): the path to my files
            base_url(str): the url of the RESTFul metadata service
        """
        JsonCacheManager.__init__(self,base_url=base_url)
        self.base_path=base_path
        
    def getVolume(self,number:int):
        if number in self.volumes_by_number:
            return self.volumes_by_number[number]
        else:
            return None
        
    def getVolumes(self):
        """
        get my volumes
        """
        volume_lod=self.load_lod("volumes")
        self.volumes_by_number={}
        for volume_record in volume_lod:
            vol_number=volume_record["number"]
            title=volume_record["title"]
            pubDate_str=volume_record["pubDate"]
            if pubDate_str:
                pubDate=datetime.fromisoformat(pubDate_str).date()
            else:
                pubDate=None
            acronym=volume_record["acronym"]
            volume=Volume(number=vol_number,title=title,date=pubDate,acronym=acronym)
            volume.vm=self
            vol_dir=f"{self.base_path}/Vol-{vol_number}"
            if os.path.isdir(vol_dir):
                volume.vol_dir=vol_dir
            else:
                volume.vol_dir=None
            self.volumes_by_number[vol_number]=volume
        
class PaperManager(JsonCacheManager):
    """
    manage all papers
    """
    
    def __init__(self,base_url:str):
        """
        constructor
        
        Args:
            base_url(str): the url of the RESTFul metadata service
        """
        JsonCacheManager.__init__(self, base_url)
        
    def getPaper(self,number:int,pdf_name:str):
        """
        get the paper with the given number and pdf name
    
        Args:
            number(int): the number of the volume the paper is part of
            pdf_name(str): the pdf name of the paper
            exceptionOnFail(bool): if True raise an exception on failure
        
        Returns:
            Paper: the paper or None if the paper is not found
        """
        pdf_path=f"Vol-{number}/{pdf_name}.pdf"
        paper=None
        if pdf_path in self.papers_by_path:
            paper=self.papers_by_path[pdf_path]
        return paper
    
    def getPapers(self,vm:VolumeManager):
        """
        get all papers
        """
        paper_lod=self.load_lod("papers")
        self.papers_by_id={}
        self.papers_by_path={}
        for paper_record in paper_lod:
            pdf_name=paper_record["pdf_name"]
            volume_number=paper_record["vol_number"]
            volume=vm.volumes_by_number[volume_number]
            #pdf_url=f"https://ceur-ws.org/Vol-{volume_number}/{pdf_name}"
            pdf_path=f"Vol-{volume_number}/{pdf_name}"
            pdf_url=f"https://ceur-ws.org/{pdf_path}"
            try:
                paper=Paper(
                    id=paper_record["id"],
                    title=paper_record["title"],
                    #authors=paper_record["authors"],
                    pdfUrl=pdf_url,
                    volume=volume
                )
                self.papers_by_id[paper_record["id"]]=paper
                self.papers_by_path[pdf_path]=paper
            except Exception as ex:
                print(f"constructor for Paper for pdfUrl '{pdf_url}' failed with {str(ex)}")