from __future__ import annotations

import html
import json
import re
import unicodedata
from datetime import date, datetime, timedelta
from itertools import product
from pathlib import Path
from typing import Any, Iterable, Sequence

from dateutil import parser as date_parser

JOURNAL_CATALOG: dict[str, dict[str, Any]] = {
    "IEEE Robotics and Automation Letters": {
        "short": "RAL",
        "aliases": (
            "ieee robotics and automation letters",
            "robotics and automation letters",
            "ra-l",
            "ral",
        ),
        "query_terms": (
            "IEEE Robotics and Automation Letters",
            "Robotics and Automation Letters",
            "RA-L",
        ),
        "path_hints": (
            "/journals/ral/",
            "/rec/journals/ral/",
        ),
    },
    "IEEE Transactions on Robotics": {
        "short": "T-RO",
        "aliases": (
            "ieee transactions on robotics",
            "transactions on robotics",
            "t-ro",
            "tro",
        ),
        "query_terms": (
            "IEEE Transactions on Robotics",
            "Transactions on Robotics",
            "T-RO",
        ),
        "path_hints": (
            "/journals/trob/",
            "/rec/journals/trob/",
            "/journals/tro/",
        ),
    },
    "IEEE Transactions on Automation Science and Engineering": {
        "short": "T-ASE",
        "aliases": (
            "ieee transactions on automation science and engineering",
            "transactions on automation science and engineering",
            "t-ase",
            "tase",
        ),
        "query_terms": (
            "IEEE Transactions on Automation Science and Engineering",
            "Transactions on Automation Science and Engineering",
            "T-ASE",
        ),
        "path_hints": (
            "/journals/tase/",
            "/rec/journals/tase/",
        ),
    },
    "IEEE/RSJ International Conference on Intelligent Robots and Systems": {
        "short": "IROS",
        "aliases": (
            "ieee rsj international conference on intelligent robots and systems",
            "ieee/rsj international conference on intelligent robots and systems",
            "international conference on intelligent robots and systems",
            "iros",
        ),
        "query_terms": (
            "IEEE/RSJ International Conference on Intelligent Robots and Systems",
            "International Conference on Intelligent Robots and Systems",
            "IROS",
        ),
        "path_hints": (
            "/conf/iros/",
            "/rec/conf/iros/",
        ),
    },
    "IEEE International Conference on Robotics and Automation": {
        "short": "ICRA",
        "aliases": (
            "ieee international conference on robotics and automation",
            "international conference on robotics and automation",
            "icra",
        ),
        "query_terms": (
            "IEEE International Conference on Robotics and Automation",
            "International Conference on Robotics and Automation",
            "ICRA",
        ),
        "path_hints": (
            "/conf/icra/",
            "/rec/conf/icra/",
        ),
    },
    "The International Journal of Robotics Research": {
        "short": "IJRR",
        "aliases": (
            "the international journal of robotics research",
            "international journal of robotics research",
            "ijrr",
        ),
        "query_terms": (
            "The International Journal of Robotics Research",
            "International Journal of Robotics Research",
            "IJRR",
        ),
        "path_hints": (
            "/journals/ijrr/",
            "/rec/journals/ijrr/",
        ),
    },
    "Robotics: Science and Systems": {
        "short": "RSS",
        "aliases": (
            "robotics science and systems",
            "robotics: science and systems",
            "rss",
        ),
        "query_terms": (
            "Robotics: Science and Systems",
            "Robotics Science and Systems",
            "RSS",
        ),
        "path_hints": (
            "/conf/rss/",
            "/rec/conf/rss/",
        ),
    },
    "Conference on Robot Learning": {
        "short": "CoRL",
        "aliases": (
            "conference on robot learning",
            "corl",
        ),
        "query_terms": (
            "Conference on Robot Learning",
            "CoRL",
        ),
        "path_hints": (
            "/conf/corl/",
            "/rec/conf/corl/",
        ),
    },
}

SUPPORTED_JOURNALS = tuple(JOURNAL_CATALOG.keys())
SUPPORTED_VENUES = SUPPORTED_JOURNALS

