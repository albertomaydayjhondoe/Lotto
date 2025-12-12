"""
Geographic Budget Allocator.

Implements geo-constrained budget allocation with España ≥35% requirement
and dynamic LATAM optimization based on cost and engagement.
"""
from typing import List, Dict, Tuple
from app.meta_targeting_optimizer.schemas import GeoAllocation, GeoConstraint


class GeoAllocator:
    """
    Geographic budget allocator with constraints and optimization.
    
    Rules:
    - España: minimum 35% of budget
    - LATAM: dynamic allocation based on CPM, CTR, ROAS
    - Rest of world: fill remaining budget
    """
    
    # Spain constraint
    SPAIN_CODE = "ES"
    SPAIN_MIN_PCT = 35.0
    
    # LATAM countries
    LATAM_COUNTRIES = {
        "MX": "Mexico",
        "AR": "Argentina",
        "CO": "Colombia",
        "CL": "Chile",
        "PE": "Peru",
        "VE": "Venezuela",
        "EC": "Ecuador",
        "GT": "Guatemala",
        "BO": "Bolivia",
        "PY": "Paraguay",
        "UY": "Uruguay",
        "CR": "Costa Rica",
        "PA": "Panama",
        "DO": "Dominican Republic",
    }
    
    # EU countries (after Spain)
    EU_COUNTRIES = {
        "FR": "France",
        "DE": "Germany",
        "IT": "Italy",
        "PT": "Portugal",
        "UK": "United Kingdom",
        "NL": "Netherlands",
        "BE": "Belgium",
        "SE": "Sweden",
        "PL": "Poland",
    }
    
    def __init__(self):
        """Initialize allocator."""
        self.constraints: List[GeoConstraint] = []
    
    def add_constraint(self, constraint: GeoConstraint):
        """Add a geographic constraint."""
        self.constraints.append(constraint)
    
    def compute_engagement_score(
        self,
        ctr: float,
        cvr: float,
        roas: float,
        cpc: float
    ) -> float:
        """
        Compute engagement score for a country.
        
        Formula:
        engagement = (CTR * 30% + CVR * 40% + ROAS * 30%) / (CPC_norm)
        
        Higher engagement and lower cost = higher score.
        """
        # Normalize metrics (assuming reasonable ranges)
        ctr_norm = min(ctr / 0.03, 1.0)  # 3% is excellent CTR
        cvr_norm = min(cvr / 0.05, 1.0)  # 5% is excellent CVR
        roas_norm = min(roas / 5.0, 1.0)  # 5x ROAS is excellent
        
        # CPC penalty (lower is better)
        cpc_norm = max(1.0 - (cpc / 2.0), 0.1)  # $2 CPC is high
        
        engagement = (ctr_norm * 0.3 + cvr_norm * 0.4 + roas_norm * 0.3) * cpc_norm
        
        return engagement
    
    def allocate_budget(
        self,
        total_budget: float,
        geo_performance: Dict[str, Dict[str, float]]
    ) -> List[GeoAllocation]:
        """
        Allocate budget across geographies with constraints.
        
        Args:
            total_budget: Total budget to allocate
            geo_performance: Dict of {country_code: {ctr, cvr, roas, cpc}}
        
        Returns:
            List of GeoAllocation objects
        """
        allocations = []
        remaining_budget = total_budget
        remaining_pct = 100.0
        
        # Step 1: Ensure Spain gets minimum 35%
        spain_budget = total_budget * (self.SPAIN_MIN_PCT / 100.0)
        spain_perf = geo_performance.get(self.SPAIN_CODE, {})
        
        allocations.append(GeoAllocation(
            country_code=self.SPAIN_CODE,
            country_name="Spain",
            budget_pct=self.SPAIN_MIN_PCT,
            budget_amount=spain_budget,
            avg_cpc=spain_perf.get("cpc", 0.0),
            avg_ctr=spain_perf.get("ctr", 0.0),
            avg_roas=spain_perf.get("roas", 0.0),
            engagement_score=self.compute_engagement_score(
                spain_perf.get("ctr", 0.015),
                spain_perf.get("cvr", 0.02),
                spain_perf.get("roas", 2.5),
                spain_perf.get("cpc", 0.5)
            )
        ))
        
        remaining_budget -= spain_budget
        remaining_pct -= self.SPAIN_MIN_PCT
        
        # Step 2: Score all other countries
        country_scores = []
        
        for country_code, perf in geo_performance.items():
            if country_code == self.SPAIN_CODE:
                continue  # Already allocated
            
            engagement = self.compute_engagement_score(
                perf.get("ctr", 0.015),
                perf.get("cvr", 0.02),
                perf.get("roas", 2.5),
                perf.get("cpc", 0.5)
            )
            
            country_name = self._get_country_name(country_code)
            
            country_scores.append({
                "code": country_code,
                "name": country_name,
                "engagement": engagement,
                "perf": perf
            })
        
        # Sort by engagement score (descending)
        country_scores.sort(key=lambda x: x["engagement"], reverse=True)
        
        # Step 3: Allocate remaining budget proportionally to engagement
        total_engagement = sum(c["engagement"] for c in country_scores)
        
        if total_engagement == 0:
            # Equal distribution if no performance data
            equal_pct = remaining_pct / len(country_scores) if country_scores else 0
            
            for country in country_scores:
                allocations.append(GeoAllocation(
                    country_code=country["code"],
                    country_name=country["name"],
                    budget_pct=equal_pct,
                    budget_amount=remaining_budget * (equal_pct / 100.0),
                    avg_cpc=country["perf"].get("cpc", 0.0),
                    avg_ctr=country["perf"].get("ctr", 0.0),
                    avg_roas=country["perf"].get("roas", 0.0),
                    engagement_score=country["engagement"]
                ))
        else:
            # Proportional allocation based on engagement
            for country in country_scores:
                pct = (country["engagement"] / total_engagement) * remaining_pct
                amount = (country["engagement"] / total_engagement) * remaining_budget
                
                allocations.append(GeoAllocation(
                    country_code=country["code"],
                    country_name=country["name"],
                    budget_pct=pct,
                    budget_amount=amount,
                    avg_cpc=country["perf"].get("cpc", 0.0),
                    avg_ctr=country["perf"].get("ctr", 0.0),
                    avg_roas=country["perf"].get("roas", 0.0),
                    engagement_score=country["engagement"]
                ))
        
        return allocations
    
    def _get_country_name(self, country_code: str) -> str:
        """Get human-readable country name."""
        if country_code in self.LATAM_COUNTRIES:
            return self.LATAM_COUNTRIES[country_code]
        elif country_code in self.EU_COUNTRIES:
            return self.EU_COUNTRIES[country_code]
        else:
            return country_code  # Fallback to code
    
    def validate_allocation(self, allocations: List[GeoAllocation]) -> Tuple[bool, str]:
        """
        Validate that allocations meet all constraints.
        
        Returns:
            (is_valid, error_message)
        """
        # Check Spain constraint
        spain_alloc = next((a for a in allocations if a.country_code == self.SPAIN_CODE), None)
        
        if not spain_alloc:
            return False, "Spain allocation missing"
        
        if spain_alloc.budget_pct < self.SPAIN_MIN_PCT:
            return False, f"Spain allocation {spain_alloc.budget_pct:.1f}% below minimum {self.SPAIN_MIN_PCT}%"
        
        # Check total adds up to 100%
        total_pct = sum(a.budget_pct for a in allocations)
        
        if abs(total_pct - 100.0) > 0.1:  # Allow 0.1% rounding error
            return False, f"Total allocation {total_pct:.1f}% does not equal 100%"
        
        return True, "Valid"
    
    def get_default_geo_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Get default geo performance data (for stub mode).
        
        Returns synthetic but realistic performance data.
        """
        performance = {}
        
        # Spain (high quality, medium cost)
        performance[self.SPAIN_CODE] = {
            "ctr": 0.022,
            "cvr": 0.025,
            "roas": 3.2,
            "cpc": 0.45
        }
        
        # LATAM (varied quality, low cost)
        latam_base = {
            "ctr": 0.018,
            "cvr": 0.020,
            "roas": 2.8,
            "cpc": 0.25
        }
        
        for code in self.LATAM_COUNTRIES.keys():
            # Add some variation
            import random
            performance[code] = {
                "ctr": latam_base["ctr"] * random.uniform(0.8, 1.2),
                "cvr": latam_base["cvr"] * random.uniform(0.8, 1.2),
                "roas": latam_base["roas"] * random.uniform(0.8, 1.2),
                "cpc": latam_base["cpc"] * random.uniform(0.8, 1.2),
            }
        
        # EU (high quality, high cost)
        eu_base = {
            "ctr": 0.020,
            "cvr": 0.023,
            "roas": 2.9,
            "cpc": 0.65
        }
        
        for code in self.EU_COUNTRIES.keys():
            import random
            performance[code] = {
                "ctr": eu_base["ctr"] * random.uniform(0.9, 1.1),
                "cvr": eu_base["cvr"] * random.uniform(0.9, 1.1),
                "roas": eu_base["roas"] * random.uniform(0.9, 1.1),
                "cpc": eu_base["cpc"] * random.uniform(0.9, 1.1),
            }
        
        return performance
