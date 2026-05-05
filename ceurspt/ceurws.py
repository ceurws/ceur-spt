"""
Created on 2023-03-18

@author: wf
"""

import dataclasses
import json
import logging
import os
import typing
import urllib.error
import urllib.request
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Dict, List, Optional

import orjson
from bs4 import BeautifulSoup, Tag

import ceurspt.ceurws_base
import ceurspt.models.dblp
from ceurspt.dataclass_util import DataClassUtil
from ceurspt.profiler import Profiler
from ceurspt.version import Version


logger = logging.getLogger(__name__)


class Scholar(ceurspt.models.dblp.DblpScholar):
    """
    a scholar
    """


class Paper(ceurspt.ceurws_base.Paper):
    """
    a CEUR-WS Paper with it's behavior
    """

    def getBasePath(self) -> Optional[str]:
        """
        get the base path to my files
        """
        if self.pdfUrl:
            base_path = self.pdfUrl.replace("https://ceur-ws.org/", "")
            base_path = base_path.replace(".pdf", "")
            base_path = f"{self.volume.vm.base_path}/{base_path}"
            if os.path.isfile(f"{base_path}.pdf"):
                return base_path
        return None

    def getContentPathByPostfix(self, postfix: str):
        """
        get the content path for the given postfix

        Args:
            postfix(str): the postfix to read

        Returns:
            str: the context path
        """
        base_path = self.getBasePath()
        if base_path is None:
            return None
        text_path = f"{base_path}{postfix}"
        if os.path.isfile(text_path):
            return text_path
        else:
            return None

    def getContentByPostfix(self, postfix: str) -> str:
        """
        get the content for the given postfix

        Args:
            postfix(str): the postfix to read

        Returns:
            str: the context
        """
        text_path = self.getContentPathByPostfix(postfix)
        content = None
        if text_path:
            with open(text_path, "r", encoding="utf-8") as text_file:
                content = text_file.read()
        return content

    def getText(self) -> str:
        """
        get the plain text content of this paper
        """
        text = self.getContentByPostfix("-content.txt")
        return text

    def getPdf(self):
        """
        get the PDF file for this paper
        """
        base_path = self.getBasePath()
        pdf = f"{base_path}.pdf"
        return pdf

    def getMergedDict(self) -> dict:
        """
        get the merged dict for this paper
        """
        my_dict = dataclasses.asdict(self)
        m_dict = {
            "version.version": Version.version,
            "version.cm_url": Version.cm_url,
            "spt.html_url": f"/{self.id}.html",
        }
        for key, value in my_dict.items():
            m_dict[f"spt.{key}"] = value
        pdf_name = self.pdfUrl.replace("https://ceur-ws.org/", "")
        if pdf_name in self.pm.paper_records_by_path:
            pdf_record = self.pm.paper_records_by_path[pdf_name]
            for key, value in pdf_record.items():
                m_dict[f"cvb.{key}"] = value
        if pdf_name in self.pm.paper_dblp_by_path:
            dblp_record = self.pm.paper_dblp_by_path[pdf_name]
            for key, value in dblp_record.items():
                m_dict[f"dblp.{key}"] = value
        return m_dict

    def as_wb_dict(self) -> dict:
        """
        wb create-entity '{"labels":{"en":"a label","fr":"un label"},"descriptions":{"en":"some description","fr":"une description"},"claims":{"P1775":["Q3576110","Q12206942"],"P2002":"bulgroz"}}'
        """
        # Sanitize title for Wikibase: collapse any internal whitespace run
        # (spaces, tabs, newlines, vertical whitespace) to a single space and
        # strip leading/trailing whitespace. Wikibase rejects monolingual-text
        # / label values with leading or trailing whitespace. See issue #24.
        title = " ".join(self.title.split())
        wb = {
            "labels": {"en": title},
            "descriptions": {
                "en": f"scientific paper published in CEUR-WS Volume {self.volume.number}"
            },
            "claims": {
                # P31  :instance of  Q13442814:scholarly article
                "P31": "Q13442814",
                #  P1433: published in
                "P1433": self.volume.wikidataid,
                # P1476:title
                "P1476": {"text": title, "language": "en"},
                # P407 :language of work or name  Q1860:English
                "P407": "Q1860",
                #  P953 :full work available at URL
                "P953": self.pdfUrl,
                # P50: author, P1545: series ordinal
                "P50": [],
                # P2093: author name string, P1545: series ordinal
                "P2093": [],
            },
        }
        author_claims = wb["claims"]["P50"]
        author_name_claims = wb["claims"]["P2093"]
        authors = self.getAuthors()
        for index, author in enumerate(authors):
            if not author.wikidata_id:
                author_name_claims.append(
                    {"value": author.name, "qualifiers": {"P1545": f"{index+1}"}}
                )
            else:
                author_claims.append(
                    {"value": author.wikidata_id, "qualifiers": {"P1545": f"{index+1}"}}
                )
        return wb

    def as_wbi_cli_text(self, qid: str) -> str:
        """
        Generates a series of Wikibase CLI command strings to add claims to the entity
        represented by this paper, based on the provided QID.

        Args:
            qid (str): The QID of the Wikibase item to which the claims will be added.

        Returns:
            str: A string containing all the 'wb add-claim' commands separated by newlines.
        """
        # Get the dictionary representation of the paper
        wb_dict = self.as_wb_dict()

        # Initialize an empty list to hold all commands
        cli_commands = []

        # Iterate through each claim to create a separate wb add-claim command
        for prop, value in wb_dict["claims"].items():
            # Handle different structures in claims (e.g., simple vs. complex with qualifiers)
            if isinstance(
                value, list
            ):  # Expecting a list of values (or complex value structures)
                for val in value:
                    # Convert value to a JSON string and escape quotes for command line
                    val_json = json.dumps(val).replace('"', '\\"')
                    cli_commands.append(f'wb add-claim {qid} {prop} "{val_json}"')
            else:  # A single value or simple structure
                # Convert value to a JSON string and escape quotes for command line
                value_json = json.dumps(value).replace('"', '\\"')
                cli_commands.append(f'wb add-claim {qid} {prop} "{value_json}"')

        # Combine all commands into a single string separated by newlines
        cli = "\n".join(cli_commands)
        return cli

    def as_quickstatements(self) -> str:
        """
        return my quickstatements
        """
        self.getMergedDict()
        if self.volume is None:
            raise ValueError(
                f"Paper {self.id!r} has no associated volume; cannot generate quickstatements."
            )
        paper_date_str = self.volume.date
        paper_date = datetime.strptime(paper_date_str, "%Y-%m-%d")
        qs_date = f"+{paper_date.isoformat(sep='T',timespec='auto')}Z/11"
        qs = f"""# created by {__file__}
CREATE
# P31  :instance of  Q13442814:scholarly article
LAST|P31|Q13442814
# P1433: published in 
LAST|P1433|{self.volume.wikidataid}
# english label
LAST|Len|"{self.title}"
# english description
LAST|Den|"scientific paper published in CEUR-WS Volume {self.volume.number}"
# P1476:title
LAST|P1476|en:"{self.title}"
# P407 :language of work or name  Q1860:English
LAST|P407|Q1860
# P953 :full work available at URL
LAST|P953|"{self.pdfUrl}"
# P577 :publication date
LAST|P577|{qs_date}
"""
        # @TODO pages ...
        authors = self.getAuthors()
        for index, author in enumerate(authors):
            if not author.wikidata_id:
                qs += f"""# P2093: author name string, P1545: series ordinal
LAST|P2093|"{author.name}"|P1545|"{index+1}"
"""
            else:
                qs += f"""# P50: author, P1545: series ordinal
LAST|P50|{author.wikidata_id}|P1545|"{index+1}"       
"""
            pass
        return qs

    def as_smw_markup(self) -> str:
        """
        return my semantic mediawiki markup

        Returns:
            str: the smw markup for this paper
        """
        m_dict = self.getMergedDict()
        self.authors = m_dict["cvb.authors"]
        if "dblp.dblp_publication_id" in m_dict:
            self.dblpUrl = m_dict["dblp.dblp_publication_id"]
        markup = f"""=Paper=
{{{{Paper
|id={self.id}
|storemode=property
|title={self.title}
|pdfUrl={self.pdfUrl}
|volume=Vol-{self.volume.number}
"""
        for attr in ["authors", "wikidataid", "dblpUrl"]:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if value:
                    markup += f"|{attr}={value}\n"
        markup += f"""}}}}
=={self.title}==
<pdf width="1500px">{self.pdfUrl}</pdf>
<pre>
{self.getText()}
</pre>
        """
        return markup

    def getAuthorIndex(self, name: str, authors: typing.List[str]):
        """
        get the author index
        """
        for i, aname in enumerate(authors):
            if name.lower().startswith(aname.lower()):
                return i
        # if not found put at end
        return len(authors) + 1

    def getAuthors(self) -> typing.List[Scholar]:
        """
        get my authors

        Returns:
            list: a list of Scholars
        """
        m_dict = self.getMergedDict()
        author_names = m_dict["cvb.authors"].split(",")
        if "dblp.authors" in m_dict:
            authors = []
            dblp_author_records = m_dict["dblp.authors"]
            for dblp_author_record in dblp_author_records:
                author = DataClassUtil.dataclass_from_dict(Scholar, dblp_author_record)
                authors.append(author)
                author.index = self.getAuthorIndex(author.label, author_names)
                if author.index < len(author_names):
                    author.name = author_names[author.index]
                else:
                    author.name = author.label
            sorted_authors = sorted(authors, key=lambda author: author.index)
        else:
            sorted_authors = []
            for author_name in author_names:
                scholar = Scholar(dblp_author_id=None, label=author_name)
                scholar.name = author_name
                sorted_authors.append(scholar)
        return sorted_authors

    def getAuthorBar(self):
        """
        show the authors of this paper
        """
        authors = self.getAuthors()
        html = ""
        for author in authors:
            icon_list = [
                {
                    "src": "/static/icons/32px-dblp-icon.png",
                    "title": "dblp",
                    "link": f"{author.dblp_author_id}",
                    "valid": author.dblp_author_id,
                },
                {
                    "src": "/static/icons/32px-ORCID-icon.png",
                    "title": "ORCID",
                    "link": f"https://orcid.org/{author.orcid_id}",
                    "valid": author.orcid_id,
                },
                {
                    "src": "/static/icons/32px-DNB.svg.png",
                    "title": "DNB",
                    "link": f"https://d-nb.info/gnd/{author.gnd_id}",
                    "valid": author.gnd_id,
                },
                {
                    "src": "/static/icons/32px-Scholia_logo.svg.png",
                    "title": "Author@scholia",
                    "link": f"https://scholia.toolforge.org/author/{author.wikidata_id}",
                    "valid": author.wikidata_id,
                },
                {
                    "src": "/static/icons/32px-Wikidata_Query_Service_Favicon_wbg.svg.png",
                    "title": "Author@wikidata",
                    "link": f"https://www.wikidata.org/wiki/{author.wikidata_id}",
                    "valid": author.wikidata_id,
                },
            ]
            soup = BeautifulSoup("<html></html>", "html.parser")
            link_tags = Volume.create_icon_list(soup, icon_list)
            red = (
                not author.wikidata_id
                and not author.dblp_author_id
                and not author.gnd_id
                and not author.orcid_id
            )
            style = "color:red" if red else ""
            html += f"""<span style="{style}">{author.label}"""
            for link_tag in link_tags:
                html += str(link_tag)
            html += "</span>"
            pass
        return html

    def paperLinkParts(self: int, inc: int = 0):
        """
        a relative paper link
        """
        if inc > 0:
            presymbol = "⫸"
            postsymbol = ""
            paper = self.next()
        elif inc < 0:
            presymbol = ""
            postsymbol = "⫷"
            paper = self.prev()
        else:
            presymbol = ""
            postsymbol = ""
            paper = self
        href = None
        text = None
        if paper:
            href = f"/{paper.id}.html"
            text = f"{presymbol}{paper.id}{postsymbol}"
        return href, text

    def paperScrollLinks(self) -> str:
        """
        get the paper scroll links
        """
        scroll_links = ""
        for inc in [-1, 0, 1]:
            href, text = self.paperLinkParts(inc)
            if href:
                scroll_links += f"""<a href="{href}">{text}</a>"""
        return scroll_links

    def prev(self) -> "Paper":
        """
        get the previous paper in this volume
        """
        return self.next(-1)

    def next(self, inc: int = 1) -> "Paper":
        """
        get the next paper in this volume with the given increment

        Args:
            inc(int): the increment +1 = next, -1 = prev
        """
        vol = self.volume
        paper = None
        if vol:
            next_index = self.paper_index + inc
            if next_index >= 0 and next_index < len(vol.papers):
                paper = vol.papers[next_index]
        return paper

    def getIconBar(self, soup):
        """
        get my icon bar

        Parameters:
            soup: The BeautifulSoup object to use for creating new tags.
        """
        pdf_name = self.pdfUrl.replace("https://ceur-ws.org/", "")
        pdf_name = pdf_name.replace(".pdf", "")
        # create a list of icons to add to the div
        icon_list = [
            {
                "src": "/static/icons/32px-text-icon.png",
                "title": "plain text",
                "link": f"/{pdf_name}.txt",
                "valid": self.getContentPathByPostfix(".txt"),
            },
            {
                "src": "/static/icons/32px-PDF_icon.svg.png",
                "title": "original pdf",
                "link": f"/{pdf_name}.pdf",
                "valid": self.getContentPathByPostfix(".pdf"),
            },
            {
                "src": "/static/icons/32px-Cermine-Icon.png",
                "title": "Cermine metadata",
                "link": f"/{pdf_name}.cermine",
                "valid": self.getContentPathByPostfix(".cermine"),
            },
            {
                "src": "/static/icons/32px-GROBID-icon.png",
                "title": "GROBID metadata",
                "link": f"/{pdf_name}.grobid",
                "valid": self.getContentPathByPostfix(".grobid"),
            },
            {
                "src": "/static/icons/32px-QuickStatements-icon.png",
                "title": "Quickstatements",
                "link": f"/{pdf_name}.qs",
                "valid": True,  # @TODO - add check for existing wikidata entry
            },
            {
                "src": "/static/icons/32px-SMW-icon.png",
                "title": "SMW markup",
                "link": f"/{pdf_name}.smw",
                "valid": True,
            },
            {
                "src": "/static/icons/32px-wbjson-icon.png",
                "title": "wikibase CLI JSON metadata",
                "link": f"/{pdf_name}.wbjson",
                "valid": True,
            },
            {
                "src": "/static/icons/32px-Wikibase_logo.svg.png",
                "title": "wikibase CLI",
                "link": f"/{pdf_name}.wbcli",
                "valid": True,
            },
            {
                "src": "/static/icons/32px-JSON_vector_logo.svg.png",
                "title": "JSON metadata",
                "link": f"/{pdf_name}.json",
                "valid": True,
            },
            {
                "src": "/static/icons/32px-YAML_Logo.svg.png",
                "title": "YAML metadata",
                "link": f"/{pdf_name}.yaml",
                "valid": True,
            },
        ]
        icon_tag = Volume.create_icon_bar(soup, icon_list=icon_list)
        return icon_tag

    def asHtml(self):
        """
        return an html response for this paper
        """
        soup = BeautifulSoup("<html></html>", "html.parser")
        icon_bar = self.getIconBar(soup)
        author_bar = self.getAuthorBar()
        content = f"""<!DOCTYPE html>
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
{str(author_bar)}
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

    def __init__(self, **kwargs):
        ceurspt.ceurws_base.Volume.__init__(self, **kwargs)
        self.papers = []

    def getMergedDict(self) -> dict:
        """
        get my merged dict

        Returns:
            dict
        """
        my_dict = dataclasses.asdict(self)
        m_dict = {
            "version.version": Version.version,
            "version.cm_url": Version.cm_url,
            "spt.html_url": f"/Vol-{self.number}.html",
        }
        for key, value in my_dict.items():
            m_dict[f"spt.{key}"] = value
        volrecord = self.vm.getVolumeRecord(self.number)
        for key, value in volrecord.items():
            if "." in key:
                m_dict[f"{key}"] = value
            else:
                m_dict[f"cvb.{key}"] = value
        return m_dict

    @classmethod
    def volLinkParts(cls, number: int, inc: int = 0):
        """
        a relative volume link
        """
        if inc > 0:
            presymbol = "⫸"
            postsymbol = ""
        elif inc < 0:
            presymbol = ""
            postsymbol = "⫷"
        else:
            presymbol = ""
            postsymbol = ""
        href = f"/Vol-{number+inc}.html"
        text = f"{presymbol}Vol-{number+inc}{postsymbol}"
        return href, text

    @classmethod
    def volLink(cls, number: int, inc: int = 0) -> str:
        """
        get a relative volume link

        Args:
            number(int): the volume number
            inc(int): the relative increment

        Returns(str):
            a relative volume link
        """
        href, text = cls.volLinkParts(number, inc)
        if number > 0:
            link = f"""<a href="{href}">{text}</a>"""
        else:
            link = ""
        return link

    @classmethod
    def volLink_soup_tag(cls, soup, number: int, inc: int = 0) -> str:
        """
        get a relative volume link as a soup tag

        Args:
            soup(BeautifulSoup): the soup
            number(int): the volume number
            inc(int): the relative increment

        Returns(str):
            a relative volume link
        """
        href, text = cls.volLinkParts(number, inc)
        link = soup.new_tag("a", href=href)
        link.string = text
        return link

    @classmethod
    def create_icon_list(
        cls, soup: BeautifulSoup, icon_list: typing.List[typing.Dict[str, str]]
    ) -> typing.List["Tag"]:
        """
        create a list of icons

        Args:
            soup: The BeautifulSoup object to use for creating new tags.
            icon_list: The list of icons to add to the <div> tag. Each icon is represented as a
                dictionary with the following keys:
                    - src (str): The URL of the icon image file.
                    - title (str): The title text to use as a tooltip for the icon.
                    - link (str): The URL to link to when the icon is clicked.

        Returns:
            a list of link_tags
        """
        link_tags = []
        # iterate over the icon list and create a new tag for each icon
        for icon_data in icon_list:
            # create a new a tag for the link
            link_tag = soup.new_tag("a")
            link_tag["href"] = icon_data["link"]
            # open link in new tab
            link_tag["target"] = "_blank"
            if not icon_data["valid"]:
                link_tag["style"] = "filter: grayscale(1);"

            # create a new img tag for the icon
            icon_tag = soup.new_tag("img")

            # add the icon attributes to the img tag
            icon_tag["src"] = icon_data["src"]
            icon_tag["title"] = icon_data["title"]

            # append the icon tag to the link tag
            link_tag.append(icon_tag)
            link_tags.append(link_tag)
        return link_tags

    @classmethod
    def create_icon_bar(
        cls,
        soup: BeautifulSoup,
        icon_list: typing.List[typing.Dict[str, str]],
        class_name: str = "icon_list",
    ) -> Tag:
        """
        Creates a new <div> tag with the specified class name and list of icons.

        Args:
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

        for link_tag in cls.create_icon_list(soup, icon_list):
            # append the link tag to the div tag
            div_tag.append(link_tag)

        # return the div tag
        return div_tag

    def getIconBar(self, soup):
        """
        get my icon bar

        Parameters:
            soup: The BeautifulSoup object to use for creating new tags.
        """
        volume_record = self.vm.getVolumeRecord(self.number)
        for wd_key, attr in [
            ("wd.event", "wd_event"),
            ("wd.eventSeries", "wd_event_series"),
        ]:
            value = None
            if wd_key in volume_record:
                value = volume_record[wd_key]
                if value:
                    value = value.replace("http://www.wikidata.org/entity/", "")
            setattr(self, attr, value)
        # create a list of icons to add to the div
        icon_list = [
            {
                "src": "/static/icons/32px-dblp-icon.png",
                "title": "dblp",
                "link": f"https://dblp.org/rec/{self.dblp}",
                "valid": self.dblp,
            },
            {
                "src": "/static/icons/32px-DNB.svg.png",
                "title": "k10plus/DNB",
                "link": f"https://opac.k10plus.de/DB=2.299/PPNSET?PPN={self.k10plus}",
                "valid": self.k10plus,
            },
            {
                "src": "/static/icons/32px-Scholia_logo.svg.png",
                "title": "Proceedings@scholia",
                "link": f"https://scholia.toolforge.org/venue/{self.wikidataid}",
                "valid": self.wikidataid,
            },
            {
                "src": "/static/icons/32px-EventIcon.png",
                "title": "Event@scholia",
                "link": f"https://scholia.toolforge.org/event/{self.wd_event}",
                "valid": self.wd_event,
            },
            {
                "src": "/static/icons/32px-EventSeriesIcon.png",
                "title": "EventSeries@scholia",
                "link": f"https://scholia.toolforge.org/event-series/{self.wd_event_series}",
                "valid": self.wd_event_series,
            },
            {
                "src": "/static/icons/32px-Wikidata_Query_Service_Favicon_wbg.svg.png",
                "title": "Proceedings@wikidata",
                "link": f"https://www.wikidata.org/wiki/{self.wikidataid}",
                "valid": self.wikidataid,
            },
            {
                "src": "/static/icons/32px-EventIcon.png",
                "title": "Event@wikidata",
                "link": f"https://www.wikidata.org/wiki/{self.wd_event}",
                "valid": self.wd_event,
            },
            {
                "src": "/static/icons/32px-EventSeriesIcon.png",
                "title": "EventSeries@wikidata",
                "link": f"https://www.wikidata.org/wiki/{self.wd_event_series}",
                "valid": self.wd_event_series,
            },
            {
                "src": "/static/icons/32px-SMW-icon.png",
                "title": "SMW markup",
                "link": f"/Vol-{self.number}.smw",
                "valid": True,
            },
            {
                "src": "/static/icons/32px-JSON_vector_logo.svg.png",
                "title": "JSON metadata",
                "link": f"/Vol-{self.number}.json",
                "valid": True,
            },
            {
                "src": "/static/icons/32px-YAML_Logo.svg.png",
                "title": "YML metadata",
                "link": f"/Vol-{self.number}.yaml",
                "valid": True,
            },
        ]
        icon_tag = Volume.create_icon_bar(soup, icon_list=icon_list)
        return icon_tag

    def addPaper(self, paper: "Paper"):
        """
        add the given paper
        """
        # @TODO fixme to use LinkML generated code
        self.papers.append(paper)
        paper.paper_index = len(self.papers) - 1

    def fix_element_tag(self, element, tag: str = "href", ext: str = ".pdf"):
        """
        fix the given element tag

        Args:
            tag(str): the tag to fix
            ext(str): the extension
        """
        org_tag_value = element[tag]
        value = org_tag_value.replace("http://ceur-ws.org/", "/")
        for file in ["ceur-ws.css", "CEUR-WS-logo.png"]:
            value = value.replace(f"../{file}", f"/static/{file}")
        if ".pdf" in value:
            value = value.replace(".pdf", ext)
            value = f"/Vol-{self.number}/{value}"
            pass
        element[tag] = value

    def add_volume_navigation(self, soup: BeautifulSoup):
        """
        Add navigation bar to volume number to jump to the volume below and above
        Args:
            soup: index page
        """
        vol_tag = soup.find("span", class_="CEURVOLNR")
        if vol_tag:
            prev_link = Volume.volLink_soup_tag(soup, self.number, -1)
            if prev_link:
                vol_tag.insert_before(prev_link)
            next_link = Volume.volLink_soup_tag(soup, self.number, +1)
            if next_link:
                vol_tag.insert_after(next_link)

    def get_empty_volume_page(self, content_html: str = None):
        """
        Get empty volume page
        """
        html_page = f"""
            <!DOCTYPE html>
            <!-- CEURVERSION=2020-07-09 -->
            <html lang="en">
            <head>
            <meta http-equiv="Content-type" content="text/html;charset=utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" type="text/css" href="/static/ceur-ws.css">
            </head>
            <!--CEURLANG=eng -->
            <body>
            
            <table style="border: 0; border-spacing: 0; border-collapse: collapse; width: 95%">
            <tbody><tr>
            <td style="text-align: left; vertical-align: middle">
            <a href="http://ceur-ws.org/"><div id="CEURWSLOGO"></div></a>
            </td>
            <td style="text-align: right; vertical-align: middle">
            <div style="float:left" id="CEURCCBY"></div>
            <span class="CEURVOLNR">Vol-{self.number}</span> <br>
            <span class="CEURURN">urn:nbn:de:0074-3365-4</span>
            </td>
            </tr>
            </tbody></table>
            {content_html}
            </body></html>
        """
        soup = BeautifulSoup(html_page, "html.parser")
        self.add_volume_navigation(soup)
        content = soup.prettify(formatter="html")
        return content

    def getHtml(self, ext: str = ".pdf", fixLinks: bool = True) -> str:
        """
        get my HTML content

        Args:
            ext(str): the extension to use for pdf page details
            fixLinks(bool): if True fix the links
        """
        index_path = f"{self.vol_dir}/index.html"
        try:
            with open(index_path, "r", encoding="utf-8") as index_html:
                content = index_html.read()
                if fixLinks:
                    soup = BeautifulSoup(content, "html.parser")
                    for element in soup.findAll(["link", "a"]):
                        self.fix_element_tag(element, tag="href", ext=ext)
                    for element in soup.findAll(["image"]):
                        self.fix_element_tag(element, tag="src", ext=ext)
                    self.add_volume_navigation(soup)
                    first_hr = soup.find("hr")
                    if first_hr:
                        icon_bar = self.getIconBar(soup)
                        first_hr.insert_before(icon_bar)
                    content = soup.prettify(formatter="html")
            return content
        except Exception as ex:
            err_html = f"""<span style="color:red">reading {index_path} for Volume {self.number} failed: {str(ex)}</span>"""
            content = self.get_empty_volume_page(err_html)
            return content

    def as_smw_markup(self) -> str:
        """
        return my semantic mediawiki markup

        Returns:
            str: the smw markup for this volume
        """
        markup = f"""=Volume=
{{{{Volume
|number={self.number}
|storemode=property
|wikidataid={self.wikidataid}
|title={self.title}
|acronym={self.acronym}
|url={self.url}
|date={self.date}
"""
        for attr in ["dblp", "k10plus"]:
            value = getattr(self, attr)
            if value:
                markup += f"|{attr}={value}\n"
        markup += """|urn=urn:nbn:de:0074-1155-8
}}"""
        return markup


