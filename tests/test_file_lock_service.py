"""
Test suite for Redis-based file locking service.

Tests cover lock acquisition, release, timeouts, concurrent access,
and error handling scenarios.
"""

import pytest
import time
import json
import threading
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.file_lock_service import FileLockService


class TestFileLockService:
    """Test cases for FileLockService."""
    
    @pytest.fixture
    def lock_service(self):
        """Create a file lock service instance for testing."""
        # Use a test Redis URL if available, otherwise mock
        return FileLockService(redis_url='redis://localhost:6379/15')  # Use DB 15 for tests
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing without actual Redis."""
        with patch('redis.from_url') as mock_redis_factory:
            mock_client = MagicMock()
            mock_redis_factory.return_value = mock_client
            mock_client.ping.return_value = True
            yield mock_client
    
    def test_lock_service_initialization(self, mock_redis):
        """Test that lock service initializes correctly."""
        service = FileLockService('redis://test:6379')
        assert service.redis_url == 'redis://test:6379'
        assert service.lock_prefix == "file_lock:"
        assert service.default_timeout == 300
        assert service.acquire_timeout == 30
    
    def test_redis_connection_success(self, mock_redis):
        """Test successful Redis connection."""
        service = FileLockService('redis://test:6379')
        client = service.redis_client
        
        mock_redis.ping.assert_called_once()
        assert client is not None
    
    def test_redis_connection_failure(self):
        """Test Redis connection failure handling."""
        with patch('app.services.file_lock_service.redis.from_url') as mock_redis_factory:
            from redis.exceptions import RedisError
            mock_redis_factory.side_effect = RedisError("Connection failed")
            
            service = FileLockService('redis://invalid:6379')
            
            with pytest.raises(RuntimeError, match="Redis connection failed"):
                _ = service.redis_client
    
    def test_generate_lock_key(self, mock_redis):
        """Test lock key generation."""
        service = FileLockService()
        
        # Test path normalization
        key1 = service._generate_lock_key('/path/to/file.txt')
        key2 = service._generate_lock_key('/path/to/../to/file.txt')
        
        assert key1 == key2  # Paths should be normalized
        assert key1.startswith('file_lock:')
        assert 'file.txt' in key1
    
    def test_generate_lock_value(self, mock_redis):
        """Test lock value generation with metadata."""
        service = FileLockService()
        
        value = service._generate_lock_value('op_123', {'user': 'test'})
        data = json.loads(value)
        
        assert data['operation_id'] == 'op_123'
        assert data['metadata']['user'] == 'test'
        assert 'timestamp' in data
        assert 'process_id' in data
    
    def test_acquire_lock_success(self, mock_redis):
        """Test successful lock acquisition."""
        service = FileLockService()
        mock_redis.set.return_value = True
        
        result = service.acquire_lock('/test/file.txt', 'op_123', timeout=60)
        
        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0].endswith('file.txt')  # Lock key contains filename
        assert call_args[1]['nx'] is True  # Only set if not exists
        assert call_args[1]['ex'] == 60  # Expiration time
    
    def test_acquire_lock_already_locked(self, mock_redis):
        """Test lock acquisition when file is already locked."""
        service = FileLockService()
        mock_redis.set.return_value = False  # Lock already exists
        
        # Mock existing lock data
        existing_lock = json.dumps({
            'operation_id': 'other_op',
            'timestamp': '2024-01-01T12:00:00',
            'process_id': 12345
        })
        mock_redis.get.return_value = existing_lock
        
        result = service.acquire_lock('/test/file.txt', 'op_123')
        
        assert result is False
        mock_redis.get.assert_called_once()
    
    def test_release_lock_success(self, mock_redis):
        """Test successful lock release."""
        service = FileLockService()
        mock_redis.eval.return_value = 1  # Successfully released
        
        result = service.release_lock('/test/file.txt', 'op_123')
        
        assert result is True
        mock_redis.eval.assert_called_once()
    
    def test_release_lock_not_owned(self, mock_redis):
        """Test lock release when not owned by operation."""
        service = FileLockService()
        mock_redis.eval.return_value = -1  # Not owned by operation
        
        result = service.release_lock('/test/file.txt', 'op_123')
        
        assert result is False
    
    def test_release_lock_doesnt_exist(self, mock_redis):
        """Test lock release when lock doesn't exist."""
        service = FileLockService()
        mock_redis.eval.return_value = 0  # Lock doesn't exist
        
        result = service.release_lock('/test/file.txt', 'op_123')
        
        assert result is False
    
    def test_extend_lock_success(self, mock_redis):
        """Test successful lock extension."""
        service = FileLockService()
        mock_redis.eval.return_value = 1  # Successfully extended
        
        result = service.extend_lock('/test/file.txt', 'op_123', additional_time=300)
        
        assert result is True
        mock_redis.eval.assert_called_once()
    
    def test_get_lock_info_exists(self, mock_redis):
        """Test getting lock info when lock exists."""
        service = FileLockService()
        
        lock_data = {
            'operation_id': 'op_123',
            'timestamp': '2024-01-01T12:00:00',
            'process_id': 12345,
            'metadata': {'user': 'test'}
        }
        mock_redis.get.return_value = json.dumps(lock_data)
        mock_redis.ttl.return_value = 240  # 4 minutes remaining
        
        info = service.get_lock_info('/test/file.txt')
        
        assert info['operation_id'] == 'op_123'
        assert info['ttl_seconds'] == 240
        assert 'expires_at' in info
    
    def test_get_lock_info_not_exists(self, mock_redis):
        """Test getting lock info when lock doesn't exist."""
        service = FileLockService()
        mock_redis.get.return_value = None
        
        info = service.get_lock_info('/test/file.txt')
        
        assert info is None
    
    def test_is_locked_true(self, mock_redis):
        """Test is_locked when file is locked."""
        service = FileLockService()
        mock_redis.get.return_value = json.dumps({'operation_id': 'op_123'})
        mock_redis.ttl.return_value = 240
        
        result = service.is_locked('/test/file.txt')
        
        assert result is True
    
    def test_is_locked_false(self, mock_redis):
        """Test is_locked when file is not locked."""
        service = FileLockService()
        mock_redis.get.return_value = None
        
        result = service.is_locked('/test/file.txt')
        
        assert result is False
    
    def test_cleanup_expired_locks(self, mock_redis):
        """Test cleanup of expired locks."""
        service = FileLockService()
        
        # Mock keys and TTL values
        mock_redis.keys.return_value = ['file_lock:/test1.txt', 'file_lock:/test2.txt']
        mock_redis.ttl.side_effect = [-1, 60]  # First key has no TTL, second is valid
        
        cleaned_count = service.cleanup_expired_locks()
        
        assert cleaned_count == 1
        mock_redis.delete.assert_called_once_with('file_lock:/test1.txt')
    
    def test_context_manager_success(self, mock_redis):
        """Test file lock context manager with successful acquisition."""
        service = FileLockService()
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1  # Successful release
        
        with service.file_lock('/test/file.txt', 'op_123', timeout=60):
            # Lock should be acquired here
            pass
        
        # Verify acquire and release were called
        mock_redis.set.assert_called_once()
        mock_redis.eval.assert_called_once()
    
    def test_context_manager_acquisition_timeout(self, mock_redis):
        """Test context manager timeout when lock cannot be acquired."""
        service = FileLockService()
        mock_redis.set.return_value = False  # Lock acquisition always fails
        mock_redis.get.return_value = json.dumps({'operation_id': 'other_op'})
        mock_redis.ttl.return_value = 240  # Mock TTL for get_lock_info
        
        with pytest.raises(RuntimeError, match="Failed to acquire file lock"):
            with service.file_lock('/test/file.txt', 'op_123', acquire_timeout=0.1):
                pass
    
    def test_context_manager_exception_handling(self, mock_redis):
        """Test that lock is released even if exception occurs in context."""
        service = FileLockService()
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        
        with pytest.raises(ValueError):
            with service.file_lock('/test/file.txt', 'op_123'):
                raise ValueError("Test exception")
        
        # Verify release was still called
        mock_redis.eval.assert_called_once()
    
    def test_concurrent_lock_acquisition(self, mock_redis):
        """Test concurrent lock acquisition behavior."""
        service = FileLockService()
        
        # Mock Redis to simulate one successful acquisition and one failure
        mock_redis.set.side_effect = [True, False]  # First succeeds, second fails
        mock_redis.get.return_value = json.dumps({'operation_id': 'op_1'})
        
        def acquire_lock(operation_id):
            return service.acquire_lock('/test/file.txt', operation_id)
        
        # Simulate concurrent access
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(acquire_lock, 'op_1')
            future2 = executor.submit(acquire_lock, 'op_2')
            
            results = [future.result() for future in as_completed([future1, future2])]
        
        # Only one should succeed
        assert results.count(True) == 1
        assert results.count(False) == 1
    
    def test_lock_with_metadata(self, mock_redis):
        """Test lock acquisition with custom metadata."""
        service = FileLockService()
        mock_redis.set.return_value = True
        
        metadata = {'user': 'test_user', 'operation_type': 'file_move'}
        service.acquire_lock('/test/file.txt', 'op_123', metadata=metadata)
        
        # Verify metadata is included in lock value
        call_args = mock_redis.set.call_args
        lock_value = call_args[0][1]
        lock_data = json.loads(lock_value)
        
        assert lock_data['metadata']['user'] == 'test_user'
        assert lock_data['metadata']['operation_type'] == 'file_move'
    
    def test_redis_error_handling(self, mock_redis):
        """Test handling of Redis errors."""
        from redis.exceptions import RedisError
        
        service = FileLockService()
        mock_redis.set.side_effect = RedisError("Connection lost")
        
        # Should return False on Redis errors, not raise exception
        result = service.acquire_lock('/test/file.txt', 'op_123')
        assert result is False
    
    def test_global_service_instance(self):
        """Test that global service instance works correctly."""
        from app.services.file_lock_service import get_file_lock_service
        
        service1 = get_file_lock_service()
        service2 = get_file_lock_service()
        
        # Should return the same instance
        assert service1 is service2


