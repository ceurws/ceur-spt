'''
Created on 2023-03-18

@author: wf
'''
import ceurspt.ceurws_base
import os
import re
from bs4 import BeautifulSoup

class Paper(ceurspt.ceurws_base.Paper):
    """
    a CEUR-WS Paper with it's behavior
    """
    
    def getPdf(self):
        """
        get the PDF file for this paper
        """
        volume=self.volume
        pdf=f"{volume.vm.base_path}/Vol-{volume.number}/paper{self.paper_number}.pdf"
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
                    href=href.replace("../ceur-ws.css","/ceur-ws.css")
                    href=re.sub(r'paper([0-9]+).pdf', fr"/Vol-{self.number}/paper\g<1>.pdf", href)
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

class VolumeManager():
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