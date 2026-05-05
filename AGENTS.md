This file provides guidelines for agents working on the pyCEURspt codebase.
# Agent Guidelines for pyCEURspt

CRITICAL: NEVER EVER DO ANY ACTION READING, MODIFYING OR RUNNING without explaing the plan Each set of intended actions needs to be explained in the format: I understood that <YOUR ANALYSIS> so that i plan to <GOALS YOU PURSUE> by <ACTIONS TO BE CONFIRMED> estimating <LINES TO BE CHANGED> lines to be changed confirm with go! YOU WILL NEVER PROCEED WITH OUT POSITIVE CONFIRMATION by go!


## Project Overview

pyCEURspt is a Python library for working with CEUR-WS (Computer Science Proceedings) workshop publications. It provides APIs for accessing volumes, papers, and metadata from the CEUR Workshop Proceedings repository.

## Build/Lint/Test Commands

### Installation
```bash
pip install .                           # Install package
scripts/install                         # Install + pdftotext
```

### Running Tests
```bash
scripts/test                            # All tests (unittest)
scripts/test -tn test_ceurws           # Run specific test
scripts/test -g                        # With green test runner
scripts/test -m                        # Module-wise tests
scripts/test -t                        # With tox
python -m unittest tests.test_ceurws  # Direct unittest
```

### Code Formatting/Linting
```bash
scripts/blackisort                     # Run black + isort
isort ceurspt/*.py tests/*.py          # Sort imports
black ceurspt/*.py tests/*.py          # Format code
```

## Code Style Guidelines

### Imports
- Use `isort` for import sorting
- Group: standard library, third-party, local/relative
- Example:
```python
import dataclasses
import json
import logging
from typing import Dict, List, Optional

import orjson
from bs4 import BeautifulSoup, Tag

import ceurspt.ceurws_base
from ceurspt.dataclass_util import DataClassUtil
```

### Formatting
- Use **black** (line length: 88)
- Use f-strings for string formatting
- Use type hints for function arguments and return values

### Types
- Use Python type hints throughout
- Use concrete return types: `-> str`, `-> Optional[List[str]]`
- Use `Optional` instead of `Union[..., None]`

### Naming Conventions
- **Classes**: PascalCase (e.g., `class Scholar`)
- **Functions/methods**: snake_case (e.g., `def get_base_path()`)
- **Constants**: UPPER_SNAKE_CASE
- **Private methods**: prefix with underscore (`_private_method()`)

### Dataclasses
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProceedingsEntry:
    title: str
    year: str
    date: str
    editor: Optional[str] = None
    volume: Optional[str] = None
```

### Error Handling
- Use exceptions for error conditions
- Catch specific exceptions, not generic `Exception`
- Use logging (`logging.getLogger(__name__)`) for debugging

### Docstrings
Google-style docstrings:
```python
def get_base_path(self) -> Optional[str]:
    """
    Get the base path to my files.

    Returns:
        Optional[str]: The base path if PDF exists, None otherwise.
    """
```

## File Structure
```
ceurspt/
├── __init__.py       # Version info
├── ceurws.py         # Main CEUR-WS functionality
├── ceurws_base.py    # Auto-generated from schema
├── bibtex.py         # BibTeX export
├── webserver.py      # Web server
├── spt_cmd.py        # CLI commands
├── profiler.py       # Profiling utilities
├── dataclass_util.py # Dataclass utilities
└── models/dblp.py   # DBLP integration
tests/
├── basetest.py       # Base test case with Profiler
├── test_ceurws.py    # CEUR-WS tests
├── test_bibtex.py    # BibTeX tests
└── test_app.py       # App tests
```

## Testing Guidelines
- Extend `Basetest` class for test cases
- Use `unittest.TestCase` assertions
- Use `Profiler` for timing tests
- Place test files in `tests/test_*.py`

## Local Cache & Test Fixtures

DO NOT poke around searching for data sources. The authoritative locations are:

- **Local JSON cache**: `~/.ceurws/` (managed by `JsonCacheManager` in `ceurspt/ceurws.py:960`).
  Contains full `volumes.json`, `papers.json`, `proceedings.json`,
  `authors_dblp.json`, `papers_dblp.json` — the same file names used in fixtures.
- **Test fixtures**: `tests/fixtures/*.json` — a curated subset of the local cache
  used by `BaseSptTest` (`tests/base_spt_test.py`) via a monkey-patch of
  `JsonCacheManager.json_path`. Tests are hermetic: no HTTP calls.

**Workflow for adding a missing volume/paper to fixtures**: copy the
record from the corresponding `~/.ceurws/<name>.json` into
`tests/fixtures/<name>.json`. Never fabricate fixture data.

## Dependencies
- `fastapi[all]`, `uvicorn` - Web framework
- `linkml-runtime` - Schema handling
- `beautifulsoup4` - HTML parsing
- `orjson` - Fast JSON
- `bibtexparser` - BibTeX parsing
- `PyYAML`, `tqdm` - YAML and progress bars

## Git/Development
- Create feature branches for new work
- Run `scripts/blackisort` before committing
- Run `scripts/test` to verify changes

## Notes
- `ceurws_base.py` is auto-generated from ceur-ws.yaml
- Manual changes to auto-generated files may be overwritten
- Project uses hatchling for packaging
- Python 3.9+ required
