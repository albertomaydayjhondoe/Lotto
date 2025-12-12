"""
Sentiment Analyzer - Audience Sentiment Analysis for Community Manager AI

Analyzes comments and reactions to detect sentiment and actionable insights.
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from collections import Counter

from .models import (
    CommentAnalysis,
    SentimentReport,
    SentimentType,
    Platform
)

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analysis system for audience comments.
    
    Features:
    - Sentiment classification (positive/neutral/negative)
    - Topic extraction
    - Hype detection
    - Actionable feedback identification
    - Multi-language support (ES/EN)
    """
    
    def __init__(self, mode: str = "live"):
        """
        Initialize sentiment analyzer.
        
        Args:
            mode: "live" or "stub"
        """
        self.mode = mode
        self._init_sentiment_lexicons()
    
    def _init_sentiment_lexicons(self) -> None:
        """Initialize sentiment word lists."""
        self.positive_words_es = [
            "increíble", "genial", "brutal", "tremendo", "fuego", "🔥",
            "me encanta", "épico", "perfecto", "best", "top", "duro",
            "arte", "obra maestra", "talento", "crack", "leyenda"
        ]
        
        self.negative_words_es = [
            "malo", "horrible", "basura", "mierda", "decepción",
            "no me gusta", "aburrido", "repetitivo", "trash",
            "flojo", "mediocre", "copia"
        ]
        
        self.hype_indicators = [
            "cuando sale", "when drop", "necesito", "esperando",
            "ya quiero", "ansias", "hype", "no puedo esperar",
            "lanzamiento", "release date", "¿cuándo?", "cuando"
        ]
    
    def analyze_comment(
        self,
        comment_text: str,
        comment_id: str,
        post_id: str,
        platform: Platform
    ) -> CommentAnalysis:
        """
        Analyze individual comment.
        
        Args:
            comment_text: Comment text
            comment_id: Comment ID
            post_id: Associated post ID
            platform: Platform where comment was posted
        
        Returns:
            CommentAnalysis with sentiment and insights
        """
        # Clean text
        text_clean = self._clean_text(comment_text)
        
        # Detect sentiment
        sentiment, score = self._detect_sentiment(text_clean)
        
        # Extract topics
        topics = self._extract_topics(text_clean)
        
        # Detect hype signals
        hype_signal = self._detect_hype(text_clean)
        
        # Check if actionable
        actionable = self._is_actionable(text_clean, topics)
        
        return CommentAnalysis(
            comment_id=comment_id,
            text=comment_text,
            sentiment=sentiment,
            sentiment_score=score,
            topics=topics,
            hype_signal=hype_signal,
            actionable_feedback=actionable,
            platform=platform,
            post_id=post_id,
            analyzed_at=datetime.utcnow()
        )
    
    def analyze_batch(
        self,
        comments: List[Dict[str, Any]],
        platform: Platform
    ) -> SentimentReport:
        """
        Analyze batch of comments.
        
        Args:
            comments: List of comment dicts with keys: id, text, post_id
            platform: Platform
        
        Returns:
            Comprehensive sentiment report
        """
        logger.info(f"📊 Analyzing {len(comments)} comments from {platform.value}")
        
        analyses = []
        for comment in comments:
            analysis = self.analyze_comment(
                comment_text=comment["text"],
                comment_id=comment["id"],
                post_id=comment["post_id"],
                platform=platform
            )
            analyses.append(analysis)
        
        # Calculate statistics
        total = len(analyses)
        positive_count = sum(1 for a in analyses if a.sentiment == SentimentType.POSITIVE)
        neutral_count = sum(1 for a in analyses if a.sentiment == SentimentType.NEUTRAL)
        negative_count = sum(1 for a in analyses if a.sentiment == SentimentType.NEGATIVE)
        
        positive_pct = (positive_count / total * 100) if total > 0 else 0
        negative_pct = (negative_count / total * 100) if total > 0 else 0
        
        avg_score = sum(a.sentiment_score for a in analyses) / total if total > 0 else 0.0
        
        # Extract top topics
        all_topics = [topic for a in analyses for topic in a.topics]
        top_topics = [
            {"topic": topic, "count": count}
            for topic, count in Counter(all_topics).most_common(10)
        ]
        
        # Detect hype
        hype_comments = [a for a in analyses if a.hype_signal]
        hype_detected = len(hype_comments) >= 5  # Threshold: 5+ hype comments
        hype_topics = list(set(t for c in hype_comments for t in c.topics))
        
        # Generate insights
        insights = self._generate_insights(analyses, positive_pct, negative_pct)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            analyses,
            positive_pct,
            negative_pct,
            hype_detected
        )
        
        report = SentimentReport(
            report_id=f"sentiment_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            analyzed_at=datetime.utcnow(),
            total_comments=total,
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            positive_percentage=positive_pct,
            negative_percentage=negative_pct,
            avg_sentiment_score=avg_score,
            top_topics=top_topics,
            hype_detected=hype_detected,
            hype_topics=hype_topics,
            insights=insights,
            recommendations=recommendations,
            time_period_days=7,
            confidence=0.88
        )
        
        logger.info(f"✅ Sentiment: {positive_pct:.1f}% positive, {negative_pct:.1f}% negative")
        return report
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove excess whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _detect_sentiment(self, text: str) -> tuple[SentimentType, float]:
        """
        Detect sentiment from text.
        
        Returns:
            (SentimentType, score) where score is -1.0 to 1.0
        """
        positive_count = sum(1 for word in self.positive_words_es if word in text)
        negative_count = sum(1 for word in self.negative_words_es if word in text)
        
        # Calculate score
        if positive_count == 0 and negative_count == 0:
            return SentimentType.NEUTRAL, 0.0
        
        score = (positive_count - negative_count) / (positive_count + negative_count + 1)
        
        # Classify
        if score > 0.2:
            return SentimentType.POSITIVE, score
        elif score < -0.2:
            return SentimentType.NEGATIVE, score
        else:
            return SentimentType.NEUTRAL, score
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        topics = []
        
        topic_keywords = {
            "music": ["música", "track", "tema", "beat", "canción", "song"],
            "video": ["vídeo", "video", "clip", "visual", "edición"],
            "aesthetic": ["estética", "aesthetic", "visual", "colores", "purple", "morado"],
            "lyrics": ["letra", "lyrics", "mensaje", "verso", "rima"],
            "production": ["producción", "production", "mezcla", "master", "sonido"],
            "vibe": ["vibe", "mood", "ambiente", "feeling", "energy"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)
        
        return topics if topics else ["general"]
    
    def _detect_hype(self, text: str) -> bool:
        """Detect hype/anticipation signals."""
        return any(indicator in text for indicator in self.hype_indicators)
    
    def _is_actionable(self, text: str, topics: List[str]) -> bool:
        """Check if comment contains actionable feedback."""
        actionable_indicators = [
            "sería genial si", "podrías", "me gustaría que",
            "estaría mejor", "sugiero", "recomiendo",
            "deberías", "would be cool", "you should"
        ]
        
        return any(indicator in text for indicator in actionable_indicators)
    
    def _generate_insights(
        self,
        analyses: List[CommentAnalysis],
        positive_pct: float,
        negative_pct: float
    ) -> List[str]:
        """Generate actionable insights."""
        insights = []
        
        # Overall sentiment insight
        if positive_pct > 75:
            insights.append("Audiencia muy positiva - contenido resonando fuertemente")
        elif positive_pct < 40:
            insights.append("Sentimiento mixto - revisar estrategia de contenido")
        
        # Topic insights
        all_topics = [topic for a in analyses for topic in a.topics]
        topic_counts = Counter(all_topics)
        
        if "aesthetic" in topic_counts and topic_counts["aesthetic"] > len(analyses) * 0.3:
            insights.append("Alta mención de estética visual - mantener identidad visual fuerte")
        
        if "music" in topic_counts and topic_counts["music"] > len(analyses) * 0.4:
            insights.append("Enfoque principal en la música - audiencia valora calidad musical")
        
        # Hype insights
        hype_count = sum(1 for a in analyses if a.hype_signal)
        if hype_count > len(analyses) * 0.2:
            insights.append(f"Alto nivel de anticipación detectado - {hype_count} comentarios esperando nuevo contenido")
        
        return insights
    
    def _generate_recommendations(
        self,
        analyses: List[CommentAnalysis],
        positive_pct: float,
        negative_pct: float,
        hype_detected: bool
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        # Sentiment-based recommendations
        if positive_pct > 70:
            recommendations.append("Replicar formato actual - está funcionando muy bien")
        
        if negative_pct > 30:
            recommendations.append("Revisar últimos posts - detectar qué no está resonando")
        
        # Hype-based recommendations
        if hype_detected:
            recommendations.append("Capitalizar hype - anunciar próximo lanzamiento pronto")
            recommendations.append("Crear contenido teaser para mantener anticipación")
        
        # Actionable feedback
        actionable = [a for a in analyses if a.actionable_feedback]
        if len(actionable) > 5:
            recommendations.append(f"Revisar {len(actionable)} comentarios con feedback accionable")
        
        return recommendations
