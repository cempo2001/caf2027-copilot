"""
Uvozi sve modele na jedno mjesto — potrebno da `Base.metadata` (i time
Alembic autogenerate) "vidi" sve tabele. Redoslijed uvoza nije bitan za
SQLAlchemy (relationships se rešavaju lijeno preko stringova), ali je
ostavljen u redoslijedu zavisnosti radi čitljivosti.
"""

from caf.models.institution import Institution
from caf.models.user import RoleEnum, User
from caf.models.subcriteria import Subcriteria
from caf.models.self_assessment import SarStatus, SelfAssessment
from caf.models.subcriteria_score import SubcriteriaScore

__all__ = [
    "Institution",
    "User",
    "RoleEnum",
    "Subcriteria",
    "SelfAssessment",
    "SarStatus",
    "SubcriteriaScore",
]
