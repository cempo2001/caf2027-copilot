"""
ConsensusService — predlog ocjene za jedan podkriterijum (api-contract-v1.md 4.5).

AI/Consensus Engine Agent (CLAUDE.md 7.5). Ništa ne upisuje — predlog je
uvijek human-in-the-loop. Tok:
1. uloga (EDITOR_ROLES) -> SAR (404, 409 ako je zaključan) -> podkriterijum (422)
2. čita SAČUVAN unos; bez teksta dokaza -> 422 consensus_needs_evidence
3. AI provajder (ako je odobren i konfigurisan); bilo kakva greška ili
   nevalidan odgovor -> Offline Math Fallback + `provider_unavailable`.
"""

import logging
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from caf.core.exceptions import ConsensusNeedsEvidenceError
from caf.core.i18n import Locale
from caf.core.security import TokenPayload
from caf.integrations.ai_provider import AiProviderError, Lang, ScoreSuggestionProvider
from caf.models import SubcriteriaScore
from caf.schemas.consensus import ConsensusResult, ConsensusSuggestionOut
from caf.services import consensus_fallback
from caf.services.sar_access import EDITOR_ROLES, SarAccess

logger = logging.getLogger(__name__)


class ConsensusService:
    def __init__(
        self,
        session: AsyncSession,
        user: TokenPayload,
        locale: Locale,
        *,
        provider: ScoreSuggestionProvider | None,
    ) -> None:
        self._session = session
        self._locale = locale
        self._provider = provider
        self._access = SarAccess(session, user, locale)

    async def suggest(self, sar_id: UUID, code: str) -> ConsensusResult:
        self._access.require_role(EDITOR_ROLES)
        sar = await self._access.load_unlocked_sar(sar_id)
        subcriteria = await self._access.load_subcriteria(code)

        score = await self._session.scalar(
            select(SubcriteriaScore).where(
                SubcriteriaScore.self_assessment_id == sar.id,
                SubcriteriaScore.subcriteria_code == subcriteria.code,
            )
        )
        evidence = (score.evidence_text or "").strip() if score else ""
        if not evidence:
            raise ConsensusNeedsEvidenceError(locale=self._locale)
        weaknesses = score.weaknesses_text if score else None
        stored_lang = score.input_lang if score else "me"
        input_lang = cast(Lang, stored_lang if stored_lang in ("me", "en") else "me")
        session_lang = cast(Lang, self._locale)

        if self._provider is not None:
            try:
                ai = await self._provider.suggest(
                    subcriteria_code=subcriteria.code,
                    criterion_number=subcriteria.criterion_number,
                    evidence=evidence,
                    weaknesses=weaknesses,
                    input_lang=input_lang,
                    session_lang=session_lang,
                )
                if 1 <= ai.score <= 5 and ai.summary.strip():
                    return ConsensusResult(
                        suggestion=ConsensusSuggestionOut(
                            suggested_score=ai.score,
                            suggested_summary_text=ai.summary.strip(),
                            source="ai",
                        ),
                        provider_unavailable=False,
                    )
                logger.warning("AI provajder vratio nevalidan predlog — koristi se fallback.")
            except AiProviderError as exc:
                logger.warning("AI provajder nedostupan — koristi se fallback: %s", exc)

        fallback = consensus_fallback.suggest(
            criterion_number=subcriteria.criterion_number,
            evidence=evidence,
            weaknesses=weaknesses,
            input_lang=input_lang,
            session_lang=session_lang,
        )
        return ConsensusResult(
            suggestion=ConsensusSuggestionOut(
                suggested_score=fallback.score,
                suggested_summary_text=fallback.summary,
                source="fallback",
                breakdown=fallback.breakdown,
            ),
            provider_unavailable=True,
        )
