#!/usr/bin/env python3
"""
Wizard Voice Assistant Test Runner
Comprehensive test execution and reporting
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class WizardTestRunner:
    """Test runner for Wizard Voice Assistant"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.results = {}
    
    def run_unit_tests(self, verbose=False):
        """Run unit tests"""
        print("🧪 Running Unit Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "unit"),
            "-v" if verbose else "-q",
            "--tb=short",
            "-m", "unit"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            self.results['unit_tests'] = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                print("✅ Unit tests passed")
            else:
                print("❌ Unit tests failed")
                if verbose:
                    print(result.stdout)
                    print(result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Unit tests timed out")
            self.results['unit_tests'] = {'success': False, 'error': 'timeout'}
            return False
        except Exception as e:
            print(f"❌ Error running unit tests: {e}")
            self.results['unit_tests'] = {'success': False, 'error': str(e)}
            return False
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests"""
        print("🔗 Running Integration Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "integration"),
            "-v" if verbose else "-q",
            "--tb=short",
            "-m", "integration"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            self.results['integration_tests'] = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                print("✅ Integration tests passed")
            else:
                print("❌ Integration tests failed")
                if verbose:
                    print(result.stdout)
                    print(result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Integration tests timed out")
            self.results['integration_tests'] = {'success': False, 'error': 'timeout'}
            return False
        except Exception as e:
            print(f"❌ Error running integration tests: {e}")
            self.results['integration_tests'] = {'success': False, 'error': str(e)}
            return False
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests"""
        print("⚡ Running Performance Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "performance"),
            "-v" if verbose else "-q",
            "--tb=short",
            "-m", "performance and not slow"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            self.results['performance_tests'] = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                print("✅ Performance tests passed")
            else:
                print("❌ Performance tests failed")
                if verbose:
                    print(result.stdout)
                    print(result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Performance tests timed out")
            self.results['performance_tests'] = {'success': False, 'error': 'timeout'}
            return False
        except Exception as e:
            print(f"❌ Error running performance tests: {e}")
            self.results['performance_tests'] = {'success': False, 'error': str(e)}
            return False
    
    def run_coverage_analysis(self):
        """Run test coverage analysis"""
        print("📊 Running Coverage Analysis...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "--cov=wizard",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json",
            "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # Parse coverage from output
            coverage_info = self.parse_coverage_output(result.stdout)
            
            self.results['coverage'] = {
                'returncode': result.returncode,
                'coverage_info': coverage_info,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                print(f"✅ Coverage analysis completed")
                if coverage_info:
                    print(f"📈 Total coverage: {coverage_info.get('total', 'N/A')}%")
            else:
                print("❌ Coverage analysis failed")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Coverage analysis timed out")
            self.results['coverage'] = {'success': False, 'error': 'timeout'}
            return False
        except Exception as e:
            print(f"❌ Error running coverage analysis: {e}")
            self.results['coverage'] = {'success': False, 'error': str(e)}
            return False
    
    def parse_coverage_output(self, output):
        """Parse coverage information from pytest output"""
        lines = output.split('\n')
        coverage_info = {}
        
        for line in lines:
            if 'TOTAL' in line and '%' in line:
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            coverage_info['total'] = int(part.rstrip('%'))
                            break
                        except ValueError:
                            pass
        
        return coverage_info
    
    def run_linting(self):
        """Run code linting"""
        print("🔍 Running Code Linting...")
        
        # Run flake8
        flake8_cmd = [sys.executable, "-m", "flake8", "wizard/", "--max-line-length=100"]
        
        try:
            flake8_result = subprocess.run(flake8_cmd, capture_output=True, text=True, timeout=120)
            
            self.results['linting'] = {
                'flake8_returncode': flake8_result.returncode,
                'flake8_output': flake8_result.stdout,
                'success': flake8_result.returncode == 0
            }
            
            if flake8_result.returncode == 0:
                print("✅ Linting passed")
            else:
                print("⚠️  Linting issues found")
                print(flake8_result.stdout)
            
            return flake8_result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Linting timed out")
            self.results['linting'] = {'success': False, 'error': 'timeout'}
            return False
        except Exception as e:
            print(f"❌ Error running linting: {e}")
            self.results['linting'] = {'success': False, 'error': str(e)}
            return False
    
    def validate_installation(self):
        """Validate installation and dependencies"""
        print("🔧 Validating Installation...")
        
        validation_results = {}
        
        # Check Python version
        python_version = sys.version_info
        validation_results['python_version'] = {
            'version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            'valid': python_version >= (3, 8)
        }
        
        # Check required packages
        required_packages = [
            'pytest', 'pyttsx3', 'speech_recognition', 'pyaudio',
            'nltk', 'psutil', 'requests', 'pathlib'
        ]
        
        package_results = {}
        for package in required_packages:
            try:
                __import__(package)
                package_results[package] = True
            except ImportError:
                package_results[package] = False
        
        validation_results['packages'] = package_results
        
        # Check test directory structure
        test_structure = {
            'tests_dir': self.test_dir.exists(),
            'unit_tests': (self.test_dir / "unit").exists(),
            'integration_tests': (self.test_dir / "integration").exists(),
            'performance_tests': (self.test_dir / "performance").exists(),
            'conftest': (self.test_dir / "conftest.py").exists()
        }
        
        validation_results['test_structure'] = test_structure
        
        self.results['validation'] = validation_results
        
        # Report results
        all_valid = True
        
        if validation_results['python_version']['valid']:
            print(f"✅ Python {validation_results['python_version']['version']}")
        else:
            print(f"❌ Python {validation_results['python_version']['version']} (requires 3.8+)")
            all_valid = False
        
        missing_packages = [pkg for pkg, available in package_results.items() if not available]
        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            all_valid = False
        else:
            print("✅ All required packages available")
        
        missing_structure = [item for item, exists in test_structure.items() if not exists]
        if missing_structure:
            print(f"❌ Missing test structure: {', '.join(missing_structure)}")
            all_valid = False
        else:
            print("✅ Test structure complete")
        
        return all_valid
    
    def generate_report(self, output_file=None):
        """Generate test report"""
        print("\n📋 Generating Test Report...")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': self.results,
            'summary': self.generate_summary()
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report saved to {output_file}")
        
        # Print summary
        print("\n📊 Test Summary:")
        print("=" * 50)
        
        for test_type, result in self.results.items():
            if isinstance(result, dict) and 'success' in result:
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                print(f"{test_type.replace('_', ' ').title()}: {status}")
        
        overall_success = all(
            result.get('success', False) 
            for result in self.results.values() 
            if isinstance(result, dict) and 'success' in result
        )
        
        print(f"\nOverall Result: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        return report
    
    def generate_summary(self):
        """Generate summary statistics"""
        summary = {
            'total_test_suites': len(self.results),
            'passed_suites': 0,
            'failed_suites': 0
        }
        
        for result in self.results.values():
            if isinstance(result, dict) and 'success' in result:
                if result['success']:
                    summary['passed_suites'] += 1
                else:
                    summary['failed_suites'] += 1
        
        summary['success_rate'] = (
            summary['passed_suites'] / summary['total_test_suites'] * 100
            if summary['total_test_suites'] > 0 else 0
        )
        
        return summary
    
    def run_all_tests(self, include_performance=True, include_coverage=True, 
                     include_linting=True, verbose=False):
        """Run all test suites"""
        print("🧙 Wizard Voice Assistant - Test Suite")
        print("=" * 50)
        
        start_time = time.time()
        
        # Validate installation first
        if not self.validate_installation():
            print("❌ Installation validation failed. Cannot proceed with tests.")
            return False
        
        # Run test suites
        results = []
        
        results.append(self.run_unit_tests(verbose))
        results.append(self.run_integration_tests(verbose))
        
        if include_performance:
            results.append(self.run_performance_tests(verbose))
        
        if include_coverage:
            results.append(self.run_coverage_analysis())
        
        if include_linting:
            results.append(self.run_linting())
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  Total test duration: {duration:.2f} seconds")
        
        # Generate report
        report = self.generate_report("test_report.json")
        
        return all(results)


def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="Wizard Voice Assistant Test Runner")
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--coverage", action="store_true", help="Run coverage analysis only")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--validate", action="store_true", help="Validate installation only")
    
    parser.add_argument("--no-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage analysis")
    parser.add_argument("--no-lint", action="store_true", help="Skip linting")
    
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--report", help="Output report file")
    
    args = parser.parse_args()
    
    runner = WizardTestRunner()
    
    # Handle single test type requests
    if args.unit:
        success = runner.run_unit_tests(args.verbose)
    elif args.integration:
        success = runner.run_integration_tests(args.verbose)
    elif args.performance:
        success = runner.run_performance_tests(args.verbose)
    elif args.coverage:
        success = runner.run_coverage_analysis()
    elif args.lint:
        success = runner.run_linting()
    elif args.validate:
        success = runner.validate_installation()
    else:
        # Run all tests
        success = runner.run_all_tests(
            include_performance=not args.no_performance,
            include_coverage=not args.no_coverage,
            include_linting=not args.no_lint,
            verbose=args.verbose
        )
    
    # Generate report if requested
    if args.report:
        runner.generate_report(args.report)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()