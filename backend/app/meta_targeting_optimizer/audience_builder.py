"""
Audience Builder for Meta Targeting.

Generates lookalikes, ranks interests/behaviors, maps pixels to genres,
and builds custom audiences.
"""
import random
from typing import List, Dict, Optional
from app.meta_targeting_optimizer.schemas import (
    InterestSpec,
    BehaviorSpec,
    LookalikeSpec,
    CustomAudienceSpec,
    SegmentScore,
    SegmentType
)


class AudienceBuilder:
    """
    Builds and optimizes audiences for Meta targeting.
    """
    
    # Genre-to-interest mapping (for pixel-based targeting)
    GENRE_INTEREST_MAP = {
        "action": ["action movies", "adventure games", "martial arts", "extreme sports"],
        "comedy": ["comedy movies", "stand-up comedy", "sitcoms", "humor"],
        "drama": ["drama series", "theater", "independent film", "documentaries"],
        "thriller": ["thriller movies", "mystery novels", "crime series", "suspense"],
        "scifi": ["science fiction", "futurism", "space exploration", "technology"],
        "romance": ["romance novels", "romantic comedy", "dating", "relationships"],
        "horror": ["horror movies", "halloween", "supernatural", "gothic culture"],
        "documentary": ["documentaries", "history", "education", "current events"],
        "animation": ["animation", "anime", "cartoons", "family entertainment"],
        "fantasy": ["fantasy", "magic", "mythology", "role-playing games"],
    }
    
    # Behavior categories
    BEHAVIOR_CATEGORIES = {
        "engaged_shoppers": "Online shoppers who frequently make purchases",
        "video_viewers": "People who watch a lot of video content",
        "mobile_users": "Heavy mobile device users",
        "travel_enthusiasts": "People interested in travel",
        "tech_early_adopters": "Early adopters of technology",
        "fitness_active": "People active in fitness and health",
        "foodies": "Food and dining enthusiasts",
        "gamers": "Video game players",
        "music_lovers": "Music streaming users",
        "sports_fans": "Sports enthusiasts",
    }
    
    def __init__(self):
        """Initialize audience builder."""
        pass
    
    def rank_interests(self, interest_scores: List[SegmentScore], top_n: int = 15) -> List[InterestSpec]:
        """
        Rank interests by composite score.
        
        Args:
            interest_scores: List of scored interest segments
            top_n: Number of top interests to return
        
        Returns:
            List of ranked InterestSpec objects
        """
        # Filter to interests only
        interests = [s for s in interest_scores if s.segment_type == SegmentType.INTEREST]
        
        # Sort by composite score (descending)
        sorted_interests = sorted(interests, key=lambda s: s.composite_score, reverse=True)
        
        # Convert to InterestSpec
        result = []
        for rank, interest in enumerate(sorted_interests[:top_n], start=1):
            result.append(InterestSpec(
                interest_id=interest.segment_id,
                interest_name=interest.segment_name,
                score=interest.composite_score,
                rank=rank
            ))
        
        return result
    
    def rank_behaviors(self, behavior_scores: List[SegmentScore], top_n: int = 10) -> List[BehaviorSpec]:
        """
        Rank behaviors by composite score.
        
        Args:
            behavior_scores: List of scored behavior segments
            top_n: Number of top behaviors to return
        
        Returns:
            List of ranked BehaviorSpec objects
        """
        # Filter to behaviors only
        behaviors = [s for s in behavior_scores if s.segment_type == SegmentType.BEHAVIOR]
        
        # Sort by composite score (descending)
        sorted_behaviors = sorted(behaviors, key=lambda s: s.composite_score, reverse=True)
        
        # Convert to BehaviorSpec
        result = []
        for rank, behavior in enumerate(sorted_behaviors[:top_n], start=1):
            result.append(BehaviorSpec(
                behavior_id=behavior.segment_id,
                behavior_name=behavior.segment_name,
                score=behavior.composite_score,
                rank=rank
            ))
        
        return result
    
    def map_pixel_to_interests(self, genre: str, subgenre: Optional[str] = None) -> List[str]:
        """
        Map content genre/subgenre to relevant Meta interests.
        
        Args:
            genre: Content genre (e.g., "action", "comedy")
            subgenre: Optional subgenre for refinement
        
        Returns:
            List of interest names
        """
        # Get base interests from genre
        interests = self.GENRE_INTEREST_MAP.get(genre.lower(), [])
        
        # TODO: In live mode, expand with subgenre-specific interests
        # For now, return base interests
        return interests
    
    def generate_lookalike_stub(
        self,
        source_audience_id: str,
        countries: List[str],
        ratio: float = 0.01
    ) -> LookalikeSpec:
        """
        Generate lookalike audience specification (STUB mode).
        
        In LIVE mode, this would call Meta API to create lookalike.
        
        Args:
            source_audience_id: Source custom audience ID
            countries: Target countries
            ratio: Lookalike ratio (0.01 = 1%, 0.10 = 10%)
        
        Returns:
            LookalikeSpec object
        """
        # Generate synthetic lookalike ID
        lookalike_id = f"lookalike_{source_audience_id}_{int(ratio*100)}"
        
        # Generate name
        country_str = "+".join(countries[:3])
        if len(countries) > 3:
            country_str += f"+{len(countries)-3}more"
        
        name = f"Lookalike {int(ratio*100)}% - {country_str}"
        
        # TODO: In LIVE mode, call Meta API
        # lookalike = meta_client.create_lookalike_audience(
        #     source_audience_id=source_audience_id,
        #     countries=countries,
        #     ratio=ratio,
        #     name=name
        # )
        
        return LookalikeSpec(
            source_audience_id=source_audience_id,
            country_codes=countries,
            ratio=ratio,
            name=name,
            description=f"Lookalike audience based on {source_audience_id}"
        )
    
    def generate_custom_audience_stub(self, audience_type: str, size: int = 10000) -> CustomAudienceSpec:
        """
        Generate custom audience specification (STUB mode).
        
        Args:
            audience_type: Type of audience (e.g., "pixel_viewers", "converters")
            size: Estimated audience size
        
        Returns:
            CustomAudienceSpec object
        """
        # Generate synthetic ID
        audience_id = f"ca_{audience_type}_{random.randint(100000, 999999)}"
        
        return CustomAudienceSpec(
            audience_id=audience_id,
            name=f"Custom - {audience_type}",
            size=size,
            description=f"Custom audience: {audience_type}"
        )
    
    def build_interest_targeting(
        self,
        genre: str,
        subgenre: Optional[str],
        interest_scores: List[SegmentScore],
        max_interests: int = 15
    ) -> List[InterestSpec]:
        """
        Build comprehensive interest targeting combining pixel mapping and scores.
        
        Args:
            genre: Content genre
            subgenre: Content subgenre
            interest_scores: Historical interest scores
            max_interests: Maximum interests to return
        
        Returns:
            List of InterestSpec objects
        """
        # Get pixel-mapped interests
        pixel_interests = self.map_pixel_to_interests(genre, subgenre)
        
        # Rank scored interests
        ranked_interests = self.rank_interests(interest_scores, top_n=max_interests)
        
        # Merge and deduplicate
        # Priority: scored interests, then pixel-mapped
        result = ranked_interests.copy()
        
        # Add pixel interests not already in scored list
        existing_names = {i.interest_name.lower() for i in result}
        
        for pixel_int in pixel_interests:
            if pixel_int.lower() not in existing_names and len(result) < max_interests:
                # Add as synthetic interest with medium score
                result.append(InterestSpec(
                    interest_id=f"pixel_{pixel_int.replace(' ', '_')}",
                    interest_name=pixel_int,
                    score=0.5,  # Medium confidence
                    rank=len(result) + 1
                ))
        
        return result[:max_interests]
    
    def build_behavior_targeting(
        self,
        behavior_scores: List[SegmentScore],
        max_behaviors: int = 10
    ) -> List[BehaviorSpec]:
        """
        Build behavior targeting from scores.
        
        Args:
            behavior_scores: Historical behavior scores
            max_behaviors: Maximum behaviors to return
        
        Returns:
            List of BehaviorSpec objects
        """
        return self.rank_behaviors(behavior_scores, top_n=max_behaviors)
    
    def build_lookalike_audiences(
        self,
        custom_audiences: List[str],
        countries: List[str],
        max_lookalikes: int = 3
    ) -> List[LookalikeSpec]:
        """
        Build lookalike audiences from custom audiences.
        
        Args:
            custom_audiences: List of custom audience IDs
            countries: Target countries
            max_lookalikes: Maximum lookalikes to create
        
        Returns:
            List of LookalikeSpec objects
        """
        lookalikes = []
        
        # Generate lookalikes at different ratios
        ratios = [0.01, 0.03, 0.05]  # 1%, 3%, 5%
        
        for audience_id in custom_audiences[:max_lookalikes]:
            for ratio in ratios:
                lookalike = self.generate_lookalike_stub(
                    source_audience_id=audience_id,
                    countries=countries,
                    ratio=ratio
                )
                lookalikes.append(lookalike)
                
                if len(lookalikes) >= max_lookalikes:
                    break
            
            if len(lookalikes) >= max_lookalikes:
                break
        
        return lookalikes
    
    def get_stub_interests(self, count: int = 15) -> List[InterestSpec]:
        """Get synthetic interests for stub mode."""
        all_interests = []
        for interests in self.GENRE_INTEREST_MAP.values():
            all_interests.extend(interests)
        
        # Shuffle and take random subset
        random.shuffle(all_interests)
        
        result = []
        for rank, interest in enumerate(all_interests[:count], start=1):
            result.append(InterestSpec(
                interest_id=f"int_{interest.replace(' ', '_')}",
                interest_name=interest,
                score=random.uniform(0.5, 0.9),
                rank=rank
            ))
        
        return result
    
    def get_stub_behaviors(self, count: int = 10) -> List[BehaviorSpec]:
        """Get synthetic behaviors for stub mode."""
        behaviors = list(self.BEHAVIOR_CATEGORIES.items())
        random.shuffle(behaviors)
        
        result = []
        for rank, (beh_id, beh_name) in enumerate(behaviors[:count], start=1):
            result.append(BehaviorSpec(
                behavior_id=f"beh_{beh_id}",
                behavior_name=beh_name,
                score=random.uniform(0.5, 0.9),
                rank=rank
            ))
        
        return result
