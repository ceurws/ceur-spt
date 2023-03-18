'''
Created on 2023-03-18

@author: wf
'''
import ceurspt.ceurws_base
import os

class Volume(ceurspt.ceurws_base.Volume):
    """
    a CEUR-WS Volume with it's behavior
    """
    
    def getHtml(self)->str:
        """
        get my HTML content
        """
        index_path=f"{self.vol_dir}/index.html"
        with open(index_path, 'r') as index_html:
            content = index_html.read()
            return content

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
            vol.vm=self
            vol.vol_dir=vol_dir
            return vol
        else:
            return None