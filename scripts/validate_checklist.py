#!/usr/bin/env python3
"""
STAKAZO - Checklist Validation Script

This script validates code changes against the mandatory checklist
defined in docs/CHECKLIST_OBLIGATORIO.md.

Usage:
    python scripts/validate_checklist.py

Output:
    scripts/validate_output.json

Exit Codes:
    0 - Validation passed (ok or warnings)
    1 - Validation failed (critical violations)
    2 - Script error
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add backend to PYTHONPATH for imports
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class ChecklistValidator:
    """Validates code changes against STAKAZO checklist."""
    
    def __init__(self):
        self.violations: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []
        self.repo_root = Path(__file__).parent.parent
        
    def run_command(self, cmd: List[str]) -> tuple[int, str, str]:
        """Execute shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def check_secrets(self) -> None:
        """Check for exposed secrets in code."""
        print("🔍 Checking for secrets...")
        
        # Patterns that indicate potential secrets
        secret_patterns = [
            r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']',
            r'api[_-]?secret\s*=\s*["\'][^"\']{10,}["\']',
            r'password\s*=\s*["\'][^"\']{5,}["\']',
            r'token\s*=\s*["\'][^"\']{20,}["\']',
            r'aws[_-]?access[_-]?key[_-]?id\s*=',
            r'aws[_-]?secret[_-]?access[_-]?key\s*=',
            r'sk-[A-Za-z0-9]{20,}',  # OpenAI API key pattern
            r'Bearer\s+[A-Za-z0-9\-\._~\+\/]{20,}',
        ]
        
        # Get all Python files (exclude tests and venv)
        code_files = list(self.repo_root.glob("backend/**/*.py"))
        
        # Directories to exclude from secret scanning
        exclude_dirs = [
            '__pycache__',
            '.pyc',
            '/tests/',
            '/test_',
            '/.venv/',
            '/venv/',
            '/site-packages/'
        ]
        
        found_secrets = False
        for file_path in code_files:
            # Skip excluded directories
            if any(excluded in str(file_path) for excluded in exclude_dirs):
                continue
            
            try:
                content = file_path.read_text()
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Filter out obvious examples and env var references
                        real_matches = [
                            m for m in matches
                            if 'example' not in m.lower()
                            and 'your_' not in m.lower()
                            and 'xxx' not in m.lower()
                            and 'os.getenv' not in m
                        ]
                        if real_matches:
                            self.violations.append(
                                f"Potential secret in {file_path.relative_to(self.repo_root)}: {pattern}"
                            )
                            found_secrets = True
            except Exception as e:
                self.warnings.append(f"Could not read {file_path}: {e}")
        
        if not found_secrets:
            self.passed.append("No exposed secrets detected")
    
    def check_linting(self) -> None:
        """Check code quality with flake8."""
        print("🎨 Running linting checks...")
        
        # Check if flake8 is installed
        code, _, _ = self.run_command(["which", "flake8"])
        if code != 0:
            self.warnings.append("flake8 not installed - skipping lint check")
            return
        
        # Run flake8 on backend
        code, stdout, stderr = self.run_command([
            "flake8",
            "backend/app/",
            "--max-line-length=100",
            "--exclude=__pycache__,*.pyc,alembic",
            "--count"
        ])
        
        if code != 0:
            error_count = len(stdout.strip().split('\n')) if stdout.strip() else 0
            if error_count > 100:
                self.warnings.append(f"flake8 found {error_count} linting errors - please address incrementally")
            elif error_count > 10:
                self.warnings.append(f"flake8 found {error_count} linting issues - consider fixing")
            else:
                self.warnings.append(f"flake8 found {error_count} minor linting issues")
        else:
            self.passed.append("Code passes linting checks (flake8)")
    
    def check_tests(self) -> None:
        """Check if tests exist and can run."""
        print("🧪 Checking test suite...")
        
        # Check if pytest is installed
        code, _, _ = self.run_command(["which", "pytest"])
        if code != 0:
            self.warnings.append("pytest not installed - skipping test check")
            return
        
        # Check for test files
        test_files = list(self.repo_root.glob("backend/tests/test_*.py"))
        if not test_files:
            self.warnings.append("No test files found in backend/tests/")
            return
        
        self.passed.append(f"Found {len(test_files)} test file(s)")
        
        # Try to collect tests (don't run them, just check they're valid)
        code, stdout, stderr = self.run_command([
            "pytest",
            "backend/tests/",
            "--collect-only",
            "-q"
        ])
        
        if code != 0:
            self.warnings.append("Test collection failed - tests may have syntax errors")
        else:
            test_count = stdout.count("<Function") + stdout.count("<Method")
            if test_count > 0:
                self.passed.append(f"Test suite is valid ({test_count} tests collected)")
            else:
                self.warnings.append("No tests collected - test files may be empty")
    
    def check_documentation(self) -> None:
        """Check if documentation exists."""
        print("📚 Checking documentation...")
        
        required_docs = [
            "docs/LINEA_MAESTRA_DESARROLLO.txt",
            "docs/CHECKLIST_OBLIGATORIO.md",
        ]
        
        for doc in required_docs:
            doc_path = self.repo_root / doc
            if not doc_path.exists():
                self.violations.append(f"Required documentation missing: {doc}")
            else:
                self.passed.append(f"Documentation exists: {doc}")
    
    def check_env_files(self) -> None:
        """Check .env files are not committed."""
        print("🔐 Checking environment files...")
        
        # Check if .env is in .gitignore
        gitignore_path = self.repo_root / ".gitignore"
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if '.env' in content:
                self.passed.append(".env is properly gitignored")
            else:
                self.warnings.append(".env not found in .gitignore")
        
        # Check if .env exists in git index
        code, stdout, _ = self.run_command(["git", "ls-files", "**/.env"])
        if stdout.strip():
            self.violations.append(".env file is tracked in git - this is a security risk!")
        else:
            self.passed.append("No .env files tracked in git")
    
    def check_imports(self) -> None:
        """Check for proper import statements."""
        print("📦 Checking imports...")
        
        python_files = list(self.repo_root.glob("backend/app/**/*.py"))
        
        issues_found = 0
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
            
            try:
                content = file_path.read_text()
                lines = content.split('\n')
                
                # Check for wildcard imports
                for i, line in enumerate(lines, 1):
                    if re.match(r'^from .+ import \*', line.strip()):
                        self.warnings.append(
                            f"Wildcard import in {file_path.relative_to(self.repo_root)}:{i}"
                        )
                        issues_found += 1
            except Exception:
                continue
        
        if issues_found == 0:
            self.passed.append("No wildcard imports detected")
    
    def check_git_status(self) -> None:
        """Check git repository status."""
        print("🔄 Checking git status...")
        
        # Check current branch
        code, stdout, _ = self.run_command(["git", "branch", "--show-current"])
        if code == 0:
            branch = stdout.strip()
            if branch == "main":
                self.warnings.append(
                    "Currently on MAIN branch - direct commits to MAIN are discouraged"
                )
            else:
                self.passed.append(f"Working on feature branch: {branch}")
        
        # Check for uncommitted changes
        code, stdout, _ = self.run_command(["git", "status", "--porcelain"])
        if code == 0 and stdout.strip():
            uncommitted = len(stdout.strip().split('\n'))
            self.warnings.append(f"{uncommitted} uncommitted change(s) in working directory")
    
    def check_python_files(self) -> None:
        """Check Python files for basic quality."""
        print("🐍 Checking Python files...")
        
        python_files = list(self.repo_root.glob("backend/app/**/*.py"))
        
        if not python_files:
            self.warnings.append("No Python files found in backend/app/")
            return
        
        self.passed.append(f"Found {len(python_files)} Python file(s) in backend/app/")
        
        # Check for print statements (debugging code)
        files_with_prints = 0
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
            
            try:
                content = file_path.read_text()
                # Look for print() but not in comments or strings context
                if re.search(r'^\s*print\(', content, re.MULTILINE):
                    files_with_prints += 1
            except Exception:
                continue
        
        if files_with_prints > 0:
            self.warnings.append(
                f"{files_with_prints} file(s) contain print() statements - "
                "consider using logging instead"
            )
        else:
            self.passed.append("No print() debug statements detected")
    
    def validate(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("=" * 60)
        print("STAKAZO - Checklist Validation")
        print("=" * 60)
        
        # Run all checks
        self.check_secrets()
        self.check_env_files()
        self.check_git_status()
        self.check_python_files()
        self.check_imports()
        self.check_linting()
        self.check_tests()
        self.check_documentation()
        
        # Determine overall status
        if self.violations:
            status = "fail"
            message = f"Validation failed with {len(self.violations)} critical violation(s)"
        elif self.warnings:
            status = "warning"
            message = f"Validation passed with {len(self.warnings)} warning(s)"
        else:
            status = "ok"
            message = "All checks passed successfully"
        
        result = {
            "status": status,
            "message": message,
            "violations": self.violations,
            "warnings": self.warnings,
            "passed": self.passed,
            "summary": {
                "violations_count": len(self.violations),
                "warnings_count": len(self.warnings),
                "passed_count": len(self.passed)
            }
        }
        
        return result


def main():
    """Main entry point."""
    validator = ChecklistValidator()
    
    try:
        result = validator.validate()
        
        # Write output JSON
        output_path = validator.repo_root / "scripts" / "validate_output.json"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Status: {result['status'].upper()}")
        print(f"Message: {result['message']}")
        print(f"\n✅ Passed: {len(result['passed'])}")
        print(f"⚠️  Warnings: {len(result['warnings'])}")
        print(f"❌ Violations: {len(result['violations'])}")
        
        if result['violations']:
            print("\n🚨 CRITICAL VIOLATIONS:")
            for i, v in enumerate(result['violations'], 1):
                print(f"  {i}. {v}")
        
        if result['warnings']:
            print("\n⚠️  WARNINGS:")
            for i, w in enumerate(result['warnings'], 1):
                print(f"  {i}. {w}")
        
        print(f"\n📄 Full report: {output_path}")
        print("=" * 60)
        
        # Exit with appropriate code
        if result['status'] == 'fail':
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ ERROR: Validation script failed: {e}", file=sys.stderr)
        
        error_result = {
            "status": "error",
            "message": f"Validation script error: {str(e)}",
            "violations": [f"Script execution failed: {str(e)}"],
            "warnings": [],
            "passed": []
        }
        
        try:
            output_path = validator.repo_root / "scripts" / "validate_output.json"
            with open(output_path, 'w') as f:
                json.dump(error_result, f, indent=2)
        except Exception:
            pass
        
        sys.exit(2)


if __name__ == "__main__":
    main()