class JsonCacheManager:
    """
    a json based cache manager
    """

    def __init__(self, base_url: str = "https://cvb.wikidata.dbis.rwth-aachen.de"):
        """
        constructor

        base_url(str): the base url to use for the json provider
        """
        self.base_url = base_url

    def json_path(self, lod_name: str) -> str:
        """
        get the json path for the given list of dicts name

        Args:
            lod_name(str): the name of the list of dicts cache to read

        Returns:
            str: the path to the list of dict cache
        """
        root_path = f"{Path.home()}/.ceurws"
        os.makedirs(root_path, exist_ok=True)
        json_path = f"{root_path}/{lod_name}.json"
        return json_path

    # minimum byte size for a cache file to be considered non-empty.
    # `[]` is 2 bytes, `{}` is 2 bytes, `[{}]` is 4 bytes — anything below
    # this threshold is treated as a corrupt/empty cache.
    MIN_VALID_BYTES = 8

    def _is_valid_local(self, json_path: str) -> bool:
        """
        Check whether a local cache file exists and is non-empty enough
        to be trusted (guards against previously-written `[]` corruption).
        """
        if not os.path.isfile(json_path):
            return False
        try:
            return os.path.getsize(json_path) >= self.MIN_VALID_BYTES
        except OSError:
            return False

    def _fetch_remote(self, lod_name: str) -> list:
        """
        fetch a list of dicts from the remote base_url, validating HTTP
        status and payload shape. Raises on 5xx, non-200, or empty body.
        """
        url = f"{self.base_url}/{lod_name}.json"
        try:
            with urllib.request.urlopen(url, timeout=60) as source:
                status = getattr(source, "status", 200)
                if status != 200:
                    raise Exception(
                        f"HTTP {status} fetching {lod_name} from {url}"
                    )
                json_str = source.read()
        except urllib.error.HTTPError as ex:
            raise Exception(
                f"HTTP {ex.code} fetching {lod_name} from {url}: {ex.reason}"
            )
        except Exception as ex:
            raise Exception(f"Could not read {lod_name} from {url} due to {ex}")
        if not json_str or len(json_str) < self.MIN_VALID_BYTES:
            raise Exception(
                f"Remote {url} returned empty/too-small payload "
                f"({len(json_str) if json_str else 0} bytes) — refusing to use"
            )
        try:
            lod = orjson.loads(json_str)
        except Exception as ex:
            raise Exception(f"Invalid JSON from {url}: {ex}")
        return lod

    def load_lod(self, lod_name: str, prefer_local: bool = True) -> list:
        """
        load my list of dicts.

        Prefers a valid non-empty local cache file; otherwise fetches
        from the remote base_url. A local file that is missing or too
        small (e.g. a previously-written `[]`) is ignored and the
        remote is used instead.

        Args:
            lod_name(str): the name of the list of dicts cache to read
            prefer_local(bool): if True, use local file when valid

        Returns:
            list: the list of dicts
        """
        json_path = self.json_path(lod_name)
        if prefer_local and self._is_valid_local(json_path):
            try:
                with open(json_path, encoding="utf-8") as json_file:
                    json_str = json_file.read()
                    return orjson.loads(json_str)
            except Exception as ex:
                # fall through to remote on local read error
                logging.warning(
                    f"Local cache {json_path} unreadable ({ex}); "
                    f"falling back to remote"
                )
        return self._fetch_remote(lod_name)

    def store(self, lod_name: str, lod: list, allow_empty: bool = False):
        """
        store my list of dicts.

        Refuses to overwrite an existing non-empty cache file with an
        empty lod unless ``allow_empty=True`` is set. This guards
        against `ceur-spt -rc` clobbering a good cache when the
        upstream returned a 5xx or an empty response.

        Args:
            lod_name(str): the name of the list of dicts cache to write
            lod(list): the list of dicts to write
            allow_empty(bool): permit writing an empty lod over an
                existing non-empty cache
        """
        json_path = self.json_path(lod_name)
        if not lod and not allow_empty and self._is_valid_local(json_path):
            raise Exception(
                f"Refusing to overwrite non-empty {json_path} with empty "
                f"lod for {lod_name} (pass allow_empty=True to force)"
            )
        with open(json_path, "wb") as json_file:
            json_file.write(orjson.dumps(lod))


