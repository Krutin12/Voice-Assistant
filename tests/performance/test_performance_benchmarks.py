"""
Performance benchmarks and tests for Wizard Voice Assistant
"""

import pytest
import time
import psutil
import os
import threading
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wizard.commands.command_router import CommandRouter
from wizard.audio.wake_word_engine import WakeWordEngine
from wizard.audio.speech_recognition import SpeechRecognizer
from wizard.main import WizardApp


@pytest.mark.performance
class TestResponseTimePerformance:
    """Test response time performance metrics"""
    
    def test_command_processing_latency(self, config_manager, sample_commands, performance_thresholds):
        """Test command processing latency"""
        router = CommandRouter(config_manager)
        
        latencies = []
        
        for command in sample_commands:
            start_time = time.perf_counter()
            response = router.process_command(command)
            end_time = time.perf_counter()
            
            latency = end_time - start_time
            latencies.append(latency)
            
            # Each command should meet latency requirement
            assert latency < performance_thresholds["command_processing"]
            assert response is not None
        
        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"Command Processing Performance:")
        print(f"  Average latency: {avg_latency:.3f}s")
        print(f"  Max latency: {max_latency:.3f}s")
        print(f"  Min latency: {min_latency:.3f}s")
        
        # Average should be well under threshold
        assert avg_latency < performance_thresholds["command_processing"] * 0.8
    
    def test_wake_word_detection_latency(self, performance_thresholds):
        """Test wake word detection latency"""
        with patch('pyaudio.PyAudio'):
            engine = WakeWordEngine(["test"], 0.5)
            
            latencies = []
            
            for _ in range(10):
                start_time = time.perf_counter()
                result = engine.is_wake_word_detected()
                end_time = time.perf_counter()
                
                latency = end_time - start_time
                latencies.append(latency)
                
                assert latency < performance_thresholds["wake_word_detection"]
                assert isinstance(result, bool)
            
            avg_latency = sum(latencies) / len(latencies)
            print(f"Wake Word Detection Average Latency: {avg_latency:.3f}s")
    
    def test_speech_recognition_latency(self, performance_thresholds):
        """Test speech recognition latency"""
        with patch('speech_recognition.Recognizer') as mock_recognizer:
            mock_instance = Mock()
            mock_instance.recognize_google.return_value = "test command"
            mock_recognizer.return_value = mock_instance
            
            recognizer = SpeechRecognizer()
            
            latencies = []
            
            for _ in range(5):
                start_time = time.perf_counter()
                result = recognizer.recognize(b"fake_audio_data")
                end_time = time.perf_counter()
                
                latency = end_time - start_time
                latencies.append(latency)
                
                # Note: This is mocked, so latency will be very low
                # In real scenarios, this would be higher
                assert result is not None
            
            avg_latency = sum(latencies) / len(latencies)
            print(f"Speech Recognition Average Latency: {avg_latency:.3f}s")


@pytest.mark.performance
class TestMemoryPerformance:
    """Test memory usage and efficiency"""
    
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def test_command_router_memory_usage(self, config_manager, sample_commands, performance_thresholds):
        """Test command router memory usage"""
        initial_memory = self.get_memory_usage()
        
        router = CommandRouter(config_manager)
        after_init_memory = self.get_memory_usage()
        
        # Process multiple commands
        for command in sample_commands * 5:  # Repeat commands
            router.process_command(command)
        
        final_memory = self.get_memory_usage()
        
        init_overhead = after_init_memory - initial_memory
        processing_overhead = final_memory - after_init_memory
        
        print(f"Memory Usage:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  After init: {after_init_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Init overhead: {init_overhead:.1f} MB")
        print(f"  Processing overhead: {processing_overhead:.1f} MB")
        
        # Memory usage should be reasonable
        assert final_memory < performance_thresholds["memory_usage"]
        assert processing_overhead < 50  # Less than 50MB for processing
    
    def test_memory_leak_detection(self, config_manager, sample_commands):
        """Test for memory leaks during extended operation"""
        router = CommandRouter(config_manager)
        
        # Baseline memory
        baseline_memory = self.get_memory_usage()
        
        # Process commands in batches and check memory
        memory_readings = []
        
        for batch in range(5):
            # Process a batch of commands
            for command in sample_commands:
                router.process_command(command)
            
            # Record memory usage
            current_memory = self.get_memory_usage()
            memory_readings.append(current_memory)
            
            # Small delay to allow garbage collection
            time.sleep(0.1)
        
        # Check for memory growth trend
        memory_growth = memory_readings[-1] - memory_readings[0]
        
        print(f"Memory Leak Test:")
        print(f"  Baseline: {baseline_memory:.1f} MB")
        print(f"  Readings: {[f'{m:.1f}' for m in memory_readings]} MB")
        print(f"  Growth: {memory_growth:.1f} MB")
        
        # Memory growth should be minimal
        assert memory_growth < 20  # Less than 20MB growth
    
    def test_concurrent_memory_usage(self, config_manager):
        """Test memory usage under concurrent load"""
        initial_memory = self.get_memory_usage()
        
        router = CommandRouter(config_manager)
        
        def process_commands():
            for _ in range(10):
                router.process_command("what time is it")
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=process_commands)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        final_memory = self.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        print(f"Concurrent Memory Usage:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Increase: {memory_increase:.1f} MB")
        
        # Memory increase should be reasonable for concurrent operations
        assert memory_increase < 100  # Less than 100MB increase


