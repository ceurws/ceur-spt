from dataclasses import dataclass, asdict
from datetime import datetime
from functools import partial
from operator import is_not
from typing import List, Optional, Union

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

from ceurspt.ceurws import Paper, Volume


@dataclass
class ProceedingsEntry:
    """
    see https://ftp.mpi-inf.mpg.de/pub/tex/mirror/ftp.dante.de/pub/tex/macros/latex/contrib/biblatex/doc/biblatex.pdf

    """
    title: str
    year: str
    date: str

    editor: Optional[Union[str, List[str]]] = None
    subtitle: Optional[str] = None
    titleaddon: Optional[str] = None
    maintitle: Optional[str] = None
    mainsubtitle: Optional[str] = None
    maintitleaddon: Optional[str] = None
    eventtitle: Optional[str] = None
    eventtitleaddon: Optional[str] = None
    eventdate: Optional[str] = None
    venue: Optional[str] = None
    language: Optional[str] = "english"
    volume: Optional[str] = None
    part: Optional[str] = None
    volumes: Optional[str] = None
    series: Optional[str] = "CEUR Workshop Proceedings"

    number: Optional[str] = None
    note: Optional[str] = None
    organization: Optional[str] = None
    publisher: Optional[str] = None
    location: Optional[str] = "Aachen"
    month: Optional[str] = None
    isbn: Optional[str] = None

    eid: Optional[str] = None
    chapter: Optional[str] = None
    pages: Optional[str] = None
    pagetotal: Optional[str] = None
    addendum: Optional[str] = None
    pubstate: Optional[str] = None
    doi: Optional[str] = None
    eprint: Optional[str] = None

    eprintclass: Optional[str] = None
    eprinttype: Optional[str] = None
    url: Optional[str] = None
    urldate: Optional[str] = None

    @classmethod
    def from_volume(cls, volume: Volume) -> "ProceedingsEntry":
        """
        Convert given volume to ProceedingsEntry
        """
        record = volume.getMergedDict()
        pub_date = datetime.fromisoformat(record.get("wd.publication_date")) if record.get("wd.publication_date") is not None else None
        proceeding = ProceedingsEntry(
                title=volume.title,
                date=pub_date.date().isoformat(),
                year=str(pub_date.year) if pub_date else None,
                url=record.get("spt.url"),
                eventtitle=record.get("wd.eventLabel", None),
                eventdate=record.get("wd.startDate", None),
                venue=",".join(filter(partial(is_not, None),[record.get("wd.locationLabel", None), record.get("wd.countryLabel", None)])),
                volume=str(volume.number),
                editor=record.get("cvb.editors", "").replace(",", " and")
        )
        proceeding.__volume = volume
        return proceeding

    def to_bibtex_record(self) -> dict:
        record = {
            'ENTRYTYPE': 'proceedings',
            'ID': self.get_id(),
            **{k: v for k, v in asdict(self).items() if v not in [None, ""]}
        }
        return record

    def get_id(self) -> str:
        entry_id = None
        if hasattr(self, "__volume") and isinstance(self.__volume, Volume):
            entry_id = self.__volume.acronym.replace(" ", "_")
        if entry_id is None:
            entry_id = f"ceur-ws:Vol-{self.volume}"
        return entry_id


