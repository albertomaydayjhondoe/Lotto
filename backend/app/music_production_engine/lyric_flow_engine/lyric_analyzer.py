"""Lyric Quality Analyzer

Analyzes lyric content for quality, themes, rhyme schemes, and coherence.
Provides detailed feedback on lyrical strengths and weaknesses.
"""

import asyncio
import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel
from enum import Enum


class RhymeScheme(str, Enum):
    """Common rhyme patterns."""
    AABB = "aabb"  # Couplets
    ABAB = "abab"  # Alternate
    ABCB = "abcb"  # Common ballad
    AAAA = "aaaa"  # Monorhyme
    FREE = "free"  # No consistent pattern


class LyricIssue(BaseModel):
    """Individual lyric issue."""
    line_number: int
    issue_type: str  # "rhyme", "grammar", "cliche", "repetition", "coherence"
    severity: str  # "minor", "moderate", "major"
    description: str
    suggestion: Optional[str] = None


class ThemeAnalysis(BaseModel):
    """Thematic content analysis."""
    primary_themes: List[str]
    secondary_themes: List[str]
    emotional_tone: str  # "confident", "melancholic", "aggressive", etc.
    subject_matter: List[str]
    maturity_rating: str  # "clean", "mild", "explicit"


class RhymeAnalysis(BaseModel):
    """Rhyme pattern analysis."""
    scheme: RhymeScheme
    rhyme_density: float  # Percentage of lines that rhyme
    internal_rhymes: int  # Rhymes within lines
    slant_rhymes: int  # Near rhymes
    perfect_rhymes: int
    rhyme_quality_score: float  # 0-100


class LyricMetrics(BaseModel):
    """Quantitative lyric metrics."""
    total_lines: int
    total_words: int
    unique_words: int
    vocabulary_diversity: float  # Unique / total
    avg_words_per_line: float
    syllables_per_line: float
    reading_level: str  # Grade level
    complexity_score: float  # 0-100


class LyricAnalysisResult(BaseModel):
    """Complete lyric analysis."""
    text: str
    quality_score: float  # 0-100
    theme_analysis: ThemeAnalysis
    rhyme_analysis: RhymeAnalysis
    metrics: LyricMetrics
    issues: List[LyricIssue]
    strengths: List[str]
    metadata: Dict