CONCEPT_TOKEN_ALIASES: dict[str, tuple[str, ...]] = {
    "uav": (
        "uav",
        "aav",
        "drone",
        "quadrotor",
        "multirotor",
        "aerial",
        "aerial robot",
        "aerial vehicle",
        "unmanned aerial vehicle",
        "micro aerial vehicle",
        "flight",
        "fly",
        "flying",
        "air",
    ),
    "uavs": (
        "uavs",
        "aavs",
        "drones",
        "quadrotors",
        "multirotors",
        "aerial robots",
        "aerial vehicles",
        "unmanned aerial vehicles",
        "micro aerial vehicles",
        "flights",
        "flying",
    ),
    "aav": (
        "aav",
        "uav",
        "drone",
        "quadrotor",
        "multirotor",
        "aerial",
        "aerial robot",
        "aerial vehicle",
        "unmanned aerial vehicle",
        "micro aerial vehicle",
        "flight",
        "fly",
        "flying",
        "air",
    ),
    "aavs": (
        "aavs",
        "uavs",
        "drones",
        "quadrotors",
        "multirotors",
        "aerial robots",
        "aerial vehicles",
        "unmanned aerial vehicles",
        "micro aerial vehicles",
        "flights",
        "flying",
    ),
    "drone": (
        "drone",
        "uav",
        "aav",
        "quadrotor",
        "multirotor",
        "aerial",
        "aerial robot",
        "aerial vehicle",
        "flight",
        "fly",
        "flying",
        "air",
    ),
    "drones": (
        "drones",
        "uavs",
        "aavs",
        "quadrotors",
        "multirotors",
        "aerial robots",
        "aerial vehicles",
        "flights",
        "flying",
    ),
    "quadrotor": (
        "quadrotor",
        "uav",
        "aav",
        "drone",
        "multirotor",
        "aerial vehicle",
        "flight",
        "fly",
        "flying",
        "air",
    ),
    "quadrotors": (
        "quadrotors",
        "uavs",
        "aavs",
        "drones",
        "multirotors",
        "aerial vehicles",
        "flights",
        "flying",
    ),
    "aerial": (
        "aerial",
        "uav",
        "aav",
        "drone",
        "quadrotor",
        "multirotor",
        "flight",
        "fly",
        "flying",
        "air",
    ),
    "flight": (
        "flight",
        "fly",
        "flying",
        "uav",
        "aav",
        "drone",
        "quadrotor",
        "multirotor",
        "aerial",
        "aerial robot",
        "aerial vehicle",
        "unmanned aerial vehicle",
        "micro aerial vehicle",
        "air",
    ),
    "fly": (
        "fly",
        "flying",
        "flight",
        "uav",
        "aav",
        "drone",
        "quadrotor",
        "multirotor",
        "aerial",
        "aerial robot",
        "aerial vehicle",
        "unmanned aerial vehicle",
        "micro aerial vehicle",
        "air",
    ),
    "flying": (
        "flying",
        "fly",
        "flight",
        "uav",
        "aav",
        "drone",
        "quadrotor",
        "multirotor",
        "aerial",
        "aerial robot",
        "aerial vehicle",
        "unmanned aerial vehicle",
        "micro aerial vehicle",
        "air",
    ),
    "air": (
        "air",
        "aerial",
        "flight",
        "fly",
        "flying",
        "uav",
        "aav",
        "drone",
        "quadrotor",
        "multirotor",
        "aerial robot",
        "aerial vehicle",
        "unmanned aerial vehicle",
        "micro aerial vehicle",
    ),
}


def ensure_dir(path: str | Path) -> Path:
    target = Path(path).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    return target