@pytest.mark.performance
class TestCPUPerformance:
    """Test CPU usage and efficiency"""
    
    def test_cpu_usage_during_processing(self, config_manager, sample_commands):
        """Test CPU usage during command processing"""
        router = CommandRouter(config_manager)
        
        # Monitor CPU usage
        process = psutil.Process(os.getpid())
        cpu_readings = []
        
        start_time = time.time()
        
        # Process commands while monitoring CPU
        for command in sample_commands * 3:
            cpu_before = process.cpu_percent()
            router.process_command(command)
            cpu_after = process.cpu_percent()
            
            cpu_readings.append(cpu_after)
            time.sleep(0.1)  # Small delay for CPU measurement
        
        end_time = time.time()
        duration = end_time - start_time
        
        avg_cpu = sum(cpu_readings) / len(cpu_readings) if cpu_readings else 0
        max_cpu = max(cpu_readings) if cpu_readings else 0
        
        print(f"CPU Performance:")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Average CPU: {avg_cpu:.1f}%")
        print(f"  Max CPU: {max_cpu:.1f}%")
        
        # CPU usage should be reasonable
        # Note: These thresholds may need adjustment based on system
        assert avg_cpu < 80  # Average CPU usage under 80%
    
    def test_idle_cpu_usage(self):
        """Test CPU usage when idle"""
        with patch('pyaudio.PyAudio'):
            engine = WakeWordEngine(["test"], 0.5)
            
            process = psutil.Process(os.getpid())
            
            # Measure baseline CPU
            baseline_cpu = process.cpu_percent(interval=1)
            
            # Simulate idle listening
            cpu_readings = []
            for _ in range(5):
                cpu_before = process.cpu_percent()
                engine.is_wake_word_detected()  # Simulate detection check
                time.sleep(0.2)
                cpu_after = process.cpu_percent()
                cpu_readings.append(cpu_after)
            
            avg_idle_cpu = sum(cpu_readings) / len(cpu_readings)
            
            print(f"Idle CPU Usage:")
            print(f"  Baseline: {baseline_cpu:.1f}%")
            print(f"  Average idle: {avg_idle_cpu:.1f}%")
            
            # Idle CPU should be low
            # Note: Actual wake word detection would use more CPU
            assert avg_idle_cpu < 30  # Less than 30% CPU when idle


@pytest.mark.performance
class TestThroughputPerformance:
    """Test throughput and scalability"""
    
    def test_command_throughput(self, config_manager, sample_commands):
        """Test command processing throughput"""
        router = CommandRouter(config_manager)
        
        # Process commands and measure throughput
        start_time = time.time()
        
        command_count = 0
        for _ in range(3):  # Repeat commands 3 times
            for command in sample_commands:
                router.process_command(command)
                command_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        throughput = command_count / duration
        
        print(f"Command Throughput:")
        print(f"  Commands processed: {command_count}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} commands/second")
        
        # Should process at least 1 command per second
        assert throughput >= 1.0
    
    def test_concurrent_command_processing(self, config_manager):
        """Test concurrent command processing"""
        router = CommandRouter(config_manager)
        
        results = []
        start_time = time.time()
        
        def process_batch():
            batch_results = []
            for _ in range(5):
                result = router.process_command("what time is it")
                batch_results.append(result)
            results.extend(batch_results)
        
        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=process_batch)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        total_commands = len(results)
        concurrent_throughput = total_commands / duration
        
        print(f"Concurrent Throughput:")
        print(f"  Total commands: {total_commands}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Concurrent throughput: {concurrent_throughput:.2f} commands/second")
        
        # All commands should complete successfully
        assert len(results) == 15  # 3 threads * 5 commands each
        for result in results:
            assert result is not None
        
        # Concurrent throughput should be reasonable
        assert concurrent_throughput >= 2.0


