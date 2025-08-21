import pytest
import time
from unittest.mock import Mock, patch
from app.services.caching_service import CachingService


class TestCachingService:
    def setup_method(self):
        """Set up test fixtures"""
        self.caching_service = CachingService()
    
    def test_init_with_default_ttl(self):
        """Test CachingService initialization with default TTL"""
        with patch('os.environ.get', return_value='60'):
            service = CachingService()
            assert service._cache_ttl == 60
    
    def test_init_with_custom_ttl(self):
        """Test CachingService initialization with custom TTL"""
        service = CachingService(cache_ttl=120)
        assert service._cache_ttl == 120
    
    def test_is_testing_environment_default_behavior(self):
        """Test testing environment detection default behavior"""
        # In unit tests without Flask context, should return False
        result = self.caching_service._is_testing_environment()
        assert result is False
    
    def test_get_cache_hit(self):
        """Test cache get returns data when available and not expired"""
        # Set up cache with data that expires in 10 seconds
        cache_key = ('test', 'key')
        test_data = {'test': 'data'}
        expires_at = time.time() + 10
        self.caching_service._cache[cache_key] = (expires_at, test_data)
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            result = self.caching_service.get(cache_key)
            
            assert result == test_data
    
    def test_get_cache_miss(self):
        """Test cache get returns None when key doesn't exist"""
        cache_key = ('test', 'key')
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            result = self.caching_service.get(cache_key)
            
            assert result is None
    
    def test_get_cache_expired(self):
        """Test cache get returns None and removes expired entry"""
        cache_key = ('test', 'key')
        test_data = {'test': 'data'}
        expires_at = time.time() - 10  # Expired 10 seconds ago
        self.caching_service._cache[cache_key] = (expires_at, test_data)
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            result = self.caching_service.get(cache_key)
            
            assert result is None
            assert cache_key not in self.caching_service._cache
    
    def test_get_in_testing_environment(self):
        """Test cache get returns None in testing environment"""
        cache_key = ('test', 'key')
        test_data = {'test': 'data'}
        self.caching_service._cache[cache_key] = (time.time() + 60, test_data)
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=True):
            result = self.caching_service.get(cache_key)
            
            assert result is None
    
    def test_set_cache_data(self):
        """Test cache set stores data with correct expiration"""
        cache_key = ('test', 'key')
        test_data = {'test': 'data'}
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            with patch('time.time', return_value=1000):
                self.caching_service.set(cache_key, test_data)
                
                assert cache_key in self.caching_service._cache
                expires_at, stored_data = self.caching_service._cache[cache_key]
                assert stored_data == test_data
                assert expires_at == 1000 + self.caching_service._cache_ttl
    
    def test_set_cache_with_custom_ttl(self):
        """Test cache set with custom TTL override"""
        cache_key = ('test', 'key')
        test_data = {'test': 'data'}
        custom_ttl = 120
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            with patch('time.time', return_value=1000):
                self.caching_service.set(cache_key, test_data, ttl=custom_ttl)
                
                expires_at, stored_data = self.caching_service._cache[cache_key]
                assert expires_at == 1000 + custom_ttl
    
    def test_set_in_testing_environment(self):
        """Test cache set does nothing in testing environment"""
        cache_key = ('test', 'key')
        test_data = {'test': 'data'}
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=True):
            self.caching_service.set(cache_key, test_data)
            
            assert cache_key not in self.caching_service._cache
    
    def test_invalidate_existing_key(self):
        """Test cache invalidate removes existing key"""
        cache_key = ('test', 'key')
        test_data = {'test': 'data'}
        self.caching_service._cache[cache_key] = (time.time() + 60, test_data)
        
        self.caching_service.invalidate(cache_key)
        
        assert cache_key not in self.caching_service._cache
    
    def test_invalidate_nonexistent_key(self):
        """Test cache invalidate handles nonexistent key gracefully"""
        cache_key = ('test', 'key')
        
        # Should not raise an exception
        self.caching_service.invalidate(cache_key)
        
        assert cache_key not in self.caching_service._cache
    
    def test_clear_cache(self):
        """Test cache clear removes all entries"""
        # Add some test data
        self.caching_service._cache[('key1',)] = (time.time() + 60, 'data1')
        self.caching_service._cache[('key2',)] = (time.time() + 60, 'data2')
        
        assert len(self.caching_service._cache) == 2
        
        self.caching_service.clear()
        
        assert len(self.caching_service._cache) == 0
    
    def test_get_cache_stats(self):
        """Test cache stats return correct information"""
        # Add some test data
        self.caching_service._cache[('key1',)] = (time.time() + 60, 'data1')
        self.caching_service._cache[('key2',)] = (time.time() + 60, 'data2')
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            stats = self.caching_service.get_cache_stats()
            
            assert stats['total_entries'] == 2
            assert stats['cache_ttl'] == self.caching_service._cache_ttl
            assert stats['is_testing'] is False
    
    def test_get_cache_stats_in_testing(self):
        """Test cache stats show testing environment correctly"""
        with patch.object(self.caching_service, '_is_testing_environment', return_value=True):
            stats = self.caching_service.get_cache_stats()
            
            assert stats['is_testing'] is True
    
    def test_cache_key_types(self):
        """Test cache works with different key types"""
        # Test with string key
        string_key = ('string', 'key')
        string_data = 'string data'
        
        # Test with mixed key
        mixed_key = ('string', 123, True)
        mixed_data = {'mixed': 'data'}
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            # Set data
            self.caching_service.set(string_key, string_data)
            self.caching_service.set(mixed_key, mixed_data)
            
            # Get data
            assert self.caching_service.get(string_key) == string_data
            assert self.caching_service.get(mixed_key) == mixed_data
    
    def test_cache_expiration_cleanup(self):
        """Test expired entries are cleaned up on access"""
        cache_key = ('test', 'key')
        test_data = {'test': 'data'}
        expires_at = time.time() - 1  # Expired 1 second ago
        self.caching_service._cache[cache_key] = (expires_at, test_data)
        
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            # First access should return None and clean up
            result = self.caching_service.get(cache_key)
            assert result is None
            assert cache_key not in self.caching_service._cache
            
            # Second access should still return None
            result = self.caching_service.get(cache_key)
            assert result is None
    
    def test_cache_ttl_environment_override(self):
        """Test cache TTL can be overridden by environment variable"""
        with patch('os.environ.get', return_value='120'):
            service = CachingService()
            assert service._cache_ttl == 120
    
    def test_cache_ttl_custom_overrides_environment(self):
        """Test custom TTL overrides environment variable"""
        with patch('os.environ.get', return_value='120'):
            service = CachingService(cache_ttl=60)
            assert service._cache_ttl == 60
    
    def test_cache_multiple_operations(self):
        """Test multiple cache operations work correctly together"""
        with patch.object(self.caching_service, '_is_testing_environment', return_value=False):
            # Set multiple entries
            self.caching_service.set(('key1',), 'data1')
            self.caching_service.set(('key2',), 'data2')
            
            # Verify they exist
            assert self.caching_service.get(('key1',)) == 'data1'
            assert self.caching_service.get(('key2',)) == 'data2'
            
            # Invalidate one
            self.caching_service.invalidate(('key1',))
            assert self.caching_service.get(('key1',)) is None
            assert self.caching_service.get(('key2',)) == 'data2'
            
            # Clear all
            self.caching_service.clear()
            assert self.caching_service.get(('key2',)) is None
