import re
import uuid
from typing import Optional


def parse_identifier(val: str, default_prefix: int = 1) -> Optional[uuid.UUID]:
    """Parse a UUID or shorthand test ID (e.g. user_001, txn_201) into a UUID.
    
    If standard UUID string: parses directly.
    If shorthand like 'user_1' or 'user_001': maps to 00000000-0000-0000-0000-000000000001.
    If invalid: returns None.
    """
    if not val:
        return None
    val_clean = val.strip()
    try:
        return uuid.UUID(val_clean)
    except ValueError:
        pass

    # Match patterns like user_001, txn_201, pay_301, acc_101
    match = re.search(r"(\d+)$", val_clean)
    if match:
        num = int(match.group(1))
        return uuid.UUID(f"{num:032x}")

    return None
