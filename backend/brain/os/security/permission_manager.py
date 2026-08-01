"""Permission Manager implementation (Phase 11.8).

Validates requested permissions across filesystem, process, device, application, and system
categories, detecting admin privilege requirements and returning structured PermissionResult models.
"""

from typing import Optional

from brain.os.security.interfaces import IPermissionManager
from brain.os.security.security_models import (
    OperationCategory,
    PermissionLevel,
    PermissionResult,
    SecurityRequest,
)


class PermissionManager(IPermissionManager):
    """Provides permission validation and admin privilege detection."""

    def validate_permission(self, request: SecurityRequest) -> PermissionResult:
        """Validate permissions required for a security request."""
        op_lower = request.operation.lower()
        res_lower = request.target_resource.lower()
        req_perm = request.requested_permission

        # Detect admin requirements
        needs_admin = (
            req_perm == PermissionLevel.ADMIN
            or "admin" in op_lower
            or "format" in op_lower
            or "system32" in res_lower
            or "root" in res_lower
        )

        if needs_admin and not request.context.is_admin:
            return PermissionResult(
                granted=False,
                permission=PermissionLevel.DENIED,
                required_privilege="Administrator",
                is_admin_required=True,
                reason="Operation requires administrator privileges",
            )

        if req_perm == PermissionLevel.DENIED:
            return PermissionResult(
                granted=False,
                permission=PermissionLevel.DENIED,
                required_privilege="None",
                is_admin_required=False,
                reason="Requested permission level is explicitly DENIED",
            )

        return PermissionResult(
            granted=True,
            permission=req_perm,
            required_privilege="User" if not needs_admin else "Administrator",
            is_admin_required=needs_admin,
            reason="Permission granted",
        )