class VolumeManager(JsonCacheManager):
    """
    manage all volumes
    """

    def __init__(self, base_path: str, base_url: str):
        """
        initialize me with the given base_path

        Args:
            base_path(str): the path to my files
            base_url(str): the url of the RESTFul metadata service
        """
        JsonCacheManager.__init__(self, base_url=base_url)
        self.base_path = base_path
        self.volumes_by_number: Dict[int, Volume] = {}
        self.volume_records_by_number: Dict[int, dict] = {}

    def head_table_html(self) -> str:
        """ """
        html = """<table width="97%" cellspacing="5" cellpadding="0" border="0">
<tbody><tr>
<td valign="middle" align="left">
<div id="CEURWSLOGO"></div>
<!--<img alt="[25years CEUR-WS]" style="padding:4px; float:left;"  width="550" src="./CEUR-WS-logo-originals/2020/CEUR-WS-25anniversary.png"> -->
</td>
<td valign="middle" align="justify">
<font size="-2" face="ARIAL,HELVETICA,VERDANA" color="#363636">

<img alt="[OpenAccess]" style="padding:6px; float:left;" src="/static/OpenAccesslogo_200x313.png" width="18">
CEUR Workshop Proceedings (CEUR-WS.org) is a
<a href="https://ceur-ws.org/CEURWS-VALUES.html">free</a>
<a href="http://www.sherpa.ac.uk/romeo/issn/1613-0073/">open-access</a>
publication service
at <a href="http://sunsite.informatik.rwth-aachen.de">Sun SITE Central Europe</a>
operated under the umbrella of
 <a href="http://www-i5.informatik.rwth-aachen.de">RWTH Aachen University</a>.
CEUR-WS.org is a recognized ISSN publication series,
<a href="https://ceur-ws.org/issn-1613-0073.html">ISSN 1613-0073</a> (<a href="https://portal.issn.org/resource/ISSN/1613-0073?format=json">json</a>).
CEUR-WS.org is hosted at http://SunSITE.Informatik.RWTH-Aachen.DE/Publications/CEUR-WS/.
This service is provided by
the <b><a href="https://ceur-ws.org/CEURWS-TEAM.html">CEUR-WS.org Team</a></b>.
See end of the page for contact details and <a href="https://ceur-ws.org/#IMPRESSUM">Impressum</a>.
</font>
</td>
</tr>
</tbody></table>"""
        return html

    def index_html(
        self, upper: Optional[int] = None, lower: Optional[int] = None
    ) -> str:
        """
        return an index going from the given upper volume number down to the given lower volume number

        Args:
            upper(int): upper volume number to start with
            lower(int): lower volume number to end with

        Returns:
            html code for index
        """
        html = f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
   "https://www.w3.org/TR/html4/loose.dtd">
