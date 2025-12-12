"""
Sprint 16: Influencer Trend Engine - Orchestration Bridge

Integrates influencer campaigns with:
- Sprint 15: Decision Policy Engine (policy validation)
- Sprint 14: Cognitive Governance (risk simulation, ledger)
- Sprint 10: Supervisor Global (final approval)

Workflow:
1. Validate campaign plan
2. Simulate risks (Sprint 14)
3. Check policies (Sprint 15)
4. Register in ledger (Sprint 14)
5. Dispatch to orchestrator (Sprint 10)
6. Monitor execution

Author: STAKAZO Project
Date: 2025-12-12
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import json

from .influencer_campaign_planner import InfluencerCampaign, PublicationPhase


class CampaignStatus(Enum):
    """Campaign execution status"""
    PENDING = "pending"
    VALIDATED = "validated"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class CampaignValidationResult:
    """Result of campaign validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'recommendations': self.recommendations
        }


@dataclass
class RiskSimulationResult:
    """Result from Sprint 14 risk simulation"""
    overall_risk_score: float  # 0-1
    risk_breakdown: Dict[str, float]  # category -> score
    high_risk_factors: List[str]
    recommended_adjustments: List[str]
    approval_recommended: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'overall_risk_score': self.overall_risk_score,
            'risk_breakdown': self.risk_breakdown,
            'high_risk_factors': self.high_risk_factors,
            'recommended_adjustments': self.recommended_adjustments,
            'approval_recommended': self.approval_recommended
        }


@dataclass
class PolicyCheckResult:
    """Result from Sprint 15 policy check"""
    policies_passed: bool
    policies_checked: List[str]
    policy_violations: List[Dict[str, Any]]
    policy_recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'policies_passed': self.policies_passed,
            'policies_checked': self.policies_checked,
            'policy_violations': self.policy_violations,
            'policy_recommendations': self.policy_recommendations
        }


@dataclass
class CampaignExecution:
    """Campaign execution state"""
    campaign: InfluencerCampaign
    status: CampaignStatus
    validation_result: Optional[CampaignValidationResult]
    risk_simulation: Optional[RiskSimulationResult]
    policy_check: Optional[PolicyCheckResult]
    ledger_id: Optional[str]
    orchestrator_job_ids: List[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'campaign_id': self.campaign.campaign_id,
            'campaign_name': self.campaign.campaign_name,
            'status': self.status.value,
            'validation_result': self.validation_result.to_dict() if self.validation_result else None,
            'risk_simulation': self.risk_simulation.to_dict() if self.risk_simulation else None,
            'policy_check': self.policy_check.to_dict() if self.policy_check else None,
            'ledger_id': self.ledger_id,
            'orchestrator_job_ids': self.orchestrator_job_ids,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat()
        }


