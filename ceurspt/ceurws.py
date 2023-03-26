'''
Created on 2023-03-18

@author: wf
'''
import ceurspt.ceurws_base
from ceurspt.version import Version
from datetime import datetime
import os
from bs4 import BeautifulSoup
import urllib.request
import json
from pathlib import Path
import dataclasses
import typing

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
    
    def getMergedDict(self)->str:
        """
        get the merged dict for this paper
        """
        my_dict=dataclasses.asdict(self)
        m_dict={
            "version.version": Version.version,
            "version.cm_url": Version.cm_url,
            "spt.html_url": f"/{self.id}.html"
        }
        for key,value in my_dict.items():
            m_dict[f"spt.{key}"]=value
        pdf_name=self.pdfUrl.replace("https://ceur-ws.org/","")
        if pdf_name in self.pm.paper_records_by_path:
            pdf_record=self.pm.paper_records_by_path[pdf_name]
            for key,value in pdf_record.items():
                m_dict[f"cvb.{key}"]=value
        pass
        return my_dict
    
    def paperLinkParts(self:int,inc:int=0):
        """
        a relative paper link
        """
        if inc>0:
            presymbol="⫸"
            postsymbol="" 
            paper=self.next()
        elif inc<0:
            presymbol=""
            postsymbol="⫷"
            paper=self.prev()
        else:
            presymbol=""
            postsymbol=""
            paper=self
        href=None
        text=None
        if paper:
            href=f"/{paper.id}.html"
            text=f"{presymbol}{paper.id}{postsymbol}"
        return href,text
    
    def paperScrollLinks(self)->str:
        """
        get the paper scroll links
        """
        scroll_links=""
        for inc in [-1,0,1]:
            href,text=self.paperLinkParts(inc)
            if href:
                scroll_links+=f"""<a href="{href}">{text}</a>"""
        return scroll_links
    
    def prev(self)->'Paper':
        """
        get the previous paper in this volume
        """
        return self.next(-1)
    
    def next(self,inc:int=1)->'Paper':
        """
        get the next paper in this volume with the given increment
        
        Args:
            inc(int): the increment +1 = next, -1 = prev
        """
        vol=self.volume
        paper=None
        if vol:
            next_index=self.paper_index+inc
            if next_index>=0 and next_index <len(vol.papers):
                paper=vol.papers[next_index]
        return paper
    
    def getIconBar(self,soup):
        """
        get my icon bar
        
        Parameters:
            soup: The BeautifulSoup object to use for creating new tags.
        """
        # create a list of icons to add to the div
        icon_list = [
            {
                "src": "/static/icons/32px-GROBID-icon.png", 
                "title": "GROBID metadata", 
                "link":f"/{self.id}.grobid", 
                # @TODO check existens of .grobid file
                "valid":True
            },
            {
                "src": "/static/icons/32px-JSON_vector_logo.svg.png", 
                "title": "JSON metadata", 
                "link":f"/{self.id}.json", 
                "valid":True
            }
        ]
        icon_tag=Volume.create_icon_bar(soup, icon_list=icon_list)
        return icon_tag
    
    def asHtml(self):
        """
        return an html response for this paper
        """
        soup=BeautifulSoup("<html></html>", 'html.parser')
        icon_bar=self.getIconBar(soup)
        content=f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta http-equiv="Content-type" content="text/html;charset=utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" type="text/css" href="/static/ceur-ws.css">
