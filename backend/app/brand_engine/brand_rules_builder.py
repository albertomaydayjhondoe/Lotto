"""
Brand Rules Builder - Auto-Generate BRAND_STATIC_RULES.json (Sprint 4)

Fusiona BrandProfile + MetricInsights + AestheticDNA → BRAND_STATIC_RULES.json

Características:
- Combina datos de 3 fuentes: interrogatorio, métricas, análisis visual
- Genera reglas específicas para contenido OFICIAL (NO satélites)
- Requiere aprobación final del artista
- Output: BRAND_STATIC_RULES.json con validación automática
- Versionado y auditoría de cambios

CRITICAL: Estas reglas SOLO aplican a canal oficial, nunca a satélites.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import uuid
import json

from .models import (
    BrandProfile,
    MetricInsights,
    AestheticDNA,
    BrandStaticRules,
    ColorRule,
    SceneRule,
    ContentRule,
    PerformanceThresholds,
    ContentCategory,
)

logger = logging.getLogger(__name__)


class BrandRulesBuilder:
    """
    Builds BRAND_STATIC_RULES.json from multiple data sources.
    
    Fuses artist identity, performance data, and visual DNA into
    comprehensive brand rules for official content.
    """
    
    def __init__(self):
        """Initialize rules builder."""
        self.profile: Optional[BrandProfile] = None
        self.insights: Optional[MetricInsights] = None
        self.dna: Optional[AestheticDNA] = None
        self.rules: Optional[BrandStaticRules] = None
    
    # ========================================
    # Data Loading
    # ========================================
    
    def load_brand_profile(self, profile: BrandProfile) -> None:
        """
        Load BrandProfile from interrogation.
        
        Args:
            profile: Complete brand profile from BrandInterrogator
        """
        self.profile = profile
        logger.info(f"Loaded BrandProfile {profile.profile_id} for {profile.artist_name}")
    
    def load_metric_insights(self, insights: MetricInsights) -> None:
        """
        Load MetricInsights from performance analysis.
        
        Args:
            insights: Insights from BrandMetricsAnalyzer
        """
        self.insights = insights
        logger.info(
            f"Loaded MetricInsights {insights.insights_id} "
            f"(sample size: {insights.sample_size}, confidence: {insights.confidence_level})"
        )
    
    def load_aesthetic_dna(self, dna: AestheticDNA) -> None:
        """
        Load AestheticDNA from visual analysis.
        
        Args:
            dna: DNA from BrandAestheticExtractor
        """
        self.dna = dna
        logger.info(
            f"Loaded AestheticDNA {dna.dna_id} "
            f"(coherence: {dna.overall_coherence_score:.2f})"
        )
    
    def validate_inputs(self) -> bool:
        """
        Validate that all required inputs are loaded.
        
        Returns:
            True if ready to build rules
        """
        if not self.profile:
            logger.error("Missing BrandProfile")
            return False
        
        if not self.insights:
            logger.error("Missing MetricInsights")
            return False
        
        if not self.dna:
            logger.error("Missing AestheticDNA")
            return False
        
        # Check data quality
        if self.insights.sample_size < 10:
            logger.warning(f"Low sample size for insights: {self.insights.sample_size}")
        
        if self.dna.analyzed_content_count < 10:
            logger.warning(f"Low content count for DNA: {self.dna.analyzed_content_count}")
        
        logger.info("All inputs validated and ready for rule generation")
        return True
    
    # ========================================
    # Rule Generation - Colors
    # ========================================
    
    def _build_color_rules(self) -> ColorRule:
        """
        Build color rules from profile + DNA + insights.
        
        Combines:
        - Artist's chosen colors (profile)
        - Dominant colors in actual content (DNA)
        - Best performing colors (insights)
        
        Returns:
            ColorRule object
        """
        # Start with artist's primary colors (highest priority)
        primary_palette = self.profile.primary_colors.copy() if self.profile else []
        
        # Add DNA dominant colors that aren't already included
        if self.dna:
            for color in self.dna.dominant_color_palette[:5]:  # Top 5 from DNA
                if color not in primary_palette:
                    primary_palette.append(color)
        
        # Validate with performance data (insights)
        # If a color performs poorly, flag it (but don't remove - artist chose it)
        if self.insights and self.insights.best_performing_colors:
            high_performing_colors = [
                item['color'] for item in self.insights.best_performing_colors[:5]
            ]
            logger.info(f"High-performing colors from metrics: {high_performing_colors}")
        
        # Secondary palette from DNA
        secondary_palette = []
        if self.dna and len(self.dna.dominant_color_palette) > 5:
            secondary_palette = self.dna.dominant_color_palette[5:10]
        
        # Prohibited colors (from artist profile)
        prohibited_colors = []  # Could extract from profile.prohibited_content
        
        # Min consistency score (based on DNA)
        min_consistency = 0.7  # Default
        if self.dna:
            # If DNA shows high consistency, require it
            if self.dna.color_consistency_score > 0.8:
                min_consistency = 0.75
            elif self.dna.color_consistency_score < 0.5:
                min_consistency = 0.6  # More lenient if artist is varied
        
        color_rule = ColorRule(
            primary_palette=primary_palette[:8],  # Limit to 8 primary colors
            secondary_palette=secondary_palette,
            prohibited_colors=prohibited_colors,
            min_consistency_score=min_consistency,
        )
        
        logger.info(f"Built ColorRule with {len(color_rule.primary_palette)} primary colors")
        
        return color_rule
    
    # ========================================
    # Rule Generation - Scenes
    # ========================================
    
    def _build_scene_rules(self) -> SceneRule:
        """
        Build scene rules from profile + DNA + insights.
        
        Combines:
        - Preferred/prohibited scenes (profile)
        - Recurring scenes in content (DNA)
        - Best performing scenes (insights)
        
        Returns:
            SceneRule object
        """
        # Start with artist's preferred scenes
        preferred_scenes = self.profile.preferred_scenes.copy() if self.profile else []
        
        # Add high-frequency scenes from DNA
        if self.dna:
            for scene_data in self.dna.recurring_scenes[:5]:  # Top 5
                scene = scene_data['scene']
                if scene not in preferred_scenes:
                    preferred_scenes.append(scene)
        
        # Validate with performance data
        if self.insights and self.insights.best_performing_scenes:
            top_performing = [
                item['scene'] for item in self.insights.best_performing_scenes[:5]
            ]
            # Prioritize scenes that appear in both DNA and insights
            for scene in top_performing:
                if scene not in preferred_scenes:
                    preferred_scenes.insert(0, scene)  # Add to front
            
            logger.info(f"Top performing scenes: {top_performing}")
        
        # All other scenes are "allowed" but not preferred
        allowed_scenes = []
        if self.dna:
            for scene_data in self.dna.recurring_scenes:
                scene = scene_data['scene']
                if scene not in preferred_scenes:
                    allowed_scenes.append(scene)
        
        # Prohibited scenes (from artist profile)
        prohibited_scenes = self.profile.prohibited_scenes.copy() if self.profile else []
        
        # Min quality score (based on insights)
        min_quality = 0.6  # Default
        if self.insights:
            # If average retention is high, require higher scene quality
            if self.insights.avg_retention_rate > 0.7:
                min_quality = 0.65
        
        scene_rule = SceneRule(
            preferred_scenes=preferred_scenes[:10],  # Top 10 preferred
            allowed_scenes=allowed_scenes,
            prohibited_scenes=prohibited_scenes,
            min_scene_quality_score=min_quality,
        )
        
        logger.info(
            f"Built SceneRule with {len(scene_rule.preferred_scenes)} preferred, "
            f"{len(scene_rule.prohibited_scenes)} prohibited"
        )
        
        return scene_rule
    
    # ========================================
    # Rule Generation - Content
    # ========================================
    
    def _build_content_rules(self) -> ContentRule:
        """
        Build content rules from profile.
        
        Uses:
        - Allowed/prohibited content (profile)
        - Tone requirements (profile)
        - Narrative guidelines (profile)
        
        Returns:
            ContentRule object
        """
        if not self.profile:
            return ContentRule()
        
        content_rule = ContentRule(
            allowed_themes=self.profile.allowed_content.copy(),
            prohibited_themes=self.profile.prohibited_content.copy(),
            tone_requirements=self.profile.tone_of_voice.copy(),
            narrative_guidelines=self.profile.key_messages.copy(),
        )
        
        logger.info(
            f"Built ContentRule with {len(content_rule.allowed_themes)} allowed themes, "
            f"{len(content_rule.prohibited_themes)} prohibited"
        )
        
        return content_rule
    
    # ========================================
    # Rule Generation - Performance Thresholds
    # ========================================
    
    def _build_performance_thresholds(self) -> PerformanceThresholds:
        """
        Build performance thresholds from insights.
        
        Sets minimum acceptable performance for official content.
        
        Returns:
            PerformanceThresholds object
        """
        # Default thresholds
        min_aesthetic = 0.6
        min_brand_affinity = 0.7
        min_virality = 0.5
        min_completion = 0.5
        
        # Adjust based on insights
        if self.insights:
            # Use average retention as baseline for completion
            if self.insights.avg_retention_rate > 0:
                min_completion = max(0.4, self.insights.avg_retention_rate * 0.8)
            
            # If DNA shows high coherence, require high brand affinity
            if self.dna and self.dna.overall_coherence_score > 0.8:
                min_brand_affinity = 0.75
        
        thresholds = PerformanceThresholds(
            min_aesthetic_score=min_aesthetic,
            min_brand_affinity_score=min_brand_affinity,
            min_virality_score=min_virality,
            min_completion_rate=min_completion,
        )
        
        logger.info(f"Built PerformanceThresholds (completion: {min_completion:.2f})")
        
        return thresholds
    
    # ========================================
    # Complete Rules Generation
    # ========================================
    
    def build_rules(
        self,
        require_manual_approval: bool = True,
        auto_reject_violations: bool = False
    ) -> BrandStaticRules:
        """
        Build complete BRAND_STATIC_RULES from all inputs.
        
        Args:
            require_manual_approval: Whether content needs manual approval
            auto_reject_violations: Whether to auto-reject rule violations
            
        Returns:
            Complete BrandStaticRules object
        """
        # Validate inputs
        if not self.validate_inputs():
            raise ValueError("Cannot build rules - missing or invalid inputs")
        
        rules_id = f"rules_{uuid.uuid4().hex[:12]}"
        version = "1.0.0"
        
        logger.info("Building complete brand static rules...")
        
        # Generate all rule components
        color_rules = self._build_color_rules()
        scene_rules = self._build_scene_rules()
        content_rules = self._build_content_rules()
        performance_thresholds = self._build_performance_thresholds()
        
        # Create complete rules
        rules = BrandStaticRules(
            rules_id=rules_id,
            version=version,
            based_on_profile_id=self.profile.profile_id,
            based_on_insights_id=self.insights.insights_id,
            based_on_dna_id=self.dna.dna_id,
            artist_name=self.profile.artist_name,
            brand_narrative=self.profile.brand_narrative,
            brand_vision=self.profile.brand_vision,
            color_rules=color_rules,
            scene_rules=scene_rules,
            content_rules=content_rules,
            performance_thresholds=performance_thresholds,
            require_manual_approval=require_manual_approval,
            auto_reject_on_rule_violation=auto_reject_violations,
            applies_to_categories=[ContentCategory.OFFICIAL],  # ONLY official content
            approved_by_artist=False,  # Needs artist approval
        )
        
        self.rules = rules
        
        logger.info(
            f"Built BrandStaticRules {rules_id} v{version} for {self.profile.artist_name}"
        )
        
        return rules
    
    # ========================================
    # Artist Approval Workflow
    # ========================================
    
    def generate_approval_summary(self) -> Dict[str, Any]:
        """
        Generate human-readable summary for artist approval.
        
        Returns:
            Dict with summary of all rules
        """
        if not self.rules:
            raise ValueError("No rules generated yet")
        
        return {
            "rules_id": self.rules.rules_id,
            "version": self.rules.version,
            "artist_name": self.rules.artist_name,
            "generated_at": self.rules.generated_at.isoformat(),
            
            "color_rules": {
                "primary_colors": self.rules.color_rules.primary_palette,
                "secondary_colors": self.rules.color_rules.secondary_palette,
                "prohibited_colors": self.rules.color_rules.prohibited_colors,
                "consistency_requirement": f"{self.rules.color_rules.min_consistency_score * 100:.0f}%",
            },
            
            "scene_rules": {
                "preferred_scenes": self.rules.scene_rules.preferred_scenes,
                "allowed_scenes": self.rules.scene_rules.allowed_scenes,
                "prohibited_scenes": self.rules.scene_rules.prohibited_scenes,
                "quality_requirement": f"{self.rules.scene_rules.min_scene_quality_score * 100:.0f}%",
            },
            
            "content_rules": {
                "allowed_themes": self.rules.content_rules.allowed_themes,
                "prohibited_themes": self.rules.content_rules.prohibited_themes,
                "tone_requirements": self.rules.content_rules.tone_requirements,
            },
            
            "performance_thresholds": {
                "min_aesthetic_score": f"{self.rules.performance_thresholds.min_aesthetic_score * 100:.0f}%",
                "min_brand_affinity": f"{self.rules.performance_thresholds.min_brand_affinity_score * 100:.0f}%",
                "min_completion_rate": f"{self.rules.performance_thresholds.min_completion_rate * 100:.0f}%",
            },
            
            "applies_to": [cat.value for cat in self.rules.applies_to_categories],
            
            "source_data": {
                "profile_id": self.rules.based_on_profile_id,
                "insights_sample_size": self.insights.sample_size if self.insights else 0,
                "dna_content_count": self.dna.analyzed_content_count if self.dna else 0,
                "insights_confidence": f"{self.insights.confidence_level * 100:.0f}%" if self.insights else "N/A",
            },
        }
    
    def approve_rules(self, approved_by: str) -> BrandStaticRules:
        """
        Mark rules as approved by artist.
        
        Args:
            approved_by: Artist identifier or name
            
        Returns:
            Approved rules
        """
        if not self.rules:
            raise ValueError("No rules to approve")
        
        self.rules.approved_by_artist = True
        self.rules.last_updated = datetime.utcnow()
        
        logger.info(f"Rules {self.rules.rules_id} approved by {approved_by}")
        
        return self.rules
    
    def reject_rules(self, reason: str) -> Dict[str, Any]:
        """
        Reject rules and provide feedback.
        
        Args:
            reason: Why rules were rejected
            
        Returns:
            Rejection info
        """
        if not self.rules:
            raise ValueError("No rules to reject")
        
        logger.warning(f"Rules {self.rules.rules_id} rejected: {reason}")
        
        return {
            "rules_id": self.rules.rules_id,
            "rejected": True,
            "reason": reason,
            "action_required": "Modify inputs or regenerate rules",
        }
    
    # ========================================
    # Export & Persistence
    # ========================================
    
    def export_to_json(self, file_path: Optional[str] = None) -> str:
        """
        Export rules to BRAND_STATIC_RULES.json.
        
        Args:
            file_path: Optional custom file path
            
        Returns:
            JSON string
        """
        if not self.rules:
            raise ValueError("No rules to export")
        
        if not self.rules.approved_by_artist:
            logger.warning("Exporting unapproved rules")
        
        # Convert to dict
        rules_dict = self.rules.model_dump()
        
        # Format as JSON
        json_str = json.dumps(rules_dict, indent=2, default=str)
        
        # Write to file if path provided
        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_str)
            logger.info(f"Exported rules to {file_path}")
        
        return json_str
    
    def save_to_database(self, db_client: Any) -> str:
        """
        Save rules to database.
        
        Args:
            db_client: Database client (implementation-specific)
            
        Returns:
            Rules ID
        """
        if not self.rules:
            raise ValueError("No rules to save")
        
        # Placeholder for database integration
        logger.info(f"Saving rules {self.rules.rules_id} to database")
        
        # TODO: Implement actual DB save
        # Example:
        # db_client.save_brand_rules(self.rules.model_dump())
        
        return self.rules.rules_id
    
    @classmethod
    def load_from_json(cls, json_str: str) -> BrandStaticRules:
        """
        Load rules from JSON string.
        
        Args:
            json_str: JSON string with rules
            
        Returns:
            BrandStaticRules object
        """
        rules_dict = json.loads(json_str)
        rules = BrandStaticRules(**rules_dict)
        
        logger.info(f"Loaded rules {rules.rules_id} from JSON")
        
        return rules
    
    # ========================================
    # Version Management
    # ========================================
    
    def create_new_version(
        self,
        changes_description: str,
        updated_profile: Optional[BrandProfile] = None,
        updated_insights: Optional[MetricInsights] = None,
        updated_dna: Optional[AestheticDNA] = None
    ) -> BrandStaticRules:
        """
        Create new version of rules with updates.
        
        Args:
            changes_description: Description of changes
            updated_profile: Optional updated profile
            updated_insights: Optional updated insights
            updated_dna: Optional updated DNA
            
        Returns:
            New version of rules
        """
        if not self.rules:
            raise ValueError("No existing rules to version")
        
        # Update inputs if provided
        if updated_profile:
            self.profile = updated_profile
        if updated_insights:
            self.insights = updated_insights
        if updated_dna:
            self.dna = updated_dna
        
        # Increment version
        current_version = self.rules.version
        major, minor, patch = current_version.split('.')
        new_version = f"{major}.{int(minor) + 1}.0"
        
        # Rebuild rules
        new_rules = self.build_rules(
            require_manual_approval=self.rules.require_manual_approval,
            auto_reject_violations=self.rules.auto_reject_on_rule_violation,
        )
        
        new_rules.version = new_version
        new_rules.approved_by_artist = False  # Needs re-approval
        
        logger.info(f"Created new version {new_version} of rules (was {current_version})")
        logger.info(f"Changes: {changes_description}")
        
        return new_rules
    
    # ========================================
    # Utilities
    # ========================================
    
    def get_build_status(self) -> Dict[str, Any]:
        """Get status of rule building process."""
        return {
            "profile_loaded": self.profile is not None,
            "insights_loaded": self.insights is not None,
            "dna_loaded": self.dna is not None,
            "rules_generated": self.rules is not None,
            "rules_approved": self.rules.approved_by_artist if self.rules else False,
            "ready_to_build": self.validate_inputs() if all([self.profile, self.insights, self.dna]) else False,
        }
    
    def clear_all(self) -> None:
        """Clear all loaded data."""
        self.profile = None
        self.insights = None
        self.dna = None
        self.rules = None
        logger.info("Cleared all builder data")
