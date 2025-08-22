"""
Test suite for FileConfigurationService

Tests file configuration, validation, and security features.
"""

import pytest
import os
import tempfile
from unittest.mock import patch
from app.services.infrastructure.file_configuration_service import FileConfigurationService, get_file_configuration_service


class TestFileConfigurationService:
    """Test cases for FileConfigurationService"""
    
    def setup_method(self):
        """Set up test environment"""
        # Reset global instance for each test
        import app.services.infrastructure.file_configuration_service as module
        module._file_config_service = None
        
        # Create fresh service instance
        self.service = FileConfigurationService()
    
    def test_allowed_extensions_loading(self):
        """Test loading allowed extensions from environment"""
        with patch.dict(os.environ, {'ALLOWED_FILE_EXTENSIONS': 'stl,obj,3mf'}):
            service = FileConfigurationService()
            assert '.stl' in service.allowed_extensions
            assert '.obj' in service.allowed_extensions
            assert '.3mf' in service.allowed_extensions
    
    def test_extension_priority_loading(self):
        """Test loading extension priority from environment"""
        with patch.dict(os.environ, {'FILE_EXTENSION_PRIORITY': '3mf,stl,obj'}):
            service = FileConfigurationService()
            assert service.extension_priority['.3mf'] == 0
            assert service.extension_priority['.stl'] == 1
            assert service.extension_priority['.obj'] == 2
    
    def test_max_file_size_loading(self):
        """Test loading maximum file size from environment"""
        with patch.dict(os.environ, {'MAX_FILE_SIZE_MB': '100'}):
            service = FileConfigurationService()
            assert service.max_file_size == 100 * 1024 * 1024
            assert service.max_file_size_mb == 100
    
    def test_min_file_size_loading(self):
        """Test loading minimum file size from environment"""
        with patch.dict(os.environ, {'MIN_FILE_SIZE_KB': '5'}):
            service = FileConfigurationService()
            assert service.min_file_size == 5 * 1024
            assert service.min_file_size_kb == 5
    
    def test_is_allowed_extension(self):
        """Test file extension validation"""
        assert self.service.is_allowed_extension('test.stl')
        assert self.service.is_allowed_extension('test.obj')
        assert self.service.is_allowed_extension('test.3mf')
        assert not self.service.is_allowed_extension('test.txt')
        assert not self.service.is_allowed_extension('test')
        assert not self.service.is_allowed_extension('')
    
    def test_get_extension_priority(self):
        """Test extension priority ranking"""
        # Test known extensions
        assert self.service.get_extension_priority('test.3mf') == 0
        assert self.service.get_extension_priority('test.form') == 1
        assert self.service.get_extension_priority('test.idea') == 2
        
        # Test unknown extensions
        assert self.service.get_extension_priority('test.unknown') > 5
        assert self.service.get_extension_priority('test') > 5
        assert self.service.get_extension_priority('') > 5
    
    def test_validate_file_size(self):
        """Test file size validation"""
        # Test valid sizes
        assert self.service.validate_file_size(1024)  # 1KB
        assert self.service.validate_file_size(50 * 1024 * 1024)  # 50MB
        
        # Test invalid sizes
        assert not self.service.validate_file_size(512)  # Too small
        assert not self.service.validate_file_size(100 * 1024 * 1024)  # Too large
    
    def test_get_file_size_validation_error(self):
        """Test file size validation error messages"""
        # Test valid size
        assert self.service.get_file_size_validation_error(1024) is None
        
        # Test too small
        error = self.service.get_file_size_validation_error(512)
        assert "too small" in error
        assert "1KB" in error
        
        # Test too large
        error = self.service.get_file_size_validation_error(100 * 1024 * 1024)
        assert "too large" in error
        assert "50MB" in error
    
    def test_validate_stl_header_ascii(self):
        """Test STL header validation for ASCII format"""
        # Valid ASCII STL
        ascii_stl = b"""solid test
facet normal 0 0 1
    outer loop
        vertex 0 0 0
        vertex 1 0 0
        vertex 0 1 0
    endloop
endfacet
endsolid test"""
        is_valid, error = self.service.validate_file_header(ascii_stl, 'test.stl')
        assert is_valid
        assert error is None
    
    def test_validate_stl_header_binary(self):
        """Test STL header validation for binary format"""
        # Create binary STL header (80 bytes) + triangle count (4 bytes)
        header = b'Binary STL file header' + b'\x00' * 60  # 80 bytes
        triangle_count = b'\x01\x00\x00\x00'  # 1 triangle, little endian
        binary_stl = header + triangle_count + b'\x00' * 50  # Add some data
        
        is_valid, error = self.service.validate_file_header(binary_stl, 'test.stl')
        assert is_valid
        assert error is None
    
    def test_validate_stl_header_invalid(self):
        """Test STL header validation for invalid files"""
        # Invalid content
        invalid_content = b'This is not an STL file'
        is_valid, error = self.service.validate_file_header(invalid_content, 'test.stl')
        assert not is_valid
        assert "Invalid STL file format" in error
    
    def test_validate_obj_header(self):
        """Test OBJ header validation"""
        # Valid OBJ file
        obj_content = b"""# OBJ file
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
f 1 2 3"""
        is_valid, error = self.service.validate_file_header(obj_content, 'test.obj')
        assert is_valid
        assert error is None
    
    def test_validate_obj_header_invalid(self):
        """Test OBJ header validation for invalid files"""
        # Invalid content
        invalid_content = b'This is not an OBJ file'
        is_valid, error = self.service.validate_file_header(invalid_content, 'test.obj')
        assert not is_valid
        assert "Invalid OBJ file format" in error
    
    def test_validate_3mf_header(self):
        """Test 3MF header validation"""
        # Valid 3MF file (ZIP with 3MF content)
        zip_header = b'PK\x03\x04'  # ZIP signature
        content = zip_header + b'[Content_Types].xml' + b'\x00' * 100
        is_valid, error = self.service.validate_file_header(content, 'test.3mf')
        assert is_valid
        assert error is None
    
    def test_validate_3mf_header_invalid(self):
        """Test 3MF header validation for invalid files"""
        # Invalid content
        invalid_content = b'This is not a 3MF file'
        is_valid, error = self.service.validate_file_header(invalid_content, 'test.3mf')
        assert not is_valid
        assert "Invalid 3MF file format" in error
    
    def test_validate_zip_based_header(self):
        """Test ZIP-based header validation for Form/Idea files"""
        # Valid ZIP file
        zip_content = b'PK\x03\x04' + b'\x00' * 100
        is_valid, error = self.service.validate_file_header(zip_content, 'test.form')
        assert is_valid
        assert error is None
        
        is_valid, error = self.service.validate_file_header(zip_content, 'test.idea')
        assert is_valid
        assert error is None
    
    def test_validate_generic_header(self):
        """Test generic header validation"""
        # Valid generic file
        content = b'Some file content that is not empty'
        is_valid, error = self.service.validate_file_header(content, 'test.unknown')
        assert is_valid
        assert error is None
    
    def test_validate_generic_header_executable(self):
        """Test generic header validation for executable files"""
        # Windows executable
        exe_content = b'MZ' + b'\x00' * 100
        is_valid, error = self.service.validate_file_header(exe_content, 'test.unknown')
        assert not is_valid
        assert "executable" in error
        
        # Linux executable
        elf_content = b'\x7fELF' + b'\x00' * 100
        is_valid, error = self.service.validate_file_header(elf_content, 'test.unknown')
        assert not is_valid
        assert "executable" in error
    
    def test_validate_file_header_empty(self):
        """Test file header validation for empty files"""
        is_valid, error = self.service.validate_file_header(b'', 'test.stl')
        assert not is_valid
        assert "File is empty" in error
    
    def test_validate_file_header_too_small(self):
        """Test file header validation for very small files"""
        is_valid, error = self.service.validate_file_header(b'123', 'test.stl')
        assert not is_valid
        assert "too small for header validation" in error
    
    def test_validate_file_header_no_extension(self):
        """Test file header validation for files without extension"""
        is_valid, error = self.service.validate_file_header(b'some content', 'test')
        assert not is_valid
        assert "No file extension found" in error or "too small for header validation" in error
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test normal filename
        assert self.service.sanitize_filename('test.stl') == 'test.stl'
        
        # Test dangerous characters
        assert self.service.sanitize_filename('test/file.stl') == 'test_file.stl'
        assert self.service.sanitize_filename('test\\file.stl') == 'test_file.stl'
        assert self.service.sanitize_filename('test:file.stl') == 'test_file.stl'
        assert self.service.sanitize_filename('test*file.stl') == 'test_file.stl'
        
        # Test leading/trailing dots and spaces
        assert self.service.sanitize_filename('.test.stl.') == 'test.stl'
        assert self.service.sanitize_filename(' test.stl ') == 'test.stl'
        
        # Test empty filename
        assert self.service.sanitize_filename('') == 'unnamed_file'
        assert self.service.sanitize_filename(None) == 'unnamed_file'
    
    def test_validate_filename_security(self):
        """Test filename security validation"""
        # Test valid filename
        is_valid, error = self.service.validate_filename_security('test.stl')
        assert is_valid
        assert error is None
        
        # Test path traversal attempts
        is_valid, error = self.service.validate_filename_security('../test.stl')
        assert not is_valid
        assert "Path traversal attempt detected" in error
        
        is_valid, error = self.service.validate_filename_security('/etc/passwd')
        assert not is_valid
        assert "Path traversal attempt detected" in error
        
        # Test dangerous characters
        is_valid, error = self.service.validate_filename_security('test*.stl')
        assert not is_valid
        assert "Dangerous character" in error
        
        # Test reserved names (Windows)
        is_valid, error = self.service.validate_filename_security('CON.stl')
        assert not is_valid
        assert "Reserved filename" in error
        
        # Test empty filename
        is_valid, error = self.service.validate_filename_security('')
        assert not is_valid
        assert "No filename provided" in error
    
    def test_get_file_extension(self):
        """Test file extension extraction"""
        assert self.service._get_file_extension('test.stl') == '.stl'
        assert self.service._get_file_extension('test.obj') == '.obj'
        assert self.service._get_file_extension('test.3mf') == '.3mf'
        assert self.service._get_file_extension('test') is None
        assert self.service._get_file_extension('') is None
        assert self.service._get_file_extension(None) is None
    
    def test_reload_configuration(self):
        """Test configuration reloading"""
        # Change environment and reload
        with patch.dict(os.environ, {'ALLOWED_FILE_EXTENSIONS': 'stl,obj'}):
            self.service.reload_configuration()
            assert '.stl' in self.service.allowed_extensions
            assert '.obj' in self.service.allowed_extensions
            assert '.3mf' not in self.service.allowed_extensions


class TestFileConfigurationServiceGlobal:
    """Test cases for global file configuration service instance"""
    
    def test_get_file_configuration_service_singleton(self):
        """Test that global service is a singleton"""
        service1 = get_file_configuration_service()
        service2 = get_file_configuration_service()
        assert service1 is service2
    
    def test_get_file_configuration_service_reset(self):
        """Test that global service can be reset"""
        # Reset global instance
        import app.services.infrastructure.file_configuration_service as module
        module._file_config_service = None
        
        service = get_file_configuration_service()
        assert service is not None
        assert isinstance(service, FileConfigurationService)
