"""Re-Export aus tt_common. Kanonische Implementierung: tt_common/authz.py.

Bewusst dünner Shim, damit bestehende Imports (from ..authz import ...) unverändert
weiterlaufen, während die Logik zentral in tt-common gepflegt wird.
"""

from tt_common.authz import (  # noqa: F401
    VALID_ROLES,
    normalize_role,
    normalize_permissions,
    normalize_memberships,
    normalize_role_permissions,
    has_role_permission,
    normalize_auth_payload,
    is_platform_admin,
    is_service_admin,
)
