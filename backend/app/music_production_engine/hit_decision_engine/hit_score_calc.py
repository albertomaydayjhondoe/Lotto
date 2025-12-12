"""Hit Score Calculator - Aggregates signals into hit probability."""
from typing import Dict, List
from pydantic import BaseModel

class HitScore(BaseModel):
    overall_score: float  # 0-100
    commercial_potential: float
    viral_potential: float
    playlist_fit: float
    longevity_score: float
    confidence: float

class HitScoreCalculator:
    def calculate(self, all_analyses: Dict) -> HitScore:
        audio_score = all_analyses.get("audio_analysis", {}).get("overall_score", 75)
        trend_alignment = all_analyses.get("trends", {}).get("alignment_score", 70)
        
        overall = (audio_score * 0.4 + trend_alignment * 0.3 + 75 * 0.3)
        
        return HitScore(
            overall_score=round(overall, 1),
            commercial_potential=round(overall + 5, 1),
            viral_potential=round(overall - 10, 1),
            playlist_fit=round(overall, 1),
            longevity_score=round(overall - 5, 1),
            confidence=0.85
        )

def get_hit_score_calculator() -> HitScoreCalculator:
    return HitScoreCalculator()
