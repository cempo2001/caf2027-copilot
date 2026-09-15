"""
Jezik sesije kao eksplicitan parametar — CLAUDE.md Sekcija 6.

Princip (Sekcija 6.1/6.2): jezik NIJE pretpostavljen default niti se
"prevodi naknadno" — svaki servis koji generiše tekst (error poruke,
izvještaji, AI pozivi) prima jezik eksplicitno kao argument.

Ovaj modul drži samo mehanizam za error poruke (backend-generisan tekst
koji korisnik vidi). Za korisnički unos i AI/CIP tekst, jezik dolazi kroz
`consensus_service` odnosno `sar_service`, ne odavde.
"""

from typing import Literal

Locale = Literal["me", "en"]

# Lokalizovane error poruke — backend vraća poruku na jeziku iz JWT
# claim-a, ne generičku poruku koju frontend "nagađa" da prevede.
_MESSAGES: dict[str, dict[Locale, str]] = {
    "sar_locked": {
        "me": "Samoprocjena je odobrena i trajno zaključana — izmjena nije moguća.",
        "en": "This self-assessment has been approved and permanently locked — editing is not possible.",
    },
    "tenant_mismatch": {
        "me": "Nemate pristup resursima ove institucije.",
        "en": "You do not have access to this institution's resources.",
    },
    "invalid_credentials": {
        "me": "Neispravno korisničko ime ili lozinka.",
        "en": "Invalid username or password.",
    },
    "validation_error": {
        "me": "Podaci koje ste unijeli nisu validni.",
        "en": "The data you submitted is not valid.",
    },
    "ai_provider_unavailable": {
        "me": "AI servis trenutno nije dostupan — korišćen je lokalni matematički fallback.",
        "en": "The AI service is currently unavailable — the local math fallback was used.",
    },
    "not_found": {
        "me": "Traženi resurs ne postoji ili vam nije dostupan.",
        "en": "The requested resource does not exist or is not available to you.",
    },
    "insufficient_role": {
        "me": "Vaša uloga nema ovlašćenje za ovu radnju.",
        "en": "Your role is not authorised to perform this action.",
    },
    "sar_incomplete": {
        "me": "Samoprocjena se ne može odobriti dok svih 28 podkriterijuma nije ocijenjeno.",
        "en": "The self-assessment cannot be approved until all 28 sub-criteria have been scored.",
    },
    "unknown_subcriteria": {
        "me": "Nepoznata šifra podkriterijuma.",
        "en": "Unknown sub-criterion code.",
    },
}


def translate(key: str, locale: Locale) -> str:
    """
    Vraća lokalizovanu poruku po ključu. Nepoznat ključ eksplicitno puca
    (KeyError) umjesto da tiho vrati prazan string — grešku u razvoju je
    jeftinije uhvatiti odmah, ne u produkciji na jeziku koji niko nije testirao.
    """
    entry = _MESSAGES[key]
    return entry.get(locale, entry["en"])