@pytest.mark.performance
@pytest.mark.slow
class TestStressPerformance:
    """Stress tests for performance under load"""
    
    def test_high_frequency_commands(self, config_manager):
        """Test performance under high frequency commands"""
        router = CommandRouter(config_manager)
        
        # Process commands rapidly
        start_time = time.time()
        successful_commands = 0
        failed_commands = 0
        
        for i in range(100):  # 100 rapid commands
            try:
                result = router.process_command(f"test command {i}")
                if result:
                    successful_commands += 1
                else:
                    failed_commands += 1
            except Exception:
                failed_commands += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        success_rate = successful_commands / (successful_commands + failed_commands)
        
        print(f"High Frequency Test:")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Successful: {successful_commands}")
        print(f"  Failed: {failed_commands}")
        print(f"  Success rate: {success_rate:.2%}")
        
        # Should maintain high success rate even under stress
        assert success_rate >= 0.95  # 95% success rate
        assert duration < 30  # Should complete within 30 seconds
    
    def test_memory_stress(self, config_manager):
        """Test memory usage under stress"""
        router = CommandRouter(config_manager)
        
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        # Create memory pressure with many commands
        for i in range(200):
            router.process_command(f"complex command with data {i} " * 10)
            
            # Check memory every 50 commands
            if i % 50 == 0:
                current_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                # Memory shouldn't grow excessively
                assert memory_increase < 500  # Less than 500MB increase
        
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"Memory Stress Test:")
        print(f"  Initial memory: {initial_memory:.1f} MB")
        print(f"  Final memory: {final_memory:.1f} MB")
        print(f"  Total increase: {total_increase:.1f} MB")
        
        # Total memory increase should be reasonable
        assert total_increase < 300  # Less than 300MB total increase


@pytest.mark.performance
class TestPerformanceRegression:
    """Test for performance regressions"""
    
    def test_baseline_performance_metrics(self, config_manager, sample_commands):
        """Establish baseline performance metrics"""
        router = CommandRouter(config_manager)
        
        # Measure various performance metrics
        metrics = {
            'command_latencies': [],
            'memory_usage': [],
            'cpu_usage': []
        }
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        for command in sample_commands:
            # Measure command latency
            start_time = time.perf_counter()
            result = router.process_command(command)
            end_time = time.perf_counter()
            
            latency = end_time - start_time
            metrics['command_latencies'].append(latency)
            
            # Measure memory
            current_memory = process.memory_info().rss / 1024 / 1024
            metrics['memory_usage'].append(current_memory - initial_memory)
            
            # Measure CPU
            cpu_usage = process.cpu_percent()
            metrics['cpu_usage'].append(cpu_usage)
            
            assert result is not None
        
        # Calculate summary statistics
        avg_latency = sum(metrics['command_latencies']) / len(metrics['command_latencies'])
        max_memory = max(metrics['memory_usage'])
        avg_cpu = sum(metrics['cpu_usage']) / len(metrics['cpu_usage'])
        
        print(f"Baseline Performance Metrics:")
        print(f"  Average latency: {avg_latency:.3f}s")
        print(f"  Max memory increase: {max_memory:.1f} MB")
        print(f"  Average CPU: {avg_cpu:.1f}%")
        
        # Store baseline metrics for comparison
        baseline = {
            'avg_latency': avg_latency,
            'max_memory': max_memory,
            'avg_cpu': avg_cpu
        }
        
        # Basic sanity checks
        assert avg_latency < 2.0  # Average latency under 2 seconds
        assert max_memory < 100   # Memory increase under 100MB
        assert avg_cpu < 90       # CPU usage under 90%
        
        return baseline