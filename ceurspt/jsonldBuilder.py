"""
CEUR-WS JSON-LD Builder

Constructs a JSON-LD document for a CEUR-WS proceedings volume from input dicts
that follow the ceur-spt structure. All terms are emitted under the namespace
https://ceur-ws.org/schema# (prefix `ceur:`).

Design goals:
- Never raise on missing input values. Instead: emit a logging warning and,
  optionally, record the issue in a `ceur:errors` array attached to the
  resource for which the value was missing.
- Accept input dicts as provided (with the dotted keys from spt/cvb/wd/dblp);
  do not require callers to massage them first.
- Be tolerant of the multiple "shadow" sources of the same fact (e.g. a title
  appearing in spt.title, cvb.title, wd.title, dblp.title) — pick the first
  non-empty one in a documented preference order.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Iterable

from ceurspt.ceurws import Volume

logger = logging.getLogger(__name__)


CEUR_NS = "https://ceur-ws.org/schema#"


def _first_non_empty(d: dict, keys: Iterable[str]) -> Any:
    """Return the first value in `d` for any key in `keys` that is not None,
    empty string, or empty collection. Returns None if nothing matches."""
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        if isinstance(v, (list, dict, tuple, set)) and len(v) == 0:
            continue
        return v
    return None


def _split_authors(s: str) -> list[str]:
    """Split a flat author string on commas (and ' and ')."""
    if not s:
        return []
    parts = re.split(r",|\s+and\s+", s)
    return [p.strip() for p in parts if p.strip()]


def _split_name(full_name: str) -> tuple[str, str]:
    """Best-effort split of a full name into (given, family).
    Treats the last whitespace-separated token as the family name. Not perfect
    for names with particles ('de Souza', 'van der Velde') but acceptable as a
    fallback when no structured author record is available."""
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return "", parts[0]
    return " ".join(parts[:-1]), parts[-1]


def _year_from_date(value: Any) -> str | None:
    """Extract a 4-digit year from a date-ish value."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        s = str(int(value))
        return s if len(s) == 4 else None
    if isinstance(value, str):
        m = re.match(r"^\s*(\d{4})", value)
        if m:
            return m.group(1)
    if isinstance(value, datetime):
        return str(value.year)
    return None


