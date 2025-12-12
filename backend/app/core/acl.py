"""
Access Control List (ACL) System

Role-based access control for Memory Vault and system resources.
Phase 1: STUB mode with in-memory ACL matrix
Phase 2: Database-backed with audit logging
"""
from enum import Enum
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """System roles"""
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    AUDITOR = "auditor"
    DASHBOARD = "dashboard"
    DEVOPS = "devops"


class Resource(str, Enum):
    """Protected resources"""
    CAMPAIGN_HISTORY = "campaign_history"
    ML_FEATURES = "ml_features"
    AUDITS = "audits"
    ORCHESTRATOR_RUNS = "orchestrator_runs"
    CLIPS_METADATA = "clips_metadata"
    MEMORY_VAULT = "memory_vault"
    BACKUPS = "backups"
    CONFIG = "config"


class Permission(str, Enum):
    """Permission levels"""
    READ = "r"
    WRITE = "w"
    READ_WRITE = "r/w"
    NONE = "-"


# ACL Matrix: Role -> Resource -> Permission
ACL_MATRIX: Dict[Role, Dict[Resource, Permission]] = {
    Role.ORCHESTRATOR: {
        Resource.CAMPAIGN_HISTORY: Permission.READ_WRITE,
        Resource.ML_FEATURES: Permission.READ_WRITE,
        Resource.AUDITS: Permission.READ,
        Resource.ORCHESTRATOR_RUNS: Permission.READ_WRITE,
        Resource.CLIPS_METADATA: Permission.READ_WRITE,
        Resource.MEMORY_VAULT: Permission.READ_WRITE,
        Resource.BACKUPS: Permission.NONE,
        Resource.CONFIG: Permission.READ,
    },
    Role.WORKER: {
        Resource.CAMPAIGN_HISTORY: Permission.READ,
        Resource.ML_FEATURES: Permission.READ_WRITE,
        Resource.AUDITS: Permission.NONE,
        Resource.ORCHESTRATOR_RUNS: Permission.NONE,
        Resource.CLIPS_METADATA: Permission.READ_WRITE,
        Resource.MEMORY_VAULT: Permission.READ,
        Resource.BACKUPS: Permission.NONE,
        Resource.CONFIG: Permission.READ,
    },
    Role.AUDITOR: {
        Resource.CAMPAIGN_HISTORY: Permission.READ,
        Resource.ML_FEATURES: Permission.READ,
        Resource.AUDITS: Permission.READ_WRITE,
        Resource.ORCHESTRATOR_RUNS: Permission.READ,
        Resource.CLIPS_METADATA: Permission.READ,
        Resource.MEMORY_VAULT: Permission.READ,
        Resource.BACKUPS: Permission.NONE,
        Resource.CONFIG: Permission.NONE,
    },
    Role.DASHBOARD: {
        Resource.CAMPAIGN_HISTORY: Permission.READ,
        Resource.ML_FEATURES: Permission.READ,
        Resource.AUDITS: Permission.NONE,
        Resource.ORCHESTRATOR_RUNS: Permission.NONE,
        Resource.CLIPS_METADATA: Permission.READ,
        Resource.MEMORY_VAULT: Permission.READ,
        Resource.BACKUPS: Permission.NONE,
        Resource.CONFIG: Permission.READ,
    },
    Role.DEVOPS: {
        Resource.CAMPAIGN_HISTORY: Permission.READ,
        Resource.ML_FEATURES: Permission.READ,
        Resource.AUDITS: Permission.READ_WRITE,
        Resource.ORCHESTRATOR_RUNS: Permission.READ,
        Resource.CLIPS_METADATA: Permission.READ,
        Resource.MEMORY_VAULT: Permission.READ,
        Resource.BACKUPS: Permission.READ_WRITE,
        Resource.CONFIG: Permission.READ_WRITE,
    },
}


class ACLChecker:
    """Access Control List permission checker"""
    
    def __init__(self, mode: str = "STUB"):
        self.mode = mode
        self.matrix = ACL_MATRIX
        logger.info(f"ACLChecker initialized in {mode} mode")
    
    def check_permission(
        self,
        role: str,
        resource: str,
        action: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Check if role has permission to perform action on resource
        
        Args:
            role: User role (orchestrator, worker, etc)
            resource: Resource to access
            action: Action to perform ('r' for read, 'w' for write)
        
        Returns:
            Tuple of (allowed: bool, permission: str, reason: Optional[str])
        """
        try:
            # Convert strings to enums
            role_enum = Role(role)
            resource_enum = Resource(resource)
        except ValueError as e:
            logger.warning(f"Invalid role or resource: {e}")
            return False, "-", f"Invalid role or resource: {e}"
        
        # Get permission from matrix
        permission = self.matrix.get(role_enum, {}).get(resource_enum, Permission.NONE)
        
        # Check if action is allowed
        allowed = False
        reason = None
        
        if permission == Permission.NONE:
            reason = f"Role '{role}' has no access to '{resource}'"
        elif action == "r":
            if permission in [Permission.READ, Permission.READ_WRITE]:
                allowed = True
            else:
                reason = f"Role '{role}' does not have read permission for '{resource}'"
        elif action == "w":
            if permission == Permission.READ_WRITE:
                allowed = True
            else:
                reason = f"Role '{role}' does not have write permission for '{resource}'"
        else:
            reason = f"Invalid action: {action}"
        
        if allowed:
            logger.debug(f"[ACL] ALLOWED: {role} -> {action} on {resource}")
        else:
            logger.warning(f"[ACL] DENIED: {role} -> {action} on {resource} | Reason: {reason}")
        
        return allowed, permission.value, reason
    
    def get_role_permissions(self, role: str) -> Dict[str, str]:
        """Get all permissions for a role"""
        try:
            role_enum = Role(role)
        except ValueError:
            return {}
        
        permissions = self.matrix.get(role_enum, {})
        return {res.value: perm.value for res, perm in permissions.items()}
    
    def get_resource_access(self, resource: str) -> Dict[str, str]:
        """Get which roles can access a resource"""
        try:
            resource_enum = Resource(resource)
        except ValueError:
            return {}
        
        access = {}
        for role, resources in self.matrix.items():
            perm = resources.get(resource_enum, Permission.NONE)
            if perm != Permission.NONE:
                access[role.value] = perm.value
        
        return access


# Global instance
acl_checker = ACLChecker(mode="STUB")


def check_permission(role: str, resource: str, action: str) -> Tuple[bool, str, Optional[str]]:
    """Convenience function for permission checking"""
    return acl_checker.check_permission(role, resource, action)


def require_permission(role: str, resource: str, action: str):
    """
    Decorator/function to enforce permissions
    Raises PermissionError if not allowed
    """
    allowed, permission, reason = check_permission(role, resource, action)
    if not allowed:
        raise PermissionError(reason or f"Access denied: {role} -> {action} on {resource}")
    return True
