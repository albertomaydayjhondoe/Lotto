"""
Gemini 2.0 Client (Google) - PASO 7.3 LIVE Implementation

This client is designed for LONG CONTEXT, LESS CRITICAL tasks:
- Comprehensive summaries (system health overview)
- Long-form reports
- Extended narrative explanations
- Broad context analysis

Status: LIVE MODE with fallback to STUB
- If AI_LLM_MODE="live" and API key present → real Gemini API calls
- If AI_LLM_MODE="stub" or no API key → stub mode
- Automatic fallback to stub on API errors
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

from app.ai_global_worker.schemas import (
    SystemSnapshot,
    AISummary,
)

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Google Gemini 2.0 client for long context, less critical tasks.
    
    Implementation (PASO 7.3):
    --------------------------
    - Uses Google Generative AI Python SDK (google-generativeai)
    - Real API calls to Gemini 2.0 models
    - Automatic fallback to stub mode on errors
    - Retry logic with exponential backoff
    - Structured logging
    
    Configuration:
    --------------
    api_key: Optional[str] - Google API key (from env: GEMINI_API_KEY)
    model: str - Model identifier (default from config: AI_GEMINI_MODEL_NAME)
    mode: str - "live" or "stub" (from config: AI_LLM_MODE)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        mode: str = "stub",
    ):
        """
        Initialize Gemini 2.0 client.
        
        Args:
            api_key: Google Gemini API key (optional, None = stub mode)
            model: Gemini model identifier (e.g., "gemini-2.0-pro", "gemini-2.0-flash-exp")
            mode: Operation mode ("live" or "stub")
        """
        self.api_key = api_key
        self.model = model
        self.mode = mode
        self.client = None
        
        # Initialize Gemini client if in live mode with API key
        if mode == "live" and api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(model)
                logger.info(f"GeminiClient initialized in LIVE mode with model: {model}")
            except ImportError:
                logger.warning("Google Generative AI SDK not installed. Install with: pip install google-generativeai")
                logger.info("Falling back to STUB mode")
                self.mode = "stub"
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                logger.info("Falling back to STUB mode")
                self.mode = "stub"
        else:
            logger.info(f"GeminiClient initialized in STUB mode (mode={mode}, has_key={api_key is not None})")
    
    async def _call_gemini_with_retry(
        self,
        prompt: str,
        generation_config: dict,
        max_retries: int = 1,
    ) -> Optional[str]:
        """
        Call Gemini API with retry logic.
        
        Args:
            prompt: Generation prompt
            generation_config: Generation configuration
            max_retries: Maximum number of retries (default: 1)
            
        Returns:
            Response text or None on failure
        """
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.generate_content_async(
                    prompt,
                    generation_config=generation_config,
                )
                return response.text
            except Exception as e:
                logger.warning(f"Gemini API call failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2.0)  # 2 second backoff
                else:
                    logger.error(f"Gemini API call failed after {max_retries + 1} attempts")
                    return None
        return None
    
    async def generate_summary(
        self,
        snapshot: SystemSnapshot,
    ) -> AISummary:
        """
        Generate comprehensive system health summary using Gemini 2.0.
        
        This is the PRIMARY use case for Gemini 2.0 (long context + less critical).
        Router policy assigns summary generation to Gemini 2.0.
        
        Gemini 2.0 Advantages:
        ----------------------
        - Large context window (up to 2M tokens)
        - Cost-effective for long-form content
        - Good at comprehensive analysis
        - Natural narrative generation
        
        Args:
            snapshot: Complete system state snapshot
            
        Returns:
            AISummary: Comprehensive health assessment with detailed insights
        """
        # Try live mode first if enabled
        if self.mode == "live" and self.client:
            try:
                logger.info("Generating summary using Gemini (live mode)")
                
                # Build comprehensive prompt
                prompt = self._build_comprehensive_summary_prompt(snapshot)
                
                # Configure generation parameters
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                    "response_mime_type": "application/json",
                }
                
                # Call API with retry
                response_text = await self._call_gemini_with_retry(
                    prompt=prompt,
                    generation_config=generation_config,
                )
                
                if response_text:
                    data = json.loads(response_text)
                    summary = AISummary(
                        overall_health=data["overall_health"],
                        health_score=data["health_score"],
                        key_insights=data["key_insights"],
                        concerns=data["concerns"],
                        positives=data["positives"],
                        generated_at=datetime.utcnow(),
                    )
                    logger.info(f"Gemini generated summary (success): health={summary.overall_health}, score={summary.health_score}")
                    return summary
                else:
                    logger.warning("Gemini API returned no response, falling back to stub")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}")
        
        # Fallback to stub implementation
        logger.info("Generating summary using stub mode (fallback)")
        return self._generate_summary_stub(snapshot)
    
    def _build_comprehensive_summary_prompt(self, snapshot: SystemSnapshot) -> str:
        """Build comprehensive prompt for summary generation."""
        return f"""You are an expert system analyst for a social media automation platform.