class CeurWsJsonLdBuilder:
    """Build a JSON-LD document for a CEUR-WS proceedings volume.

    Parameters
    ----------
    volume : dict
        The proceedings dict (spt./cvb./wd. flat keys).
    papers : list[dict]
        A list of paper dicts (spt./cvb./dblp. flat keys).
    include_errors : bool, default False
        If True, missing-value warnings are also written into `ceur:errors`
        arrays inside the JSON-LD. If False, warnings only go to the logger.
    strict_required : bool, default False
        Affects the *severity* of missing-value warnings only. The build never
        fails. When True, missing properties marked as Crossref-required are
        logged at WARNING level; otherwise at INFO level.
    """

    # Crossref-mandated minimum
    SERIES_REQUIRED = ("ceur:title", "ceur:issn")
    PROCEEDINGS_REQUIRED = (
        "ceur:proceedings_title",
        "ceur:publisher",
        "ceur:publication_year",
    )
    PAPER_REQUIRED = ("ceur:title", "ceur:contributors", "ceur:landing_page")

    def __init__(
        self,
        volume: dict,
        papers: list[dict] | None = None,
        include_errors: bool = False,
        strict_required: bool = False,
    ):
        self.volume = volume or {}
        self.papers = papers or []
        self.include_errors = include_errors
        self.strict_required = strict_required

    def _miss(self, errors: list[dict], prop: str, scope: str, required: bool):
        """Record a missing value: log + optionally append to error list.
        Deduplicates by (prop, scope) within the given errors list."""
        # If we've already recorded this property at this scope, skip.
        for e in errors:
            if e.get("ceur:property") == prop and e.get("ceur:scope") == scope:
                return
        level = logging.WARNING if required else logging.INFO
        msg = f"missing {'required ' if required else ''}property {prop} on {scope}"
        logger.log(level, msg)
        errors.append(
            {
                "ceur:property": prop,
                "ceur:scope": scope,
                "ceur:severity": "error" if required else "warning",
                "ceur:message": msg,
            }
        )

    def _attach_errors(self, node: dict, errors: list[dict]) -> None:
        if self.include_errors and errors:
            # Strip the internal `ceur:scope` helper before serializing
            cleaned = [
                {k: v for k, v in e.items() if k != "ceur:scope"} for e in errors
            ]
            node["ceur:errors"] = cleaned

    def build(self) -> dict:
        doc = {
            "@context": {
                "ceur": CEUR_NS,
                "@vocab": CEUR_NS,
            },
        }
        doc.update(self._build_proceedings())
        return doc

    def _build_proceedings(self) -> dict:
        v = self.volume
        errors: list[dict] = []

        landing = _first_non_empty(v, ["spt.url", "cvb.url", "cvb.volname"])
        volume_nr = _first_non_empty(v, ["cvb.volume_number"])
        if not volume_nr:
            num = _first_non_empty(v, ["spt.number", "cvb.number", "wd.sVolume"])
            volume_nr = f"Vol-{num}" if num is not None else None

        proc_title = _first_non_empty(
            v, ["spt.title", "cvb.title", "wd.title", "wd.itemLabel"]
        )
        publisher = "CEUR-WS.org"

        pub_date = _first_non_empty(
            v,
            [
                "cvb.published",
                "cvb.ceurpubdate",
                "spt.date",
                "cvb.pubDate",
                "wd.publication_date",
            ],
        )
        pub_year = _first_non_empty(v, ["cvb.year", "cvb.pubYear"]) or _year_from_date(
            pub_date
        )

        urn = _first_non_empty(v, ["spt.urn", "cvb.urn", "wd.URN_NBN"])
        archive = _first_non_empty(v, ["cvb.archive"])
        language = _first_non_empty(v, ["cvb.lang", "wd.language_of_work_or_nameLabel"])

        node: dict = {
            "@id": landing or f"urn:ceur:{volume_nr}" if volume_nr else "_:proceedings",
            "@type": "ceur:Proceedings",
            "ceur:series": self._build_series(errors_parent=errors),
            "ceur:volume_nr": volume_nr,
            "ceur:proceedings_title": proc_title,
            "ceur:publisher": publisher,
            "ceur:publication_date": pub_date,
            "ceur:publication_year": pub_year,
            "ceur:landing_page": landing,
            "ceur:urn": urn,
            "ceur:archive": archive,
            "ceur:language": language,
            "ceur:license": "https://creativecommons.org/licenses/by/4.0/",
            "ceur:event": self._build_event(errors_parent=errors),
            "ceur:editors": self._build_editors(errors_parent=errors),
            "ceur:has_paper": [self._build_paper(p) for p in self.papers],
        }

        # Wikidata cross-link if present
        wd_item = _first_non_empty(v, ["wd.item"])
        if wd_item:
            node["ceur:wikidata"] = wd_item

        # Validate required props at the proceedings level
        for prop in self.PROCEEDINGS_REQUIRED:
            if not node.get(prop):
                self._miss(errors, prop, scope="proceedings", required=True)

        # Drop None-valued keys, then attach errors
        node = {k: val for k, val in node.items() if val not in (None, [], "")}
        self._attach_errors(node, errors)
        return node

    def _build_series(self, errors_parent: list[dict]) -> dict:
        # Series facts are constants for CEUR-WS but we still validate.
        errors: list[dict] = []
        node = {
            "@type": "ceur:Series",
            "ceur:title": "CEUR Workshop Proceedings",
            "ceur:title_short": "CEUR-WS",
            "ceur:issn": "1613-0073",
            "ceur:publisher": "CEUR-WS.org",
            "ceur:series_url": "https://ceur-ws.org/",
        }
        for prop in self.SERIES_REQUIRED:
            if not node.get(prop):
                self._miss(errors, prop, scope="series", required=True)
        self._attach_errors(node, errors)
        return node

    def _build_event(self, errors_parent: list[dict]) -> dict | None:
        v = self.volume
        errors: list[dict] = []

        name = _first_non_empty(
            v,
            [
                "cvb.h3",
                "cvb.voltitle",
                "cvb.h1",
                "wd.eventLabel",
            ],
        )
        acronym = _first_non_empty(
            v, ["spt.acronym", "cvb.acronym", "wd.short_name"]
        )
        ordinal = _first_non_empty(
            v, ["cvb.ordinal", "wd.eventSeriesOrdinal"]
        )
        location = _first_non_empty(v, ["cvb.location", "cvb.loctime"])
        city = _first_non_empty(v, ["cvb.city"])
        country = _first_non_empty(v, ["cvb.country"])
        date_from = _first_non_empty(v, ["cvb.dateFrom"])
        date_to = _first_non_empty(v, ["cvb.dateTo"])
        homepage = _first_non_empty(v, ["cvb.homepage", "wd.homePage"])
        colocated = _first_non_empty(v, ["cvb.colocated"])
        virtual = v.get("cvb.virtualEvent")

        node: dict = {
            "@type": "ceur:Event",
            "ceur:conference_name": name,
            "ceur:conference_acronym": acronym,
            "ceur:conference_number": ordinal,
            "ceur:conference_location": location,
            "ceur:conference_city": city,
            "ceur:conference_country": country,
            "ceur:conference_date_start": date_from,
            "ceur:conference_date_end": date_to,
            "ceur:conference_homepage": homepage,
            "ceur:conference_colocated_with": colocated,
            "ceur:conference_virtual": virtual if isinstance(virtual, bool) else None,
        }

        if not node.get("ceur:conference_name") and not node.get(
            "ceur:conference_acronym"
        ):
            self._miss(
                errors_parent,
                "ceur:event",
                scope="proceedings",
                required=False,
            )
            return None

        if not node.get("ceur:conference_name"):
            self._miss(errors, "ceur:conference_name", scope="event", required=False)
        if not node.get("ceur:conference_location"):
            self._miss(errors, "ceur:conference_location", scope="event", required=False)

        node = {k: val for k, val in node.items() if val not in (None, [], "")}
        self._attach_errors(node, errors)
        return node

    def _build_editors(self, errors_parent: list[dict]) -> list[dict]:
        v = self.volume
        raw = _first_non_empty(v, ["cvb.editors"])
        if not raw:
            self._miss(errors_parent, "ceur:editors", scope="proceedings", required=False)
            return []
        out = []
        for name in _split_authors(raw):
            given, family = _split_name(name)
            out.append(
                {
                    "@type": "ceur:Person",
                    "ceur:given_name": given,
                    "ceur:family_name": family,
                }
            )
        return out

    def _build_paper(self, p: dict) -> dict:
        errors: list[dict] = []

        title = _first_non_empty(
            p, ["spt.title", "cvb.title", "dblp.title"]
        )
        if isinstance(title, str):
            title = title.rstrip(".")  # dblp.title often ends with a period

        landing = _first_non_empty(p, ["spt.pdfUrl", "spt.html_url"])
        if landing and landing.startswith("/"):
            landing = "https://ceur-ws.org" + landing

        pages_from = p.get("cvb.pagesFrom")
        pages_to = p.get("cvb.pagesTo")
        pages = p.get("cvb.pages")
        if not pages and pages_from and pages_to:
            pages = f"{pages_from}-{pages_to}"

        session = _first_non_empty(p, ["spt.session"])
        wd_id = _first_non_empty(p, ["spt.wikidataid"])
        dblp_pub = _first_non_empty(p, ["dblp.dblp_publication_id"])

        contributors = self._build_contributors(p, errors)

        node: dict = {
            "@id": landing or f"_:paper-{p.get('spt.id', id(p))}",
            "@type": "ceur:ConferencePaper",
            "ceur:title": title,
            "ceur:landing_page": landing,
            "ceur:pages": pages,
            "ceur:page_first": str(pages_from) if pages_from is not None else None,
            "ceur:page_last": str(pages_to) if pages_to is not None else None,
            "ceur:session": session,
            "ceur:wikidata": wd_id,
            "ceur:dblp": dblp_pub,
            "ceur:contributors": contributors,
        }

        for prop in self.PAPER_REQUIRED:
            val = node.get(prop)
            if val in (None, [], ""):
                self._miss(errors, prop, scope=f"paper {p.get('spt.id', '?')}", required=True)

        node = {k: val for k, val in node.items() if val not in (None, [], "")}
        self._attach_errors(node, errors)
        return node

    # ----- contributors ----------------------------------------------------
    def _build_contributors(self, p: dict, paper_errors: list[dict]) -> list[dict]:
        # Prefer the structured dblp.authors list when available.
        dblp_authors = p.get("dblp.authors")
        if isinstance(dblp_authors, list) and dblp_authors:
            out = []
            for i, a in enumerate(dblp_authors):
                label = a.get("label") or ""
                given, family = _split_name(label)
                person = {
                    "@type": "ceur:Person",
                    "ceur:given_name": given,
                    "ceur:family_name": family,
                    "ceur:sequence": "first" if i == 0 else "additional",
                }
                if a.get("orcid_id"):
                    person["ceur:orcid"] = a["orcid_id"]
                if a.get("wikidata_id"):
                    person["ceur:wikidata"] = a["wikidata_id"]
                if a.get("dblp_author_id"):
                    person["ceur:dblp"] = a["dblp_author_id"]
                if a.get("gnd_id"):
                    person["ceur:gnd"] = a["gnd_id"]
                out.append(person)
            return out

        # Fall back to the flat cvb.authors string.
        raw = _first_non_empty(p, ["cvb.authors"])
        if not raw:
            self._miss(
                paper_errors,
                "ceur:contributors",
                scope=f"paper {p.get('spt.id', '?')}",
                required=True,
            )
            return []
        out = []
        for i, name in enumerate(_split_authors(raw)):
            given, family = _split_name(name)
            out.append(
                {
                    "@type": "ceur:Person",
                    "ceur:given_name": given,
                    "ceur:family_name": family,
                    "ceur:sequence": "first" if i == 0 else "additional",
                }
            )
        return out

    @classmethod
    def from_volume(cls, volume: Volume, include_errors: bool) -> "CeurWsJsonLdBuilder":
        return CeurWsJsonLdBuilder(
            volume=volume.getMergedDict(),
            papers=[paper.getMergedDict() for paper in volume.papers],
            include_errors=include_errors
        )