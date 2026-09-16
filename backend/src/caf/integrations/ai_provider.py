"""
AI provajder za predlog ocjene — interfejs, bez izabranog modela.

AI/Consensus Engine Agent (CLAUDE.md 7.5). CLAUDE.md Sekcija 2 zabranjuje
pretpostavljanje/izmišljanje modela: konkretan provajder i model bira se
eksplicitnom odlukom i upisuje u CLAUDE.md. Dok se to ne desi,
`build_ai_provider` vraća `None` i servis koristi isključivo Offline Math
Fallback (uz `X-Consensus-Warning` header).

Implementacija stvarnog provajdera dolazi kao nova klasa koja zadovoljava
`ScoreSuggestionProvider`, sa obaveznim timeout-om i jezikom sesije kao
parametrom poziva (CLAUDE.md 6.2 — bez "generiši pa prevedi").
"""

import logging
from dataclasses import dataclass
from typing import Literal, Protocol

from caf.core.config import Settings

logger = logging.getLogger(__name__)

Lang = Literal["me", "en"]


class AiProviderError(Exception):
    """Provajder nije dostupan, istekao je timeout ili je odgovor neupotrebljiv."""


@dataclass(frozen=True)
class AiSuggestion:
    score: int
    summary: str


class ScoreSuggestionProvider(Protocol):
    async def suggest(
        self,
        *,
        subcriteria_code: str,
        criterion_number: int,
        evidence: str,
        weaknesses: str | None,
        input_lang: Lang,
        session_lang: Lang,
    ) -> AiSuggestion: ...


def build_ai_provider(settings: Settings) -> ScoreSuggestionProvider | None:
    if not settings.ai_provider:
        return None
    # Nijedan provajder još nije odobren (CLAUDE.md Sekcija 2). Pogrešno
    # podešen .env ne smije tiho "raditi" — bilježi se i koristi fallback.
    logger.warning(
        "AI_PROVIDER=%r nije podržan dok se model ne odobri; koristi se Offline Math Fallback.",
        settings.ai_provider,
    )
    return None