class OrchestrationBridgeTrends:
    """
    Bridges influencer campaigns with Sprint 10/14/15.
    
    Responsibilities:
    - Validate campaigns before execution
    - Simulate risks (Sprint 14)
    - Enforce policies (Sprint 15)
    - Register in ledger (Sprint 14)
    - Dispatch to orchestrator (Sprint 10)
    - Monitor progress
    """
    
    def __init__(
        self,
        governance_module=None,  # Sprint 14: CognitiveGovernanceOrchestrator
        policy_evaluator=None,  # Sprint 15: PolicyEvaluator
        supervisor_module=None,  # Sprint 10: SupervisorGlobal
        risk_threshold: float = 0.45
    ):
        """
        Initialize orchestration bridge.
        
        Args:
            governance_module: Sprint 14 governance orchestrator (optional)
            policy_evaluator: Sprint 15 policy evaluator (optional)
            supervisor_module: Sprint 10 supervisor (optional)
            risk_threshold: Maximum acceptable risk
        """
        self.governance = governance_module
        self.policy_evaluator = policy_evaluator
        self.supervisor = supervisor_module
        self.risk_threshold = risk_threshold
        
        # Track active campaigns
        self._active_campaigns: Dict[str, CampaignExecution] = {}
    
    def request_trend_launch(
        self,
        campaign: InfluencerCampaign,
        auto_approve: bool = False
    ) -> CampaignExecution:
        """
        Request trend launch (full validation + approval flow).
        
        Workflow:
        1. Validate campaign
        2. Simulate risks (Sprint 14)
        3. Check policies (Sprint 15)
        4. Register in ledger (Sprint 14)
        5. Request approval (Sprint 10 Supervisor)
        6. If approved, dispatch actions
        
        Args:
            campaign: Influencer campaign plan
            auto_approve: Skip human approval (for testing)
        
        Returns:
            CampaignExecution with status
        """
        print(f"\n🟣 Trend Launch Request: {campaign.campaign_name}")
        
        # Create execution state
        execution = CampaignExecution(
            campaign=campaign,
            status=CampaignStatus.PENDING,
            validation_result=None,
            risk_simulation=None,
            policy_check=None,
            ledger_id=None,
            orchestrator_job_ids=[],
            started_at=None,
            completed_at=None
        )
        
        # Step 1: Validate
        print("  ↳ [1/6] Validating campaign...")
        validation = self.validate_influencer_pack(campaign)
        execution.validation_result = validation
        
        if not validation.is_valid:
            execution.status = CampaignStatus.FAILED
            print("  ✗ Validation failed")
            return execution
        
        print("  ✓ Validation passed")
        execution.status = CampaignStatus.VALIDATED
        
        # Step 2: Simulate risks (Sprint 14)
        print("  ↳ [2/6] Simulating campaign risks...")
        risk_sim = self.simulate_campaign_risk(campaign)
        execution.risk_simulation = risk_sim
        
        if not risk_sim.approval_recommended:
            print(f"  ⚠ Risk simulation advises against approval (risk: {risk_sim.overall_risk_score:.2f})")
            
            if not auto_approve:
                execution.status = CampaignStatus.FAILED
                return execution
        
        print(f"  ✓ Risk acceptable ({risk_sim.overall_risk_score:.2f})")
        
        # Step 3: Check policies (Sprint 15)
        print("  ↳ [3/6] Checking decision policies...")
        policy_check = self.check_policies(campaign)
        execution.policy_check = policy_check
        
        if not policy_check.policies_passed:
            print(f"  ✗ Policy violations detected: {len(policy_check.policy_violations)}")
            
            if not auto_approve:
                execution.status = CampaignStatus.FAILED
                return execution
        
        print(f"  ✓ Policies passed ({len(policy_check.policies_checked)} checked)")
        
        # Step 4: Register in ledger (Sprint 14)
        print("  ↳ [4/6] Registering in governance ledger...")
        ledger_id = self.register_campaign_ledger(campaign, risk_sim)
        execution.ledger_id = ledger_id
        print(f"  ✓ Ledger entry: {ledger_id}")
        
        # Step 5: Request approval (Sprint 10)
        print("  ↳ [5/6] Requesting supervisor approval...")
        
        if auto_approve or self._request_supervisor_approval(campaign, risk_sim):
            execution.status = CampaignStatus.APPROVED
            print("  ✓ Approved")
        else:
            execution.status = CampaignStatus.ABORTED
            print("  ✗ Supervisor rejected")
            return execution
        
        # Step 6: Dispatch to orchestrator (Sprint 10)
        print("  ↳ [6/6] Dispatching actions to orchestrator...")
        job_ids = self.dispatch_actions_to_orchestrator(campaign)
        execution.orchestrator_job_ids = job_ids
        execution.status = CampaignStatus.IN_PROGRESS
        execution.started_at = datetime.now()
        print(f"  ✓ Dispatched {len(job_ids)} orchestrator jobs")
        
        # Track
        self._active_campaigns[campaign.campaign_id] = execution
        
        print(f"✓ Trend launch initiated: {campaign.campaign_id}")
        return execution
    
    def validate_influencer_pack(
        self,
        campaign: InfluencerCampaign
    ) -> CampaignValidationResult:
        """
        Validate campaign before execution.
        
        Checks:
        - Pack has minimum creators
        - Budget is reasonable
        - Timeline is valid
        - Variants are assigned
        - No scheduling conflicts
        """
        errors = []
        warnings = []
        recommendations = []
        
        pack = campaign.pack
        timeline = campaign.timeline
        
        # Check creators
        if pack.total_creators < 5:
            errors.append(f"Insufficient creators: {pack.total_creators} (min: 5)")
        
        if len(pack.primary_creators) < 2:
            errors.append(f"Insufficient primary creators: {len(pack.primary_creators)} (min: 2)")
        
        # Check budget
        if pack.total_budget_usd < 100:
            errors.append(f"Budget too low: ${pack.total_budget_usd} (min: $100)")
        
        if pack.average_cpm > 50:
            warnings.append(f"High average CPM: ${pack.average_cpm} (typical: $8-15)")
        
        # Check timeline
        campaign_duration_hours = (timeline.campaign_end - timeline.campaign_start).total_seconds() / 3600
        
        if campaign_duration_hours < 24:
            warnings.append(f"Short campaign: {campaign_duration_hours:.0f}h (recommended: 72h+)")
        
        if len(timeline.schedules) == 0:
            errors.append("No schedules defined")
        
        # Check diversity
        if pack.diversity_score < 0.5:
            warnings.append(f"Low diversity: {pack.diversity_score:.2f} (recommended: 0.6+)")
        
        # Check risk
        if pack.max_risk_score > self.risk_threshold:
            errors.append(f"Risk too high: {pack.max_risk_score:.2f} (max: {self.risk_threshold})")
        
        # Recommendations
        if pack.satellite_sync_count < 10:
            recommendations.append(f"Consider more satellites ({pack.satellite_sync_count} → 10+) for better organic spread")
        
        if campaign.expected_outcomes.confidence_level == "low":
            recommendations.append("Low confidence - consider higher-quality creators")
        
        is_valid = len(errors) == 0
        
        return CampaignValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def simulate_campaign_risk(
        self,
        campaign: InfluencerCampaign
    ) -> RiskSimulationResult:
        """
        Simulate campaign risk (Sprint 14 integration).
        
        If Sprint 14 available, use actual risk simulation.
        Otherwise, use heuristic estimation.
        """
        if self.governance:
            # Use Sprint 14 CognitiveGovernance
            try:
                # Call governance risk simulation
                sim_result = self.governance.simulate_campaign_risk(
                    campaign_data=campaign.to_dict()
                )
                
                return RiskSimulationResult(
                    overall_risk_score=sim_result['overall_risk'],
                    risk_breakdown=sim_result['breakdown'],
                    high_risk_factors=sim_result['high_risk_factors'],
                    recommended_adjustments=sim_result['adjustments'],
                    approval_recommended=sim_result['approval_recommended']
                )
            except Exception as e:
                print(f"Warning: Sprint 14 simulation failed, using fallback: {e}")
        
        # Fallback: heuristic risk estimation
        pack = campaign.pack
        risk_map = campaign.risk_map
        
        # Aggregate risks
        creator_risk = pack.max_risk_score
        trend_risk = campaign.blueprint.risk_score
        timeline_risk = risk_map.overall_risk_score
        
        # Weight risks
        overall_risk = (
            creator_risk * 0.50 +
            trend_risk * 0.30 +
            timeline_risk * 0.20
        )
        
        # Identify high-risk factors
        high_risk_factors = []
        
        if creator_risk > 0.4:
            high_risk_factors.append(f"High-risk creators (score: {creator_risk:.2f})")
        
        if trend_risk > 0.3:
            high_risk_factors.append(f"Edgy trend content (score: {trend_risk:.2f})")
        
        if len(risk_map.high_risk_windows) > 0:
            high_risk_factors.append(f"High-risk time windows ({len(risk_map.high_risk_windows)})")
        
        # Adjustments
        adjustments = []
        
        if overall_risk > 0.4:
            adjustments.append("Replace highest-risk creator with safer alternative")
            adjustments.append("Review trend content before publication")
        
        if len(risk_map.high_risk_windows) > 1:
            adjustments.append("Increase monitoring during high-risk windows")
        
        # Approval recommendation
        approval = overall_risk < self.risk_threshold
        
        return RiskSimulationResult(
            overall_risk_score=round(overall_risk, 3),
            risk_breakdown={
                'creators': round(creator_risk, 3),
                'trend_content': round(trend_risk, 3),
                'timeline': round(timeline_risk, 3)
            },
            high_risk_factors=high_risk_factors,
            recommended_adjustments=adjustments,
            approval_recommended=approval
        )
    
    def check_policies(
        self,
        campaign: InfluencerCampaign
    ) -> PolicyCheckResult:
        """
        Check campaign against decision policies (Sprint 15).
        
        Policies checked:
        - Budget limits
        - Risk thresholds
        - Creator diversity
        - Timeline constraints
        """
        if self.policy_evaluator:
            # Use Sprint 15 PolicyEvaluator
            try:
                policy_result = self.policy_evaluator.evaluate_campaign(
                    campaign_data=campaign.to_dict()
                )
                
                return PolicyCheckResult(
                    policies_passed=policy_result['passed'],
                    policies_checked=policy_result['policies_checked'],
                    policy_violations=policy_result['violations'],
                    policy_recommendations=policy_result['recommendations']
                )
            except Exception as e:
                print(f"Warning: Sprint 15 policy check failed, using fallback: {e}")
        
        # Fallback: basic policy checks
        policies_checked = [
            "budget_limit",
            "risk_threshold",
            "diversity_minimum",
            "creator_count"
        ]
        
        violations = []
        
        # Budget policy (max $10k per campaign)
        if campaign.pack.total_budget_usd > 10000:
            violations.append({
                'policy': 'budget_limit',
                'violation': f'Budget ${campaign.pack.total_budget_usd:,.2f} exceeds limit ($10,000)',
                'severity': 'high'
            })
        
        # Risk policy
        if campaign.pack.max_risk_score > self.risk_threshold:
            violations.append({
                'policy': 'risk_threshold',
                'violation': f'Risk {campaign.pack.max_risk_score:.2f} exceeds threshold ({self.risk_threshold})',
                'severity': 'high'
            })
        
        # Diversity policy
        if campaign.pack.diversity_score < 0.5:
            violations.append({
                'policy': 'diversity_minimum',
                'violation': f'Diversity {campaign.pack.diversity_score:.2f} below minimum (0.5)',
                'severity': 'medium'
            })
        
        # Creator count policy (min 5)
        if campaign.pack.total_creators < 5:
            violations.append({
                'policy': 'creator_count',
                'violation': f'Only {campaign.pack.total_creators} creators (min: 5)',
                'severity': 'high'
            })
        
        recommendations = []
        
        if len(violations) > 0:
            recommendations.append("Address policy violations before retrying")
        
        policies_passed = len([v for v in violations if v['severity'] == 'high']) == 0
        
        return PolicyCheckResult(
            policies_passed=policies_passed,
            policies_checked=policies_checked,
            policy_violations=violations,
            policy_recommendations=recommendations
        )
    
    def register_campaign_ledger(
        self,
        campaign: InfluencerCampaign,
        risk_sim: RiskSimulationResult
    ) -> str:
        """
        Register campaign in governance ledger (Sprint 14).
        
        Creates audit trail for compliance.
        """
        if self.governance:
            try:
                ledger_entry = self.governance.register_campaign(
                    campaign_id=campaign.campaign_id,
                    campaign_data=campaign.to_dict(),
                    risk_assessment=risk_sim.to_dict()
                )
                
                return ledger_entry['ledger_id']
            except Exception as e:
                print(f"Warning: Sprint 14 ledger registration failed: {e}")
        
        # Fallback: generate ledger ID
        ledger_id = f"ledger_{campaign.campaign_id}_{int(datetime.now().timestamp())}"
        
        print(f"  (Simulated ledger registration: {ledger_id})")
        
        return ledger_id
    
    def _request_supervisor_approval(
        self,
        campaign: InfluencerCampaign,
        risk_sim: RiskSimulationResult
    ) -> bool:
        """Request approval from Sprint 10 Supervisor"""
        if self.supervisor:
            try:
                approval = self.supervisor.approve_campaign(
                    campaign_id=campaign.campaign_id,
                    risk_score=risk_sim.overall_risk_score,
                    budget=campaign.pack.total_budget_usd
                )
                
                return approval['approved']
            except Exception as e:
                print(f"Warning: Supervisor approval failed: {e}")
        
        # Fallback: auto-approve if risk acceptable
        return risk_sim.approval_recommended
    
    def dispatch_actions_to_orchestrator(
        self,
        campaign: InfluencerCampaign
    ) -> List[str]:
        """
        Dispatch campaign actions to orchestrator (Sprint 10).
        
        Creates orchestrator jobs for:
        - Creator notifications
        - Satellite activations
        - Ad launches
        - Monitoring tasks
        """
        job_ids = []
        
        # Job 1: Notify creators
        job_id_creators = f"job_notify_creators_{campaign.campaign_id}_{int(datetime.now().timestamp())}"
        job_ids.append(job_id_creators)
        
        print(f"    • Created job: {job_id_creators} (notify {campaign.pack.total_creators} creators)")
        
        # Job 2: Schedule satellite activations
        for i, wave in enumerate(campaign.satellite_sync_schedule):
            job_id_sat = f"job_satellite_wave_{i+1}_{campaign.campaign_id}"
            job_ids.append(job_id_sat)
        
        print(f"    • Created {len(campaign.satellite_sync_schedule)} satellite wave jobs")
        
        # Job 3: Launch ads
        if len(campaign.ads_schedule) > 0:
            job_id_ads = f"job_ads_{campaign.campaign_id}"
            job_ids.append(job_id_ads)
            print(f"    • Created job: {job_id_ads} (ads)")
        
        # Job 4: Monitoring
        job_id_monitor = f"job_monitor_{campaign.campaign_id}"
        job_ids.append(job_id_monitor)
        print(f"    • Created job: {job_id_monitor} (monitoring)")
        
        # In production, actually dispatch to orchestrator
        if self.supervisor:
            try:
                self.supervisor.dispatch_jobs(job_ids)
            except Exception as e:
                print(f"Warning: Job dispatch failed: {e}")
        
        return job_ids
    
    def monitor_campaign_progress(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """Monitor active campaign progress"""
        if campaign_id not in self._active_campaigns:
            return {'error': 'Campaign not found'}
        
        execution = self._active_campaigns[campaign_id]
        
        # In production, query orchestrator for actual job status
        # For now, return execution state
        
        progress = {
            'campaign_id': campaign_id,
            'campaign_name': execution.campaign.campaign_name,
            'status': execution.status.value,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'total_jobs': len(execution.orchestrator_job_ids),
            'completed_jobs': 0,  # Would query orchestrator
            'current_phase': 'seed',  # Would determine from timeline + current time
            'expected_outcomes': execution.campaign.expected_outcomes.to_dict()
        }
        
        return progress


if __name__ == "__main__":
    # Example usage
    from .influencer_scraper import InfluencerScraper
    from .influencer_analysis import InfluencerAnalyzer
    from .influencer_selector import InfluencerSelector
    from .trend_synthesis_engine import TrendSynthesisEngine
    from .influencer_campaign_planner import InfluencerCampaignPlanner
    
    # Full pipeline
    scraper = InfluencerScraper()
    analyzer = InfluencerAnalyzer()
    selector = InfluencerSelector()
    trend_engine = TrendSynthesisEngine()
    planner = InfluencerCampaignPlanner()
    bridge = OrchestrationBridgeTrends()
    
    # Create campaign
    urls = [f"https://www.tiktok.com/@creator{i}" for i in range(1, 10)]
    raw_data = scraper.scrape_multiple(urls)
    profiles = analyzer.analyze_batch(raw_data)
    pack = selector.select_optimal_pack(profiles, budget_usd=5000.0)
    
    if pack:
        blueprint, variants = trend_engine.synthesize_trend(
            song_name="Bailando en la Noche",
            song_tempo=128,
            song_mood="energetic",
            visual_aesthetic="urban raw"
        )
        
        campaign = planner.plan_campaign(
            campaign_name="Bailando Launch",
            pack=pack,
            blueprint=blueprint,
            variants=variants
        )
        
        # Request launch
        execution = bridge.request_trend_launch(campaign, auto_approve=True)
        
        print(f"\n✓ Campaign execution: {execution.status.value}")
        print(f"  Ledger ID: {execution.ledger_id}")
        print(f"  Orchestrator jobs: {len(execution.orchestrator_job_ids)}")
    else:
        print("❌ Failed to create pack")
