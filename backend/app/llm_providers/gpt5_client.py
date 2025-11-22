"""
GPT-5 Client (OpenAI) - PASO 7.3 LIVE Implementation

This client is designed for SHORT, CRITICAL tasks:
- Recommendations (high-impact, prioritized actions)
- Action plans (critical execution steps)
- Quick diagnostic decisions

Status: LIVE MODE with fallback to STUB
- If AI_LLM_MODE="live" and API key present → real OpenAI API calls
- If AI_LLM_MODE="stub" or no API key → stub mode
- Automatic fallback to stub on API errors
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from app.ai_global_worker.schemas import (
    SystemSnapshot,
    AISummary,
    AIRecommendation,
    AIActionPlan,
)

logger = logging.getLogger(__name__)


class GPT5Client:
    """
    OpenAI GPT client for critical, short-context tasks.
    
    Implementation (PASO 7.3):
    --------------------------
    - Uses OpenAI Python SDK (openai>=1.0.0)
    - Real API calls to GPT-4 (or GPT-5 when available)
    - Automatic fallback to stub mode on errors
    - Retry logic with exponential backoff
    - Structured logging
    
    Configuration:
    --------------
    api_key: Optional[str] - OpenAI API key (from env: OPENAI_API_KEY)
    model: str - Model identifier (default from config: AI_OPENAI_MODEL_NAME)
    mode: str - "live" or "stub" (from config: AI_LLM_MODE)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        mode: str = "stub",
    ):
        """
        Initialize GPT client.
        
        Args:
            api_key: OpenAI API key (optional, None = stub mode)
            model: GPT model identifier (e.g., "gpt-4", "gpt-4-turbo")
            mode: Operation mode ("live" or "stub")
        """
        self.api_key = api_key
        self.model = model
        self.mode = mode
        self.client = None
        
        # Initialize OpenAI client if in live mode with API key
        if mode == "live" and api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=api_key)
                logger.info(f"GPT5Client initialized in LIVE mode with model: {model}")
            except ImportError:
                logger.warning("OpenAI SDK not installed. Install with: pip install openai")
                logger.info("Falling back to STUB mode")
                self.mode = "stub"
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                logger.info("Falling back to STUB mode")
                self.mode = "stub"
        else:
            logger.info(f"GPT5Client initialized in STUB mode (mode={mode}, has_key={api_key is not None})")
    
    async def _call_openai_with_retry(
        self,
        messages: list,
        response_format: dict,
        temperature: float,
        max_tokens: int,
        max_retries: int = 1,
    ) -> Optional[str]:
        """
        Call OpenAI API with retry logic.
        
        Args:
            messages: Chat messages
            response_format: Response format configuration
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            max_retries: Maximum number of retries (default: 1)
            
        Returns:
            Response text or None on failure
        """
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format=response_format,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=30.0,  # 30 second timeout
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2.0)  # 2 second backoff
                else:
                    logger.error(f"OpenAI API call failed after {max_retries + 1} attempts")
                    return None
        return None
    
    async def generate_summary(
        self,
        snapshot: SystemSnapshot,
    ) -> AISummary:
        """
        Generate system health summary using OpenAI GPT.
        
        Note: This method is available but NOT used by default router.
        Router policy assigns summary generation to Gemini 2.0.
        Kept for flexibility and testing purposes.
        
        Args:
            snapshot: Complete system state snapshot
            
        Returns:
            AISummary: Health assessment with score and insights
        """
        # Try live mode first if enabled
        if self.mode == "live" and self.client:
            try:
                logger.info("Generating summary using OpenAI (live mode)")
                
                # Build prompt
                prompt = self._build_summary_prompt(snapshot)
                
                # Call API with retry
                response_text = await self._call_openai_with_retry(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert system analyst for a social media automation platform.
Analyze the provided metrics and generate a comprehensive health summary in JSON format.

Return JSON with this structure:
{
  "overall_health": "excellent" | "good" | "warning" | "critical",
  "health_score": 0-100,
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "concerns": ["concern 1", "concern 2"],
  "positives": ["positive 1", "positive 2"]
}"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=800,
                )
                
                if response_text:
                    data = json.loads(response_text)
                    summary = AISummary(
                        **data,
                        generated_at=datetime.utcnow()
                    )
                    logger.info(f"OpenAI generated summary (success): health={summary.overall_health}, score={summary.health_score}")
                    return summary
                else:
                    logger.warning("OpenAI API returned no response, falling back to stub")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            except Exception as e:
                logger.error(f"Error calling OpenAI API: {e}")
        
        # Fallback to stub implementation
        logger.info("Generating summary using stub mode (fallback)")
        return self._generate_summary_stub(snapshot)
    
    def _build_summary_prompt(self, snapshot: SystemSnapshot) -> str:
        """Build prompt for summary generation."""
        return f"""Analyze this social media automation system:

METRICS:
- Queue: {snapshot.queue_pending} pending, {snapshot.queue_processing} processing, {snapshot.queue_failed} failed
- Publishing: {snapshot.publish_total_24h} in 24h ({snapshot.publish_success_rate:.1f}% success), {snapshot.publish_failed_24h} failed
- Content: {snapshot.clips_ready} clips ready, {snapshot.clips_pending_analysis} pending analysis
- Jobs: {snapshot.jobs_pending} pending, {snapshot.jobs_failed} failed
- Campaigns: {snapshot.campaigns_active} active, {snapshot.campaigns_draft} draft
- Alerts: {snapshot.alerts_critical} critical, {snapshot.alerts_warning} warnings
- System: Orchestrator {'running' if snapshot.orchestrator_running else 'stopped'}

Provide a concise health summary with score (0-100), key insights, concerns, and positives."""
    
    def _generate_summary_stub(self, snapshot: SystemSnapshot) -> AISummary:
        """Stub implementation using heuristics-based health scoring."""
        health_score = self._calculate_health_score(snapshot)
        health_status = self._get_health_status(health_score)
        
        return AISummary(
            overall_health=health_status,
            health_score=health_score,
            key_insights=[
                f"System processing {snapshot.publish_total_24h} publications in last 24h",
                f"Queue health: {snapshot.queue_pending} pending, {snapshot.queue_processing} processing",
                f"Success rate: {snapshot.publish_success_rate:.1f}%",
            ],
            concerns=self._generate_concerns(snapshot),
            positives=self._generate_positives(snapshot),
            generated_at=datetime.utcnow(),
        )
    
    async def generate_recommendations(
        self,
        snapshot: SystemSnapshot,
    ) -> List[AIRecommendation]:
        """
        Generate prioritized recommendations using OpenAI GPT.
        
        This is a PRIMARY use case for GPT (critical + short).
        Router policy assigns this task to GPT.
        
        Args:
            snapshot: Complete system state snapshot
            
        Returns:
            List[AIRecommendation]: Prioritized recommendations (1-5 items)
        """
        # Try live mode first if enabled
        if self.mode == "live" and self.client:
            try:
                logger.info("Generating recommendations using OpenAI (live mode)")
                
                # Build prompt
                prompt = self._build_recommendations_prompt(snapshot)
                
                # Call API with retry
                response_text = await self._call_openai_with_retry(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert system optimizer for a social media automation platform. 
Analyze the system state and generate 1-5 prioritized, actionable recommendations in JSON format.
Focus on high-impact, low-effort improvements.

Return JSON with this structure:
{
  "recommendations": [
    {
      "priority": "critical" | "high" | "medium" | "low",
      "category": "performance" | "content" | "system" | "automation",
      "title": "Brief title (max 60 chars)",
      "description": "Detailed description with specific metrics",
      "impact": "Expected impact if implemented",
      "effort": "low" | "medium" | "high",
      "action_type": "process_queue" | "process_pending_jobs" | "scale_workers" | null,
      "action_payload": {}
    }
  ]
}"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.5,
                    max_tokens=1200,
                )
                
                if response_text:
                    data = json.loads(response_text)
                    recommendations = [
                        AIRecommendation(
                            id=str(uuid.uuid4()),
                            **rec
                        )
                        for rec in data.get("recommendations", [])
                    ]
                    logger.info(f"OpenAI generated {len(recommendations)} recommendations (success)")
                    return recommendations
                else:
                    logger.warning("OpenAI API returned no response, falling back to stub")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            except Exception as e:
                logger.error(f"Error calling OpenAI API: {e}")
        
        # Fallback to stub implementation
        logger.info("Generating recommendations using stub mode (fallback)")
        return self._generate_recommendations_stub(snapshot)
    
    def _build_recommendations_prompt(self, snapshot: SystemSnapshot) -> str:
        """Build prompt for recommendations generation."""
        return f"""Analyze this social media automation system and provide recommendations:

SYSTEM METRICS:
- Queue: {snapshot.queue_pending} pending, {snapshot.queue_processing} processing, {snapshot.queue_failed} failed
- Publishing: {snapshot.publish_total_24h} publications in 24h, {snapshot.publish_success_rate:.1f}% success rate
- Publishing: {snapshot.publish_failed_24h} failed in 24h
- Content: {snapshot.clips_ready} clips ready, {snapshot.clips_pending_analysis} pending analysis
- Jobs: {snapshot.jobs_pending} pending, {snapshot.jobs_failed} failed
- Campaigns: {snapshot.campaigns_active} active, {snapshot.campaigns_draft} draft
- Alerts: {snapshot.alerts_critical} critical, {snapshot.alerts_warning} warnings
- System: Orchestrator {'running' if snapshot.orchestrator_running else 'stopped'}

Generate 1-5 prioritized recommendations to improve system performance and reliability.
Focus on actionable items with clear impact and effort estimates."""
    
    def _generate_recommendations_stub(self, snapshot: SystemSnapshot) -> List[AIRecommendation]:
        """Stub implementation using rule-based recommendation generation."""
        recommendations = []
        
        # Queue backlog
        if snapshot.queue_pending > 20:
            recommendations.append(AIRecommendation(
                id=str(uuid.uuid4()),
                priority="high",
                category="performance",
                title="Process Queue Backlog",
                description=f"Queue has {snapshot.queue_pending} pending items. Process backlog to maintain system responsiveness.",
                impact="Reduce publish delays and improve user experience",
                effort="medium",
                action_type="process_queue",
                action_payload={},
            ))
        
        # Low clip inventory
        if snapshot.clips_ready < 10:
            recommendations.append(AIRecommendation(
                id=str(uuid.uuid4()),
                priority="high",
                category="content",
                title="Increase Clip Production",
                description=f"Only {snapshot.clips_ready} clips ready. Upload more videos or process existing ones.",
                impact="Maintain consistent publishing schedule",
                effort="low",
                action_type="process_pending_jobs",
                action_payload={},
            ))
        
        # Failed jobs
        if snapshot.jobs_failed > 0:
            recommendations.append(AIRecommendation(
                id=str(uuid.uuid4()),
                priority="medium",
                category="system",
                title="Retry Failed Jobs",
                description=f"{snapshot.jobs_failed} jobs failed. Investigate and retry with exponential backoff.",
                impact="Recover lost content and reduce waste",
                effort="low",
            ))
        
        # Critical alerts
        if snapshot.alerts_critical > 0:
            recommendations.append(AIRecommendation(
                id=str(uuid.uuid4()),
                priority="critical",
                category="system",
                title="Address Critical Alerts",
                description=f"{snapshot.alerts_critical} critical alerts require immediate attention.",
                impact="Prevent system failures and data loss",
                effort="high",
            ))
        
        # Low success rate
        if snapshot.publish_success_rate < 80.0:
            recommendations.append(AIRecommendation(
                id=str(uuid.uuid4()),
                priority="high",
                category="performance",
                title="Improve Publish Success Rate",
                description=f"Success rate is {snapshot.publish_success_rate:.1f}%. Investigate and fix publish failures.",
                impact="Increase content delivery reliability",
                effort="high",
            ))
        
        return recommendations[:5]  # Max 5 recommendations
    
    async def generate_action_plan(
        self,
        snapshot: SystemSnapshot,
        recommendations: List[AIRecommendation],
    ) -> AIActionPlan:
        """
        Generate executable action plan using OpenAI GPT.
        
        This is a PRIMARY use case for GPT (critical + short).
        Router policy assigns this task to GPT.
        
        Args:
            snapshot: Complete system state snapshot
            recommendations: Previously generated recommendations
            
        Returns:
            AIActionPlan: Ordered steps with risk assessment
        """
        # Try live mode first if enabled
        if self.mode == "live" and self.client:
            try:
                logger.info("Generating action plan using OpenAI (live mode)")
                
                # Build prompt
                prompt = self._build_action_plan_prompt(snapshot, recommendations)
                
                # Call API with retry
                response_text = await self._call_openai_with_retry(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert operations planner for a social media automation platform.
Create a detailed, step-by-step action plan based on the provided recommendations.
Include risk assessment and automation capabilities.

Return JSON with this structure:
{
  "title": "Concise plan title",
  "objective": "What this plan aims to achieve",
  "steps": [
    {
      "step": 1,
      "action": "process_queue" | "manual_review" | "scale_workers" | etc,
      "description": "What to do in this step",
      "automated": true | false,
      "estimated_duration": "30 minutes" | "2 hours" | etc
    }
  ],
  "estimated_duration": "Total time estimate",
  "risk_level": "low" | "medium" | "high",
  "automated": true | false
}"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=1000,
                )
                
                if response_text:
                    data = json.loads(response_text)
                    plan = AIActionPlan(
                        plan_id=str(uuid.uuid4()),
                        **data
                    )
                    logger.info(f"OpenAI generated action plan with {len(plan.steps)} steps (success)")
                    return plan
                else:
                    logger.warning("OpenAI API returned no response, falling back to stub")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            except Exception as e:
                logger.error(f"Error calling OpenAI API: {e}")
        
        # Fallback to stub implementation
        logger.info("Generating action plan using stub mode (fallback)")
        return self._generate_action_plan_stub(snapshot, recommendations)
    
    def _build_action_plan_prompt(
        self,
        snapshot: SystemSnapshot,
        recommendations: List[AIRecommendation]
    ) -> str:
        """Build prompt for action plan generation."""
        recs_text = "\n".join([
            f"- [{rec.priority.upper()}] {rec.title}: {rec.description}"
            for rec in recommendations
        ])
        
        return f"""Create an action plan based on these recommendations:

RECOMMENDATIONS:
{recs_text}

SYSTEM CONTEXT:
- Queue: {snapshot.queue_pending} pending, {snapshot.queue_failed} failed
- Publishing: {snapshot.publish_success_rate:.1f}% success rate
- Clips ready: {snapshot.clips_ready}
- Critical alerts: {snapshot.alerts_critical}

Generate an ordered, step-by-step plan to address these recommendations.
Include risk assessment and automation feasibility."""
    
    def _generate_action_plan_stub(
        self,
        snapshot: SystemSnapshot,
        recommendations: List[AIRecommendation]
    ) -> AIActionPlan:
        """Stub implementation using rule-based plan generation."""
        steps = []
        step_num = 1
        
        # Build plan from recommendations
        for rec in recommendations:
            if rec.priority in ["critical", "high"]:
                steps.append({
                    "step": step_num,
                    "action": rec.action_type if rec.action_type else "manual_review",
                    "description": rec.description,
                    "automated": rec.action_type is not None,
                    "estimated_duration": "30 minutes" if rec.effort == "low" else "2 hours",
                })
                step_num += 1
        
        # Calculate risk level
        has_critical = any(r.priority == "critical" for r in recommendations)
        has_high_effort = any(r.effort == "high" for r in recommendations)
        
        if has_critical or has_high_effort:
            risk_level = "high"
        elif any(r.priority == "high" for r in recommendations):
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Check if fully automated
        automated = all(
            step.get("automated", False) for step in steps
        ) if steps else False
        
        return AIActionPlan(
            plan_id=str(uuid.uuid4()),
            title="System Optimization Plan",
            objective="Improve system health and performance based on current state",
            steps=steps if steps else [
                {
                    "step": 1,
                    "action": "monitor",
                    "description": "Continue monitoring system health",
                    "automated": True,
                    "estimated_duration": "Continuous",
                }
            ],
            estimated_duration=f"{len(steps) * 30} minutes" if steps else "Ongoing",
            risk_level=risk_level,
            automated=automated,
        )
    
    # Helper methods for stub implementation
    
    def _calculate_health_score(self, snapshot: SystemSnapshot) -> float:
        """Calculate health score from snapshot metrics."""
        score = 100.0
        
        # Queue backlog penalty
        if snapshot.queue_pending > 50:
            score -= 20
        elif snapshot.queue_pending > 20:
            score -= 10
        
        # Success rate impact
        if snapshot.publish_success_rate < 50:
            score -= 30
        elif snapshot.publish_success_rate < 80:
            score -= 15
        
        # Critical alerts
        score -= snapshot.alerts_critical * 10
        
        # Failed jobs
        if snapshot.jobs_failed > 5:
            score -= 15
        elif snapshot.jobs_failed > 0:
            score -= 5
        
        # Clip inventory
        if snapshot.clips_ready < 5:
            score -= 10
        
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
    
    def _generate_concerns(self, snapshot: SystemSnapshot) -> List[str]:
        """Generate list of concerns from snapshot."""
        concerns = []
        
        if snapshot.queue_pending > 20:
            concerns.append(f"High queue backlog: {snapshot.queue_pending} items")
        
        if snapshot.clips_ready < 10:
            concerns.append(f"Low clip inventory: {snapshot.clips_ready} clips ready")
        
        if snapshot.jobs_failed > 0:
            concerns.append(f"Failed jobs: {snapshot.jobs_failed} require attention")
        
        if snapshot.alerts_critical > 0:
            concerns.append(f"Critical alerts: {snapshot.alerts_critical} unresolved")
        
        if snapshot.publish_success_rate < 80:
            concerns.append(f"Low success rate: {snapshot.publish_success_rate:.1f}%")
        
        return concerns
    
    def _generate_positives(self, snapshot: SystemSnapshot) -> List[str]:
        """Generate list of positive aspects from snapshot."""
        positives = []
        
        if snapshot.publish_success_rate >= 90:
            positives.append(f"Excellent publish success rate: {snapshot.publish_success_rate:.1f}%")
        
        if snapshot.campaigns_active > 0:
            positives.append(f"{snapshot.campaigns_active} active campaigns running")
        
        if snapshot.orchestrator_running:
            positives.append("Orchestrator is running normally")
        
        if snapshot.alerts_critical == 0:
            positives.append("No critical alerts")
        
        if snapshot.queue_pending < 10:
            positives.append("Queue is healthy with minimal backlog")
        
        return positives