<title>{self.id} - {self.title}</title>
</head>
<body>
<table style="border: 0; border-spacing: 0; border-collapse: collapse; width: 95%">
<tbody><tr>
<td style="text-align: left; vertical-align: middle">
<a href="http://ceur-ws.org/"><div id="CEURWSLOGO"></div></a>
</td>
<td style="text-align: right; vertical-align: middle">
<div style="float:left" id="CEURCCBY"></div>
{Volume.volLink(self.volume.number,-1)}
<span class="CEURVOLNR">{Volume.volLink(self.volume.number)}</span>
{Volume.volLink(self.volume.number,+1)}<br>
<span class="CEURURN">urn:nbn:de:0074-{self.volume.number}-0</span>
<p class="unobtrusive copyright" style="text-align: justify">Copyright &copy; {self.volume.date[:4]} for
the individual papers by the papers' authors. 
Copyright &copy; <span class="CEURPUBYEAR">{self.volume.date[:4]}</span> for the volume
as a collection by its editors.
This volume and its papers are published under the
Creative Commons License Attribution 4.0 International
<A HREF="https://creativecommons.org/licenses/by/4.0/">(<span class="CEURLIC">CC BY 4.0</span>)</A>.</p>
</td>
</tr>
</tbody></table>
{str(icon_bar)}
<hr/>
{self.paperScrollLinks()}
<hr/>
<h1>{self.title}<h1>
<embed src="{self.pdfUrl}" style="width:100vw;height:100vh" type="application/pdf">
<body>
</body>
        """
        return content

class Volume(ceurspt.ceurws_base.Volume):
    """
    a CEUR-WS Volume with it's behavior
    """
    def __init__(self,**kwargs):
        ceurspt.ceurws_base.Volume.__init__(self,**kwargs)
        self.papers=[]
        
    def getMergedDict(self)->dict:
        """
        get my merged dict
        
        Returns:
            dict
        """
        my_dict=dataclasses.asdict(self)
        m_dict={
            "version.version": Version.version,
            "version.cm_url": Version.cm_url,
            "spt.html_url": f"/Vol-{self.number}.html"
        }
        for key,value in my_dict.items():
            m_dict[f"spt.{key}"]=value
        volrecord=self.vm.getVolumeRecord(self.number)
        for key,value in volrecord.items():
            if "." in key:
                m_dict[f"{key}"]=value
            else:
                m_dict[f"cvb.{key}"]=value
        return m_dict
        
    @classmethod
    def volLinkParts(cls,number:int,inc:int=0):
        """
        a relative volume link
        """
        if inc>0:
            presymbol="⫸"
            postsymbol="" 
        elif inc<0:
            presymbol=""
            postsymbol="⫷"
        else:
            presymbol=""
            postsymbol=""
        href=f"/Vol-{number+inc}.html"
        text=f"{presymbol}Vol-{number+inc}{postsymbol}"
        return href,text
    
    @classmethod
    def volLink(cls,number:int,inc:int=0)->str:
        """
        get a relative volume link
        
        Args:
            number(int): the volume number
            inc(int): the relative increment
            
        Returns(str):
            a relative volume link
        """
        href,text=cls.volLinkParts(number, inc)
        if number>0:
            link=f"""<a href="{href}">{text}</a>"""
        else:
            link=""
        return link
    
    @classmethod
    def volLink_soup_tag(cls,soup,number:int,inc:int=0)->str:
        """
        get a relative volume link as a soup tag
        
        Args:
            soup(BeautifulSoup): the soup
            number(int): the volume number
            inc(int): the relative increment
            
        Returns(str):
            a relative volume link
        """
        href,text=cls.volLinkParts(number, inc)
        link=soup.new_tag("a", href=href)
        link.string=text
        return link
        
    @classmethod
    def create_icon_bar(self,soup: BeautifulSoup, icon_list: typing.List[typing.Dict[str, str]],class_name: str="icon_list", ) -> "Tag":
        """
        Creates a new <div> tag with the specified class name and list of icons.
    
        Parameters:
            soup: The BeautifulSoup object to use for creating new tags.
            icon_list: The list of icons to add to the <div> tag. Each icon is represented as a
                dictionary with the following keys:
                    - src (str): The URL of the icon image file.
                    - title (str): The title text to use as a tooltip for the icon.
                    - link (str): The URL to link to when the icon is clicked.
            class_name: The name of the CSS class to apply to the <div> tag.
    
        Returns:
            Tag: The new <div> tag with the specified class name and list of icons.
        """
    
        # create a new div tag
        div_tag = soup.new_tag("div")
        
        div_tag.append(soup.new_tag("hr"))
    
        # add the specified class name to the div tag
        div_tag["class"] = [class_name]
    
        # iterate over the icon list and create a new tag for each icon
        for icon_data in icon_list:
            # create a new a tag for the link
            link_tag = soup.new_tag("a")
            link_tag["href"] = icon_data["link"]
            # open link in new tab
            link_tag["target"] = "_blank"
            if not icon_data["valid"]:
                link_tag["disabled"]="disabled"
    
            # create a new img tag for the icon
            icon_tag = soup.new_tag("img")
    
            # add the icon attributes to the img tag
            icon_tag["src"] = icon_data["src"]
            icon_tag["title"] = icon_data["title"]
    
            # append the icon tag to the link tag
            link_tag.append(icon_tag)
    
            # append the link tag to the div tag
            div_tag.append(link_tag)
    
        # return the div tag
        return div_tag
    
    def getIconBar(self,soup):
        """
        get my icon bar
        
        Parameters:
            soup: The BeautifulSoup object to use for creating new tags.
        """
        volume_record=self.vm.getVolumeRecord(self.number)
        for wd_key,attr in [("wd.event","wd_event"),("wd.eventSeries","wd_event_series")]:
            value=None
            if wd_key in volume_record:
                value=volume_record[wd_key]
                if value:
                    value=value.replace("http://www.wikidata.org/entity/","")
            setattr(self,attr,value)
        # create a list of icons to add to the div
        icon_list = [
            {
                "src": "/static/icons/32px-dblp-icon.png", 
                "title": "dblp",
                "link":f"https://dblp.org/rec/{self.dblp}",
                "valid":self.dblp 
            },
            {
                "src": "/static/icons/32px-DNB.svg.png",
                "title":"k10plus/DNB",
                "link":f"https://opac.k10plus.de/DB=2.299/PPNSET?PPN={self.k10plus}",
                "valid":self.k10plus 
            },
            {
                "src": "/static/icons/32px-Scholia_logo.svg.png", 
                "title": "Proceedings@scholia",
                "link":f"https://scholia.toolforge.org/venue/{self.wikidataid}", 
                "valid":self.wikidataid 
            },
            {
                "src": "/static/icons/32px-EventIcon.png", 
                "title": "Event@scholia",
                "link":f"https://scholia.toolforge.org/event/{self.wd_event}", 
                "valid":self.wd_event 
            },
            {
                "src": "/static/icons/32px-EventSeriesIcon.png", 
                "title": "EventSeries@scholia",
                "link":f"https://scholia.toolforge.org/event-series/{self.wd_event_series}", 
                "valid":self.wd_event_series 
            },
            {
                "src": "/static/icons/32px-Wikidata_Query_Service_Favicon_wbg.svg.png", 
                "title": "Proceedings@wikidata", 
                "link":f"https://www.wikidata.org/wiki/{self.wikidataid}", 
                "valid":self.wikidataid 
            },
            {
                "src": "/static/icons/32px-EventIcon.png", 
                "title": "Event@wikidata", 
                "link":f"https://www.wikidata.org/wiki/{self.wd_event}", 
                "valid":self.wd_event 
            },
            {
                "src": "/static/icons/32px-EventSeriesIcon.png", 
                "title": "EventSeries@wikidata", 
                "link":f"https://www.wikidata.org/wiki/{self.wd_event_series}", 
                "valid":self.wd_event_series 
            },
            {
                "src": "/static/icons/32px-JSON_vector_logo.svg.png", 
                "title": "JSON metadata", 
                "link":f"/Vol-{self.number}.json", 
                "valid":True
            },
            
        ]
        icon_tag=Volume.create_icon_bar(soup, icon_list=icon_list)
        return icon_tag
    
    def addPaper(self,paper:'Paper'):
        """
        add the given paper
        """
        # @TODO fixme to use LinkML generated code
        self.papers.append(paper)
        paper.paper_index=len(self.papers)-1
        
    def fix_element_tag(self,element,tag:str="href",ext:str=".pdf"):
        """
        fix the given element tag
        
        Args:
            tag(str): the tag to fix
            ext(str): the extension
        """
        org_tag_value=element[tag] 
        value=org_tag_value.replace("http://ceur-ws.org/","/")
        for file in ["ceur-ws.css","CEUR-WS-logo.png"]:
            value=value.replace(f"../{file}",f"/static/{file}")
        if ".pdf" in value:
            value=value.replace(".pdf",ext)
            value=f"/Vol-{self.number}/{value}"
            pass
        element[tag]=value
    
    def getHtml(self,ext:str=".pdf",fixLinks:bool=True)->str:
        """
        get my HTML content
        
        Args:
            ext(str): the extension to use for pdf page details
            fixLinks(bool): if True fix the links
        """
        index_path=f"{self.vol_dir}/index.html"
        try: 
            with open(index_path, 'r') as index_html:
                content = index_html.read()
                if fixLinks:
                    soup = BeautifulSoup(content, 'html.parser')
                    for element in soup.findAll(['link','a']):
                        self.fix_element_tag(element,tag="href",ext=ext)
                    for element in soup.findAll(['image']):
                        self.fix_element_tag(element, tag="src", ext=ext)
                    vol_tag = soup.find("span", class_="CEURVOLNR")
                    if vol_tag:
                        prev_link=Volume.volLink_soup_tag(soup, self.number, -1)
                        if prev_link:
                            vol_tag.insert_before(prev_link)
                        next_link=Volume.volLink_soup_tag(soup, self.number, +1)
                        if next_link:
                            vol_tag.insert_after(next_link)
                    first_hr=soup.find("hr")
                    if first_hr:
                        icon_bar=self.getIconBar(soup)
                        first_hr.insert_before(icon_bar)
                    content=soup.prettify( formatter="html" )
            return content
        except Exception as ex:
            err_html=f"""<span style="color:red">reading {index_path} for Volume {self.number} failed: {str(ex)}</span>"""
            return err_html
    
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
        
    def json_path(self,lod_name:str)->str:
        """
        get the json pasth for the given list of dicts name
        
        Args:
            lod_name(str): the name of the list of dicts cache to read
            
        Returns:
            str: the path to the list of dict cache
        """
        root_path=f"{Path.home()}/.ceurws"
        os.makedirs(root_path, exist_ok=True)
        json_path=f"{root_path}/{lod_name}.json"
        return  json_path
        
    def load_lod(self,lod_name:str)->list:
        """
        load my list of dicts
        
        Args:
            lod_name(str): the name of the list of dicts cache to read
            
        Returns:
            list: the list of dicts
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
        
        Args:
            lod_name(str): the name of the list of dicts cache to write
            lod(list): the list of dicts to write
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
        """
        get my volume by volume number
        
        Args:
            number(int): the volume to get
        """
        if number in self.volumes_by_number:
            return self.volumes_by_number[number]
        else:
            return None
        
    def getVolumeRecord(self,number:int):
        if number in self.volume_records_by_number:
            return self.volume_records_by_number[number]
        else:
            return None
        
    def getVolumes(self):
        """
        get my volumes
        """
        volume_lod=self.load_lod("volumes")
        proceedings_lod=self.load_lod("proceedings")
        self.volumes_by_number={}
        self.volume_records_by_number={}
        for volume_record in volume_lod:
            vol_number=volume_record["number"]
            self.volume_records_by_number[vol_number]=volume_record
            title=volume_record["title"]
            pubDate_str=volume_record["pubDate"]
            if pubDate_str:
                pubDate=datetime.fromisoformat(pubDate_str).date()
            else:
                pubDate=None
            acronym=volume_record["acronym"]
            volume=Volume(number=vol_number,title=title,date=pubDate,acronym=acronym)
            volume.vm=self
            volume.number=int(volume.number)
            vol_dir=f"{self.base_path}/Vol-{vol_number}"
            if os.path.isdir(vol_dir):
                volume.vol_dir=vol_dir
            else:
                volume.vol_dir=None
            self.volumes_by_number[vol_number]=volume
        for proc_record in proceedings_lod:
            number=proc_record["sVolume"]
            volume_record=self.volume_records_by_number[number]
            volume=self.volumes_by_number[number]
            for key,value in proc_record.items():
                volume_record[f"wd.{key}"]=value
            map_pairs=[
                ("item","wikidataid"),
                ("itemDescription","description"),
                ("dblpProceedingsId","dblp"),
                ("described_at_URL","url"),
                ("ppnId","k10plus"),
                ("URN_NBN","urn")
            ]
            for wd_id,attr in map_pairs:
                wd_key=f"wd.{wd_id}"
                if wd_key in volume_record:
                    value=volume_record[wd_key]
                    if isinstance(value,str):
                        value=value.replace("http://www.wikidata.org/entity/","")
                        value=value.replace("https://www.wikidata.org/wiki/","")
                    setattr(volume,attr,value)
                    pass
        
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
            paper.pm=self
        return paper
    
    def getPapers(self,vm:VolumeManager):
        """
        get all papers
        """
        paper_lod=self.load_lod("papers")
        self.papers_by_id={}
        self.paper_records_by_path={}
        self.papers_by_path={}
        for paper_record in paper_lod:
            pdf_name=paper_record["pdf_name"]
            volume_number=paper_record["vol_number"]
            volume=vm.getVolume(volume_number)
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
                if volume:
                    volume.addPaper(paper)
                self.papers_by_id[paper_record["id"]]=paper
                self.papers_by_path[pdf_path]=paper
                self.paper_records_by_path[pdf_path]=paper_record
            except Exception as ex:
                print(f"handling of Paper for pdfUrl '{pdf_url}' failed with {str(ex)}")
        