@dataclass
class InProceedingsEntry:
    """
    see https://ftp.mpi-inf.mpg.de/pub/tex/mirror/ftp.dante.de/pub/tex/macros/latex/contrib/biblatex/doc/biblatex.pdf
    """
    title: str
    author: Union[str, List[str]]
    booktitle: str
    year: str
    date: str

    editor: Optional[Union[str, List[str]]] = None
    subtitle: Optional[str] = None
    titleaddon: Optional[str] = None
    maintitle: Optional[str] = None

    mainsubtitle: Optional[str] = None
    maintitleaddon: Optional[str] = None
    booksubtitle: Optional[str] = None
    booktitleaddon: Optional[str] = None

    eventtitle: Optional[str] = None
    eventtitleaddon: Optional[str] = None
    eventdate: Optional[str] = None
    venue: Optional[str] = None
    language: Optional[str] = "english"

    volume: Optional[str] = None
    part: Optional[str] = None
    volumes: Optional[str] = None
    series: Optional[str] = "CEUR Workshop Proceedings"
    number: Optional[str] = None
    note: Optional[str] = None
    organization: Optional[str] = None

    publisher: Optional[str] = None
    location: Optional[str] = "Aachen"
    month: Optional[str] = None
    isbn: Optional[str] = None
    eid: Optional[str] = None
    chapter: Optional[str] = None
    pages: Optional[str] = None
    addendum: Optional[str] = None

    pubstate: Optional[str] = None
    doi: Optional[str] = None
    eprint: Optional[str] = None
    eprintclass: Optional[str] = None
    eprinttype: Optional[str] = None
    url: Optional[str] = None
    urldate: Optional[str] = None

    @classmethod
    def from_paper(cls, paper: Paper) -> "InProceedingsEntry":
        record = paper.getMergedDict()
        pub_date = datetime.fromisoformat(record.get("spt.volume").get("date")) if record.get("spt.volume") is not None else None
        authors = record.get("cvb.authors", None)
        if authors is not None:
            if isinstance(authors, str):
                authors = authors.replace(",", " and ")
        elif "dblp.authors" in record:
            authors = " and ".join([author_record.get("label") for author_record in record.get("dblp.authors")])
        in_proceedings = InProceedingsEntry(
                title=record.get("spt.title", None),
                author=authors,
                year=str(pub_date.year),
                date=pub_date.date().isoformat(),
                booktitle=record.get("spt.volume", {}).get("title", None),
                url=str(record.get("spt.pdfUrl")) if record.get("spt.pdfUrl", None) else None,
                volume=str(record.get("spt.volume", {}).get("number"))
        )
        if hasattr(paper, "vm") and isinstance(paper.vm, Volume):
            volume_record = paper.vm.getMergedDict()
            in_proceedings.eventtitle = volume_record.get("wd.eventLabel", None)
            in_proceedings.eventdate = volume_record.get("wd.startDate", None)
            in_proceedings.venue = ",".join(filter(partial(is_not, None), [volume_record.get("wd.locationLabel", None), volume_record.get("wd.countryLabel", None)]))
            in_proceedings.editor = volume_record.get("cvb.editors", "").replace(",", " and")
        in_proceedings.__paper = paper
        return in_proceedings

    def to_bibtex_record(self, crossref: Optional[str] = None) -> dict:
        """
        Convert to bibtex compatible dict
        Args:
            crossref: bibtex key of the proceedings. If set the proceeding specific fields are excluded.
        """
        proceedings_keys = ["series", "location", "eventtitle", "venue", "volume", "editor", "eventdate"]
        record_fields = {k: v for k, v in asdict(self).items() if v not in [None, ""]}
        if crossref is not None:
            record_fields = {k:v for k, v in record_fields.items() if k not in proceedings_keys}
            record_fields["crossref"] = crossref
        record = {
            'ENTRYTYPE': 'inproceedings',
            'ID': f"ceur-ws:{self.get_id()}",
            **record_fields
        }
        return record

    def get_id(self) -> str:
        entry_id = None
        try:
            entry_id = self.__paper.getMergedDict().get("spt.id", None).replace("/", ":")
        except KeyError:
            pass
        return entry_id


class BibTexConverter:
    """
    Convert volumes and papers to corresponding bibtex entries
    """

    @classmethod
    def convert_volume(cls, volume: Volume) -> str:
        """
        convert given volume to biblatex entry
        """
        library = BibDatabase()
        proceedings_entry = ProceedingsEntry.from_volume(volume)
        library.entries.append(proceedings_entry.to_bibtex_record())
        for paper in volume.papers:
            in_proceedings_entry = InProceedingsEntry.from_paper(paper)
            library.entries.append(in_proceedings_entry.to_bibtex_record(crossref=proceedings_entry.get_id()))
        bibtex = bibtexparser.dumps(library)
        return bibtex

    @classmethod
    def convert_paper(cls, paper: Paper) -> str:
        """
        convert given paper to biblatex entry
        """
        library = BibDatabase()
        in_proceedings_entry = InProceedingsEntry.from_paper(paper)
        library.entries.append(in_proceedings_entry.to_bibtex_record())
        bibtex = bibtexparser.dumps(library)
        return bibtex
