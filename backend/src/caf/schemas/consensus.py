"""AI/Consensus DTO — api-contract-v1.md, sekcija 4.5."""

from typing import Literal

from pydantic import BaseModel, Field


class ConsensusSuggestionOut(BaseModel):
    suggested_score: int = Field(ge=1, le=5)
    suggested_summary_text: str
    source: Literal["ai", "fallback"]
    # Human-in-the-loop (CLAUDE.md 7.5) — uvijek true, predlog se ne upisuje sam.
    requires_human_confirmation: Literal[True] = True
    # Ocjena po PDCA fazi / dimenziji rezultata (samo za fallback; AI izvor je prazan).
    breakdown: dict[str, int] = Field(default_factory=dict)


class ConsensusResult(BaseModel):
    """Interni rezultat servisa: odgovor + da li treba upozoriti na fallback."""

    suggestion: ConsensusSuggestionOut
    provider_unavailable: bool
