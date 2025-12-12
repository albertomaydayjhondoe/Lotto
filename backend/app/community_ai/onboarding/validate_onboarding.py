#!/usr/bin/env python3
"""
Onboarding System Validation Script

Validates the complete onboarding system without pytest dependency.
"""

import json
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")


def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")


def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")


def validate_file_exists(filepath, description):
    """Validate file exists."""
    if filepath.exists():
        print_success(f"{description} exists: {filepath.name}")
        return True
    else:
        print_error(f"{description} missing: {filepath}")
        return False


def validate_json_schema(data, required_keys, description):
    """Validate JSON has required keys."""
    missing_keys = [k for k in required_keys if k not in data]
    
    if len(missing_keys) == 0:
        print_success(f"{description} schema valid (all {len(required_keys)} keys present)")
        return True
    else:
        print_error(f"{description} schema invalid - missing keys: {', '.join(missing_keys)}")
        return False


def main():
    print("\n" + "="*80)
    print("🧪 ONBOARDING SYSTEM VALIDATION")
    print("="*80 + "\n")
    
    base_dir = Path(__file__).parent.parent
    onboarding_dir = base_dir / "onboarding"
    brand_dir = base_dir / "brand"
    
    all_passed = True
    
    # Test 1: Validate source files exist
    print("1️⃣  Validating Source Files\n")
    
    files_to_check = [
        (onboarding_dir / "onboarding_questions.json", "Questionnaire"),
        (onboarding_dir / "onboarding_answers.json", "Example Answers"),
        (onboarding_dir / "brand_generator.py", "Brand Generator"),
        (onboarding_dir / "satellite_generator.py", "Satellite Generator"),
        (onboarding_dir / "strategy_generator.py", "Strategy Generator"),
        (onboarding_dir / "onboarding_orchestrator.py", "Orchestrator"),
        (onboarding_dir / "__init__.py", "Module Init"),
    ]
    
    for filepath, description in files_to_check:
        if not validate_file_exists(filepath, description):
            all_passed = False
    
    print()
    
    # Test 2: Validate generated files exist
    print("2️⃣  Validating Generated Configuration Files\n")
    
    generated_files = [
        (brand_dir / "brand_static_rules.json", "Brand Rules"),
        (brand_dir / "satellite_rules.json", "Satellite Rules"),
        (brand_dir / "content_strategy.json", "Content Strategy"),
    ]
    
    for filepath, description in generated_files:
        if not validate_file_exists(filepath, description):
            all_passed = False
    
    print()
    
    # Test 3: Validate answers completeness
    print("3️⃣  Validating Onboarding Answers\n")
    
    answers_path = onboarding_dir / "onboarding_answers.json"
    if answers_path.exists():
        with open(answers_path, 'r', encoding='utf-8') as f:
            answers = json.load(f)
        
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
        
        if validate_json_schema(answers, required_sections, "Answers"):
            # Check critical section
            if "official_vs_satellite" in answers:
                ovs = answers["official_vs_satellite"]
                critical_questions = [
                    "q29_official_content_types",
                    "q31_satellite_content_types",
                    "q32_satellite_rules",
                    "q33_quality_threshold_official",
                    "q34_quality_threshold_satellite"
                ]
                
                if validate_json_schema(ovs, critical_questions, "Official vs Satellite Section"):
                    # Validate quality thresholds
                    official_quality = ovs.get("q33_quality_threshold_official", 0)
                    satellite_quality = ovs.get("q34_quality_threshold_satellite", 0)
                    
                    if official_quality >= 8:
                        print_success(f"Official quality threshold valid: {official_quality}/10")
                    else:
                        print_error(f"Official quality threshold too low: {official_quality}/10 (should be ≥8)")
                        all_passed = False
                    
                    if satellite_quality >= 5:
                        print_success(f"Satellite quality threshold valid: {satellite_quality}/10")
                    else:
                        print_error(f"Satellite quality threshold too low: {satellite_quality}/10 (should be ≥5)")
                        all_passed = False
                    
                    if official_quality > satellite_quality:
                        print_success("Quality distinction valid: Official > Satellite")
                    else:
                        print_error("Quality distinction invalid: Official should be > Satellite")
                        all_passed = False
                else:
                    all_passed = False
        else:
            all_passed = False
    
    print()
    
    # Test 4: Validate brand rules
    print("4️⃣  Validating Brand Rules\n")
    
    brand_rules_path = brand_dir / "brand_static_rules.json"
    if brand_rules_path.exists():
        with open(brand_rules_path, 'r', encoding='utf-8') as f:
            brand_rules = json.load(f)
        
        required_sections = [
            "artist_identity",
            "visual_rules",
            "content_boundaries",
            "platform_guidelines",
            "music_context",
            "brand_signature",
            "quality_standards",
            "metrics_priorities"
        ]
        
        if validate_json_schema(brand_rules, required_sections, "Brand Rules"):
            # Check visual rules
            if "visual_rules" in brand_rules:
                visual = brand_rules["visual_rules"]
                if "color_palette" in visual:
                    palette = visual["color_palette"]
                    if "allowed" in palette and len(palette["allowed"]) > 0:
                        print_success(f"Color palette defined: {len(palette['allowed'])} colors")
                    else:
                        print_error("Color palette empty")
                        all_passed = False
                    
                    if "signature_color" in palette:
                        print_success(f"Signature color: {palette['signature_color']}")
                    else:
                        print_error("Signature color missing")
                        all_passed = False
            
            # Check quality standards
            if "quality_standards" in brand_rules:
                quality = brand_rules["quality_standards"]
                if "official_channel" in quality:
                    official = quality["official_channel"]
                    if "minimum_quality_score" in official:
                        score = official["minimum_quality_score"]
                        if score >= 8:
                            print_success(f"Official quality threshold: {score}/10")
                        else:
                            print_error(f"Official quality threshold too low: {score}/10")
                            all_passed = False
                
                if "validation_gates" in quality:
                    gates = quality["validation_gates"]
                    print_success(f"Validation gates defined: {len(gates)} gates")
        else:
            all_passed = False
    
    print()
    
    # Test 5: Validate satellite rules
    print("5️⃣  Validating Satellite Rules\n")
    
    satellite_rules_path = brand_dir / "satellite_rules.json"
    if satellite_rules_path.exists():
        with open(satellite_rules_path, 'r', encoding='utf-8') as f:
            satellite_rules = json.load(f)
        
        required_sections = [
            "philosophy",
            "content_rules",
            "prohibitions",
            "freedoms",
            "quality_standards",
            "posting_strategy",
            "experimentation_rules",
            "ml_learning_rules"
        ]
        
        if validate_json_schema(satellite_rules, required_sections, "Satellite Rules"):
            # Check prohibitions
            if "prohibitions" in satellite_rules:
                prohibitions = satellite_rules["prohibitions"]
                if "absolute_prohibitions" in prohibitions:
                    absolute = prohibitions["absolute_prohibitions"]
                    no_rules = [p for p in absolute if p.startswith("NO_")]
                    if len(no_rules) >= 3:
                        print_success(f"Prohibitions defined: {len(no_rules)} NO_ rules")
                    else:
                        print_error(f"Insufficient prohibitions: {len(no_rules)} (need ≥3)")
                        all_passed = False
            
            # Check freedoms
            if "freedoms" in satellite_rules:
                freedoms = satellite_rules["freedoms"]
                if "creative_freedoms" in freedoms:
                    creative = freedoms["creative_freedoms"]
                    si_rules = [f for f in creative if f.startswith("SI_")]
                    if len(si_rules) >= 3:
                        print_success(f"Freedoms defined: {len(si_rules)} SI_ rules")
                    else:
                        print_error(f"Insufficient freedoms: {len(si_rules)} (need ≥3)")
                        all_passed = False
            
            # Check quality standards
            if "quality_standards" in satellite_rules:
                quality = satellite_rules["quality_standards"]
                if "minimum_quality_score" in quality:
                    score = quality["minimum_quality_score"]
                    if score <= 6:
                        print_success(f"Satellite quality threshold: {score}/10")
                    else:
                        print_error(f"Satellite quality threshold too high: {score}/10 (should be ≤6)")
                        all_passed = False
        else:
            all_passed = False
    
    print()
    
    # Test 6: Validate content strategy
    print("6️⃣  Validating Content Strategy\n")
    
    content_strategy_path = brand_dir / "content_strategy.json"
    if content_strategy_path.exists():
        with open(content_strategy_path, 'r', encoding='utf-8') as f:
            content_strategy = json.load(f)
        
        required_sections = [
            "official_channel",
            "satellite_channels",
            "content_mix",
            "timing_optimization",
            "platform_strategies",
            "kpi_framework",
            "experimentation_guidelines",
            "adaptation_rules"
        ]
        
        if validate_json_schema(content_strategy, required_sections, "Content Strategy"):
            # Check posting frequencies
            if "official_channel" in content_strategy:
                official = content_strategy["official_channel"]
                if "posting_schedule" in official:
                    schedule = official["posting_schedule"]
                    if "posts_per_week" in schedule:
                        official_posts = schedule["posts_per_week"]
                        print_success(f"Official posting: {official_posts} posts/week")
            
            if "satellite_channels" in content_strategy:
                satellite = content_strategy["satellite_channels"]
                if "posting_schedule" in satellite:
                    schedule = satellite["posting_schedule"]
                    if "posts_per_week" in schedule:
                        satellite_posts = schedule["posts_per_week"]
                        print_success(f"Satellite posting: {satellite_posts} posts/week")
                        
                        # Validate satellite > official
                        if satellite_posts > official_posts:
                            print_success("Posting frequency distinction valid: Satellite > Official")
                        else:
                            print_error("Posting frequency distinction invalid: Satellite should be > Official")
                            all_passed = False
            
            # Check KPI framework
            if "kpi_framework" in content_strategy:
                kpi = content_strategy["kpi_framework"]
                if "primary_kpis" in kpi and len(kpi["primary_kpis"]) > 0:
                    print_success(f"Primary KPIs defined: {len(kpi['primary_kpis'])} metrics")
        else:
            all_passed = False
    
    print()
    
    # Final report
    print("="*80)
    if all_passed:
        print_success("ALL VALIDATION TESTS PASSED ✅")
        print("\n🎉 Onboarding system fully validated and operational!")
        print("\n📚 Next Steps:")
        print("   1. Review generated files in brand/ directory")
        print("   2. Integrate with CM modules")
        print("   3. Test with real content")
        print("   4. Deploy to production")
    else:
        print_error("SOME VALIDATION TESTS FAILED ❌")
        print("\n⚠️  Please fix the errors above before proceeding.")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
