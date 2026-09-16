"""Faza 1 — popuna naziva 28 podkriterijuma (name_me/name_en).

Database & Security Agent (CLAUDE.md Sekcija 7.2) — čisto podatkovna migracija
(UPDATE postojećih redova iz 0001, bez izmjene šeme/RLS-a). Zatvara napomenu
iz 0001_initial_schema.py: "Nazivi ... ostaju NULL dok se ne unesu iz zvaničnog
EIPA teksta".

IZVOR SADRŽAJA: eksterno dostavljen dokument (CAF_Questions_2.docx, 16.9.2026)
koji parafrazira CAF 2020 model — nije provjeren red-po-red naspram zvaničnog
EIPA CAF 2020/2026 teksta. Team Lead je odobrio djelimično usvajanje (nazivi +
usmjeravajuća pitanja kao sadržaj, model ocjenjivanja OSTAJE nepromijenjen:
slobodan tekst + ručna ocjena 1-5). Preporuka: provjeriti nazive naspram
zvaničnog dokumenta prije CER podnošenja (vidi i frontend
features/wizard/content/caf-content.ts, koji nosi istu napomenu i isti izvor).

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

# (code, name_me, name_en) — 28 podkriterijuma, redoslijed prati CAF strukturu
# (4-4-3-6-3 Enableri 1-5, 2-2-2-2 Rezultati 6-9), potvrđeno naspram distribucije
# koju je 0001 već pretpostavila.
NAMES = [
    ('1.1', 'Rukovodstvo razvija misiju, viziju, vrijednosti i strategiju', 'Leaders develop the mission, vision, values and strategy'),
    ('1.2', 'Rukovodstvo podržava sistem upravljanja institucijom', 'Leaders support the organisation''s management system'),
    ('1.3', 'Rukovodstvo komunicira sa zaposlenima i motiviše ih', 'Leaders communicate with and motivate staff'),
    ('1.4', 'Rukovodstvo upravlja odnosima sa političkim vlastima i zainteresovanim stranama', 'Leaders manage relationships with political authorities and stakeholders'),
    ('2.1', 'Prepoznavanje potreba i očekivanja zainteresovanih strana, eksternog okruženja i relevantnih upravljačkih informacija', 'Identify the needs and expectations of stakeholders, the external environment, and the relevant management information'),
    ('2.2', 'Razvoj strategija i planova na osnovu prikupljenih informacija', 'Develop strategies and plans based on gathered information'),
    ('2.3', 'Saopštavanje, sprovođenje i preispitivanje strategija i planova', 'Communicate, implement, and review strategies and plans'),
    ('2.4', 'Upravljanje promjenama i inovacijama radi agilnosti i otpornosti institucije', 'Manage change and innovation to ensure the agility and resilience of the organisation'),
    ('3.1', 'Upravljanje i unapređenje ljudskih resursa u podršci strategiji i planiranju institucije', 'Manage and improve human resources to support the strategy and planning of the organisation'),
    ('3.2', 'Razvoj i upravljanje kompetencijama zaposlenih', 'Develop and manage competencies of people'),
    ('3.3', 'Uključivanje i osnaživanje zaposlenih i podrška njihovoj dobrobiti', 'Involve and empower people and support their well-being'),
    ('4.1', 'Razvoj i upravljanje partnerstvima sa relevantnim organizacijama', 'Develop and manage partnerships with relevant organisations'),
    ('4.2', 'Razvoj i sprovođenje partnerstava sa građanima i organizacijama civilnog društva', 'Develop and implement partnerships with citizens and civil society organisations'),
    ('4.3', 'Upravljanje finansijama', 'Manage finances'),
    ('4.4', 'Upravljanje informacijama i znanjem', 'Manage information and knowledge'),
    ('4.5', 'Upravljanje tehnologijom', 'Manage technology'),
    ('4.6', 'Upravljanje prostorom i objektima', 'Manage facilities'),
    ('5.1', 'Oblikovanje i upravljanje procesima radi pružanja vrijednosti građanima/korisnicima i ostvarenja strateških ciljeva', 'Design and manage processes to deliver citizen/customer value and achieve strategic objectives'),
    ('5.2', 'Razvoj i pružanje usluga i proizvoda usmjerenih na građane/korisnike', 'Develop and deliver citizen/customer-oriented services and products'),
    ('5.3', 'Inoviranje procesa uz uključivanje građana/korisnika', 'Innovate processes involving citizens/customers'),
    ('6.1', 'Mjerenje percepcije', 'Perception measurements'),
    ('6.2', 'Mjerenje učinka', 'Performance measurements'),
    ('7.1', 'Mjerenje percepcije', 'Perception measurements'),
    ('7.2', 'Mjerenje učinka', 'Performance measurements'),
    ('8.1', 'Mjerenje percepcije', 'Perception measurements'),
    ('8.2', 'Mjerenje učinka', 'Performance measurements'),
    ('9.1', 'Eksterni rezultati', 'External results'),
    ('9.2', 'Interni rezultati', 'Internal results'),
]


def upgrade() -> None:
    subcriteria_table = sa.table(
        "subcriteria",
        sa.column("code", sa.String),
        sa.column("name_me", sa.String),
        sa.column("name_en", sa.String),
    )
    connection = op.get_bind()
    for code, name_me, name_en in NAMES:
        connection.execute(
            subcriteria_table.update()
            .where(subcriteria_table.c.code == code)
            .values(name_me=name_me, name_en=name_en)
        )


def downgrade() -> None:
    subcriteria_table = sa.table(
        "subcriteria",
        sa.column("code", sa.String),
        sa.column("name_me", sa.String),
        sa.column("name_en", sa.String),
    )
    connection = op.get_bind()
    for code, _, _ in NAMES:
        connection.execute(
            subcriteria_table.update()
            .where(subcriteria_table.c.code == code)
            .values(name_me=None, name_en=None)
        )

