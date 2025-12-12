"""
SPRINT 11 - Satellite Intelligence Optimization
Module: Satellite Intelligence API

API interna para generar propuestas de contenido inteligentes.

Orquesta todos los módulos de Sprint 11:
- Identity-Aware Clip Scoring
- Timing Optimizer
- Universe Profile Manager
- Sound Test Recommender
- Variant Generator Bridge
- Proposal Evaluator

Integra con:
- Sprint 10 Supervisor (validation)
- Sprint 8 Satellite Engine (behavior simulation)
- Vision Engine (clip metadata)
- Content Engine (audio features)
- ML Persistence (virality models)
- Rules Engine (policy constraints)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import uuid

from .sat_intel_contracts import (
    ContentProposal,
    ProposalBatch,
    GenerateProposalRequest,
    GenerateProposalResponse,
    EvaluateProposalRequest,
    EvaluateProposalResponse,
    ContentMetadata,
    ClipScore,
    TimingWindow,
    ContentVariant,
    ProposalStatus,
    ProposalPriority,
    RiskLevel,
    calculate_priority,
    calculate_risk_level,
)

from .identity_aware_clip_scoring import IdentityAwareClipScorer
from .timing_optimizer import TimingOptimizer
from .universe_profile_manager import UniverseProfileManager
from .variant_generator_bridge import VariantGeneratorBridge
from .proposal_evaluator import ProposalEvaluator

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class SatIntelConfig:
    """Configuración global del Satellite Intelligence System"""
    
    # Generation limits
    max_proposals_per_batch: int = 100
    max_accounts_per_batch: int = 50
    
    # Quality thresholds
    min_clip_score: float = 0.5
    min_timing_score: float = 0.4
    max_risk_score: float = 0.7
    
    # Batch optimization
    ensure_timing_diversity: bool = True
    balance_niches: bool = True
    
    # Integration flags
    use_supervisor_validation: bool = True
    simulate_only: bool = False


# ============================================================================
# SATELLITE INTELLIGENCE API
# ============================================================================

class SatelliteIntelligenceAPI:
    """
    API principal del Satellite Intelligence System.
    
    Flujo de generación de propuestas:
    1. Cargar content metadata (Vision + Content Engines)
    2. Cargar account profiles (Universe Profile Manager)
    3. Score clips para cada account (Identity-Aware Scorer)
    4. Generar timing windows (Timing Optimizer)
    5. Generar variantes (Variant Generator)
    6. Crear propuestas
    7. Evaluar propuestas (Proposal Evaluator)
    8. Filtrar y rankear
    9. (Opcional) Validar con Supervisor (Sprint 10)
    10. Retornar batch
    """
    
    def __init__(self, config: Optional[SatIntelConfig] = None):
        self.config = config or SatIntelConfig()
        
        # Initialize submodules
        self.clip_scorer = IdentityAwareClipScorer()
        self.timing_optimizer = TimingOptimizer()
        self.profile_manager = UniverseProfileManager()
        self.variant_generator = VariantGeneratorBridge()
        self.proposal_evaluator = ProposalEvaluator()
        
        logger.info("SatelliteIntelligenceAPI initialized")
    
    # ========================================================================
    # PUBLIC API - PROPOSAL GENERATION
    # ========================================================================
    
    def generate_proposals(
        self,
        request: GenerateProposalRequest
    ) -> GenerateProposalResponse:
        """
        Genera propuestas de contenido basadas en request.
        
        Args:
            request: GenerateProposalRequest con content pool, accounts, constraints
        
        Returns:
            GenerateProposalResponse con proposals, statistics, errors
        """
        start_time = datetime.now()
        batch_id = f"batch_{start_time.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Generating proposals: batch_id={batch_id}, "
                   f"content_pool={len(request.content_ids)}, "
                   f"simulate_only={request.simulate_only}")
        
        errors = []
        
        try:
            # 1. Load content metadata
            content_metadata = self._load_content_metadata(request.content_ids)
            if not content_metadata:
                errors.append("Failed to load content metadata")
                return self._empty_response(batch_id, start_time, errors)
            
            # 2. Load account profiles
            accounts = self._load_account_profiles(request.account_ids)
            if not accounts:
                errors.append("No active accounts available")
                return self._empty_response(batch_id, start_time, errors)
            
            # 3. Score clips for each account
            logger.debug("Scoring clips...")
            score_matrix = self.clip_scorer.score_matrix(
                content_metadata,
                accounts,
                start_time
            )
            
            # 4. Generate timing windows
            logger.debug("Generating timing windows...")
            timing_windows = self.timing_optimizer.batch_find_windows(
                accounts,
                start_time,
                request.target_timeframe_hours,
                ensure_diversity=self.config.ensure_timing_diversity
            )
            
            # 5. Generate variants
            logger.debug("Generating content variants...")
            # TODO: Load audio track IDs from content metadata
            audio_track_ids = {}  # content_id -> audio_id
            variants_matrix = self.variant_generator.batch_generate_variants(
                request.content_ids,
                accounts,
                audio_track_ids
            )
            
            # 6. Create proposals
            logger.debug("Creating proposals...")
            proposals = self._create_proposals_from_matrix(
                score_matrix,
                timing_windows,
                variants_matrix,
                accounts,
                batch_id
            )
            
            # 7. Filter by constraints
            proposals = self._filter_by_constraints(
                proposals,
                request.min_clip_score,
                request.max_risk_score
            )
            
            # 8. Evaluate proposals
            logger.debug("Evaluating proposals...")
            accounts_dict = {a.account_id: a for a in accounts}
            evaluations = self.proposal_evaluator.batch_evaluate(proposals, accounts_dict)
            
            # 9. Filter approved and rank
            approved_proposals = [
                p for p, e in zip(proposals, evaluations) if e.approved
            ]
            
            ranked_proposals = self._rank_proposals(approved_proposals)
            
            # 10. Limit to max_proposals
            if request.max_proposals:
                ranked_proposals = ranked_proposals[:request.max_proposals]
            
            # 11. Update proposal statuses
            for proposal in ranked_proposals:
                proposal.status = ProposalStatus.APPROVED
            
            # 12. Statistics
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            high_priority_count = sum(
                1 for p in ranked_proposals
                if p.priority in [ProposalPriority.HIGH, ProposalPriority.CRITICAL]
            )
            
            response = GenerateProposalResponse(
                batch_id=batch_id,
                generated_at=start_time,
                proposals=ranked_proposals,
                total_generated=len(proposals),
                high_priority_count=high_priority_count,
                approved_count=len(ranked_proposals),
                rejected_count=len(proposals) - len(ranked_proposals),
                processing_time_ms=processing_time_ms,
                errors=errors
            )
            
            logger.info(f"Batch {batch_id} complete: {len(ranked_proposals)} proposals approved, "
                       f"{processing_time_ms:.0f}ms")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating proposals: {e}", exc_info=True)
            errors.append(f"Generation error: {str(e)}")
            return self._empty_response(batch_id, start_time, errors)
    
    def evaluate_proposals(
        self,
        request: EvaluateProposalRequest
    ) -> EvaluateProposalResponse:
        """
        Evalúa propuestas existentes.
        
        Args:
            request: EvaluateProposalRequest con proposal_ids, options
        
        Returns:
            EvaluateProposalResponse con evaluations, statistics
        """
        logger.info(f"Evaluating {len(request.proposal_ids)} proposals")
        
        # TODO: Load proposals from DB
        # Por ahora: mock implementation
        
        evaluated_at = datetime.now()
        
        return EvaluateProposalResponse(
            evaluated_at=evaluated_at,
            evaluations=[],
            total_evaluated=0,
            approved_count=0,
            rejected_count=0,
            requires_human_review_count=0
        )
    
    def get_proposals(
        self,
        batch_id: Optional[str] = None,
        account_id: Optional[str] = None,
        status: Optional[ProposalStatus] = None,
        limit: int = 100
    ) -> List[ContentProposal]:
        """
        Recupera propuestas con filtros opcionales.
        
        Args:
            batch_id: Filtrar por batch
            account_id: Filtrar por cuenta
            status: Filtrar por status
            limit: Límite de resultados
        
        Returns:
            Lista de ContentProposal
        """
        # TODO: Implement DB retrieval
        logger.info(f"Getting proposals: batch={batch_id}, account={account_id}, "
                   f"status={status}, limit={limit}")
        
        return []
    
    # ========================================================================
    # INTERNAL - DATA LOADING
    # ========================================================================
    
    def _load_content_metadata(self, content_ids: List[str]) -> List[ContentMetadata]:
        """
        Carga metadata de contenidos desde Vision + Content Engines.
        
        TODO: Integración real con engines
        """
        logger.debug(f"Loading metadata for {len(content_ids)} contents")
        
        # Mock implementation
        from .sat_intel_contracts import ContentType
        
        metadata_list = []
        for content_id in content_ids[:20]:  # Limit for demo
            metadata = ContentMetadata(
                content_id=content_id,
                content_type=ContentType.VIDEO_CLIP,
                duration_seconds=12.0,
                visual_tags=["music", "performance", "studio"],
                color_palette=["#FF5733", "#3498DB"],
                scene_types=["studio", "closeup"],
                motion_intensity=0.7,
                audio_track_id=f"audio_{content_id}",
                bpm=120,
                energy=0.75,
                valence=0.65,
                avg_retention=None,
                avg_virality_score=None,
                file_path=f"/content/{content_id}.mp4",
                created_at=datetime.now()
            )
            metadata_list.append(metadata)
        
        logger.debug(f"Loaded {len(metadata_list)} content metadata")
        return metadata_list
    
    def _load_account_profiles(self, account_ids: Optional[List[str]]) -> List:
        """
        Carga profiles de cuentas desde Universe Profile Manager.
        
        Si account_ids es None, retorna todas las cuentas activas.
        """
        if account_ids:
            logger.debug(f"Loading profiles for {len(account_ids)} accounts")
            profiles = [
                self.profile_manager.get_profile(aid)
                for aid in account_ids
            ]
            profiles = [p for p in profiles if p and p.is_active]
        else:
            logger.debug("Loading all active accounts")
            profiles = self.profile_manager.get_active_accounts()
        
        logger.debug(f"Loaded {len(profiles)} account profiles")
        return profiles
    
    # ========================================================================
    # INTERNAL - PROPOSAL CREATION
    # ========================================================================
    
    def _create_proposals_from_matrix(
        self,
        score_matrix: Dict[str, Dict[str, ClipScore]],
        timing_windows: Dict[str, TimingWindow],
        variants_matrix: Dict[str, Dict[str, ContentVariant]],
        accounts: List,
        batch_id: str
    ) -> List[ContentProposal]:
        """Crea propuestas combinando scores, timing, variantes"""
        
        proposals = []
        
        for content_id in score_matrix:
            for account_id in score_matrix[content_id]:
                clip_score = score_matrix[content_id][account_id]
                timing_window = timing_windows.get(account_id)
                variant = variants_matrix[content_id][account_id]
                
                if not timing_window:
                    logger.warning(f"No timing window for account {account_id}, skipping")
                    continue
                
                # Find account
                account = next((a for a in accounts if a.account_id == account_id), None)
                if not account:
                    continue
                
                # Calculate priority and risk
                priority = calculate_priority(clip_score, timing_window.optimal_score, 0.0)
                risk_score = self._calculate_risk_score(clip_score, account)
                risk_level = calculate_risk_level(risk_score)
                
                # Create proposal
                proposal = ContentProposal(
                    proposal_id=f"prop_{uuid.uuid4().hex[:12]}",
                    created_at=datetime.now(),
                    content_id=content_id,
                    account_id=account_id,
                    niche_id=account.niche_id,
                    variant=variant,
                    timing_window=timing_window,
                    clip_score=clip_score,
                    priority=priority,
                    risk_level=risk_level,
                    risk_score=risk_score,
                    rationale=self._generate_rationale(clip_score, timing_window, priority),
                    alternatives_considered=[],
                    constraints_applied=[],
                    status=ProposalStatus.PENDING_EVALUATION,
                    metadata={
                        "batch_id": batch_id,
                        "uses_official_assets": False,
                    }
                )
                
                proposals.append(proposal)
        
        logger.debug(f"Created {len(proposals)} proposals")
        return proposals
    
    def _calculate_risk_score(self, clip_score: ClipScore, account) -> float:
        """Calcula risk score combinado"""
        
        # Base risk from clip score
        base_risk = 1.0 - clip_score.total_score
        
        # Account risk signals
        account_risk = 0.0
        if account.shadowban_signals > 0:
            account_risk += 0.3
        if account.correlation_signals > 0:
            account_risk += 0.2
        
        # Warmup risk
        if not account.warmup_completed:
            account_risk += 0.1
        
        total_risk = min((base_risk * 0.6 + account_risk * 0.4), 1.0)
        return total_risk
    
    def _generate_rationale(
        self,
        clip_score: ClipScore,
        timing_window: TimingWindow,
        priority: ProposalPriority
    ) -> str:
        """Genera rationale para una propuesta"""
        
        parts = [
            f"Priority: {priority.value}",
            f"Clip score: {clip_score.total_score:.2f}",
            f"Timing: {timing_window.optimal_score:.2f}",
        ]
        
        # Highlight strengths
        if clip_score.niche_match_score >= 0.7:
            parts.append("Strong niche match")
        if clip_score.virality_score >= 0.7:
            parts.append("High virality potential")
        if clip_score.uniqueness_score >= 0.9:
            parts.append("Fresh content")
        
        return " | ".join(parts)
    
    # ========================================================================
    # INTERNAL - FILTERING & RANKING
    # ========================================================================
    
    def _filter_by_constraints(
        self,
        proposals: List[ContentProposal],
        min_clip_score: float,
        max_risk_score: float
    ) -> List[ContentProposal]:
        """Filtra propuestas por constraints"""
        
        filtered = [
            p for p in proposals
            if p.clip_score.total_score >= min_clip_score
            and p.risk_score <= max_risk_score
        ]
        
        logger.debug(f"Filtered: {len(filtered)} / {len(proposals)} proposals")
        return filtered
    
    def _rank_proposals(self, proposals: List[ContentProposal]) -> List[ContentProposal]:
        """Rankea propuestas por prioridad y score"""
        
        def priority_value(p: ContentProposal) -> int:
            mapping = {
                ProposalPriority.LOW: 1,
                ProposalPriority.MEDIUM: 2,
                ProposalPriority.HIGH: 3,
                ProposalPriority.CRITICAL: 4,
            }
            return mapping.get(p.priority, 1)
        
        ranked = sorted(
            proposals,
            key=lambda p: (
                priority_value(p),
                p.clip_score.total_score,
                p.timing_window.optimal_score,
                -p.risk_score
            ),
            reverse=True
        )
        
        return ranked
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _empty_response(
        self,
        batch_id: str,
        start_time: datetime,
        errors: List[str]
    ) -> GenerateProposalResponse:
        """Crea response vacío en caso de error"""
        
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return GenerateProposalResponse(
            batch_id=batch_id,
            generated_at=start_time,
            proposals=[],
            total_generated=0,
            high_priority_count=0,
            approved_count=0,
            rejected_count=0,
            processing_time_ms=processing_time_ms,
            errors=errors
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def generate_proposals_simple(
    content_ids: List[str],
    max_proposals: int = 50
) -> GenerateProposalResponse:
    """
    Helper para generación simple de propuestas.
    
    Útil para testing y demos.
    """
    api = SatelliteIntelligenceAPI()
    
    request = GenerateProposalRequest(
        content_ids=content_ids,
        account_ids=None,  # All active accounts
        max_proposals=max_proposals,
        min_clip_score=0.5,
        max_risk_score=0.7,
        target_timeframe_hours=24,
        include_alternatives=True,
        simulate_only=False
    )
    
    return api.generate_proposals(request)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SatIntelConfig",
    "SatelliteIntelligenceAPI",
    "generate_proposals_simple",
]
