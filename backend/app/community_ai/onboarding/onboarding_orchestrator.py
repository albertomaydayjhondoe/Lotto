#!/usr/bin/env python3
"""
Onboarding Orchestrator: Master script to run all generators

This script orchestrates the complete onboarding flow:
1. Load onboarding_answers.json
2. Generate brand_static_rules.json
3. Generate satellite_rules.json
4. Generate content_strategy.json
5. Validate all outputs
6. Report status
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from brand_generator import BrandGenerator
from satellite_generator import SatelliteGenerator
from strategy_generator import StrategyGenerator


class OnboardingOrchestrator:
    """
    Orchestrates the complete artist onboarding and configuration generation.
    """
    
    def __init__(self, answers_path: str, output_dir: str):
        """
        Initialize orchestrator.
        
        Args:
            answers_path: Path to onboarding_answers.json
            output_dir: Directory where generated files will be saved
        """
        self.answers_path = Path(answers_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load answers
        with open(self.answers_path, 'r', encoding='utf-8') as f:
            self.answers = json.load(f)
        
        self.artist_name = self.answers.get("artist_name", "Unknown")
        self.artist_id = self.answers.get("artist_id", "unknown")
        
    def validate_answers(self) -> Dict[str, Any]:
        """
        Validate onboarding answers completeness.
        
        Returns:
            Dict with validation results
        """
        required_sections = [
            "visual_identity",
            "brand_tone",
            "music_context",
            "fashion_identity",
            "narrative_storytelling",
            "official_vs_satellite",
            "audience_targeting",
            "content_strategy",
            "platform_guidelines",
            "metrics_priorities"
        ]
        
        missing_sections = []
        incomplete_sections = []
        
        for section in required_sections:
            if section not in self.answers:
                missing_sections.append(section)
            else:
                # Check if section has data
                section_data = self.answers[section]
                if not section_data or len(section_data) == 0:
                    incomplete_sections.append(section)
        
        validation_result = {
            "valid": len(missing_sections) == 0 and len(incomplete_sections) == 0,
            "missing_sections": missing_sections,
            "incomplete_sections": incomplete_sections,
            "total_sections": len(required_sections),
            "completed_sections": len(required_sections) - len(missing_sections) - len(incomplete_sections)
        }
        
        return validation_result
    
    def generate_all(self) -> Dict[str, Any]:
        """
        Generate all configuration files.
        
        Returns:
            Dict with generation results
        """
        results = {
            "brand_rules": None,
            "satellite_rules": None,
            "content_strategy": None,
            "errors": []
        }
        
        # Generate brand rules
        try:
            brand_generator = BrandGenerator(str(self.answers_path))
            brand_rules_path = self.output_dir / "brand_static_rules.json"
            brand_generator.save(str(brand_rules_path))
            results["brand_rules"] = str(brand_rules_path)
        except Exception as e:
            results["errors"].append(f"Brand rules generation failed: {str(e)}")
        
        # Generate satellite rules
        try:
            satellite_generator = SatelliteGenerator(str(self.answers_path))
            satellite_rules_path = self.output_dir / "satellite_rules.json"
            satellite_generator.save(str(satellite_rules_path))
            results["satellite_rules"] = str(satellite_rules_path)
        except Exception as e:
            results["errors"].append(f"Satellite rules generation failed: {str(e)}")
        
        # Generate content strategy
        try:
            strategy_generator = StrategyGenerator(str(self.answers_path))
            content_strategy_path = self.output_dir / "content_strategy.json"
            strategy_generator.save(str(content_strategy_path))
            results["content_strategy"] = str(content_strategy_path)
        except Exception as e:
            results["errors"].append(f"Content strategy generation failed: {str(e)}")
        
        return results
    
    def validate_outputs(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate generated configuration files.
        
        Args:
            results: Generation results from generate_all()
            
        Returns:
            Dict with validation results
        """
        validation = {
            "all_generated": True,
            "file_checks": {},
            "schema_checks": {},
            "errors": []
        }
        
        # Check brand rules
        if results["brand_rules"]:
            brand_path = Path(results["brand_rules"])
            validation["file_checks"]["brand_rules"] = brand_path.exists()
            
            if brand_path.exists():
                try:
                    with open(brand_path, 'r') as f:
                        brand_data = json.load(f)
                    
                    required_keys = ["artist_identity", "visual_rules", "content_boundaries", 
                                    "platform_guidelines", "music_context", "brand_signature"]
                    missing_keys = [k for k in required_keys if k not in brand_data]
                    
                    validation["schema_checks"]["brand_rules"] = {
                        "valid": len(missing_keys) == 0,
                        "missing_keys": missing_keys
                    }
                except Exception as e:
                    validation["errors"].append(f"Brand rules validation error: {str(e)}")
        else:
            validation["all_generated"] = False
        
        # Check satellite rules
        if results["satellite_rules"]:
            satellite_path = Path(results["satellite_rules"])
            validation["file_checks"]["satellite_rules"] = satellite_path.exists()
            
            if satellite_path.exists():
                try:
                    with open(satellite_path, 'r') as f:
                        satellite_data = json.load(f)
                    
                    required_keys = ["philosophy", "content_rules", "prohibitions", 
                                    "freedoms", "quality_standards"]
                    missing_keys = [k for k in required_keys if k not in satellite_data]
                    
                    validation["schema_checks"]["satellite_rules"] = {
                        "valid": len(missing_keys) == 0,
                        "missing_keys": missing_keys
                    }
                except Exception as e:
                    validation["errors"].append(f"Satellite rules validation error: {str(e)}")
        else:
            validation["all_generated"] = False
        
        # Check content strategy
        if results["content_strategy"]:
            strategy_path = Path(results["content_strategy"])
            validation["file_checks"]["content_strategy"] = strategy_path.exists()
            
            if strategy_path.exists():
                try:
                    with open(strategy_path, 'r') as f:
                        strategy_data = json.load(f)
                    
                    required_keys = ["official_channel", "satellite_channels", "content_mix",
                                    "timing_optimization", "kpi_framework"]
                    missing_keys = [k for k in required_keys if k not in strategy_data]
                    
                    validation["schema_checks"]["content_strategy"] = {
                        "valid": len(missing_keys) == 0,
                        "missing_keys": missing_keys
                    }
                except Exception as e:
                    validation["errors"].append(f"Content strategy validation error: {str(e)}")
        else:
            validation["all_generated"] = False
        
        return validation
    
    def print_report(self, validation: Dict[str, Any], generation: Dict[str, Any], 
                     output_validation: Dict[str, Any]) -> None:
        """
        Print comprehensive onboarding report.
        
        Args:
            validation: Answers validation results
            generation: Generation results
            output_validation: Output validation results
        """
        print("\n" + "="*80)
        print("🎯 ARTIST ONBOARDING REPORT")
        print("="*80)
        
        print(f"\n📋 Artist: {self.artist_name}")
        print(f"🆔 Artist ID: {self.artist_id}")
        print(f"📁 Output Directory: {self.output_dir}")
        
        print("\n" + "-"*80)
        print("1️⃣  QUESTIONNAIRE VALIDATION")
        print("-"*80)
        
        if validation["valid"]:
            print(f"✅ All {validation['total_sections']} sections completed")
        else:
            print(f"⚠️  Incomplete questionnaire: {validation['completed_sections']}/{validation['total_sections']} sections")
            if validation["missing_sections"]:
                print(f"   Missing: {', '.join(validation['missing_sections'])}")
            if validation["incomplete_sections"]:
                print(f"   Incomplete: {', '.join(validation['incomplete_sections'])}")
        
        print("\n" + "-"*80)
        print("2️⃣  CONFIGURATION GENERATION")
        print("-"*80)
        
        if generation["brand_rules"]:
            print(f"✅ Brand rules: {generation['brand_rules']}")
        else:
            print("❌ Brand rules: FAILED")
        
        if generation["satellite_rules"]:
            print(f"✅ Satellite rules: {generation['satellite_rules']}")
        else:
            print("❌ Satellite rules: FAILED")
        
        if generation["content_strategy"]:
            print(f"✅ Content strategy: {generation['content_strategy']}")
        else:
            print("❌ Content strategy: FAILED")
        
        if generation["errors"]:
            print("\n⚠️  Generation Errors:")
            for error in generation["errors"]:
                print(f"   - {error}")
        
        print("\n" + "-"*80)
        print("3️⃣  OUTPUT VALIDATION")
        print("-"*80)
        
        if output_validation["all_generated"]:
            print("✅ All files generated successfully")
        else:
            print("⚠️  Some files missing")
        
        for file_type, exists in output_validation["file_checks"].items():
            status = "✅" if exists else "❌"
            print(f"{status} {file_type}: {'EXISTS' if exists else 'MISSING'}")
        
        print("\n📊 Schema Validation:")
        all_schemas_valid = True
        for file_type, schema_check in output_validation["schema_checks"].items():
            if schema_check["valid"]:
                print(f"   ✅ {file_type}: VALID")
            else:
                print(f"   ❌ {file_type}: INVALID")
                print(f"      Missing keys: {', '.join(schema_check['missing_keys'])}")
                all_schemas_valid = False
        
        if output_validation["errors"]:
            print("\n⚠️  Validation Errors:")
            for error in output_validation["errors"]:
                print(f"   - {error}")
        
        print("\n" + "-"*80)
        print("4️⃣  SUMMARY")
        print("-"*80)
        
        success = (
            validation["valid"] and 
            len(generation["errors"]) == 0 and 
            output_validation["all_generated"] and
            all_schemas_valid
        )
        
        if success:
            print("✅ ONBOARDING COMPLETE")
            print("\n🎉 All configuration files generated and validated successfully!")
            print("\n📚 Next Steps:")
            print("   1. Review generated files in output directory")
            print("   2. Integrate brand_static_rules.json with CM modules")
            print("   3. Configure satellite channels with satellite_rules.json")
            print("   4. Apply content_strategy.json to posting scheduler")
            print("\n📖 Documentation: docs/artist_onboarding.md")
        else:
            print("⚠️  ONBOARDING INCOMPLETE")
            print("\n🔧 Action Required:")
            if not validation["valid"]:
                print("   - Complete missing questionnaire sections")
            if generation["errors"]:
                print("   - Fix generation errors")
            if not output_validation["all_generated"]:
                print("   - Regenerate missing files")
            if not all_schemas_valid:
                print("   - Fix schema validation errors")
        
        print("\n" + "="*80 + "\n")
    
    def run(self) -> bool:
        """
        Run complete onboarding orchestration.
        
        Returns:
            True if successful, False otherwise
        """
        print("\n🚀 Starting Artist Onboarding Orchestration...")
        
        # Step 1: Validate answers
        print("\n1️⃣  Validating questionnaire answers...")
        validation = self.validate_answers()
        
        if not validation["valid"]:
            print("⚠️  Questionnaire incomplete - proceeding anyway...")
        
        # Step 2: Generate all configuration files
        print("\n2️⃣  Generating configuration files...")
        generation = self.generate_all()
        
        # Step 3: Validate outputs
        print("\n3️⃣  Validating generated files...")
        output_validation = self.validate_outputs(generation)
        
        # Step 4: Print report
        self.print_report(validation, generation, output_validation)
        
        # Determine success
        success = (
            validation["valid"] and
            len(generation["errors"]) == 0 and
            output_validation["all_generated"]
        )
        
        return success


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python onboarding_orchestrator.py <answers_path> <output_dir>")
        print("\nExample:")
        print("  python onboarding_orchestrator.py onboarding_answers.json ../brand/")
        print("\nDescription:")
        print("  Orchestrates complete artist onboarding:")
        print("  - Validates questionnaire answers")
        print("  - Generates brand_static_rules.json")
        print("  - Generates satellite_rules.json")
        print("  - Generates content_strategy.json")
        print("  - Validates all outputs")
        print("  - Prints comprehensive report")
        sys.exit(1)
    
    answers_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    orchestrator = OnboardingOrchestrator(answers_path, output_dir)
    success = orchestrator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