<html>
  <head> 
    <meta http-equiv="Content-Type" content="Type=text/html;charset=utf-8">
    <meta name="description" content="CEUR-WS.org provides free online scientific papers">
    <meta name="keywords" content="open access, open archive, free scientific paper, workshop proceedings, online publishing, computer science, information systems" >

    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- automatically refresh daily-->
    <meta http-equiv="expires" content="86400">
    <link rel="stylesheet" type="text/css" href="/static/ceur-ws.css">
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
    <title>CEUR-WS.org - CEUR Workshop Proceedings (free, open-access publishing, computer science/information systems)</title>
    <link rel="shortcut icon" href="/static/ceur-ws.ico">
  </head>
  <body>
     {self.head_table_html()}
     <div>
"""
        # prepare the indexing
        # get the volumes as a list from 1 - top e.g. 3365
        volumes = list(self.volumes_by_number.values())
        # reverse the list
        volumes.reverse()
        # make sure upper and lower values are valid
        if upper is None:
            upper = volumes[0].number
        if lower is None:
            lower = 1
        # loop over the reversed list
        for vol_index in range(len(volumes)):
            vol = volumes[vol_index]
            vol_number = vol.number
            if vol_number > upper:
                continue
            if vol_number < lower:
                break
            if isinstance(vol.title, str):
                vol_title = escape(vol.title)
            else:
                vol_title = "Title missing (Might be one of the empty volumes)"
            if vol_title is None:
                pass
            html += f"""       <div style='bgcolor:#DCDBD7'>
         <b><a name='Vol-{vol_number}'>Vol-{vol_number}</a></b>
         <a href='/Vol-{vol_number}.html'>{vol_title}</a>
       </div>
