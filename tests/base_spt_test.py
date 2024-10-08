"""
Created on 2023-03-23

@author: wf
"""

from pathlib import Path

from ceurspt.ceurws import PaperManager, VolumeManager
from tests.basetest import Basetest


class BaseSptTest(Basetest):
    """
    Basetest for Single Point of Truth
    """

    def setUp(self, debug=False, profile=True):
        """
        prepare the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.script_path = Path(__file__)
        self.base_path = f"{self.script_path.parent.parent}/ceur-ws"
        self.base_url = "http://cvb2.bitplan.com"
        self.vm = VolumeManager(base_path=self.base_path, base_url=self.base_url)
        self.vm.getVolumes()
        self.pm = PaperManager(base_url=self.base_url)
        self.pm.getPapers(self.vm)
