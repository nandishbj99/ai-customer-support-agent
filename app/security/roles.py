from enum import Enum
from typing import List, Set


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"
    SERVICE = "SERVICE"


# Role hierarchy definition (higher roles include permissions of lower roles)
ROLE_HIERARCHY = {
    UserRole.CUSTOMER: {UserRole.CUSTOMER},
    UserRole.SUPPORT_AGENT: {UserRole.CUSTOMER, UserRole.SUPPORT_AGENT},
    UserRole.SUPERVISOR: {UserRole.CUSTOMER, UserRole.SUPPORT_AGENT, UserRole.SUPERVISOR},
    UserRole.ADMIN: {UserRole.CUSTOMER, UserRole.SUPPORT_AGENT, UserRole.SUPERVISOR, UserRole.ADMIN, UserRole.SERVICE},
    UserRole.SERVICE: {UserRole.SERVICE},
}


def has_role(user_role: str, required_roles: List[UserRole]) -> bool:
    """Check if a user role satisfies any of the required roles considering hierarchy."""
    try:
        current = UserRole(user_role.upper())
    except (ValueError, AttributeError):
        return False

    effective_roles: Set[UserRole] = ROLE_HIERARCHY.get(current, {current})
    return any(req in effective_roles for req in required_roles)