class LyricAnalyzer:
    """
    Comprehensive lyric quality analysis.
    
    In production, would integrate:
    - NLP libraries (spaCy, NLTK)
    - Rhyme dictionaries
    - Sentiment analysis
    - Theme detection models
    """
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    async def analyze(
        self,
        lyrics: str,
        context: Optional[Dict] = None
    ) -> LyricAnalysisResult:
        """
        Analyze lyric quality and content.
        
        Args:
            lyrics: Full lyric text
            context: Optional context (genre, target audience, etc.)
            
        Returns:
            LyricAnalysisResult
        """
        # Simulate processing time
        await asyncio.sleep(0.04)
        
        lyrics_hash = hash(lyrics)
        
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        words = lyrics.split()
        unique_words = set(word.lower().strip('.,!?') for word in words)
        
        # Theme analysis
        theme_analysis = self._analyze_themes(lyrics, context)
        
        # Rhyme analysis
        rhyme_analysis = self._analyze_rhymes(lines, lyrics_hash)
        
        # Metrics
        metrics = LyricMetrics(
            total_lines=len(lines),
            total_words=len(words),
            unique_words=len(unique_words),
            vocabulary_diversity=round(len(unique_words) / len(words), 3) if words else 0,
            avg_words_per_line=round(len(words) / len(lines), 1) if lines else 0,
            syllables_per_line=round(self._estimate_syllables(lyrics) / len(lines), 1) if lines else 0,
            reading_level="9-10th grade",
            complexity_score=65 + (lyrics_hash % 30)
        )
        
        # Issues detection
        issues = self._detect_issues(lines, lyrics_hash)
        
        # Strengths
        strengths = self._identify_strengths(
            rhyme_analysis,
            metrics,
            theme_analysis,
            lyrics_hash
        )
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(
            rhyme_analysis,
            metrics,
            len(issues)
        )
        
        return LyricAnalysisResult(
            text=lyrics,
            quality_score=quality_score,
            theme_analysis=theme_analysis,
            rhyme_analysis=rhyme_analysis,
            metrics=metrics,
            issues=issues,
            strengths=strengths,
            metadata={
                "analyzer": "lyric_analyzer_v1",
                "context_applied": bool(context),
                "stub_mode": True
            }
        )
    
    def _analyze_themes(self, lyrics: str, context: Optional[Dict]) -> ThemeAnalysis:
        """Analyze thematic content."""
        lyrics_lower = lyrics.lower()
        
        # Simple keyword-based theme detection (STUB)
        themes = {
            "success": ["success", "money", "cash", "win", "top", "champion"],
            "struggle": ["struggle", "pain", "fight", "battle", "survive"],
            "ambition": ["grind", "hustle", "work", "dream", "vision", "goal"],
            "relationships": ["love", "heart", "girl", "relationship", "together"],
            "confidence": ["king", "queen", "boss", "power", "strong", "confident"],
            "lifestyle": ["party", "night", "club", "drink", "vibe"],
        }
        
        detected_themes = []
        for theme, keywords in themes.items():
            if any(keyword in lyrics_lower for keyword in keywords):
                detected_themes.append(theme)
        
        primary = detected_themes[:2] if len(detected_themes) >= 2 else detected_themes
        secondary = detected_themes[2:4] if len(detected_themes) > 2 else []
        
        # Emotional tone (simplified)
        if "aggressive" in lyrics_lower or "fight" in lyrics_lower:
            tone = "aggressive"
        elif "sad" in lyrics_lower or "pain" in lyrics_lower:
            tone = "melancholic"
        else:
            tone = "confident"
        
        # Maturity rating
        explicit_words = ["fuck", "shit", "bitch", "nigga"]
        has_explicit = any(word in lyrics_lower for word in explicit_words)
        rating = "explicit" if has_explicit else "clean"
        
        return ThemeAnalysis(
            primary_themes=primary or ["ambition", "lifestyle"],
            secondary_themes=secondary,
            emotional_tone=tone,
            subject_matter=detected_themes or ["general"],
            maturity_rating=rating
        )
    
    def _analyze_rhymes(self, lines: List[str], lyrics_hash: int) -> RhymeAnalysis:
        """Analyze rhyme patterns."""
        # STUB: Simplified rhyme detection based on last word similarity
        
        # Extract last words
        last_words = []
        for line in lines:
            words = line.split()
            if words:
                last_word = words[-1].strip('.,!?').lower()
                last_words.append(last_word)
        
        # Detect scheme (simplified)
        if len(last_words) >= 4:
            # Check for AABB pattern
            if (self._words_rhyme(last_words[0], last_words[1]) and
                self._words_rhyme(last_words[2], last_words[3])):
                scheme = RhymeScheme.AABB
            # Check for ABAB pattern
            elif (self._words_rhyme(last_words[0], last_words[2]) and
                  self._words_rhyme(last_words[1], last_words[3])):
                scheme = RhymeScheme.ABAB
            else:
                scheme = RhymeScheme.FREE
        else:
            scheme = RhymeScheme.FREE
        
        # Count rhymes (STUB uses hash for deterministic results)
        rhyming_lines = 60 + (lyrics_hash % 35)
        rhyme_density = rhyming_lines / 100
        
        return RhymeAnalysis(
            scheme=scheme,
            rhyme_density=rhyme_density,
            internal_rhymes=5 + (lyrics_hash % 10),
            slant_rhymes=8 + (lyrics_hash % 12),
            perfect_rhymes=15 + (lyrics_hash % 15),
            rhyme_quality_score=70 + (lyrics_hash % 25)
        )
    
    def _words_rhyme(self, word1: str, word2: str) -> bool:
        """Simple rhyme check (STUB: checks last 2 characters)."""
        if len(word1) < 2 or len(word2) < 2:
            return False
        return word1[-2:] == word2[-2:]
    
    def _detect_issues(self, lines: List[str], lyrics_hash: int) -> List[LyricIssue]:
        """Detect potential issues in lyrics."""
        issues = []
        
        # Check for clichés (simplified)
        cliche_phrases = ["follow my dreams", "reach for the stars", "against all odds"]
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for cliche in cliche_phrases:
                if cliche in line_lower:
                    issues.append(LyricIssue(
                        line_number=i + 1,
                        issue_type="cliche",
                        severity="minor",
                        description=f"Potential cliché: '{cliche}'",
                        suggestion="Consider a more original expression"
                    ))
        
        # Check for excessive repetition
        word_counts = {}
        for line in lines:
            for word in line.lower().split():
                word = word.strip('.,!?')
                if len(word) > 3:  # Only check longer words
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        for word, count in word_counts.items():
            if count > 8:  # More than 8 times
                issues.append(LyricIssue(
                    line_number=0,
                    issue_type="repetition",
                    severity="moderate",
                    description=f"Word '{word}' used {count} times",
                    suggestion="Vary vocabulary to avoid repetition"
                ))
        
        # STUB: Add random issue based on hash
        if lyrics_hash % 3 == 0:
            issues.append(LyricIssue(
                line_number=5,
                issue_type="rhyme",
                severity="minor",
                description="Rhyme scheme breaks in this section",
                suggestion="Consider adjusting line ending for consistency"
            ))
        
        return issues
    
    def _identify_strengths(
        self,
        rhyme_analysis: RhymeAnalysis,
        metrics: LyricMetrics,
        theme_analysis: ThemeAnalysis,
        lyrics_hash: int
    ) -> List[str]:
        """Identify lyrical strengths."""
        strengths = []
        
        if rhyme_analysis.rhyme_quality_score >= 80:
            strengths.append("Strong rhyme scheme and consistency")
        
        if metrics.vocabulary_diversity >= 0.6:
            strengths.append("Good vocabulary diversity")
        
        if rhyme_analysis.internal_rhymes >= 8:
            strengths.append("Effective use of internal rhymes")
        
        if len(theme_analysis.primary_themes) >= 2:
            strengths.append("Well-developed thematic content")
        
        if metrics.complexity_score >= 75:
            strengths.append("Sophisticated lyrical complexity")
        
        if not strengths:
            strengths.append("Solid foundation to build upon")
        
        return strengths
    
    def _calculate_quality_score(
        self,
        rhyme_analysis: RhymeAnalysis,
        metrics: LyricMetrics,
        num_issues: int
    ) -> float:
        """Calculate overall quality score."""
        score = 50  # Base
        
        # Rhyme contribution
        score += rhyme_analysis.rhyme_quality_score * 0.3
        
        # Vocabulary contribution
        score += metrics.vocabulary_diversity * 15
        
        # Complexity contribution
        score += metrics.complexity_score * 0.2
        
        # Penalty for issues
        score -= num_issues * 3
        
        return round(min(100, max(0, score)), 1)
    
    def _estimate_syllables(self, text: str) -> int:
        """Rough syllable count (STUB: simplified)."""
        # Count vowel groups as syllables
        text = text.lower()
        vowels = 'aeiouy'
        syllables = 0
        previous_was_vowel = False
        
        for char in text:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllables += 1
            previous_was_vowel = is_vowel
        
        return max(1, syllables)


# Factory function
def get_lyric_analyzer() -> LyricAnalyzer:
    """
    Get lyric analyzer instance.
    
    Returns:
        LyricAnalyzer instance
    """
    return LyricAnalyzer()