"""
        html += """    </div>
  </body>
</html>"""
        return html

    def index_alt_html(
            self, upper: Optional[int] = None, lower: Optional[int] = None
    ) -> str:
        """
        return an index going from the given upper volume number down to the given lower volume number

        Args:
            upper(int): upper volume number to start with
            lower(int): lower volume number to end with

        Returns:
            html code for index
        """
        html = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
   "https://www.w3.org/TR/html4/loose.dtd">
<html>
  <head> 
    <meta http-equiv="Content-Type" content="Type=text/html;charset=utf-8">
    <meta name="description" content="CEUR-WS.org provides free online scientific papers">
    <meta name="keywords" content="open access, open archive, free scientific paper, workshop proceedings, online publishing, computer science, information systems" >

    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- automatically refresh daily-->
    <meta http-equiv="expires" content="86400">
    <link rel="stylesheet" type="text/css" href="/static/ceur-ws.css">
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
    <title>CEUR-WS.org - CEUR Workshop Proceedings (free, open-access publishing, computer science/information systems)</title>
    <link rel="shortcut icon" href="/static/ceur-ws.ico">
    <!-- Filter bar styles. Kept in-file so the page stays a single document; -->
   <!-- visually consistent with ceur-ws.css (arial, #404040 text, grey swatches). -->
   <style type="text/css">
      #VOLFILTER {
         width: 97%;
         margin: 0 0 10px 0;
         padding: 8px 10px;
         background-color: #F5F4EF;
         border: 1px solid #DCDBD7;
         font-family: arial, sans-serif;
         font-size: small;
         color: #404040;
      }
      #VOLFILTER fieldset {
         border: 0;
         margin: 0;
         padding: 0;
         display: inline;
      }
      #VOLFILTER label.mode {
         margin-right: 14px;
         font-weight: bold;
         cursor: pointer;
      }
      #VOLFILTER .controls {
         display: inline-block;
         margin-left: 18px;
      }
      #VOLFILTER select,
      #VOLFILTER input[type="number"] {
         font-family: arial, sans-serif;
         font-size: small;
         padding: 2px 4px;
         border: 1px solid #B8B7B3;
         background-color: #FFFFFF;
         color: #404040;
      }
      #VOLFILTER input[type="number"] { width: 6em; }
      #VOLFILTER .sep { margin: 0 6px; color: #777777; }
      #VOLFILTER .count {
         float: right;
         color: #777777;
         font-size: smaller;
         padding-top: 2px;
      }
      #VOLFILTER button.reset {
         margin-left: 14px;
         font-family: arial, sans-serif;
         font-size: x-small;
         padding: 2px 8px;
         border: 1px solid #B8B7B3;
         background-color: #FFFFFF;
         color: #404040;
         cursor: pointer;
      }
      #VOLFILTER button.reset:hover { color: #000080; }
      #VOLFILTER .hidden-controls { display: none !important; }
      .VOLGROUP.filtered-out { display: none; }
      #NO-RESULTS {
         display: none;
         width: 97%;
         padding: 12px;
         background-color: #FFFFFF;
         border: 1px solid #DCDBD7;
         font-family: arial, sans-serif;
         font-size: small;
         color: #777777;
         text-align: center;
      }
   </style>
  </head>
  """
        html += f"""
  <body>
     {self.head_table_html()}
     <div>
       <!-- ====================================================================== -->
   <!-- FILTER BAR                                                             -->
   <!-- ====================================================================== -->
   <!-- Filter options are derived automatically from the data-year and        -->
   <!-- data-vol attributes on each .VOLGROUP tbody below. Editors do NOT      -->
   <!-- need to touch this bar when adding a new volume.                       -->
   <!-- ====================================================================== -->
   <div id="VOLFILTER">
      <span class="count" id="VOLCOUNT">&nbsp;</span>
      <fieldset>
         <label class="mode"><input type="radio" name="filtermode" value="all" checked> All</label>
         <label class="mode"><input type="radio" name="filtermode" value="year"> By year</label>
         <label class="mode"><input type="radio" name="filtermode" value="range"> By volume range</label>
      </fieldset>

      <span class="controls" id="YEAR-CONTROLS">
         Year:
         <select id="YEAR-SELECT"></select>
      </span>

      <span class="controls" id="RANGE-CONTROLS">
         Vol-<input type="number" id="RANGE-FROM" min="1" step="1" placeholder="from">
         <span class="sep">to</span>
         Vol-<input type="number" id="RANGE-TO" min="1" step="1" placeholder="to">
      </span>

      <button type="button" class="reset" id="VOLRESET">Reset</button>
   </div>

   <div id="NO-RESULTS">No volumes match the current filter.</div>

   <!-- ====================================================================== -->
   <!-- VOLUMES TABLE                                                          -->
   <!-- ====================================================================== -->
   <!-- MAINTAINER NOTE: to add a volume, copy one <tbody class="VOLGROUP"> -->
   <!-- block below. On the header <tr>, set:                                  -->
   <!--   data-vol="NNNN"   (the volume number, integer)                       -->
   <!--   data-year="YYYY"  (the publication year)                             -->
   <!-- Everything else (filter dropdown, count, range bounds) updates         -->
   <!-- automatically on page load. No JS edits required.                      -->
   <!-- ====================================================================== -->
   <TABLE id="MAINTABLE" cellspacing=0 cellpadding=3 border=0 width="97%">
"""
        # prepare the indexing
        # get the volumes as a list from 1 - top e.g. 3365
        volumes: list[Volume] = list(self.volumes_by_number.values())
        # reverse the list
        volumes.reverse()
        # make sure upper and lower values are valid
        if upper is None:
            upper = volumes[0].number
        if lower is None:
            lower = 1
        # loop over the reversed list
        for vol_index in range(len(volumes)):
            vol = volumes[vol_index]
            vol_number = vol.number
            if vol_number > upper:
                continue
            if vol_number < lower:
                break
            if isinstance(vol.title, str):
                vol_title = escape(vol.title)
            else:
                vol_title = "Title missing (Might be one of the empty volumes)"
            if vol_title is None:
                pass
            vol_record = vol.getMergedDict()
            h1 = vol_record.get("cvb.h1")
            year = vol_record.get("cvb.year")
            editors = vol_record.get("cvb.editors")
            submitter = vol_record.get("cvb.submittedBy")
            published = vol_record.get("cvb.published")
            urn = vol_record.get("cvb.urn")
            html += f"""
<tbody class="VOLGROUP" data-vol="{vol_number}" data-year="{year}">
 <tr><th colspan="2">&nbsp;</th></tr>
 <tr>
    <td align="left" bgcolor="#DCDBD7"><b><a name="Vol-{vol_number}">Vol-{vol_number}</a></b></td>
    <td align="left" bgcolor="#DCDBD7"><b><font color="#000000"><a href="/Vol-{vol_number}/">{h1}</a></font></b></td>
 </tr>
 <tr>
    <td bgcolor="#FFFFFF">{vol_title}<br>
       Edited by: {editors}<br>
       Submitted by: {submitter}<br>
       Published on CEUR-WS: {published}<br>
       ONLINE: <a href="/Vol-{vol_number}/">https://ceur-ws.org/Vol-{vol_number}/</a><br>
       URN: <a href="https://nbn-resolving.org/{urn}">{urn}</a><br>
       ARCHIVE: <a href="https://ceur-ws.org/ftp-dir/Vol-{vol_number}.zip">https://ceur-ws.org/ftp-dir/Vol-{vol_number}.zip</a>
    </td>
 </tr>
</tbody>
"""
        html += """ 
   </TABLE>
      </div>
  
   <!-- ====================================================================== -->
   <!-- Filter script — plain JS, no dependencies, <2KB.                       -->
   <!-- Reads data-vol and data-year from every tbody.VOLGROUP and             -->
   <!-- hides/shows them based on the selected filter mode.                    -->
   <!-- ====================================================================== -->
   <script type="text/javascript">
   (function () {
      var groups   = Array.prototype.slice.call(document.querySelectorAll('tbody.VOLGROUP'));
      var yearSel  = document.getElementById('YEAR-SELECT');
      var yearBox  = document.getElementById('YEAR-CONTROLS');
      var rangeBox = document.getElementById('RANGE-CONTROLS');
      var rFrom    = document.getElementById('RANGE-FROM');
      var rTo      = document.getElementById('RANGE-TO');
      var countEl  = document.getElementById('VOLCOUNT');
      var noRes    = document.getElementById('NO-RESULTS');
      var resetBtn = document.getElementById('VOLRESET');
      var modes    = document.querySelectorAll('input[name="filtermode"]');

      // Collect years and vol bounds from the data-* attributes.
      var years = {}, minVol = Infinity, maxVol = -Infinity;
      groups.forEach(function (g) {
         var y = parseInt(g.getAttribute('data-year'), 10);
         var v = parseInt(g.getAttribute('data-vol'),  10);
         if (!isNaN(y)) years[y] = true;
         if (!isNaN(v)) {
            if (v < minVol) minVol = v;
            if (v > maxVol) maxVol = v;
         }
      });

      // Populate the year dropdown, newest first.
      var yearList = Object.keys(years).map(Number).sort(function (a, b) { return b - a; });
      yearList.forEach(function (y) {
         var o = document.createElement('option');
         o.value = String(y);
         o.textContent = String(y);
         yearSel.appendChild(o);
      });

      // Seed range inputs with the full known range as placeholders.
      rFrom.placeholder = String(minVol);
      rTo.placeholder   = String(maxVol);

      function currentMode() {
         for (var i = 0; i < modes.length; i++) if (modes[i].checked) return modes[i].value;
         return 'all';
      }

      function setControlVisibility(mode) {
         yearBox.classList.toggle('hidden-controls',  mode !== 'year');
         rangeBox.classList.toggle('hidden-controls', mode !== 'range');
      }

      function apply() {
         var mode = currentMode();
         setControlVisibility(mode);

         var selYear = parseInt(yearSel.value, 10);
         var fromV   = parseInt(rFrom.value, 10); if (isNaN(fromV)) fromV = -Infinity;
         var toV     = parseInt(rTo.value,   10); if (isNaN(toV))   toV   =  Infinity;
         if (fromV > toV) { var t = fromV; fromV = toV; toV = t; }

         var shown = 0;
         groups.forEach(function (g) {
            var y = parseInt(g.getAttribute('data-year'), 10);
            var v = parseInt(g.getAttribute('data-vol'),  10);
            var keep = true;
            if (mode === 'year')  keep = (y === selYear);
            if (mode === 'range') keep = (v >= fromV && v <= toV);
            g.classList.toggle('filtered-out', !keep);
            if (keep) shown++;
         });

         countEl.textContent = shown + ' of ' + groups.length + ' volumes shown';
         noRes.style.display = (shown === 0) ? 'block' : 'none';
      }

      // Wire events.
      modes.forEach(function (m) { m.addEventListener('change', apply); });
      yearSel.addEventListener('change', function () {
         // Auto-switch to "year" mode when user picks a year.
         document.querySelector('input[name="filtermode"][value="year"]').checked = true;
         apply();
      });
      [rFrom, rTo].forEach(function (el) {
         el.addEventListener('input', function () {
            document.querySelector('input[name="filtermode"][value="range"]').checked = true;
            apply();
         });
      });
      resetBtn.addEventListener('click', function () {
         document.querySelector('input[name="filtermode"][value="all"]').checked = true;
         yearSel.selectedIndex = 0;
         rFrom.value = '';
         rTo.value   = '';
         apply();
      });

      apply();
   })();
   </script>
  </body>
</html>"""
        return html

    def getVolume(self, number: int):
        """
        get my volume by volume number

        Args:
            number(int): the volume to get
        """
        if isinstance(number, str) and number.isdigit():
            number = int(number)
        if number in self.volumes_by_number:
            return self.volumes_by_number[number]
        else:
            return None

    def getVolumeRecord(self, number: int):
        if number in self.volume_records_by_number:
            return self.volume_records_by_number[number]
        else:
            return None

    def getVolumes(self, verbose: bool = False):
        """
        get my volumes

        Args:
            verbose(bool): if True show verbose loading information
        """
        profiler = Profiler("Loading volumes", profile=verbose)
        volume_lod = self.load_lod("volumes")
        proceedings_lod = self.load_lod("proceedings")
        self.volumes_by_number = {}
        self.volume_records_by_number = {}
        for volume_record in volume_lod:
            vol_number = volume_record["number"]
            self.volume_records_by_number[vol_number] = volume_record
            title = volume_record["title"]
            pub_date_str = volume_record["pubDate"]
            if pub_date_str:
                pub_date = datetime.fromisoformat(pub_date_str).date()
            else:
                pub_date = None
            acronym = volume_record["acronym"]
            volume = Volume(
                number=vol_number, title=title, date=pub_date, acronym=acronym
            )
            volume.vm = self
            volume.number = int(volume.number)
            vol_dir = f"{self.base_path}/Vol-{vol_number}"
            if os.path.isdir(vol_dir):
                volume.vol_dir = vol_dir
            else:
                volume.vol_dir = None
            self.volumes_by_number[vol_number] = volume
        for proc_record in proceedings_lod:
            number = proc_record["sVolume"]
            if not number:
                print(f"Warning: {proc_record} has no volume number")
            else:
                if number not in self.volume_records_by_number:
                    logger.debug(
                        "Volumes and Proceedings cache are out of sync! Volume number: {number} not found in volumes"
                    )
                    continue
                volume_record = self.volume_records_by_number[number]
                volume = self.volumes_by_number[number]
                for key, value in proc_record.items():
                    volume_record[f"wd.{key}"] = value
                map_pairs = [
                    ("item", "wikidataid"),
                    ("itemDescription", "description"),
                    ("dblpProceedingsId", "dblp"),
                    ("described_at_URL", "url"),
                    ("ppnId", "k10plus"),
                    ("URN_NBN", "urn"),
                ]
                for wd_id, attr in map_pairs:
                    wd_key = f"wd.{wd_id}"
                    if wd_key in volume_record:
                        value = volume_record[wd_key]
                        if isinstance(value, str):
                            value = value.replace("http://www.wikidata.org/entity/", "")
                            value = value.replace("https://www.wikidata.org/wiki/", "")
                        setattr(volume, attr, value)
                        pass
        msg = f"{len(self.volumes_by_number)} volumes"
        profiler.time(msg)


