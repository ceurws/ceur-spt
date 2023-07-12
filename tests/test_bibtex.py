import unittest

from ceurspt.bibtex import BibTexConverter
from tests.base_spt_test import BaseSptTest


class TestBibTexConverter(BaseSptTest):
    """
    tests BibTexConverter
    """

    def test_from_volume(self):
        """
        tests from_value
        """
        volume = self.vm.getVolume(3262)
        pe = BibTexConverter.convert_volume(volume)
        expected_biblatex_volume = """@proceedings{ceur-ws:Vol-3262,
 date = {2022-11-03},
 editor = {Lucie-Aimée Kaffee and Simon Razniewski and Gabriel Amaral and Kholoud Saad Alghamdi},
 eventtitle = {The Third Wikidata Workshop},
 language = {english},
 location = {Aachen},
 series = {CEUR Workshop Proceedings},
 title = {Proceedings of the 3rd Wikidata Workshop 2022},
 url = {http://ceur-ws.org/Vol-3262/},
 volume = {3262},
 year = {2022}
}"""
        for exp_line in expected_biblatex_volume.split("\n"):
            self.assertIn(exp_line, pe[:len(expected_biblatex_volume)])
        expected_biblatex_paper = """@inproceedings{ceur-ws:Vol-3262:paper7,
 author = {Wolfgang Fahl and Tim Holzheim and Andrea Westerinen and Christoph Lange and Stefan Decker},
 booktitle = {Proceedings of the 3rd Wikidata Workshop 2022},
 crossref = {ceur-ws:Vol-3262},
 date = {2022-11-03},
 language = {english},
 title = {Property cardinality analysis to extract truly tabular query results from Wikidata},
 url = {https://ceur-ws.org/Vol-3262/paper7.pdf},
 year = {2022}
}"""
        for exp_line in expected_biblatex_paper.split("\n"):
            self.assertIn(exp_line, pe)

    def test_from_paper(self):
        """
        tests from_paper
        """
        paper = self.pm.getPaper(3262, "paper7")
        pe = BibTexConverter.convert_paper(paper)
        biblatex = """@inproceedings{ceur-ws:Vol-3262:paper7,
 author = {Wolfgang Fahl and Tim Holzheim and Andrea Westerinen and Christoph Lange and Stefan Decker},
 booktitle = {Proceedings of the 3rd Wikidata Workshop 2022},
 date = {2022-11-03},
 language = {english},
 location = {Aachen},
 series = {CEUR Workshop Proceedings},
 title = {Property cardinality analysis to extract truly tabular query results from Wikidata},
 url = {https://ceur-ws.org/Vol-3262/paper7.pdf},
 volume = {3262},
 year = {2022}
}"""
        for exp_line in biblatex.split("\n"):
            self.assertIn(exp_line, pe[:len(biblatex)])


if __name__ == '__main__':
    unittest.main()
