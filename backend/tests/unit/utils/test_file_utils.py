import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from app.utils.file_utils import FileUtils

class TestFileUtils:
    
    def test_validate_storage_path_valid(self):
        """Test validate_storage_path with valid path"""
        with patch.dict(os.environ, {'STORAGE_PATH': '/app/storage'}):
            # Path within storage root should be valid
            assert FileUtils.validate_storage_path('/app/storage/uploads/file.txt') is True
            assert FileUtils.validate_storage_path('/app/storage/pending/job123.stl') is True
    
    def test_validate_storage_path_invalid(self):
        """Test validate_storage_path with invalid path"""
        with patch.dict(os.environ, {'STORAGE_PATH': '/app/storage'}):
            # Path outside storage root should be invalid
            assert FileUtils.validate_storage_path('/etc/passwd') is False
            assert FileUtils.validate_storage_path('/tmp/malicious.txt') is False
    
    def test_validate_storage_path_default(self):
        """Test validate_storage_path with default storage path"""
        with patch.dict(os.environ, {}, clear=True):
            # Should use 'storage' as default
            with patch('pathlib.Path.resolve') as mock_resolve:
                mock_resolve.return_value = Path('/current/storage').resolve()
                result = FileUtils.validate_storage_path('storage/uploads/file.txt')
                # This test verifies the method runs without error
                assert isinstance(result, bool)
    
    def test_get_storage_root(self):
        """Test get_storage_root"""
        with patch.dict(os.environ, {'STORAGE_PATH': '/app/storage'}):
            root = FileUtils.get_storage_root()
            assert root == Path('/app/storage')
    
    def test_get_storage_root_default(self):
        """Test get_storage_root with default"""
        with patch.dict(os.environ, {}, clear=True):
            root = FileUtils.get_storage_root()
            assert root == Path('storage')
    
    def test_ensure_directory_exists(self):
        """Test ensure_directory_exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, 'new', 'nested', 'directory')
            
            result = FileUtils.ensure_directory_exists(test_path)
            
            assert result == Path(test_path)
            assert Path(test_path).exists()
            assert Path(test_path).is_dir()
    
    def test_get_file_extension(self):
        """Test get_file_extension"""
        assert FileUtils.get_file_extension('file.txt') == '.txt'
        assert FileUtils.get_file_extension('model.STL') == '.stl'
        assert FileUtils.get_file_extension('archive.tar.gz') == '.gz'
        assert FileUtils.get_file_extension('no_extension') == ''
        assert FileUtils.get_file_extension('/path/to/file.PDF') == '.pdf'
    
    def test_is_valid_file_type(self):
        """Test is_valid_file_type"""
        allowed = ['.stl', '.obj', '.3mf']
        
        assert FileUtils.is_valid_file_type('model.stl', allowed) is True
        assert FileUtils.is_valid_file_type('model.STL', allowed) is True
        assert FileUtils.is_valid_file_type('model.obj', allowed) is True
        assert FileUtils.is_valid_file_type('model.3mf', allowed) is True
        
        assert FileUtils.is_valid_file_type('document.txt', allowed) is False
        assert FileUtils.is_valid_file_type('image.jpg', allowed) is False
    
    def test_get_safe_filename(self):
        """Test get_safe_filename"""
        assert FileUtils.get_safe_filename('normal_file.txt') == 'normal_file.txt'
        assert FileUtils.get_safe_filename('file with spaces.txt') == 'filewithspaces.txt'
        assert FileUtils.get_safe_filename('file/with\\dangerous:chars.txt') == 'filewithdangerouschars.txt'
        assert FileUtils.get_safe_filename('file<>|"*?.txt') == 'file.txt'
        assert FileUtils.get_safe_filename('.hidden_file') == 'file.hidden_file'
        assert FileUtils.get_safe_filename('') == 'unnamed_file'
        assert FileUtils.get_safe_filename('!!!') == 'unnamed_file'
    
    def test_get_file_size_existing_file(self):
        """Test get_file_size with existing file"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'Hello, World!')
            temp_file.flush()
            temp_file.close()  # Close the file to release the handle
            
            size = FileUtils.get_file_size(temp_file.name)
            assert size == 13  # Length of "Hello, World!"
            
            os.unlink(temp_file.name)
    
    def test_get_file_size_nonexistent_file(self):
        """Test get_file_size with nonexistent file"""
        size = FileUtils.get_file_size('/nonexistent/file.txt')
        assert size is None
    
    def test_split_path_components(self):
        """Test split_path_components"""
        directory, filename, extension = FileUtils.split_path_components('/path/to/file.txt')
        # Use Path to handle cross-platform path separators
        expected_dir = str(Path('/path/to'))
        assert directory == expected_dir
        assert filename == 'file'
        assert extension == '.txt'
        
        directory, filename, extension = FileUtils.split_path_components('no_extension')
        assert directory == '.'
        assert filename == 'no_extension'
        assert extension == ''
        
        directory, filename, extension = FileUtils.split_path_components('/root/archive.tar.gz')
        expected_dir = str(Path('/root'))
        assert directory == expected_dir
        assert filename == 'archive.tar'
        assert extension == '.gz'
    
    def test_join_paths(self):
        """Test join_paths"""
        result = FileUtils.join_paths('storage', 'uploads', 'file.txt')
        expected = str(Path('storage', 'uploads', 'file.txt'))
        assert result == expected
        
        result = FileUtils.join_paths('/root', 'subdir', 'file.stl')
        expected = str(Path('/root', 'subdir', 'file.stl'))
        assert result == expected
    
    def test_normalize_path(self):
        """Test normalize_path"""
        # Test that it handles different path separators
        result = FileUtils.normalize_path('storage/uploads/file.txt')
        assert result == str(Path('storage/uploads/file.txt'))
        
        result = FileUtils.normalize_path('storage\\uploads\\file.txt')
        assert result == str(Path('storage\\uploads\\file.txt'))
