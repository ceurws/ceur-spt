import json
import unittest

from ceurspt.jsonldBuilder import CeurWsJsonLdBuilder


class TestJsonldBuilder(unittest.TestCase):

    def test_build(self):
        volume = {
            "spt.html_url": "/Vol-3262.html",
            "spt.number": 3262,
            "spt.acronym": "Wikidata 2022",
            "spt.wikidataid": "Q115053286",
            "spt.title": "Proceedings of the 3rd Wikidata Workshop 2022",
            "spt.url": "http://ceur-ws.org/Vol-3262/",
            "spt.date": "2022-11-03",
            "spt.urn": "urn:nbn:de:0074-3262-0",
            "cvb.number": 3262,
            "cvb.title": "Proceedings of the 3rd Wikidata Workshop 2022",
            "cvb.acronym": "Wikidata 2022",
            "cvb.country": "People's Republic of China",
            "cvb.city": "Hangzhou",
            "cvb.virtualEvent": True,
            "cvb.editors": "Lucie-Aimée Kaffee, Simon Razniewski, Gabriel Amaral, Kholoud Saad Alghamdi",
            "cvb.loctime": "Virtual Event, Hangzhou, China, October 2022",
            "cvb.published": "2022-11-03",
            "cvb.year": "2022",
            "cvb.urn": "urn:nbn:de:0074-3262-0",
            "cvb.archive": "https://ceur-ws.org/ftp-dir/Vol-3262.zip",
            "cvb.volume_number": "Vol-3262",
            "cvb.voltitle": "Wikidata Workshop 2022",
            "cvb.homepage": "https://wikidataworkshop.github.io/2022/",
            "cvb.h3": "Proceedings of the 3rd Wikidata Workshop 2022 co-located with the 21st International Semantic Web Conference (ISWC2022)",
            "cvb.colocated": "ISWC2022",
            "wd.item": "http://www.wikidata.org/entity/Q115053286",
            "wd.eventSeriesOrdinal": "3",
        }

        papers = [
            {
                "spt.id": "Vol-3262/paper1",
                "spt.title": "Formalizing Property Constraints in Wikidata",
                "spt.pdfUrl": "https://ceur-ws.org/Vol-3262/paper1.pdf",
                "cvb.authors": "Nicolas Ferranti,Axel Polleres,Jairo Francisco De Souza,Shqiponja Ahmetaj",
                "dblp.dblp_publication_id": "https://dblp.org/rec/conf/semweb/FerrantiPSA22",
                "dblp.authors": [
                    {"dblp_author_id": "https://dblp.org/pid/144/7445",
                     "label": "Shqiponja Ahmetaj",
                     "wikidata_id": "Q104507237",
                     "orcid_id": "0000-0003-3165-3568",
                     "gnd_id": None},
                    {"dblp_author_id": "https://dblp.org/pid/225/0568",
                     "label": "Nicolas Ferranti",
                     "wikidata_id": "Q112275836",
                     "orcid_id": "0000-0002-5574-1987",
                     "gnd_id": None},
                ],
            },
            # A deliberately under-specified paper to demonstrate graceful failure
            {"spt.id": "Vol-3262/paper-broken"},
        ]

        builder = CeurWsJsonLdBuilder(volume, papers, include_errors=True)
        jsonld_record = builder.build()
        #print(json.dumps(builder.build(), indent=2, ensure_ascii=False))
        assert "ceur:urn" in jsonld_record


if __name__ == '__main__':
    unittest.main()
