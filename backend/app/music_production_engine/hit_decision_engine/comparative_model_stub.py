"""Comparative Model Stub - Compares tracks to hit references."""
import asyncio
from typing import Dict, List
from pydantic import BaseModel

class ComparisonResult(BaseModel):
    reference_track: str
    similarity_score: float
    matching_elements: List[str]

class ComparativeModelStub:
    async def compare_to_hits(self, track_features: Dict) -> List[ComparisonResult]:
        await asyncio.sleep(0.04)
        return [
            ComparisonResult(reference_track="Hit Song A", similarity_score=0.82, matching_elements=["bpm", "energy"]),
            ComparisonResult(reference_track="Hit Song B", similarity_score=0.75, matching_elements=["structure", "vocal_style"])
        ]

def get_comparative_model() -> ComparativeModelStub:
    return ComparativeModelStub()