Analyze the provided system metrics and generate a comprehensive health summary.

SYSTEM METRICS:
- Queue Status:
  * Pending: {snapshot.queue_pending} items
  * Processing: {snapshot.queue_processing} items
  * Failed: {snapshot.queue_failed} items

- Publishing Performance (24h):
  * Total publications: {snapshot.publish_total_24h}
  * Success rate: {snapshot.publish_success_rate:.1f}%
  * Failed publications: {snapshot.publish_failed_24h}

- Content Inventory:
  * Clips ready: {snapshot.clips_ready}
  * Clips pending analysis: {snapshot.clips_pending_analysis}

- Job Processing:
  * Pending: {snapshot.jobs_pending}
  * Failed: {snapshot.jobs_failed}

- Campaign Activity:
  * Active campaigns: {snapshot.campaigns_active}
  * Draft campaigns: {snapshot.campaigns_draft}

- System Alerts:
  * Critical alerts: {snapshot.alerts_critical}
  * Warning alerts: {snapshot.alerts_warning}

- System Status:
  * Orchestrator: {'Running' if snapshot.orchestrator_running else 'Stopped'}

TASK:
Generate a comprehensive health summary in JSON format with this exact structure:
{{
  "overall_health": "excellent" | "good" | "warning" | "critical",
  "health_score": <number 0-100>,
  "key_insights": [
    "<detailed insight about system state>",
    "<insight about trends or patterns>",
    "<insight about performance>"
  ],
  "concerns": [
    "<specific concern with metrics>",
    "<potential issue or risk>"
  ],
  "positives": [
    "<positive aspect of system performance>",
    "<strength or achievement>"
  ]
}}