def timestamp_for_run(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y%m%d_%H%M%S")


def dump_json(path: str | Path, data: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def strip_html_tags(value: str | None) -> str | None:
    if not value:
        return None
    text = html.unescape(value)
    text = re.sub(r"</?(jats:)?[^>]+>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = normalize_whitespace(text)
    return text or None


def normalize_title(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", value)
    text = strip_html_tags(text) or ""
    text = text.casefold()
    text = re.sub(r"[^a-z0-9一-鿿]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def keyword_search_forms(keyword: str, limit: int = 32) -> list[str]:
    normalized = normalize_title(keyword)
    if not normalized:
        return []

    tokens = [token for token in normalized.split() if token]
    if not tokens:
        return []

    option_lists: list[tuple[str, ...]] = []
    for token in tokens:
        aliases = CONCEPT_TOKEN_ALIASES.get(token, (token,))
        option_lists.append(aliases)

    expanded: list[str] = [" ".join(tokens)]
    for combo in product(*option_lists):
        expanded.append(" ".join(combo))
        if len(expanded) >= limit:
            break
    return unique_preserve_order(expanded)


def expanded_execution_keywords(keywords: Iterable[str]) -> list[tuple[str, str]]:
    execution_pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for keyword in keywords:
        normalized_keyword = normalize_whitespace(keyword)
        if not normalized_keyword:
            continue
        for form in keyword_search_forms(keyword):
            pair = (normalized_keyword, normalize_whitespace(form))
            if not pair[1] or pair in seen:
                continue
            seen.add(pair)
            execution_pairs.append(pair)
    return execution_pairs


def keyword_matches_text(keyword: str, text: str) -> bool:
    lowered = text.casefold()
    for form in keyword_search_forms(keyword):
        form_norm = form.casefold().strip()
        if not form_norm:
            continue
        if form_norm in lowered:
            return True
        parts = [item for item in re.split(r"\W+", form_norm) if len(item) > 2]
        if parts and all(part in lowered for part in parts):
            return True
    return False


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = normalize_whitespace(value).lower()
    text = re.sub(r"^https?://(dx\.)?doi\.org/", "", text)
    text = text.strip().strip(".")
    return text or None


def safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in values:
        if not item:
            continue
        norm = item.strip()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        output.append(norm)
    return output


def chunks(values: Sequence[Any], size: int) -> list[list[Any]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    return [list(values[index:index + size]) for index in range(0, len(values), size)]


def first_nonempty(*values: str | None) -> str | None:
    for item in values:
        if item and str(item).strip():
            return str(item).strip()
    return None


def better_text(left: str | None, right: str | None) -> str | None:
    left = (left or "").strip()
    right = (right or "").strip()
    if not left and not right:
        return None
    if not left:
        return right
    if not right:
        return left
    return right if len(right) > len(left) else left


def guess_doi_from_url(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"(10\.\d{4,9}/[^\s]+)", url, flags=re.IGNORECASE)
    if not match:
        return None
    return normalize_doi(match.group(1))


def normalize_author_name(value: str | None) -> str:
    if not value:
        return ""
    return normalize_title(value)


def author_overlap_ratio(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = {normalize_author_name(item) for item in left if normalize_author_name(item)}
    right_set = {normalize_author_name(item) for item in right if normalize_author_name(item)}
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / max(1, min(len(left_set), len(right_set)))


def _contains_alias(text: str, alias: str) -> bool:
    if alias in {"ral", "tro", "tase", "icra", "iros", "ijrr", "rss", "corl"}:
        return re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text) is not None
    return alias in text


def canonicalize_journal_name(value: str | None) -> str | None:
    if not value:
        return None
    text = normalize_whitespace(value).casefold()
    for canonical, meta in JOURNAL_CATALOG.items():
        if any(_contains_alias(text, alias) for alias in meta["aliases"]):
            return canonical
    return normalize_whitespace(value) or None


def normalize_requested_journals(values: Iterable[str] | None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in values or []:
        canonical = canonicalize_journal_name(item)
        if not canonical:
            continue
        if canonical in seen:
            continue
        seen.add(canonical)
        output.append(canonical)
    return output or ["IEEE Robotics and Automation Letters"]


def journal_query_terms(journal: str) -> list[str]:
    canonical = canonicalize_journal_name(journal) or journal
    meta = JOURNAL_CATALOG.get(canonical)
    if not meta:
        return [canonical]
    return list(unique_preserve_order(meta["query_terms"]))


def infer_journal_from_values(values: Iterable[str | None]) -> str | None:
    prepared = [normalize_whitespace(value).casefold() for value in values if value and normalize_whitespace(value)]
    for canonical, meta in JOURNAL_CATALOG.items():
        for text in prepared:
            if any(_contains_alias(text, alias) for alias in meta["aliases"]):
                return canonical
            if any(path_hint in text for path_hint in meta.get("path_hints", ())):
                return canonical
    return None


def journal_matches_requested(value: str | None, requested_journals: Iterable[str]) -> bool:
    if not value:
        return False
    text = normalize_whitespace(value).casefold()
    for canonical in normalize_requested_journals(requested_journals):
        meta = JOURNAL_CATALOG.get(canonical, {})
        aliases = meta.get("aliases", ())
        path_hints = meta.get("path_hints", ())
        if any(_contains_alias(text, alias) for alias in aliases):
            return True
        if any(path_hint in text for path_hint in path_hints):
            return True
    return False


def record_matches_requested_journals(record: Any, requested_journals: Iterable[str]) -> bool:
    values = [
        getattr(record, "journal", None),
        getattr(record, "raw_venue", None),
        getattr(record, "dblp_url", None),
        getattr(record, "url", None),
    ]
    return any(journal_matches_requested(item, requested_journals) for item in values if item)


def journal_scope_label(requested_journals: Iterable[str]) -> str:
    canonical_journals = normalize_requested_journals(requested_journals)
    labels: list[str] = []
    for journal in canonical_journals:
        meta = JOURNAL_CATALOG.get(journal)
        if meta:
            labels.append(f"{journal} ({meta['short']})")
        else:
            labels.append(journal)
    return "; ".join(labels)


def run_dir_prefix(requested_journals: Iterable[str]) -> str:
    canonical_journals = normalize_requested_journals(requested_journals)
    if len(canonical_journals) == 1:
        meta = JOURNAL_CATALOG.get(canonical_journals[0])
        if meta:
            short = str(meta["short"]).casefold().replace("-", "")
            return f"{short}_search"
    return "robot_journal_search"


def parse_crossref_message_date(message: dict[str, Any]) -> tuple[str | None, int | None]:
    for key in ("published-print", "published-online", "issued", "created"):
        block = message.get(key)
        if not isinstance(block, dict):
            continue
        parts_list = block.get("date-parts")
        if not parts_list:
            continue
        parts = parts_list[0]
        if not parts:
            continue
        year = safe_int(parts[0])
        if year is None:
            continue
        month = safe_int(parts[1]) if len(parts) > 1 else None
        day = safe_int(parts[2]) if len(parts) > 2 else None
        if month and day:
            return f"{year:04d}-{month:02d}-{day:02d}", year
        if month:
            return f"{year:04d}-{month:02d}", year
        return f"{year:04d}", year
    return None, None


def parse_date_to_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date_parser.parse(value).date()
    except Exception:
        return None


def within_time_window(
    publication_date: str | None,
    publication_year: int | None,
    years_back: int | None,
    days_back: int | None,
    today: date | None = None,
) -> bool:
    if years_back is None and days_back is None:
        return True

    today = today or date.today()
    candidate = parse_date_to_date(publication_date)

    if candidate is None and publication_year is not None:
        candidate = date(publication_year, 12, 31)

    if candidate is None:
        return False

    if years_back is not None:
        year_cutoff = date(today.year - years_back, 1, 1)
        if candidate < year_cutoff:
            return False

    if days_back is not None:
        day_cutoff = today - timedelta(days=days_back)
        if candidate < day_cutoff:
            return False

    return True


def metadata_completeness(record: Any) -> int:
    score = 0
    if getattr(record, "title", None):
        score += 1
    if getattr(record, "authors", None):
        score += 1
    if getattr(record, "abstract", None):
        score += 1
    if getattr(record, "doi", None):
        score += 1
    if getattr(record, "url", None):
        score += 1
    if getattr(record, "journal", None):
        score += 1
    if getattr(record, "publication_year", None):
        score += 1
    if getattr(record, "publication_date", None):
        score += 1
    if getattr(record, "dblp_url", None):
        score += 1
    if getattr(record, "subjects", None):
        score += 1
    if getattr(record, "publisher", None):
        score += 1
    if getattr(record, "pdf_url", None):
        score += 1
    if getattr(record, "semantic_scholar_url", None):
        score += 1
    if getattr(record, "semantic_scholar_fields_of_study", None):
        score += 1
    if getattr(record, "semantic_scholar_citation_count", None) is not None:
        score += 1
    return score


def reconcile_preferred_fields(record: Any) -> Any:
    semantic_abstract = getattr(record, "semantic_scholar_abstract", None)
    crossref_abstract = getattr(record, "crossref_abstract", None)
    current_abstract = getattr(record, "abstract", None)

    if semantic_abstract:
        record.abstract = semantic_abstract
        record.abstract_source = "semantic_scholar"
    elif crossref_abstract:
        record.abstract = crossref_abstract
        record.abstract_source = "crossref"
    elif current_abstract:
        record.abstract = current_abstract
        record.abstract_source = getattr(record, "abstract_source", None) or "existing"
    else:
        record.abstract = None
        record.abstract_source = None

    semantic_pdf = getattr(record, "semantic_scholar_open_access_pdf_url", None)
    current_pdf = getattr(record, "pdf_url", None)
    if semantic_pdf:
        record.pdf_url = semantic_pdf
        record.pdf_url_source = "semantic_scholar"
    elif current_pdf:
        record.pdf_url = current_pdf
        record.pdf_url_source = getattr(record, "pdf_url_source", None) or "existing"
    else:
        record.pdf_url = None
        record.pdf_url_source = None

    semantic_date = getattr(record, "semantic_scholar_publication_date", None)
    current_date = getattr(record, "publication_date", None)
    preferred_date = better_text(current_date, semantic_date) or current_date or semantic_date
    if preferred_date:
        record.publication_date = preferred_date

    if not getattr(record, "publication_year", None) and preferred_date:
        parsed = parse_date_to_date(preferred_date)
        if parsed is not None:
            record.publication_year = parsed.year

    return record


def cut_text(value: str | None, limit: int = 160) -> str:
    text = normalize_whitespace(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def first_sentence(value: str | None, limit: int = 140) -> str:
    text = strip_html_tags(value) or ""
    if not text:
        return ""
    parts = re.split(r"(?<=[。！？.!?])\s+", text)
    sentence = parts[0] if parts else text
    return cut_text(sentence, limit=limit)
