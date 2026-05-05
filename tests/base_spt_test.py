"""
Created on 2023-03-23

@author: wf
"""

from pathlib import Path

from ceurspt.ceurws import JsonCacheManager, PaperManager, VolumeManager
from tests.basetest import Basetest


class BaseSptTest(Basetest):
    """
    Basetest for Single Point of Truth.

    Uses local fixture JSON files under ``tests/fixtures/`` instead of
    a live remote (previously ``http://cvb2.bitplan.com``) so tests are
    hermetic, fast, and immune to upstream data drift / outages.
    """

    FIXTURES_DIR = Path(__file__).parent / "fixtures"

    @classmethod
    def _install_fixture_json_path(cls) -> None:
        """
        Monkey-patch JsonCacheManager.json_path to resolve to our
        checked-in fixture files. Idempotent.
        """
        fixtures_dir = cls.FIXTURES_DIR

        def _fixture_json_path(self, lod_name: str) -> str:  # noqa: ARG001
            return str(fixtures_dir / f"{lod_name}.json")

        JsonCacheManager.json_path = _fixture_json_path  # type: ignore[assignment]

    def setUp(self, debug=False, profile=True):
        """
        prepare the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.script_path = Path(__file__)
        self.base_path = f"{self.script_path.parent.parent}/ceur-ws"
        # base_url is still required by constructors but should never
        # be reached: fixture JSON files satisfy load_lod locally.
        self.base_url = "file://tests/fixtures"
        self._install_fixture_json_path()
        self.vm = VolumeManager(base_path=self.base_path, base_url=self.base_url)
        self.vm.getVolumes()
        self.pm = PaperManager(base_url=self.base_url)
        self.pm.getPapers(self.vm)