class TestFileLockServiceIntegration:
    """Integration tests that require actual Redis connection."""
    
    @pytest.fixture
    def redis_service(self):
        """Create service connected to test Redis database."""
        try:
            service = FileLockService('redis://localhost:6379/15')
            # Test connection
            service.redis_client.ping()
            # Clear any existing locks
            service.redis_client.flushdb()
            return service
        except Exception:
            pytest.skip("Redis not available for integration tests")
    
    def test_real_lock_acquisition_and_release(self, redis_service):
        """Test actual lock acquisition and release with real Redis."""
        file_path = '/test/integration_test.txt'
        operation_id = 'integration_test_op'
        
        # Acquire lock
        assert redis_service.acquire_lock(file_path, operation_id, timeout=10)
        
        # Verify lock exists
        assert redis_service.is_locked(file_path)
        
        # Get lock info
        info = redis_service.get_lock_info(file_path)
        assert info['operation_id'] == operation_id
        assert info['ttl_seconds'] > 0
        
        # Release lock
        assert redis_service.release_lock(file_path, operation_id)
        
        # Verify lock is gone
        assert not redis_service.is_locked(file_path)
    
    def test_real_lock_timeout(self, redis_service):
        """Test that locks automatically expire."""
        file_path = '/test/timeout_test.txt'
        operation_id = 'timeout_test_op'
        
        # Acquire lock with short timeout
        assert redis_service.acquire_lock(file_path, operation_id, timeout=1)
        assert redis_service.is_locked(file_path)
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Lock should be gone
        assert not redis_service.is_locked(file_path)
    
    def test_real_concurrent_access(self, redis_service):
        """Test concurrent access with real Redis."""
        file_path = '/test/concurrent_test.txt'
        
        def try_acquire_lock(operation_id):
            return redis_service.acquire_lock(file_path, operation_id, timeout=5)
        
        # Start multiple threads trying to acquire the same lock
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(try_acquire_lock, f'op_{i}') 
                for i in range(5)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        # Only one should succeed
        successful_acquisitions = sum(results)
        assert successful_acquisitions == 1
        
        # Clean up
        redis_service.redis_client.flushdb()
    
    def test_real_context_manager(self, redis_service):
        """Test context manager with real Redis."""
        file_path = '/test/context_test.txt'
        operation_id = 'context_test_op'
        
        # Verify no lock initially
        assert not redis_service.is_locked(file_path)
        
        with redis_service.file_lock(file_path, operation_id, timeout=10):
            # Should be locked inside context
            assert redis_service.is_locked(file_path)
        
        # Should be unlocked after context
        assert not redis_service.is_locked(file_path)
