from dataclasses import dataclass
from typing import Optional


@dataclass
class LeadData:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    problem: Optional[str] = None
    intent_level: Optional[str] = None  # low / medium / high

    def is_qualified(self) -> bool:
        """
        Business rule for qualification.
        Adjust later as needed.
        """
        return bool(
            self.intent_level == "high" and
            (self.email or self.phone)
        )