class PaperManager(JsonCacheManager):
    """
    manage all papers
    """

    def __init__(self, base_url: str):
        """
        constructor

        Args:
            base_url(str): the url of the RESTFul metadata service
        """
        JsonCacheManager.__init__(self, base_url)
        self.papers_by_id: Dict[str, Paper] = {}
        self.papers_by_path: Dict[str, Paper] = {}
        self.paper_records_by_path: Dict[str, dict] = {}
        self.paper_dblp_by_path: Dict[str, dict] = {}

    def getPaper(self, number: int, pdf_name: str):
        """
        get the paper with the given number and pdf name

        Args:
            number(int): the number of the volume the paper is part of
            pdf_name(str): the pdf name of the paper

        Returns:
            Paper: the paper or None if the paper is not found
        """
        pdf_path = f"Vol-{number}/{pdf_name}.pdf"
        paper = None
        if pdf_path in self.papers_by_path:
            paper = self.papers_by_path[pdf_path]
            paper.pm = self
        return paper

    def get_volume_papers(self, number: int) -> List[Paper]:
        """
        Get all papers of given volume number
        Args:
            number(int): the number of the volume the papers are part of
        Returns:
            list of papers
        """
        volume_papers = [
            paper
            for pdf_path, paper in self.papers_by_path.items()
            if pdf_path.startswith(f"Vol-{number}/")
        ]
        return volume_papers

    def getPapers(self, vm: VolumeManager, verbose: bool = False):
        """
        get all papers

        Args:
            vm: VolumeManager
            verbose(bool): if True show verbose loading information
        """
        profiler = Profiler("Loading papers ...", profile=verbose)
        paper_lod = self.load_lod("papers")
        msg = f"{len(paper_lod)} papers"
        profiler.time(msg)
        profiler = Profiler("Loading dblp paper metadata ...", profile=verbose)
        paper_dblp_lod = self.load_lod("papers_dblp")
        msg = f"{len(paper_dblp_lod)} dblp indexed papers"
        profiler.time(msg)
        profiler = Profiler("Linking papers and volumes...", profile=verbose)
        self.papers_by_id = {}
        self.paper_records_by_path = {}
        self.papers_by_path = {}
        for _index, paper_record in enumerate(paper_lod):
            pdf_name = paper_record["pdf_name"]
            volume_number = paper_record["vol_number"]
            volume = vm.getVolume(volume_number)
            # pdf_url=f"https://ceur-ws.org/Vol-{volume_number}/{pdf_name}"
            pdf_path = f"Vol-{volume_number}/{pdf_name}"
            pdf_url = f"https://ceur-ws.org/{pdf_path}"
            try:
                paper = Paper(
                    id=paper_record["id"],
                    title=paper_record["title"],
                    # authors=paper_record["authors"],
                    pdfUrl=pdf_url,
                    volume=volume,
                )
                paper.pm = self
                if volume:
                    volume.addPaper(paper)
                self.papers_by_id[paper_record["id"]] = paper
                self.papers_by_path[pdf_path] = paper
                self.paper_records_by_path[pdf_path] = paper_record
            except Exception as ex:
                print(
                    f"handling of Paper for pdfUrl '{pdf_url}' failed with {str(ex)}",
                    flush=True,
                )
        self.paper_dblp_by_path = {}
        for _index, dblp_record in enumerate(paper_dblp_lod):
            pdf_id = dblp_record["pdf_id"]
            self.paper_dblp_by_path[f"{pdf_id}.pdf"] = dblp_record
        msg = f"{len(self.papers_by_path)} papers linked to volumes"
        profiler.time(msg)
