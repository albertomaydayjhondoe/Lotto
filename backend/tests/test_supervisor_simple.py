#!/usr/bin/env python3
"""
Simple test runner for Sprint 10 - Supervisor Layer
No dependencies on pytest - pure Python
"""

print('Running Supervisor Layer Tests...')
print('=' * 60)

from app.supervisor import (
    SupervisorOrchestrator,
    GlobalSummaryGenerator,
    GPTSupervisor,
    GeminiValidator,
    SupervisorConfig,
    create_supervision_input,
    EngineSource,
    SeverityLevel,
    DecisionType,
    Decision,
    Action,
    Metrics,
    CostReport,
)
from datetime import datetime

tests_passed = 0
tests_failed = 0

def test(name, condition, error_msg=''):
    global tests_passed, tests_failed
    if condition:
        print(f'✓ {name}')
        tests_passed += 1
        return True
    else:
        print(f'✗ {name}: {error_msg}')
        tests_failed += 1
        return False

# Test 1: Imports and instantiation
print('\n[Suite 1: Basic Functionality]')
config = SupervisorConfig()
test('Config creation', config is not None)
orchestrator = SupervisorOrchestrator(config)
test('Orchestrator creation', orchestrator is not None)

# Test 2: Summary generation
print('\n[Suite 2: Summary Generation]')
input_data = create_supervision_input(
    engine_source=EngineSource.SATELLITE,
    severity=SeverityLevel.MEDIUM
)
summary_gen = GlobalSummaryGenerator()
summary = summary_gen.generate_summary(input_data)
test('Summary generated', summary is not None)
test('Summary has ID', summary.summary_id is not None)

# Test 3: GPT analysis
print('\n[Suite 3: GPT Analysis]')
gpt = GPTSupervisor()
analysis = gpt.analyze(summary)
test('GPT analysis', analysis is not None)
test('GPT confidence valid', 0.0 <= analysis.confidence <= 1.0)

# Test 4: Gemini validation
print('\n[Suite 4: Gemini Validation]')
gemini = GeminiValidator(config)
validation = gemini.validate(summary, analysis)
test('Gemini validation', validation is not None)
test('Has risk score', 0.0 <= validation.risk_score <= 1.0)

# Test 5: Budget rejection
print('\n[Suite 5: Budget Rejection]')
input_budget = create_supervision_input(
    engine_source=EngineSource.META_ADS,
    severity=SeverityLevel.CRITICAL
)
input_budget.costs = CostReport(today=60.0, month_accumulated=500.0, budget_total=1000.0)
summary_budget = summary_gen.generate_summary(input_budget)
analysis_budget = gpt.analyze(summary_budget)
validation_budget = gemini.validate(summary_budget, analysis_budget)
test('Budget exceeded rejected', validation_budget.approved == False)

# Test 6: Integration
print('\n[Suite 6: Full Integration]')
result = orchestrator.supervise(input_data)
test('Full supervision', result is not None)
test('Has all components', len(result.components_executed) == 3)

print('')
print('=' * 60)
print(f'RESULTS: {tests_passed} passed, {tests_failed} failed')
if tests_failed == 0:
    print('✅ ALL TESTS PASSED - Sprint 10 COMPLETE')
else:
    print(f'❌ {tests_failed} tests failed')
print('=' * 60)
