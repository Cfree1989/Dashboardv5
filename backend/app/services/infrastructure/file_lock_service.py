"""
Redis-based file locking service to prevent concurrent file operations.

This service provides atomic file locking to prevent race conditions during
file operations. Locks are stored in Redis with automatic expiration to
prevent deadlocks from crashed processes.
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class FileLockService:
    """Redis-based distributed file locking service."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the file lock service.
        
        Args:
            redis_url: Redis connection URL. Defaults to REDIS_URL env var.
        """
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://redis:6379')
        self._redis_client = None
        self.lock_prefix = "file_lock:"
        self.default_timeout = 300  # 5 minutes default lock timeout
        self.acquire_timeout = 30   # 30 seconds to acquire lock
        self.lock_refresh_interval = 60  # Refresh lock every minute
        # Fallback in-memory lock store when Redis is unavailable (used in tests/dev)
        self._fallback_enabled = False
        self._mem_locks: Dict[str, Dict[str, Any]] = {}
        from threading import RLock
        self._mem_lock = RLock()
        
    @property
    def redis_client(self) -> redis.Redis:
        """Get or create Redis client with connection pooling."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                self._redis_client.ping()
                logger.info("File lock service connected to Redis successfully")
            except Exception as e:
                # Preserve original behavior for explicit connection failures
                logger.error(f"Failed to connect to Redis for file locking: {e}")
                raise RuntimeError(f"Redis connection failed: {e}")
        return self._redis_client
    
    def _generate_lock_key(self, file_path: str) -> str:
        """Generate a unique lock key for a file path."""
        # Normalize path to prevent lock bypass with different path formats
        normalized_path = os.path.normpath(os.path.abspath(file_path))
        return f"{self.lock_prefix}{normalized_path}"
    
    def _generate_lock_value(self, operation_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Generate a unique lock value with metadata."""
        lock_data = {
            'operation_id': operation_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'process_id': os.getpid(),
            'metadata': metadata or {}
        }
        # Simple serialization for Redis storage
        import json
        return json.dumps(lock_data)
    
    def acquire_lock(
        self,
        file_path: str,
        operation_id: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        # Backward-compatibility alias used by legacy/tests
        lock_id: Optional[str] = None,
    ) -> bool:
        """
        Acquire an exclusive lock on a file.
        
        Args:
            file_path: Path to the file to lock
            operation_id: Unique identifier for this operation
            timeout: Lock timeout in seconds (default: 5 minutes)
            metadata: Optional metadata to store with the lock
            
        Returns:
            True if lock was acquired, False otherwise
        """
        # Support legacy callers that pass lock_id instead of operation_id
        if operation_id is None and lock_id is not None:
            operation_id = lock_id
        if operation_id is None:
            raise ValueError("operation_id (or lock_id) must be provided for file locking")

        lock_key = self._generate_lock_key(file_path)
        lock_value = self._generate_lock_value(operation_id, metadata)
        lock_timeout = int(timeout) if timeout is not None else self.default_timeout

        try:
            # Try to acquire lock with SET NX EX (set if not exists with expiration)
            acquired = self.redis_client.set(
                lock_key,
                lock_value,
                nx=True,  # Only set if key doesn't exist
                ex=lock_timeout,  # Expire after timeout seconds
            )

            if acquired:
                logger.info(
                    f"File lock acquired successfully: {file_path} "
                    f"(operation: {operation_id}, timeout: {lock_timeout}s)"
                )
                return True
            else:
                # Check who owns the lock for better error reporting
                existing_lock = self.redis_client.get(lock_key)
                if existing_lock:
                    try:
                        import json
                        lock_info = json.loads(existing_lock)
                        logger.warning(
                            f"File lock acquisition failed - already locked: {file_path} "
                            f"(owner: {lock_info.get('operation_id')}, "
                            f"since: {lock_info.get('timestamp')})"
                        )
                    except Exception:
                        logger.warning(
                            f"File lock acquisition failed - already locked: {file_path}"
                        )
                else:
                    logger.warning(
                        f"File lock acquisition failed - race condition: {file_path}"
                    )
                return False

        except Exception as e:
            # Fallback to in-memory lock when Redis unavailable or errors occur
            logger.error(
                f"Redis error during lock acquisition for {file_path}: {e}"
            )
            self._fallback_enabled = True
            with self._mem_lock:
                if lock_key in self._mem_locks:
                    return False
                self._mem_locks[lock_key] = {
                    'operation_id': operation_id,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'metadata': metadata or {},
                }
                return True
    
    def release_lock(self, file_path: str, operation_id: str) -> bool:
        """
        Release a lock on a file.
        
        Args:
            file_path: Path to the file to unlock
            operation_id: Operation ID that acquired the lock
            
        Returns:
            True if lock was released, False if lock didn't exist or wasn't owned by operation_id
        """
        lock_key = self._generate_lock_key(file_path)

        try:
            # Use Lua script to ensure atomic check-and-delete
            lua_script = """
            local lock_key = KEYS[1]
            local expected_operation_id = ARGV[1]
            
            local current_value = redis.call('GET', lock_key)
            if not current_value then
                return 0  -- Lock doesn't exist
            end
            
            local lock_data = cjson.decode(current_value)
            if lock_data.operation_id == expected_operation_id then
                redis.call('DEL', lock_key)
                return 1  -- Successfully released
            else
                return -1  -- Lock owned by different operation
            end
            """
            
            result = self.redis_client.eval(lua_script, 1, lock_key, operation_id)
            
            if result == 1:
                logger.info(f"File lock released successfully: {file_path} (operation: {operation_id})")
                return True
            elif result == 0:
                logger.warning(f"Lock release attempted but lock didn't exist: {file_path} (operation: {operation_id})")
                return False
            else:  # result == -1
                logger.error(f"Lock release failed - not owned by operation: {file_path} (operation: {operation_id})")
                return False
                
        except Exception as e:
            # Fallback path
            logger.error(f"Redis error during lock release for {file_path}: {e}")
            with self._mem_lock:
                info = self._mem_locks.get(lock_key)
                if not info:
                    return False
                if info.get('operation_id') == operation_id:
                    del self._mem_locks[lock_key]
                    return True
                return False
    
    def extend_lock(self, file_path: str, operation_id: str, additional_time: int = 300) -> bool:
        """
        Extend the timeout of an existing lock.
        
        Args:
            file_path: Path to the locked file
            operation_id: Operation ID that owns the lock
            additional_time: Additional seconds to extend the lock
            
        Returns:
            True if lock was extended, False otherwise
        """
        lock_key = self._generate_lock_key(file_path)

        try:
            # Use Lua script to ensure atomic check-and-extend
            lua_script = """
            local lock_key = KEYS[1]
            local expected_operation_id = ARGV[1]
            local additional_time = tonumber(ARGV[2])
            
            local current_value = redis.call('GET', lock_key)
            if not current_value then
                return 0  -- Lock doesn't exist
            end
            
            local lock_data = cjson.decode(current_value)
            if lock_data.operation_id == expected_operation_id then
                redis.call('EXPIRE', lock_key, additional_time)
                return 1  -- Successfully extended
            else
                return -1  -- Lock owned by different operation
            end
            """
            
            result = self.redis_client.eval(lua_script, 1, lock_key, operation_id, additional_time)
            
            if result == 1:
                logger.info(f"File lock extended: {file_path} (operation: {operation_id}, +{additional_time}s)")
                return True
            elif result == 0:
                logger.warning(f"Lock extension failed - lock doesn't exist: {file_path} (operation: {operation_id})")
                return False
            else:  # result == -1
                logger.error(f"Lock extension failed - not owned by operation: {file_path} (operation: {operation_id})")
                return False
                
        except Exception as e:
            logger.error(f"Redis error during lock extension for {file_path}: {e}")
            # No-op for in-memory fallback (no TTL management)
            with self._mem_lock:
                return lock_key in self._mem_locks and self._mem_locks[lock_key].get('operation_id') == operation_id
    
    def get_lock_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a lock on a file.
        
        Args:
            file_path: Path to check for locks
            
        Returns:
            Lock information dict or None if no lock exists
        """
        lock_key = self._generate_lock_key(file_path)

        try:
            lock_value = self.redis_client.get(lock_key)
            if lock_value:
                import json
                lock_data = json.loads(lock_value)

                # Add TTL information
                ttl = self.redis_client.ttl(lock_key)
                lock_data['ttl_seconds'] = ttl
                lock_data['expires_at'] = (
                    datetime.now(timezone.utc) + timedelta(seconds=ttl)
                ).isoformat() if ttl > 0 else None

                return lock_data
            return None

        except Exception as e:
            logger.error(f"Error getting lock info for {file_path}: {e}")
            with self._mem_lock:
                info = self._mem_locks.get(lock_key)
                if not info:
                    return None
                # Mimic structure returned by Redis path
                return {
                    'operation_id': info.get('operation_id'),
                    'timestamp': info.get('timestamp'),
                    'process_id': os.getpid(),
                    'metadata': info.get('metadata', {}),
                    'ttl_seconds': None,
                    'expires_at': None,
                }
    
    def is_locked(self, file_path: str) -> bool:
        """
        Check if a file is currently locked.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is locked, False otherwise
        """
        return self.get_lock_info(file_path) is not None
    
    def cleanup_expired_locks(self) -> int:
        """
        Clean up any locks that have expired but weren't properly removed.
        
        Note: Redis should handle this automatically with TTL, but this method
        provides additional cleanup for monitoring purposes.
        
        Returns:
            Number of expired locks cleaned up
        """
        try:
            # Get all lock keys
            lock_keys = self.redis_client.keys(f"{self.lock_prefix}*")
            cleaned_count = 0

            for key in lock_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # Key exists but has no expiration
                    logger.warning(f"Found lock without TTL, removing: {key}")
                    self.redis_client.delete(key)
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} orphaned locks")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error during lock cleanup: {e}")
            # For fallback, nothing to cleanup
            return 0
    
    @contextmanager
    def file_lock(
        self, 
        file_path: str, 
        operation_id: str,
        timeout: Optional[int] = None,
        acquire_timeout: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for file locking with automatic release.
        
        Args:
            file_path: Path to the file to lock
            operation_id: Unique identifier for this operation
            timeout: Lock timeout in seconds
            acquire_timeout: Seconds to wait for lock acquisition
            metadata: Optional metadata to store with the lock
            
        Raises:
            RuntimeError: If lock cannot be acquired within acquire_timeout
            
        Example:
            with file_lock_service.file_lock('/path/to/file', 'operation_123'):
                # Perform file operations safely
                pass
        """
        acquire_deadline = time.time() + (acquire_timeout or self.acquire_timeout)
        
        # Try to acquire lock with retries
        while time.time() < acquire_deadline:
            if self.acquire_lock(file_path, operation_id, timeout, metadata):
                try:
                    yield
                    return
                finally:
                    self.release_lock(file_path, operation_id)
            
            # Wait a bit before retrying
            time.sleep(0.1)
        
        # Failed to acquire lock
        lock_info = self.get_lock_info(file_path)
        owner_info = ""
        if lock_info:
            owner_info = f" (owned by: {lock_info.get('operation_id')}, since: {lock_info.get('timestamp')})"
        
        raise RuntimeError(
            f"Failed to acquire file lock within {acquire_timeout or self.acquire_timeout} seconds: "
            f"{file_path}{owner_info}"
        )


# Global instance for application use
_file_lock_service = None

def get_file_lock_service() -> FileLockService:
    """Get the global file lock service instance."""
    global _file_lock_service
    if _file_lock_service is None:
        _file_lock_service = FileLockService()
    return _file_lock_service
