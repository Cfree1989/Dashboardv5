"""
Performance tests for atomic file operations.

This test suite covers:
- Performance comparison between atomic and non-atomic operations
- Memory usage analysis
- Disk I/O impact measurement
- Concurrent operation performance
- Scalability testing
"""

import pytest
import tempfile
import json
import shutil
import time
try:
    import psutil
except ImportError:
    import pytest; pytest.skip("psutil not installed", allow_module_level=True)
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
import statistics

from app.services.atomic_file_service import get_atomic_file_service
from app.services.file_service import move_authoritative  # Old non-atomic method


class TestAtomicFilePerformance:
    """Performance tests for atomic file operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def atomic_service(self):
        """Get atomic file service instance."""
        return get_atomic_file_service()
    
    def create_test_files(self, temp_dir, num_files=10, file_size_kb=100):
        """Create test files with specified size."""
        files = []
        for i in range(num_files):
            file_path = temp_dir / f"test_file_{i}.txt"
            metadata_path = temp_dir / f"test_file_{i}_metadata.json"
            
            # Create test file with specified size
            content = "x" * (file_size_kb * 1024)
            with open(file_path, 'w') as f:
                f.write(content)
            
            # Create metadata file
            metadata = {
                "status": "UPLOADED",
                "file_path": str(file_path),
                "created_at": "2024-01-01T12:00:00Z",
                "size": len(content),
                "job_id": f"job_{i}"
            }
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            files.append((file_path, metadata_path))
        
        return files
    
    def measure_memory_usage(self):
        """Measure current memory usage."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def test_performance_comparison_atomic_vs_non_atomic(self, temp_dir, atomic_service):
        """Compare performance between atomic and non-atomic file operations."""
        # Create test files
        test_files = self.create_test_files(temp_dir, 50, file_size_kb=50)
        
        # Test atomic operations
        atomic_times = []
        atomic_memory_before = self.measure_memory_usage()
        
        for i, (file_path, metadata_path) in enumerate(test_files):
            target_dir = temp_dir / f"atomic_target_{i}"
            target_dir.mkdir()
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            start_time = time.time()
            
            with atomic_service.move_file(
                source_path=str(file_path),
                target_path=str(target_path),
                metadata_path=str(metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=f"atomic_job_{i}"
            ) as operation:
                pass
            
            end_time = time.time()
            atomic_times.append(end_time - start_time)
        
        atomic_memory_after = self.measure_memory_usage()
        atomic_memory_used = atomic_memory_after - atomic_memory_before
        
        # Test non-atomic operations (simulated)
        non_atomic_times = []
        non_atomic_memory_before = self.measure_memory_usage()
        
        # Create fresh test files for non-atomic test
        test_files_2 = self.create_test_files(temp_dir, 50, file_size_kb=50)
        
        for i, (file_path, metadata_path) in enumerate(test_files_2):
            target_dir = temp_dir / f"non_atomic_target_{i}"
            target_dir.mkdir()
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            start_time = time.time()
            
            # Simulate non-atomic operation (copy then delete)
            shutil.copy2(file_path, target_path)
            shutil.copy2(metadata_path, target_metadata_path)
            file_path.unlink()
            metadata_path.unlink()
            
            end_time = time.time()
            non_atomic_times.append(end_time - start_time)
        
        non_atomic_memory_after = self.measure_memory_usage()
        non_atomic_memory_used = non_atomic_memory_after - non_atomic_memory_before
        
        # Calculate statistics
        atomic_avg = statistics.mean(atomic_times)
        atomic_std = statistics.stdev(atomic_times) if len(atomic_times) > 1 else 0
        atomic_min = min(atomic_times)
        atomic_max = max(atomic_times)
        
        non_atomic_avg = statistics.mean(non_atomic_times)
        non_atomic_std = statistics.stdev(non_atomic_times) if len(non_atomic_times) > 1 else 0
        non_atomic_min = min(non_atomic_times)
        non_atomic_max = max(non_atomic_times)
        
        # Performance assertions
        # Atomic operations should not be more than 50% slower than non-atomic
        performance_ratio = atomic_avg / non_atomic_avg
        assert performance_ratio < 1.5, f"Atomic operations too slow: {performance_ratio:.2f}x slower than non-atomic"
        
        # Memory usage should be reasonable
        assert atomic_memory_used < 100, f"Atomic operations used too much memory: {atomic_memory_used:.2f} MB"
        
        print(f"Performance Comparison Results:")
        print(f"Atomic Operations:")
        print(f"  Average: {atomic_avg:.4f}s (±{atomic_std:.4f}s)")
        print(f"  Range: {atomic_min:.4f}s - {atomic_max:.4f}s")
        print(f"  Memory: {atomic_memory_used:.2f} MB")
        print(f"Non-Atomic Operations:")
        print(f"  Average: {non_atomic_avg:.4f}s (±{non_atomic_std:.4f}s)")
        print(f"  Range: {non_atomic_min:.4f}s - {non_atomic_max:.4f}s")
        print(f"  Memory: {non_atomic_memory_used:.2f} MB")
        print(f"Performance Ratio: {performance_ratio:.2f}x")
    
    def test_concurrent_performance_scaling(self, temp_dir, atomic_service):
        """Test performance scaling with concurrent operations."""
        # Test with different numbers of concurrent operations
        concurrency_levels = [1, 2, 4, 8]
        results = {}
        
        for concurrency in concurrency_levels:
            # Create test files for this concurrency level
            test_files = self.create_test_files(temp_dir, 20, file_size_kb=25)
            
            def perform_move(file_info):
                """Perform a single move operation."""
                file_path, metadata_path = file_info
                target_dir = temp_dir / f"concurrent_{concurrency}_{file_path.stem}"
                target_dir.mkdir()
                target_path = target_dir / file_path.name
                target_metadata_path = target_dir / metadata_path.name
                
                start_time = time.time()
                
                with atomic_service.move_file(
                    source_path=str(file_path),
                    target_path=str(target_path),
                    metadata_path=str(metadata_path),
                    target_metadata_path=str(target_metadata_path),
                    job_id=f"concurrent_job_{file_path.stem}"
                ) as operation:
                    pass
                
                end_time = time.time()
                return end_time - start_time
            
            # Execute concurrent operations
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(perform_move, file_info) for file_info in test_files]
                operation_times = [future.result() for future in as_completed(futures)]
            total_time = time.time() - start_time
            
            results[concurrency] = {
                'total_time': total_time,
                'avg_operation_time': statistics.mean(operation_times),
                'throughput': len(test_files) / total_time,
                'operation_times': operation_times
            }
        
        # Verify performance characteristics
        for concurrency in concurrency_levels:
            result = results[concurrency]
            
            # Throughput should increase with concurrency (up to a point)
            if concurrency > 1:
                prev_result = results[concurrency // 2]
                # Throughput should not decrease significantly with increased concurrency
                throughput_ratio = result['throughput'] / prev_result['throughput']
                assert throughput_ratio > 0.5, f"Throughput degraded too much with {concurrency} workers: {throughput_ratio:.2f}"
            
            # Individual operation time should remain reasonable
            assert result['avg_operation_time'] < 1.0, f"Operation time too high with {concurrency} workers: {result['avg_operation_time']:.3f}s"
        
        print(f"Concurrent Performance Results:")
        for concurrency, result in results.items():
            print(f"  {concurrency} workers:")
            print(f"    Total time: {result['total_time']:.3f}s")
            print(f"    Avg operation: {result['avg_operation_time']:.4f}s")
            print(f"    Throughput: {result['throughput']:.2f} ops/sec")
    
    def test_memory_usage_under_load(self, temp_dir, atomic_service):
        """Test memory usage under sustained load."""
        # Create many small files to test memory usage
        test_files = self.create_test_files(temp_dir, 200, file_size_kb=1)
        
        memory_samples = []
        
        def perform_move_with_memory_tracking(file_info):
            """Perform move operation and track memory usage."""
            memory_before = self.measure_memory_usage()
            
            file_path, metadata_path = file_info
            target_dir = temp_dir / f"memory_test_{file_path.stem}"
            target_dir.mkdir()
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            with atomic_service.move_file(
                source_path=str(file_path),
                target_path=str(target_path),
                metadata_path=str(metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=f"memory_job_{file_path.stem}"
            ) as operation:
                pass
            
            memory_after = self.measure_memory_usage()
            return memory_after - memory_before
        
        # Execute operations and track memory
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(perform_move_with_memory_tracking, file_info) for file_info in test_files]
            memory_deltas = [future.result() for future in as_completed(futures)]
            memory_samples.extend(memory_deltas)
        
        # Calculate memory statistics
        avg_memory_delta = statistics.mean(memory_samples)
        max_memory_delta = max(memory_samples)
        memory_std = statistics.stdev(memory_samples) if len(memory_samples) > 1 else 0
        
        # Memory usage assertions
        assert avg_memory_delta < 10, f"Average memory usage too high: {avg_memory_delta:.2f} MB"
        assert max_memory_delta < 50, f"Peak memory usage too high: {max_memory_delta:.2f} MB"
        
        print(f"Memory Usage Results:")
        print(f"  Average memory delta: {avg_memory_delta:.2f} MB (±{memory_std:.2f} MB)")
        print(f"  Peak memory delta: {max_memory_delta:.2f} MB")
        print(f"  Total operations: {len(memory_samples)}")
    
    def test_disk_io_impact(self, temp_dir, atomic_service):
        """Test disk I/O impact of atomic operations."""
        # Create large files to measure disk I/O impact
        test_files = self.create_test_files(temp_dir, 10, file_size_kb=1000)  # 1MB files
        
        # Measure disk I/O before operations
        disk_io_before = psutil.disk_io_counters()
        
        operation_times = []
        
        for i, (file_path, metadata_path) in enumerate(test_files):
            target_dir = temp_dir / f"disk_io_test_{i}"
            target_dir.mkdir()
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            start_time = time.time()
            
            with atomic_service.move_file(
                source_path=str(file_path),
                target_path=str(target_path),
                metadata_path=str(metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=f"disk_io_job_{i}"
            ) as operation:
                pass
            
            end_time = time.time()
            operation_times.append(end_time - start_time)
        
        # Measure disk I/O after operations
        disk_io_after = psutil.disk_io_counters()
        
        # Calculate I/O statistics
        read_bytes = disk_io_after.read_bytes - disk_io_before.read_bytes
        write_bytes = disk_io_after.write_bytes - disk_io_before.write_bytes
        read_count = disk_io_after.read_count - disk_io_before.read_count
        write_count = disk_io_after.write_count - disk_io_before.write_count
        
        avg_operation_time = statistics.mean(operation_times)
        total_data_moved = sum(file_path.stat().st_size for file_path, _ in test_files)
        
        # I/O efficiency assertions
        # Atomic operations should not use significantly more I/O than necessary
        expected_read_bytes = total_data_moved * 2  # Read source + staging
        expected_write_bytes = total_data_moved * 2  # Write staging + target
        
        read_efficiency = read_bytes / expected_read_bytes
        write_efficiency = write_bytes / expected_write_bytes
        
        assert read_efficiency < 3.0, f"Read I/O too high: {read_efficiency:.2f}x expected"
        assert write_efficiency < 3.0, f"Write I/O too high: {write_efficiency:.2f}x expected"
        
        print(f"Disk I/O Impact Results:")
        print(f"  Total data moved: {total_data_moved / 1024 / 1024:.2f} MB")
        print(f"  Read bytes: {read_bytes / 1024 / 1024:.2f} MB ({read_efficiency:.2f}x expected)")
        print(f"  Write bytes: {write_bytes / 1024 / 1024:.2f} MB ({write_efficiency:.2f}x expected)")
        print(f"  Read operations: {read_count}")
        print(f"  Write operations: {write_count}")
        print(f"  Average operation time: {avg_operation_time:.3f}s")
    
    def test_staging_directory_cleanup_performance(self, temp_dir, atomic_service):
        """Test performance of staging directory cleanup."""
        # Create many small operations to test cleanup performance
        test_files = self.create_test_files(temp_dir, 100, file_size_kb=1)
        
        cleanup_times = []
        
        for i, (file_path, metadata_path) in enumerate(test_files):
            target_dir = temp_dir / f"cleanup_test_{i}"
            target_dir.mkdir()
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            # Measure cleanup time by timing the context manager exit
            start_time = time.time()
            
            with atomic_service.move_file(
                source_path=str(file_path),
                target_path=str(target_path),
                metadata_path=str(metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=f"cleanup_job_{i}"
            ) as operation:
                pass  # Context manager exit triggers cleanup
            
            end_time = time.time()
            cleanup_times.append(end_time - start_time)
        
        # Calculate cleanup statistics
        avg_cleanup_time = statistics.mean(cleanup_times)
        max_cleanup_time = max(cleanup_times)
        cleanup_std = statistics.stdev(cleanup_times) if len(cleanup_times) > 1 else 0
        
        # Cleanup performance assertions
        assert avg_cleanup_time < 0.1, f"Average cleanup time too high: {avg_cleanup_time:.4f}s"
        assert max_cleanup_time < 0.5, f"Peak cleanup time too high: {max_cleanup_time:.4f}s"
        
        print(f"Staging Directory Cleanup Results:")
        print(f"  Average cleanup time: {avg_cleanup_time:.4f}s (±{cleanup_std:.4f}s)")
        print(f"  Peak cleanup time: {max_cleanup_time:.4f}s")
        print(f"  Total operations: {len(cleanup_times)}")
    
    def test_metadata_operation_performance(self, temp_dir, atomic_service):
        """Test performance of metadata operations within atomic file operations."""
        # Create test files with large metadata
        test_files = self.create_test_files(temp_dir, 50, file_size_kb=10)
        
        # Create large metadata for each file
        for file_path, metadata_path in test_files:
            large_metadata = {
                "status": "UPLOADED",
                "file_path": str(file_path),
                "created_at": "2024-01-01T12:00:00Z",
                "size": file_path.stat().st_size,
                "job_id": f"metadata_job_{file_path.stem}",
                "large_field": "x" * 10000,  # 10KB metadata
                "array_field": list(range(1000)),  # Large array
                "nested_field": {
                    "level1": {"level2": {"level3": "deep_value"}},
                    "array": list(range(500))
                }
            }
            with open(metadata_path, 'w') as f:
                json.dump(large_metadata, f)
        
        metadata_operation_times = []
        
        for i, (file_path, metadata_path) in enumerate(test_files):
            target_dir = temp_dir / f"metadata_test_{i}"
            target_dir.mkdir()
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            start_time = time.time()
            
            with atomic_service.move_file(
                source_path=str(file_path),
                target_path=str(target_path),
                metadata_path=str(metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=f"metadata_job_{i}"
            ) as operation:
                # Update metadata during operation
                with open(target_metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                metadata["status"] = "READYTOPRINT"
                metadata["updated_at"] = "2024-01-01T13:00:00Z"
                metadata["processed_by"] = "test_staff"
                
                with open(target_metadata_path, 'w') as f:
                    json.dump(metadata, f)
            
            end_time = time.time()
            metadata_operation_times.append(end_time - start_time)
        
        # Calculate metadata operation statistics
        avg_metadata_time = statistics.mean(metadata_operation_times)
        max_metadata_time = max(metadata_operation_times)
        
        # Metadata operation performance assertions
        assert avg_metadata_time < 0.5, f"Average metadata operation time too high: {avg_metadata_time:.4f}s"
        assert max_metadata_time < 1.0, f"Peak metadata operation time too high: {max_metadata_time:.4f}s"
        
        print(f"Metadata Operation Performance Results:")
        print(f"  Average time: {avg_metadata_time:.4f}s")
        print(f"  Peak time: {max_metadata_time:.4f}s")
        print(f"  Total operations: {len(metadata_operation_times)}")
        print(f"  Metadata size: ~10KB per file")
