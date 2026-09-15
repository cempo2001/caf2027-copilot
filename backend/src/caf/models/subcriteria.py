"""
Subcriteria — statička referentna tabela CAF okvira (9 kriterijuma / 28
podkriterijuma). CLAUDE.md Sekcija 1, Nivo 1.

VAŽNO — namjerno prazan sadržaj za sada: `name_me`/`name_en` i
`guiding_question_me`/`guiding_question_en` NISU popunjeni tačnim
tekstom CAF 2020/2026 modela u seed migraciji. Zvaničan tekst svih 28
podkriterijuma i usmjeravajućih pitanja mora doći iz zvaničnog CAF
dokumenta (EIPA), ne izmišljen ili parafraziran od strane agenta —
CLAUDE.md ne dozvoljava izmišljen/pretpostavljen sadržaj kad je u
pitanju zvanična metodologija. Sponsor/CAFLead ili Chief Architect agent
mora dostaviti tačan izvorni tekst prije nego što se Faza 1 UI pokaže
stvarnim korisnicima — seed migracija (Korak 4) ubacuje samo strukturu
(kodove i brojeve kriterijuma), ne i tekst.

NIJE tenant-scoped — nema `institution_id`, referentni podaci su
zajednički za sve institucije, pa RLS nije potreban (vidi guardrail u
CLAUDE.md Sekciji 7.2: RLS je obavezan samo za tabele koje SADRŽE
institution_id).
"""

from sqlalchemy import Integer, String, Text

from sqlalchemy.orm import Mapped, mapped_column

from caf.db.base import Base


class Subcriteria(Base):
    __tablename__ = "subcriteria"

    # Kod oblika "1.1".."9.3" — prirodan primarni ključ (CAF standard,
    # stabilan, ne mijenja se).
    code: Mapped[str] = mapped_column(String(4), primary_key=True)
    criterion_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Namjerno nullable=True dok se ne popuni zvaničnim tekstom (vidi
    # napomenu u docstring-u iznad).
    name_me: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    guiding_question_me: Mapped[str | None] = mapped_column(Text, nullable=True)
    guiding_question_en: Mapped[str | None] = mapped_column(Text, nullable=True)

    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
