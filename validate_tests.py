#!/usr/bin/env python3
"""
Test Suite Validation Script
Validates the completeness and correctness of the Wizard test suite
"""

import sys
import os
from pathlib import Path
import ast
import importlib.util

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestSuiteValidator:
    """Validates the test suite for completeness and quality"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.wizard_dir = self.project_root / "wizard"
        self.validation_results = {}
    
    def validate_test_structure(self):
        """Validate test directory structure"""
        print("🏗️  Validating test structure...")
        
        required_structure = {
            "tests/__init__.py": "Test package initialization",
            "tests/conftest.py": "Pytest configuration and fixtures",
            "tests/unit/__init__.py": "Unit tests package",
            "tests/integration/__init__.py": "Integration tests package", 
            "tests/performance/__init__.py": "Performance tests package",
            "pytest.ini": "Pytest configuration file",
            "run_tests.py": "Test runner script"
        }
        
        missing_files = []
        existing_files = []
        
        for file_path, description in required_structure.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                existing_files.append((file_path, description))
                print(f"  ✅ {file_path} - {description}")
            else:
                missing_files.append((file_path, description))
                print(f"  ❌ {file_path} - {description}")
        
        self.validation_results['structure'] = {
            'existing': existing_files,
            'missing': missing_files,
            'complete': len(missing_files) == 0
        }
        
        return len(missing_files) == 0
    
    def validate_test_coverage(self):
        """Validate test coverage of main modules"""
        print("\n📊 Validating test coverage...")
        
        # Find all Python modules in wizard directory
        wizard_modules = []
        for py_file in self.wizard_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                relative_path = py_file.relative_to(self.wizard_dir)
                module_name = str(relative_path).replace("/", ".").replace("\\", ".").replace(".py", "")
                wizard_modules.append((module_name, py_file))
        
        # Find all test files
        test_files = []
        for py_file in self.test_dir.rglob("test_*.py"):
            test_files.append(py_file)
        
        # Check coverage
        covered_modules = []
        uncovered_modules = []
        
        for module_name, module_path in wizard_modules:
            # Look for corresponding test file
            test_file_patterns = [
                f"test_{module_name.split('.')[-1]}.py",
                f"test_{module_name.replace('.', '_')}.py"
            ]
            
            found_test = False
            for test_file in test_files:
                if any(pattern in test_file.name for pattern in test_file_patterns):
                    found_test = True
                    break
            
            if found_test:
                covered_modules.append(module_name)
                print(f"  ✅ {module_name}")
            else:
                uncovered_modules.append(module_name)
                print(f"  ⚠️  {module_name} (no dedicated test file)")
        
        coverage_percentage = len(covered_modules) / len(wizard_modules) * 100 if wizard_modules else 0
        
        self.validation_results['coverage'] = {
            'total_modules': len(wizard_modules),
            'covered_modules': len(covered_modules),
            'uncovered_modules': len(uncovered_modules),
            'coverage_percentage': coverage_percentage,
            'uncovered_list': uncovered_modules
        }
        
        print(f"\n  📈 Test coverage: {coverage_percentage:.1f}% ({len(covered_modules)}/{len(wizard_modules)} modules)")
        
        return coverage_percentage >= 70  # 70% minimum coverage
    
    def validate_test_quality(self):
        """Validate test quality and completeness"""
        print("\n🔍 Validating test quality...")
        
        quality_issues = []
        test_stats = {
            'total_test_files': 0,
            'total_test_functions': 0,
            'total_test_classes': 0,
            'files_with_fixtures': 0,
            'files_with_mocks': 0
        }
        
        for test_file in self.test_dir.rglob("test_*.py"):
            if test_file.name == "conftest.py":
                continue
                
            test_stats['total_test_files'] += 1
            
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to analyze test structure
                tree = ast.parse(content)
                
                file_test_functions = 0
                file_test_classes = 0
                has_fixtures = False
                has_mocks = False
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name.startswith('test_'):
                            file_test_functions += 1
                        # Check for fixtures
                        for decorator in node.decorator_list:
                            if (isinstance(decorator, ast.Name) and decorator.id == 'fixture') or \
                               (isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture'):
                                has_fixtures = True
                    
                    elif isinstance(node, ast.ClassDef):
                        if node.name.startswith('Test'):
                            file_test_classes += 1
                
                # Check for mocks in imports
                if 'mock' in content or 'Mock' in content or 'patch' in content:
                    has_mocks = True
                
                test_stats['total_test_functions'] += file_test_functions
                test_stats['total_test_classes'] += file_test_classes
                
                if has_fixtures:
                    test_stats['files_with_fixtures'] += 1
                if has_mocks:
                    test_stats['files_with_mocks'] += 1
                
                # Quality checks
                if file_test_functions == 0 and file_test_classes == 0:
                    quality_issues.append(f"No test functions or classes in {test_file.name}")
                
                if file_test_functions < 3 and file_test_classes == 0:
                    quality_issues.append(f"Few test functions in {test_file.name} ({file_test_functions})")
                
                print(f"  📄 {test_file.name}: {file_test_functions} functions, {file_test_classes} classes")
                
            except Exception as e:
                quality_issues.append(f"Error parsing {test_file.name}: {e}")
                print(f"  ❌ Error parsing {test_file.name}: {e}")
        
        # Print statistics
        print(f"\n  📊 Test Statistics:")
        print(f"    Total test files: {test_stats['total_test_files']}")
        print(f"    Total test functions: {test_stats['total_test_functions']}")
        print(f"    Total test classes: {test_stats['total_test_classes']}")
        print(f"    Files with fixtures: {test_stats['files_with_fixtures']}")
        print(f"    Files with mocks: {test_stats['files_with_mocks']}")
        
        # Print quality issues
        if quality_issues:
            print(f"\n  ⚠️  Quality Issues:")
            for issue in quality_issues:
                print(f"    - {issue}")
        else:
            print(f"\n  ✅ No quality issues found")
        
        self.validation_results['quality'] = {
            'stats': test_stats,
            'issues': quality_issues,
            'quality_score': max(0, 100 - len(quality_issues) * 10)  # Deduct 10 points per issue
        }
        
        return len(quality_issues) <= 3  # Allow up to 3 minor issues
    
    def validate_test_markers(self):
        """Validate test markers and categorization"""
        print("\n🏷️  Validating test markers...")
        
        expected_markers = ['unit', 'integration', 'performance', 'audio', 'slow']
        found_markers = set()
        unmarked_tests = []
        
        for test_file in self.test_dir.rglob("test_*.py"):
            if test_file.name == "conftest.py":
                continue
            
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for pytest markers
                file_has_markers = False
                for marker in expected_markers:
                    if f"@pytest.mark.{marker}" in content:
                        found_markers.add(marker)
                        file_has_markers = True
                
                if not file_has_markers:
                    unmarked_tests.append(test_file.name)
                
            except Exception as e:
                print(f"  ❌ Error checking markers in {test_file.name}: {e}")
        
        print(f"  📋 Found markers: {', '.join(sorted(found_markers))}")
        
        if unmarked_tests:
            print(f"  ⚠️  Files without markers: {', '.join(unmarked_tests)}")
        else:
            print(f"  ✅ All test files have appropriate markers")
        
        self.validation_results['markers'] = {
            'expected_markers': expected_markers,
            'found_markers': list(found_markers),
            'unmarked_files': unmarked_tests,
            'marker_coverage': len(found_markers) / len(expected_markers) * 100
        }
        
        return len(unmarked_tests) <= 1  # Allow one unmarked file
    
    def validate_fixtures_and_mocks(self):
        """Validate fixtures and mocking setup"""
        print("\n🔧 Validating fixtures and mocks...")
        
        # Check conftest.py
        conftest_path = self.test_dir / "conftest.py"
        conftest_quality = {
            'exists': conftest_path.exists(),
            'has_fixtures': False,
            'has_mock_fixtures': False,
            'fixture_count': 0
        }
        
        if conftest_path.exists():
            try:
                with open(conftest_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count fixtures
                fixture_count = content.count('@pytest.fixture')
                conftest_quality['fixture_count'] = fixture_count
                conftest_quality['has_fixtures'] = fixture_count > 0
                
                # Check for mock fixtures
                if 'mock' in content.lower() or 'Mock' in content:
                    conftest_quality['has_mock_fixtures'] = True
                
                print(f"  ✅ conftest.py: {fixture_count} fixtures")
                
            except Exception as e:
                print(f"  ❌ Error reading conftest.py: {e}")
        else:
            print(f"  ❌ conftest.py not found")
        
        # Check for proper mocking patterns
        mock_patterns = {
            'patch_usage': 0,
            'mock_objects': 0,
            'proper_cleanup': 0
        }
        
        for test_file in self.test_dir.rglob("test_*.py"):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '@patch(' in content or 'patch(' in content:
                    mock_patterns['patch_usage'] += 1
                
                if 'Mock()' in content or 'MagicMock()' in content:
                    mock_patterns['mock_objects'] += 1
                
                # Check for proper cleanup (context managers, fixtures)
                if 'with patch(' in content or '@pytest.fixture' in content:
                    mock_patterns['proper_cleanup'] += 1
                
            except Exception as e:
                print(f"  ❌ Error checking mocks in {test_file.name}: {e}")
        
        print(f"  🎭 Mock usage: {mock_patterns['patch_usage']} files use @patch")
        print(f"  🎭 Mock objects: {mock_patterns['mock_objects']} files use Mock objects")
        print(f"  🧹 Proper cleanup: {mock_patterns['proper_cleanup']} files use proper cleanup")
        
        self.validation_results['fixtures_mocks'] = {
            'conftest_quality': conftest_quality,
            'mock_patterns': mock_patterns
        }
        
        return conftest_quality['has_fixtures'] and mock_patterns['patch_usage'] > 0
    
    def validate_performance_tests(self):
        """Validate performance test implementation"""
        print("\n⚡ Validating performance tests...")
        
        perf_test_dir = self.test_dir / "performance"
        perf_validation = {
            'directory_exists': perf_test_dir.exists(),
            'has_benchmarks': False,
            'has_thresholds': False,
            'has_stress_tests': False
        }
        
        if perf_test_dir.exists():
            for test_file in perf_test_dir.glob("test_*.py"):
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for performance-related patterns
                    if 'time.perf_counter()' in content or 'time.time()' in content:
                        perf_validation['has_benchmarks'] = True
                    
                    if 'performance_thresholds' in content or 'threshold' in content:
                        perf_validation['has_thresholds'] = True
                    
                    if 'stress' in content.lower() or 'load' in content.lower():
                        perf_validation['has_stress_tests'] = True
                    
                    print(f"  ⚡ {test_file.name}: Performance test file")
                    
                except Exception as e:
                    print(f"  ❌ Error checking {test_file.name}: {e}")
        else:
            print(f"  ❌ Performance test directory not found")
        
        print(f"  📊 Has benchmarks: {'✅' if perf_validation['has_benchmarks'] else '❌'}")
        print(f"  🎯 Has thresholds: {'✅' if perf_validation['has_thresholds'] else '❌'}")
        print(f"  💪 Has stress tests: {'✅' if perf_validation['has_stress_tests'] else '❌'}")
        
        self.validation_results['performance'] = perf_validation
        
        return all([
            perf_validation['directory_exists'],
            perf_validation['has_benchmarks'],
            perf_validation['has_thresholds']
        ])
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n📋 Validation Report")
        print("=" * 50)
        
        # Calculate overall score
        validation_scores = []
        
        for category, results in self.validation_results.items():
            if category == 'structure':
                score = 100 if results['complete'] else 50
            elif category == 'coverage':
                score = min(100, results['coverage_percentage'])
            elif category == 'quality':
                score = results['quality_score']
            elif category == 'markers':
                score = results['marker_coverage']
            elif category == 'fixtures_mocks':
                score = 80 if results['conftest_quality']['has_fixtures'] else 40
            elif category == 'performance':
                score = 100 if all(results.values()) else 60
            else:
                score = 50
            
            validation_scores.append(score)
            print(f"{category.replace('_', ' ').title()}: {score:.1f}/100")
        
        overall_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
        
        print(f"\nOverall Test Suite Quality: {overall_score:.1f}/100")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if overall_score >= 90:
            print("  ✅ Excellent test suite! Well done.")
        elif overall_score >= 80:
            print("  👍 Good test suite with minor improvements needed.")
        elif overall_score >= 70:
            print("  ⚠️  Adequate test suite but needs improvement.")
        else:
            print("  ❌ Test suite needs significant improvement.")
        
        # Specific recommendations
        if self.validation_results.get('coverage', {}).get('coverage_percentage', 0) < 80:
            print("  - Add more test files to improve coverage")
        
        if len(self.validation_results.get('quality', {}).get('issues', [])) > 2:
            print("  - Address test quality issues")
        
        if not self.validation_results.get('performance', {}).get('has_benchmarks', False):
            print("  - Add performance benchmarks")
        
        return overall_score
    
    def run_validation(self):
        """Run complete test suite validation"""
        print("🧙 Wizard Voice Assistant - Test Suite Validation")
        print("=" * 55)
        
        validation_steps = [
            ("Test Structure", self.validate_test_structure),
            ("Test Coverage", self.validate_test_coverage),
            ("Test Quality", self.validate_test_quality),
            ("Test Markers", self.validate_test_markers),
            ("Fixtures & Mocks", self.validate_fixtures_and_mocks),
            ("Performance Tests", self.validate_performance_tests)
        ]
        
        results = []
        
        for step_name, step_function in validation_steps:
            try:
                result = step_function()
                results.append(result)
            except Exception as e:
                print(f"❌ Error in {step_name}: {e}")
                results.append(False)
        
        # Generate final report
        overall_score = self.generate_validation_report()
        
        return all(results) and overall_score >= 70


def main():
    """Main validation entry point"""
    validator = TestSuiteValidator()
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()