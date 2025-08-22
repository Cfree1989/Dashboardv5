"""
Tests for FileConfigurationService
"""

import pytest
import os
from unittest.mock import patch
from app.services.infrastructure.file_configuration_service import (
    FileConfigurationService,
    get_file_configuration_service
)


class TestFileConfigurationService:
    """Test cases for FileConfigurationService"""
    
    def test_default_allowed_extensions(self):
        """Test default allowed extensions are loaded correctly"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            expected = {'.stl', '.obj', '.3mf', '.form', '.idea'}
            assert service.allowed_extensions == expected
    
    def test_custom_allowed_extensions(self):
        """Test custom allowed extensions from environment"""
        custom_exts = 'stl,obj,3mf,ply,fbx'
        with patch.dict(os.environ, {'ALLOWED_FILE_EXTENSIONS': custom_exts}):
            service = FileConfigurationService()
            expected = {'.stl', '.obj', '.3mf', '.ply', '.fbx'}
            assert service.allowed_extensions == expected
    
    def test_allowed_extensions_with_dots(self):
        """Test allowed extensions that already have dots"""
        custom_exts = '.stl,.obj,.3mf'
        with patch.dict(os.environ, {'ALLOWED_FILE_EXTENSIONS': custom_exts}):
            service = FileConfigurationService()
            expected = {'.stl', '.obj', '.3mf'}
            assert service.allowed_extensions == expected
    
    def test_default_extension_priority(self):
        """Test default extension priority is loaded correctly"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            expected = {'.3mf': 0, '.form': 1, '.idea': 2, '.stl': 3, '.obj': 4}
            assert service.extension_priority == expected
    
    def test_custom_extension_priority(self):
        """Test custom extension priority from environment"""
        custom_priority = 'stl,obj,3mf'
        with patch.dict(os.environ, {'FILE_EXTENSION_PRIORITY': custom_priority}):
            service = FileConfigurationService()
            expected = {'.stl': 0, '.obj': 1, '.3mf': 2}
            assert service.extension_priority == expected
    
    def test_default_max_file_size(self):
        """Test default max file size is loaded correctly"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            expected = 50 * 1024 * 1024  # 50MB in bytes
            assert service.max_file_size == expected
            assert service.max_file_size_mb == 50
    
    def test_custom_max_file_size(self):
        """Test custom max file size from environment"""
        with patch.dict(os.environ, {'MAX_FILE_SIZE_MB': '100'}):
            service = FileConfigurationService()
            expected = 100 * 1024 * 1024  # 100MB in bytes
            assert service.max_file_size == expected
            assert service.max_file_size_mb == 100
    
    def test_invalid_max_file_size(self):
        """Test handling of invalid max file size"""
        with patch.dict(os.environ, {'MAX_FILE_SIZE_MB': 'invalid'}):
            service = FileConfigurationService()
            expected = 50 * 1024 * 1024  # Should fall back to default
            assert service.max_file_size == expected
            assert service.max_file_size_mb == 50
    
    def test_default_storage_paths(self):
        """Test default storage paths are loaded correctly"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            paths = service.storage_paths
            assert paths['root'] == 'storage'
            assert paths['uploaded'] == os.path.join('storage', 'Uploaded')
            assert paths['pending'] == os.path.join('storage', 'Pending')
            assert paths['ready_to_print'] == os.path.join('storage', 'ReadyToPrint')
            assert paths['printing'] == os.path.join('storage', 'Printing')
            assert paths['completed'] == os.path.join('storage', 'Completed')
            assert paths['rejected'] == os.path.join('storage', 'Rejected')
            assert paths['archived'] == os.path.join('storage', 'Archived')
    
    def test_custom_storage_root(self):
        """Test custom storage root from environment"""
        with patch.dict(os.environ, {'STORAGE_PATH': '/custom/storage'}):
            service = FileConfigurationService()
            paths = service.storage_paths
            assert paths['root'] == '/custom/storage'
            assert paths['uploaded'] == os.path.join('/custom/storage', 'Uploaded')
    
    def test_get_storage_path(self):
        """Test getting storage path for specific status"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            assert service.get_storage_path('UPLOADED') == os.path.join('storage', 'Uploaded')
            assert service.get_storage_path('PENDING') == os.path.join('storage', 'Pending')
            assert service.get_storage_path('READYTOPRINT') == os.path.join('storage', 'ReadyToPrint')
            assert service.get_storage_path('UNKNOWN_STATUS') == 'storage'  # fallback
    
    def test_is_allowed_extension(self):
        """Test file extension validation"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            assert service.is_allowed_extension('test.stl') is True
            assert service.is_allowed_extension('test.obj') is True
            assert service.is_allowed_extension('test.3mf') is True
            assert service.is_allowed_extension('test.txt') is False
            assert service.is_allowed_extension('test') is False
            assert service.is_allowed_extension('') is False
            assert service.is_allowed_extension(None) is False
    
    def test_get_extension_priority(self):
        """Test getting extension priority"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            assert service.get_extension_priority('test.3mf') == 0
            assert service.get_extension_priority('test.form') == 1
            assert service.get_extension_priority('test.stl') == 3
            assert service.get_extension_priority('test.obj') == 4
            assert service.get_extension_priority('test.txt') == 6  # beyond known extensions
            assert service.get_extension_priority('test') == 6
            assert service.get_extension_priority('') == 6
    
    def test_validate_file_size(self):
        """Test file size validation"""
        with patch.dict(os.environ, {'MAX_FILE_SIZE_MB': '10'}):
            service = FileConfigurationService()
            max_size = 10 * 1024 * 1024  # 10MB
            
            assert service.validate_file_size(max_size) is True
            assert service.validate_file_size(max_size - 1) is True
            assert service.validate_file_size(max_size + 1) is False
            assert service.validate_file_size(0) is True
    
    def test_get_allowed_extensions_list(self):
        """Test getting allowed extensions as list"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            extensions = service.get_allowed_extensions_list()
            assert isinstance(extensions, list)
            assert len(extensions) == 5
            assert '.stl' in extensions
            assert '.obj' in extensions
            assert '.3mf' in extensions
    
    def test_get_allowed_extensions_set(self):
        """Test getting allowed extensions as set"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            extensions = service.get_allowed_extensions_set()
            assert isinstance(extensions, set)
            assert len(extensions) == 5
            assert '.stl' in extensions
            assert '.obj' in extensions
            assert '.3mf' in extensions
    
    def test_reload_configuration(self):
        """Test reloading configuration from environment"""
        service = FileConfigurationService()
        original_extensions = service.allowed_extensions.copy()
        
        # Change environment and reload
        with patch.dict(os.environ, {'ALLOWED_FILE_EXTENSIONS': 'stl,obj'}):
            service.reload_configuration()
            new_extensions = service.allowed_extensions
            assert new_extensions == {'.stl', '.obj'}
            assert new_extensions != original_extensions
    
    def test_immutable_properties(self):
        """Test that properties return copies, not references"""
        with patch.dict(os.environ, {}, clear=True):
            service = FileConfigurationService()
            
            # Test allowed_extensions
            extensions1 = service.allowed_extensions
            extensions2 = service.allowed_extensions
            assert extensions1 is not extensions2  # Should be different objects
            
            # Test extension_priority
            priority1 = service.extension_priority
            priority2 = service.extension_priority
            assert priority1 is not priority2  # Should be different objects
            
            # Test storage_paths
            paths1 = service.storage_paths
            paths2 = service.storage_paths
            assert paths1 is not paths2  # Should be different objects


class TestFileConfigurationServiceGlobal:
    """Test cases for global file configuration service"""
    
    def test_get_file_configuration_service_singleton(self):
        """Test that get_file_configuration_service returns singleton"""
        service1 = get_file_configuration_service()
        service2 = get_file_configuration_service()
        assert service1 is service2
    
    def test_get_file_configuration_service_type(self):
        """Test that get_file_configuration_service returns correct type"""
        service = get_file_configuration_service()
        assert isinstance(service, FileConfigurationService)
