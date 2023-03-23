'''
Created on 2023-03-18

@author: wf
'''
import ceurspt.ceurws_base
from ceurspt.ceurws_base import URI
import os
import re
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
        volume=self.volume
        for sep in ["","-","0","-0"]:
            base_path=f"{volume.vm.base_path}/Vol-{volume.number}/paper{sep}{self.paper_number}"
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
                    href=re.sub(r'paper[\-]?([0-9]+).pdf', fr"/Vol-{self.number}/paper-\g<1>.pdf", href)
                    pass
                    a['href']=href
                content=soup.prettify( formatter="html" )
            return content
        
    def getPaper(self,paper_number:int):
        """
        get the paper with the given number
        
        Args:
            paper_number(int): the number of the paper
        """
        paper=Paper()
        paper.paper_number=paper_number
        paper.volume=self
        return paper
    
class JsonCacheManager():
    """
    a json based cache manager
    """
    def __init__(self,base_url:str="http://cvb.bitplan.com"):
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
    def __init__(self,base_path:str):
        """
        initialize me with the given base_path
    
        Args:
            base_path(str): the path to my files
        """
        self.base_path=base_path
        
    def getVolumes(self):
        """
        get my volumes
        """
        volume_lod=self.load_lod("volumes")
        self.volumes_by_number={}
        for volume_record in volume_lod:
            vol_number=volume_record["number"]
            title=volume_record["title"]
            volume=Volume(number=vol_number,title=title)
            self.volumes_by_number[vol_number]=volume
        
    def getVolume(self,number:int)->Volume:
        """
        get the volume with the given number
        
        Args:
            number(int): the volume to get
            
        Returns:
            Volume: the volume
        """       
        vol_dir=f"{self.base_path}/Vol-{number}"
        if os.path.isdir(vol_dir):
            vol=Volume(number=number)
            vol.number=int(vol.number)
            vol.vm=self
            vol.vol_dir=vol_dir
            return vol
        else:
            return None
        
class PaperManager(JsonCacheManager):
    """
    manage all papers
    """
    
    def getPapers(self,vm:VolumeManager):
        """
        get all papers
        """
        paper_lod=self.load_lod("papers")
        self.papers_by_id={}
        for paper_record in paper_lod:
            pdf_name=paper_record["pdf_name"]
            volume_number=paper_record["vol_number"]
            volume=vm.volumes_by_number[volume_number]
            pdf_url=f"https://ceur-ws.org/Vol-{volume_number}/{pdf_name}"
            paper=Paper(
                id=paper_record["id"],
                title=paper_record["title"],
                authors=paper_record["authors"],
                pdfUrl=pdf_url,
                volume=volume
            )
            self.papers_by_id[paper_record["id"]]=paper