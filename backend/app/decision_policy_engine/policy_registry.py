"""
Sprint 15: Decision Policy Engine - Policy Registry

Central registry for policy management: registration, retrieval, versioning,
deprecation, A/B testing, and policy lifecycle management.

Author: STAKAZO Project
Date: 2025-12-12
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from collections import defaultdict

from .decision_policy_models import (
    Policy,
    PolicyStatus,
    PolicyScope,
    AccountState
)


class PolicyRegistry:
    """
    Central registry for policy management.
    
    Features:
    - Policy registration and versioning
    - Active policy retrieval
    - Policy deprecation and archival
    - A/B testing support
    - Policy history tracking
    - Version comparison
    """
    
    def __init__(self, storage_path: str = "storage/policies"):
        """
        Initialize policy registry.
        
        Args:
            storage_path: Path to store policy JSON files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for fast retrieval
        self._policy_cache: Dict[str, Policy] = {}
        self._policy_history: Dict[str, List[Policy]] = defaultdict(list)
        
        # Load existing policies
        self._load_policies()
    
    def _load_policies(self):
        """Load all policies from storage into cache"""
        if not self.storage_path.exists():
            return
        
        for policy_file in self.storage_path.glob("*.json"):
            try:
                with open(policy_file, 'r', encoding='utf-8') as f:
                    policy_data = json.load(f)
                    policy = Policy.from_dict(policy_data)
                    
                    # Add to cache
                    self._policy_cache[policy.policy_id] = policy
                    
                    # Add to history
                    base_id = policy.policy_id.rsplit('_v', 1)[0] if '_v' in policy.policy_id else policy.policy_id
                    self._policy_history[base_id].append(policy)
            
            except Exception as e:
                print(f"Warning: Failed to load policy from {policy_file}: {e}")
        
        # Sort history by version
        for base_id in self._policy_history:
            self._policy_history[base_id].sort(
                key=lambda p: p.metadata.version,
                reverse=True
            )
    
    def register_policy(self, policy: Policy) -> bool:
        """
        Register a new policy or new version of existing policy.
        
        Args:
            policy: Policy to register
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate policy structure
            if not policy.policy_id:
                raise ValueError("Policy must have a policy_id")
            
            if not policy.metadata.version:
                raise ValueError("Policy must have a version")
            
            # Check if policy already exists
            if policy.policy_id in self._policy_cache:
                existing = self._policy_cache[policy.policy_id]
                if existing.metadata.version == policy.metadata.version:
                    raise ValueError(f"Policy {policy.policy_id} version {policy.metadata.version} already exists")
            
            # Save to storage
            policy_file = self.storage_path / f"{policy.policy_id}.json"
            with open(policy_file, 'w', encoding='utf-8') as f:
                f.write(policy.to_json())
            
            # Update cache
            self._policy_cache[policy.policy_id] = policy
            
            # Update history
            base_id = policy.policy_id.rsplit('_v', 1)[0] if '_v' in policy.policy_id else policy.policy_id
            self._policy_history[base_id].append(policy)
            self._policy_history[base_id].sort(key=lambda p: p.metadata.version, reverse=True)
            
            return True
        
        except Exception as e:
            print(f"Error registering policy: {e}")
            return False
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """
        Get a specific policy by ID.
        
        Args:
            policy_id: Policy identifier
        
        Returns:
            Policy if found, None otherwise
        """
        return self._policy_cache.get(policy_id)
    
    def get_active_policies(
        self,
        scope: Optional[PolicyScope] = None,
        account_state: Optional[AccountState] = None,
        a_b_test_group: Optional[str] = None
    ) -> List[Policy]:
        """
        Get all active policies, optionally filtered.
        
        Args:
            scope: Filter by policy scope
            account_state: Filter by applicable account state
            a_b_test_group: Filter by A/B test group
        
        Returns:
            List of active policies matching filters
        """
        policies = []
        
        for policy in self._policy_cache.values():
            # Status check
            if policy.status not in [PolicyStatus.ACTIVE, PolicyStatus.TESTING]:
                continue
            
            # Expiry check
            if policy.expiry_date and datetime.now() > policy.expiry_date:
                continue
            
            # Scope filter
            if scope and policy.scope != scope:
                continue
            
            # Account state filter
            if account_state and account_state not in policy.applicable_states:
                continue
            
            # A/B test filter
            if a_b_test_group is not None:
                if policy.metadata.a_b_test_group != a_b_test_group:
                    continue
            
            policies.append(policy)
        
        # Sort by confidence weight (descending)
        policies.sort(key=lambda p: p.confidence_weight, reverse=True)
        
        return policies
    
    def deprecate_policy(self, policy_id: str, reason: str = "") -> bool:
        """
        Deprecate a policy (mark as deprecated but keep in registry).
        
        Args:
            policy_id: Policy to deprecate
            reason: Reason for deprecation
        
        Returns:
            True if successful, False otherwise
        """
        policy = self.get_policy(policy_id)
        if not policy:
            return False
        
        try:
            # Update status
            policy.status = PolicyStatus.DEPRECATED
            
            # Update metadata
            if reason:
                policy.metadata.change_notes = f"DEPRECATED: {reason}"
            
            # Save updated policy
            policy_file = self.storage_path / f"{policy.policy_id}.json"
            with open(policy_file, 'w', encoding='utf-8') as f:
                f.write(policy.to_json())
            
            # Update cache
            self._policy_cache[policy_id] = policy
            
            return True
        
        except Exception as e:
            print(f"Error deprecating policy: {e}")
            return False
    
    def disable_policy(self, policy_id: str, reason: str = "") -> bool:
        """
        Disable a policy (can be re-enabled later).
        
        Args:
            policy_id: Policy to disable
            reason: Reason for disabling
        
        Returns:
            True if successful, False otherwise
        """
        policy = self.get_policy(policy_id)
        if not policy:
            return False
        
        try:
            policy.status = PolicyStatus.DISABLED
            
            if reason:
                policy.metadata.change_notes = f"DISABLED: {reason}"
            
            policy_file = self.storage_path / f"{policy.policy_id}.json"
            with open(policy_file, 'w', encoding='utf-8') as f:
                f.write(policy.to_json())
            
            self._policy_cache[policy_id] = policy
            
            return True
        
        except Exception as e:
            print(f"Error disabling policy: {e}")
            return False
    
    def enable_policy(self, policy_id: str) -> bool:
        """
        Enable a previously disabled policy.
        
        Args:
            policy_id: Policy to enable
        
        Returns:
            True if successful, False otherwise
        """
        policy = self.get_policy(policy_id)
        if not policy:
            return False
        
        if policy.status != PolicyStatus.DISABLED:
            return False
        
        try:
            policy.status = PolicyStatus.ACTIVE
            
            policy_file = self.storage_path / f"{policy.policy_id}.json"
            with open(policy_file, 'w', encoding='utf-8') as f:
                f.write(policy.to_json())
            
            self._policy_cache[policy_id] = policy
            
            return True
        
        except Exception as e:
            print(f"Error enabling policy: {e}")
            return False
    
    def archive_policy(self, policy_id: str) -> bool:
        """
        Archive a policy (remove from active cache but keep in storage).
        
        Args:
            policy_id: Policy to archive
        
        Returns:
            True if successful, False otherwise
        """
        policy = self.get_policy(policy_id)
        if not policy:
            return False
        
        try:
            policy.status = PolicyStatus.ARCHIVED
            
            policy_file = self.storage_path / f"{policy.policy_id}.json"
            with open(policy_file, 'w', encoding='utf-8') as f:
                f.write(policy.to_json())
            
            self._policy_cache[policy_id] = policy
            
            return True
        
        except Exception as e:
            print(f"Error archiving policy: {e}")
            return False
    
    def get_policy_history(self, base_policy_id: str) -> List[Policy]:
        """
        Get all versions of a policy.
        
        Args:
            base_policy_id: Base policy ID (without version suffix)
        
        Returns:
            List of policies sorted by version (newest first)
        """
        return self._policy_history.get(base_policy_id, [])
    
    def get_latest_version(self, base_policy_id: str) -> Optional[Policy]:
        """
        Get the latest version of a policy.
        
        Args:
            base_policy_id: Base policy ID (without version suffix)
        
        Returns:
            Latest policy version or None
        """
        history = self.get_policy_history(base_policy_id)
        return history[0] if history else None
    
    def compare_policy_versions(
        self,
        policy_id_1: str,
        policy_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two policy versions.
        
        Args:
            policy_id_1: First policy ID
            policy_id_2: Second policy ID
        
        Returns:
            Dictionary with comparison results
        """
        policy1 = self.get_policy(policy_id_1)
        policy2 = self.get_policy(policy_id_2)
        
        if not policy1 or not policy2:
            return {'error': 'One or both policies not found'}
        
        comparison = {
            'policy_1': {
                'id': policy1.policy_id,
                'version': policy1.metadata.version,
                'status': policy1.status.value,
                'confidence_weight': policy1.confidence_weight
            },
            'policy_2': {
                'id': policy2.policy_id,
                'version': policy2.metadata.version,
                'status': policy2.status.value,
                'confidence_weight': policy2.confidence_weight
            },
            'differences': []
        }
        
        # Compare key attributes
        if policy1.scope != policy2.scope:
            comparison['differences'].append(f"Scope: {policy1.scope.value} vs {policy2.scope.value}")
        
        if policy1.applicable_states != policy2.applicable_states:
            comparison['differences'].append("Applicable states differ")
        
        if len(policy1.conditions) != len(policy2.conditions):
            comparison['differences'].append(f"Conditions count: {len(policy1.conditions)} vs {len(policy2.conditions)}")
        
        if len(policy1.actions) != len(policy2.actions):
            comparison['differences'].append(f"Actions count: {len(policy1.actions)} vs {len(policy2.actions)}")
        
        if policy1.confidence_weight != policy2.confidence_weight:
            comparison['differences'].append(f"Confidence: {policy1.confidence_weight} vs {policy2.confidence_weight}")
        
        if policy1.max_allowed_risk_score != policy2.max_allowed_risk_score:
            comparison['differences'].append(f"Max risk: {policy1.max_allowed_risk_score} vs {policy2.max_allowed_risk_score}")
        
        return comparison
    
    def start_a_b_test(
        self,
        policy_id_a: str,
        policy_id_b: str
    ) -> bool:
        """
        Start an A/B test between two policy versions.
        
        Both policies will be marked as TESTING with a_b_test_group set.
        
        Args:
            policy_id_a: Policy A
            policy_id_b: Policy B
        
        Returns:
            True if successful, False otherwise
        """
        policy_a = self.get_policy(policy_id_a)
        policy_b = self.get_policy(policy_id_b)
        
        if not policy_a or not policy_b:
            return False
        
        try:
            # Update policies
            policy_a.status = PolicyStatus.TESTING
            policy_a.metadata.a_b_test_group = "A"
            
            policy_b.status = PolicyStatus.TESTING
            policy_b.metadata.a_b_test_group = "B"
            
            # Save both
            self.register_policy(policy_a)
            self.register_policy(policy_b)
            
            return True
        
        except Exception as e:
            print(f"Error starting A/B test: {e}")
            return False
    
    def end_a_b_test(
        self,
        winning_policy_id: str,
        losing_policy_id: str
    ) -> bool:
        """
        End an A/B test by promoting winner and deprecating loser.
        
        Args:
            winning_policy_id: Policy to promote to ACTIVE
            losing_policy_id: Policy to deprecate
        
        Returns:
            True if successful, False otherwise
        """
        winner = self.get_policy(winning_policy_id)
        loser = self.get_policy(losing_policy_id)
        
        if not winner or not loser:
            return False
        
        try:
            winner.status = PolicyStatus.ACTIVE
            winner.metadata.a_b_test_group = None
            winner.metadata.change_notes = f"A/B test winner over {losing_policy_id}"
            
            loser.status = PolicyStatus.DEPRECATED
            loser.metadata.change_notes = f"A/B test loser to {winning_policy_id}"
            
            self.register_policy(winner)
            self.register_policy(loser)
            
            return True
        
        except Exception as e:
            print(f"Error ending A/B test: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with statistics
        """
        status_counts = defaultdict(int)
        scope_counts = defaultdict(int)
        
        for policy in self._policy_cache.values():
            status_counts[policy.status.value] += 1
            scope_counts[policy.scope.value] += 1
        
        return {
            'total_policies': len(self._policy_cache),
            'by_status': dict(status_counts),
            'by_scope': dict(scope_counts),
            'total_base_policies': len(self._policy_history),
            'active_count': status_counts[PolicyStatus.ACTIVE.value],
            'testing_count': status_counts[PolicyStatus.TESTING.value],
            'deprecated_count': status_counts[PolicyStatus.DEPRECATED.value]
        }
    
    def search_policies(
        self,
        name_contains: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> List[Policy]:
        """
        Search policies by metadata.
        
        Args:
            name_contains: Search in policy name
            tags: Filter by tags (must have all)
            created_by: Filter by creator
        
        Returns:
            List of matching policies
        """
        results = []
        
        for policy in self._policy_cache.values():
            # Name filter
            if name_contains and name_contains.lower() not in policy.name.lower():
                continue
            
            # Tags filter
            if tags and not all(tag in policy.metadata.tags for tag in tags):
                continue
            
            # Creator filter
            if created_by and policy.metadata.created_by != created_by:
                continue
            
            results.append(policy)
        
        return results


if __name__ == "__main__":
    # Example usage
    from decision_policy_models import create_example_policy
    
    registry = PolicyRegistry()
    
    # Create and register example policy
    policy = create_example_policy()
    success = registry.register_policy(policy)
    print(f"✓ Policy registered: {success}")
    
    # Get active policies
    active = registry.get_active_policies()
    print(f"✓ Active policies: {len(active)}")
    
    # Get statistics
    stats = registry.get_statistics()
    print(f"✓ Registry statistics:")
    print(f"  Total: {stats['total_policies']}")
    print(f"  Active: {stats['active_count']}")
    print(f"  Testing: {stats['testing_count']}")
