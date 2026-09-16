"""
Offline Math Fallback za predlog ocjene (api-contract-v1.md 4.5).

AI/Consensus Engine Agent (CLAUDE.md 7.5). Čist Python (samo stdlib),
deterministički, bez mreže — radi i kad nema interneta ni AI provajdera.

Algoritam:
1. Tekst dokaza se normalizuje (mala slova, bez dijakritika, đ -> dj).
2. Za Enabler kriterijume (1–5) ocjenjuju se PDCA faze (plan/do/check/act),
   za Rezultate (6–9) dimenzije mjerenje/trend/cilj/poređenje — isto kao
   dva CAF panela ocjenjivanja.
3. Svaka faza dobija 1 + broj različitih prepoznatih indikatora (max 5).
4. Predlog = zaokružena aritmetička sredina faza. Dokaz kraći od
   `MIN_EVIDENCE_WORDS` riječi ograničava predlog na `SHORT_EVIDENCE_CAP`.

Jezik (CLAUDE.md 6.1): indikatori se biraju po jeziku NA KOM JE TEKST
UNESEN (`input_lang`) — liste za crnogorski su zasebne, ne prevod
engleskih. Oznake u objašnjenju su na jeziku SESIJE; citirani korisnički
tekst ostaje na originalnom jeziku, bez prevođenja.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

Lang = Literal["me", "en"]

MIN_EVIDENCE_WORDS = 20
SHORT_EVIDENCE_CAP = 2
MAX_QUOTE_CHARS = 300

ENABLER_DIMENSIONS = ("plan", "do", "check", "act")
RESULT_DIMENSIONS = ("measurement", "trend", "target", "comparison")

# Korijeni riječi (prefiksi), već normalizovani (bez dijakritika).
_ENABLER_INDICATORS: dict[Lang, dict[str, tuple[str, ...]]] = {
    "me": {
        "plan": ("plan", "strateg", "cilj", "misij", "vizij", "prioritet", "definis",
                 "utvrdj", "program", "politik"),
        "do": ("sprovod", "sproved", "implement", "realiz", "primjen", "uveden", "uvodi",
               "obuk", "odrzan", "organizov", "izrad"),
        "check": ("prac", "prati", "mjer", "evalu", "analiz", "revizij", "izvjestaj",
                  "indikator", "anket", "pregled", "kontrol"),
        "act": ("unaprijedj", "unapredj", "poboljs", "korektiv", "izmijen", "izmjen",
                "revidir", "azurir", "nauc", "korigov"),
    },
    "en": {
        "plan": ("plan", "strateg", "objective", "goal", "mission", "vision", "priorit",
                 "defin", "policy", "policies"),
        "do": ("implement", "deliver", "deploy", "introduc", "train", "execut", "conduct",
               "rolled", "launch", "establish"),
        "check": ("monitor", "measur", "evaluat", "review", "audit", "report", "indicator",
                  "kpi", "survey", "assess"),
        "act": ("improv", "correct", "adjust", "revis", "updat", "lesson", "refin", "adapt",
                "follow"),
    },
}

_RESULT_INDICATORS: dict[Lang, dict[str, tuple[str, ...]]] = {
    "me": {
        "measurement": ("mjer", "anket", "indikator", "podac", "podat", "statist",
                        "istraziv", "kpi"),
        "trend": ("trend", "rast", "porast", "pad", "povec", "smanj", "godin", "period",
                  "kontinuir"),
        "target": ("cilj", "planiran", "ocekiv", "standard", "norm"),
        "comparison": ("uporedi", "uporedj", "poredj", "benchmark", "prosjek", "drugih",
                       "slicn", "region"),
    },
    "en": {
        "measurement": ("measur", "survey", "indicator", "kpi", "data", "statistic", "metric"),
        "trend": ("trend", "increas", "decreas", "grow", "declin", "year", "annual",
                  "consistent"),
        "target": ("target", "goal", "objective", "expect", "standard"),
        "comparison": ("compar", "benchmark", "average", "peer", "other", "similar"),
    },
}

_LABELS: dict[Lang, dict[str, str]] = {
    "me": {
        "plan": "Planiranje", "do": "Sprovođenje", "check": "Provjera", "act": "Unapređenje",
        "measurement": "Mjerenje", "trend": "Trend", "target": "Ciljevi",
        "comparison": "Poređenje",
        "intro": "Offline procjena (bez AI-ja) — prepoznati elementi u dokazima",
        "weakest": "Najslabije pokriveno",
        "short": "Dokaz je kratak, pa je predlog ograničen",
        "quote": "Ključni dokaz",
        "weaknesses": "Navedene slabosti",
    },
    "en": {
        "plan": "Plan", "do": "Do", "check": "Check", "act": "Act",
        "measurement": "Measurement", "trend": "Trend", "target": "Targets",
        "comparison": "Comparison",
        "intro": "Offline assessment (no AI) — elements recognised in the evidence",
        "weakest": "Least covered",
        "short": "The evidence is short, so the suggestion is capped",
        "quote": "Key evidence",
        "weaknesses": "Stated weaknesses",
    },
}

_TOKEN = re.compile(r"\w+", re.UNICODE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class FallbackSuggestion:
    score: int
    breakdown: dict[str, int]
    summary: str


def normalize(text: str) -> str:
    lowered = text.lower().replace("đ", "dj")
    decomposed = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _dimension_score(tokens: list[str], stems: tuple[str, ...]) -> int:
    hits = sum(1 for stem in stems if any(token.startswith(stem) for token in tokens))
    return min(5, 1 + hits)


def _first_sentence(text: str) -> str:
    first = _SENTENCE_END.split(text.strip(), maxsplit=1)[0].strip()
    if len(first) > MAX_QUOTE_CHARS:
        first = first[: MAX_QUOTE_CHARS - 1].rstrip() + "…"
    return first


def is_results_criterion(criterion_number: int) -> bool:
    return criterion_number >= 6


def suggest(
    *,
    criterion_number: int,
    evidence: str,
    weaknesses: str | None,
    input_lang: Lang,
    session_lang: Lang,
) -> FallbackSuggestion:
    indicators = (
        _RESULT_INDICATORS if is_results_criterion(criterion_number) else _ENABLER_INDICATORS
    )[input_lang]
    tokens = _TOKEN.findall(normalize(evidence))
    breakdown = {dim: _dimension_score(tokens, stems) for dim, stems in indicators.items()}

    mean = sum(breakdown.values()) / len(breakdown)
    score = int(mean + 0.5)  # zaokruživanje "pola naviše", nezavisno od banker's rounding
    word_count = len(evidence.split())
    capped = word_count < MIN_EVIDENCE_WORDS and score > SHORT_EVIDENCE_CAP
    if capped:
        score = SHORT_EVIDENCE_CAP
    score = max(1, min(5, score))

    labels = _LABELS[session_lang]
    parts = ", ".join(f"{labels[dim]} {value}/5" for dim, value in breakdown.items())
    lowest = min(breakdown.values())
    weakest = ", ".join(labels[dim] for dim, value in breakdown.items() if value == lowest)
    lines = [f"{labels['intro']}: {parts}.", f"{labels['weakest']}: {weakest}."]
    if capped:
        lines.append(f"{labels['short']} ({word_count} < {MIN_EVIDENCE_WORDS}).")
    lines.append(f"{labels['quote']}: {_first_sentence(evidence)}")
    if weaknesses and weaknesses.strip():
        lines.append(f"{labels['weaknesses']}: {_first_sentence(weaknesses)}")
    return FallbackSuggestion(score=score, breakdown=breakdown, summary="\n".join(lines))
