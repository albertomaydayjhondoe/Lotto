"""
Curator AutoMailer — Blacklist Manager

Manages curator blacklists and exclusions.
STUB MODE: In-memory blacklist storage.
"""

from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
from enum import Enum


class BlacklistType(Enum):
    """Blacklist types"""
    PERMANENT = "permanent"
    PROJECT = "project"
    TEMPORARY = "temporary"


class BlacklistManagerStub:
    """
    STUB: Manages curator blacklists.
    
    Maintains separate lists for:
    - Permanent blacklist (unsubscribe requests)
    - Project-specific blacklist (not interested in this artist)
    - Temporary blacklist (try again later)
    
    In LIVE mode, this would use:
    - Database storage
    - CRM integration
    - GDPR compliance tracking
    
    Phase 3: In-memory storage only.
    """
    
    def __init__(self):
        self.stub_mode = True
        self._permanent_blacklist: Set[str] = set()
        self._project_blacklists: Dict[str, Set[str]] = {}
        self._temporary_blacklist: Dict[str, str] = {}  # email -> expiry_date
        
    def add_to_permanent_blacklist(
        self,
        curator_email: str,
        reason: str = "unsubscribe_request"
    ) -> Dict[str, Any]:
        """
        Add curator to permanent blacklist.
        
        Args:
            curator_email: Curator's email
            reason: Reason for blacklisting
            
        Returns:
            Confirmation dict
        """
        self._permanent_blacklist.add(curator_email.lower())
        
        # Remove from other lists
        for project_list in self._project_blacklists.values():
            project_list.discard(curator_email.lower())
        
        if curator_email.lower() in self._temporary_blacklist:
            del self._temporary_blacklist[curator_email.lower()]
        
        return {
            "status": "blacklisted_permanent",
            "curator_email": curator_email,
            "blacklist_type": "permanent",
            "reason": reason,
            "added_at": datetime.utcnow().isoformat(),
            "stub_mode": True
        }
    
    def add_to_project_blacklist(
        self,
        curator_email: str,
        project_id: str,
        reason: str = "not_interested"
    ) -> Dict[str, Any]:
        """
        Add curator to project-specific blacklist.
        
        Args:
            curator_email: Curator's email
            project_id: Project/artist ID
            reason: Reason for blacklisting
            
        Returns:
            Confirmation dict
        """
        if project_id not in self._project_blacklists:
            self._project_blacklists[project_id] = set()
        
        self._project_blacklists[project_id].add(curator_email.lower())
        
        return {
            "status": "blacklisted_project",
            "curator_email": curator_email,
            "project_id": project_id,
            "blacklist_type": "project",
            "reason": reason,
            "added_at": datetime.utcnow().isoformat(),
            "stub_mode": True
        }
    
    def add_to_temporary_blacklist(
        self,
        curator_email: str,
        days: int = 30,
        reason: str = "try_again_later"
    ) -> Dict[str, Any]:
        """
        Add curator to temporary blacklist.
        
        Args:
            curator_email: Curator's email
            days: Days to blacklist
            reason: Reason for temporary blacklist
            
        Returns:
            Confirmation dict
        """
        expiry = datetime.utcnow() + timedelta(days=days)
        self._temporary_blacklist[curator_email.lower()] = expiry.isoformat()
        
        return {
            "status": "blacklisted_temporary",
            "curator_email": curator_email,
            "blacklist_type": "temporary",
            "reason": reason,
            "expires_at": expiry.isoformat(),
            "days": days,
            "stub_mode": True
        }
    
    def is_blacklisted(
        self,
        curator_email: str,
        project_id: str = None
    ) -> Dict[str, Any]:
        """
        Check if curator is blacklisted.
        
        Args:
            curator_email: Curator's email
            project_id: Optional project ID to check
            
        Returns:
            Blacklist status dict
        """
        email_lower = curator_email.lower()
        
        # Check permanent blacklist
        if email_lower in self._permanent_blacklist:
            return {
                "is_blacklisted": True,
                "blacklist_type": "permanent",
                "reason": "Permanently blacklisted",
                "can_contact": False
            }
        
        # Check project blacklist
        if project_id and project_id in self._project_blacklists:
            if email_lower in self._project_blacklists[project_id]:
                return {
                    "is_blacklisted": True,
                    "blacklist_type": "project",
                    "project_id": project_id,
                    "reason": "Blacklisted for this project",
                    "can_contact": False
                }
        
        # Check temporary blacklist
        if email_lower in self._temporary_blacklist:
            expiry_str = self._temporary_blacklist[email_lower]
            expiry = datetime.fromisoformat(expiry_str)
            
            if datetime.utcnow() < expiry:
                return {
                    "is_blacklisted": True,
                    "blacklist_type": "temporary",
                    "expires_at": expiry_str,
                    "reason": "Temporarily blacklisted",
                    "can_contact": False
                }
            else:
                # Expired, remove from list
                del self._temporary_blacklist[email_lower]
        
        return {
            "is_blacklisted": False,
            "can_contact": True
        }
    
    def remove_from_blacklist(
        self,
        curator_email: str,
        blacklist_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Remove curator from blacklist.
        
        Args:
            curator_email: Curator's email
            blacklist_type: Type to remove from ("permanent", "project", "temporary", "all")
            
        Returns:
            Confirmation dict
        """
        email_lower = curator_email.lower()
        removed_from = []
        
        if blacklist_type in ["permanent", "all"]:
            if email_lower in self._permanent_blacklist:
                self._permanent_blacklist.discard(email_lower)
                removed_from.append("permanent")
        
        if blacklist_type in ["project", "all"]:
            for project_id, project_list in self._project_blacklists.items():
                if email_lower in project_list:
                    project_list.discard(email_lower)
                    removed_from.append(f"project_{project_id}")
        
        if blacklist_type in ["temporary", "all"]:
            if email_lower in self._temporary_blacklist:
                del self._temporary_blacklist[email_lower]
                removed_from.append("temporary")
        
        return {
            "status": "removed",
            "curator_email": curator_email,
            "removed_from": removed_from,
            "removed_at": datetime.utcnow().isoformat(),
            "stub_mode": True
        }
    
    def get_blacklist_stats(self) -> Dict[str, Any]:
        """Get blacklist statistics"""
        active_temporary = sum(
            1 for expiry_str in self._temporary_blacklist.values()
            if datetime.fromisoformat(expiry_str) > datetime.utcnow()
        )
        
        total_project = sum(len(plist) for plist in self._project_blacklists.values())
        
        return {
            "permanent_blacklist_count": len(self._permanent_blacklist),
            "project_blacklist_count": total_project,
            "temporary_blacklist_count": active_temporary,
            "total_blacklisted": len(self._permanent_blacklist) + total_project + active_temporary,
            "projects_with_blacklists": len(self._project_blacklists),
            "stub_mode": True
        }
    
    def export_blacklist(
        self,
        blacklist_type: str = "permanent"
    ) -> List[str]:
        """
        Export blacklist emails.
        
        Args:
            blacklist_type: Type to export ("permanent", "temporary", "all")
            
        Returns:
            List of blacklisted emails
        """
        if blacklist_type == "permanent":
            return list(self._permanent_blacklist)
        elif blacklist_type == "temporary":
            return [
                email for email, expiry_str in self._temporary_blacklist.items()
                if datetime.fromisoformat(expiry_str) > datetime.utcnow()
            ]
        elif blacklist_type == "all":
            all_emails = set(self._permanent_blacklist)
            all_emails.update(self._temporary_blacklist.keys())
            for project_list in self._project_blacklists.values():
                all_emails.update(project_list)
            return list(all_emails)
        
        return []