Provide 3-5 key insights, 0-3 concerns, and 1-3 positives. Be specific and reference actual metrics."""
    
    def _generate_summary_stub(self, snapshot: SystemSnapshot) -> AISummary:
        """Stub implementation using heuristics-based health scoring."""
        health_score = self._calculate_health_score(snapshot)
        health_status = self._get_health_status(health_score)
        
        # Generate comprehensive insights (more detailed than GPT-5 stub)
        key_insights = self._generate_key_insights(snapshot)
        concerns = self._generate_concerns(snapshot)
        positives = self._generate_positives(snapshot)
        
        return AISummary(
            overall_health=health_status,
            health_score=health_score,
            key_insights=key_insights,
            concerns=concerns,
            positives=positives,
            generated_at=datetime.utcnow(),
        )
    
    # Helper methods for stub implementation
    
    def _calculate_health_score(self, snapshot: SystemSnapshot) -> float:
        """
        Calculate comprehensive health score from snapshot metrics.
        
        Uses similar logic to GPT-5 but can be tuned differently
        for Gemini's analysis style in future.
        """
        score = 100.0
        
        # Queue metrics
        if snapshot.queue_pending > 50:
            score -= 20
        elif snapshot.queue_pending > 20:
            score -= 10
        
        if snapshot.queue_failed > 10:
            score -= 15
        elif snapshot.queue_failed > 5:
            score -= 8
        
        # Publishing metrics
        if snapshot.publish_success_rate < 50:
            score -= 30
        elif snapshot.publish_success_rate < 80:
            score -= 15
        elif snapshot.publish_success_rate < 90:
            score -= 5
        
        # Content metrics
        if snapshot.clips_ready < 5:
            score -= 15
        elif snapshot.clips_ready < 10:
            score -= 8
        
        if snapshot.jobs_failed > 5:
            score -= 15
        elif snapshot.jobs_failed > 0:
            score -= 5
        
        # Alert metrics
        score -= snapshot.alerts_critical * 10
        score -= snapshot.alerts_warning * 3
        
        # Campaign activity (positive indicator)
        if snapshot.campaigns_active > 0:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def _get_health_status(self, score: float) -> str:
        """Convert health score to status string."""
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "warning"
        else:
            return "critical"
    
    def _generate_key_insights(self, snapshot: SystemSnapshot) -> List[str]:
        """
        Generate comprehensive key insights.
        
        Gemini is designed for longer, more detailed insights.
        """
        insights = []
        
        # Publishing overview
        insights.append(
            f"Publishing Activity: System processed {snapshot.publish_total_24h} "
            f"publications in the last 24 hours with a {snapshot.publish_success_rate:.1f}% "
            f"success rate. {snapshot.publish_failed_24h} publications failed."
        )
        
        # Queue status
        queue_health = "healthy" if snapshot.queue_pending < 20 else "congested"
        insights.append(
            f"Queue Status: Currently {queue_health} with {snapshot.queue_pending} pending items, "
            f"{snapshot.queue_processing} being processed, and {snapshot.queue_failed} failed."
        )
        
        # Content inventory
        inventory_status = "adequate" if snapshot.clips_ready >= 10 else "low"
        insights.append(
            f"Content Inventory: {inventory_status.capitalize()} with {snapshot.clips_ready} "
            f"clips ready for publishing and {snapshot.clips_pending_analysis} pending analysis."
        )
        
        # Campaign activity
        if snapshot.campaigns_active > 0:
            insights.append(
                f"Campaign Activity: {snapshot.campaigns_active} active campaigns running, "
                f"with {snapshot.campaigns_draft} in draft status."
            )
        
        # Orchestrator status
        orchestrator_status = "operational" if snapshot.orchestrator_running else "stopped"
        insights.append(
            f"Orchestrator: Currently {orchestrator_status}. "
            f"Executed {snapshot.orchestrator_actions_last_24h} actions in the last 24 hours."
        )
        
        # Alert summary
        if snapshot.alerts_critical > 0 or snapshot.alerts_warning > 0:
            insights.append(
                f"Alert Status: {snapshot.alerts_critical} critical alerts and "
                f"{snapshot.alerts_warning} warning alerts require attention."
            )
        else:
            insights.append("Alert Status: No active alerts - system is stable.")
        
        return insights
    
    def _generate_concerns(self, snapshot: SystemSnapshot) -> List[str]:
        """Generate comprehensive list of concerns."""
        concerns = []
        
        # Critical alerts first
        if snapshot.alerts_critical > 0:
            concerns.append(
                f"CRITICAL: {snapshot.alerts_critical} critical alerts detected. "
                "Immediate investigation required to prevent system failures."
            )
        
        # Queue issues
        if snapshot.queue_pending > 50:
            concerns.append(
                f"High queue backlog: {snapshot.queue_pending} items pending. "
                "This may cause significant publish delays and impact user experience."
            )
        elif snapshot.queue_pending > 20:
            concerns.append(
                f"Moderate queue backlog: {snapshot.queue_pending} items pending. "
                "Monitor closely to prevent further buildup."
            )
        
        if snapshot.queue_failed > 10:
            concerns.append(
                f"Significant queue failures: {snapshot.queue_failed} failed items. "
                "Investigate error patterns and implement fixes."
            )
        
        # Publishing performance
        if snapshot.publish_success_rate < 80:
            concerns.append(
                f"Low publish success rate: {snapshot.publish_success_rate:.1f}%. "
                f"With {snapshot.publish_failed_24h} failures in last 24h, "
                "troubleshooting is needed to improve reliability."
            )
        
        # Content inventory
        if snapshot.clips_ready < 5:
            concerns.append(
                f"Critical clip shortage: Only {snapshot.clips_ready} clips ready. "
                "Content production may stall without immediate action."
            )
        elif snapshot.clips_ready < 10:
            concerns.append(
                f"Low clip inventory: {snapshot.clips_ready} clips ready. "
                "Increase production to maintain publishing schedule."
            )
        
        # Failed jobs
        if snapshot.jobs_failed > 5:
            concerns.append(
                f"Multiple job failures: {snapshot.jobs_failed} jobs failed. "
                "This indicates potential systemic issues requiring investigation."
            )
        elif snapshot.jobs_failed > 0:
            concerns.append(
                f"Job failures detected: {snapshot.jobs_failed} jobs failed. "
                "Review logs and retry with appropriate fixes."
            )
        
        # Orchestrator
        if not snapshot.orchestrator_running:
            concerns.append(
                "Orchestrator is not running. Automated workflows may be impacted."
            )
        
        return concerns
    
    def _generate_positives(self, snapshot: SystemSnapshot) -> List[str]:
        """Generate comprehensive list of positive aspects."""
        positives = []
        
        # Excellent success rate
        if snapshot.publish_success_rate >= 95:
            positives.append(
                f"Outstanding publish reliability: {snapshot.publish_success_rate:.1f}% success rate "
                f"with {snapshot.publish_total_24h} publications in 24h demonstrates excellent system stability."
            )
        elif snapshot.publish_success_rate >= 90:
            positives.append(
                f"Strong publish performance: {snapshot.publish_success_rate:.1f}% success rate "
                "indicates reliable content delivery."
            )
        
        # Active campaigns
        if snapshot.campaigns_active > 3:
            positives.append(
                f"High campaign activity: {snapshot.campaigns_active} active campaigns "
                "demonstrate strong platform utilization."
            )
        elif snapshot.campaigns_active > 0:
            positives.append(
                f"{snapshot.campaigns_active} active campaigns running successfully."
            )
        
        # Healthy queue
        if snapshot.queue_pending < 10 and snapshot.queue_failed < 5:
            positives.append(
                "Queue is healthy with minimal backlog and few failures. "
                "Processing is efficient and responsive."
            )
        
        # Good clip inventory
        if snapshot.clips_ready >= 20:
            positives.append(
                f"Excellent content inventory: {snapshot.clips_ready} clips ready "
                "ensures sustained publishing capacity."
            )
        elif snapshot.clips_ready >= 10:
            positives.append(
                f"Adequate content inventory: {snapshot.clips_ready} clips ready "
                "supports current publishing needs."
            )
        
        # No critical alerts
        if snapshot.alerts_critical == 0:
            positives.append(
                "No critical alerts - all major system components operating normally."
            )
        
        # Orchestrator active
        if snapshot.orchestrator_running:
            if snapshot.orchestrator_actions_last_24h > 0:
                positives.append(
                    f"Orchestrator is operational and executed {snapshot.orchestrator_actions_last_24h} "
                    "actions in the last 24 hours, maintaining automated workflows."
                )
            else:
                positives.append(
                    "Orchestrator is running and ready to execute automated actions."
                )
        
        # High volume processing
        if snapshot.publish_total_24h > 50:
            positives.append(
                f"High-volume processing: Successfully handling {snapshot.publish_total_24h} "
                "publications per day demonstrates strong system capacity."
            )
        
        return positives
