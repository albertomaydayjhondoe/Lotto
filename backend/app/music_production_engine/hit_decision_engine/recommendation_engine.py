"""Recommendation Engine - Provides actionable improvement advice."""
from typing import Dict, List
from pydantic import BaseModel

class Recommendation(BaseModel):
    category: str
    priority: str
    action: str
    expected_impact: str

class RecommendationEngine:
    def generate_recommendations(self, hit_score: Dict, analyses: Dict) -> List[Recommendation]:
        recommendations = []
        
        if hit_score.get("overall_score", 0) < 75:
            recommendations.append(Recommendation(
                category="production",
                priority="high",
                action="Improve mix clarity and stereo imaging",
                expected_impact="+5-10 points"
            ))
        
        if analyses.get("lyric_analysis", {}).get("quality_score", 0) < 70:
            recommendations.append(Recommendation(
                category="lyrics",
                priority="medium",
                action="Refine rhyme scheme and word choice",
                expected_impact="+3-7 points"
            ))
        
        recommendations.append(Recommendation(
            category="marketing",
            priority="medium",
            action="Target playlist curators in identified genres",
            expected_impact="Increased playlist placement probability"
        ))
        
        return recommendations

def get_recommendation_engine() -> RecommendationEngine:
    return RecommendationEngine()
