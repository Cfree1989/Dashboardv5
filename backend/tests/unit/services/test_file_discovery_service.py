"""
Tests for FileDiscoveryService

Tests the complex file discovery logic extracted from candidate_files endpoint.
"""

import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

from app.services.infrastructure.file_discovery_service import FileDiscoveryService, CandidateFileResult
from app.services.infrastructure import file_configuration_service


class TestCandidateFileResult:
    def test_to_dict(self):
        """Test CandidateFileResult.to_dict() returns proper structure"""
        result = CandidateFileResult(
            files=['test1.stl', 'test2.3mf'],
            files_detailed=[
                {'name': 'test1.stl', 'mtime': 1234567890},
                {'name': 'test2.3mf', 'mtime': 1234567891}
            ],
            recommended='test2.3mf'
        )
        
        expected = {
            'files': ['test1.stl', 'test2.3mf'],
            'files_detailed': [
                {'name': 'test1.stl', 'mtime': 1234567890},
                {'name': 'test2.3mf', 'mtime': 1234567891}
            ],
            'recommended': 'test2.3mf'
        }
        
        assert result.to_dict() == expected


class TestFileDiscoveryService:
    def setup_method(self):
        self.service = FileDiscoveryService()
        
        # Create mock job for testing
        self.mock_job = Mock()
        self.mock_job.id = 'test-job-123'
        self.mock_job.short_id = 'TJ123'
        self.mock_job.display_name = 'test_model.stl'
        self.mock_job.original_filename = 'original.stl'
        self.mock_job.file_path = '/storage/test/test_model.stl'

    def test_load_allowed_extensions_default(self):
        """Test loading default allowed extensions"""
        with patch.dict(os.environ, {}, clear=True):
            # Reset the global singleton to pick up new environment variables
            file_configuration_service._file_config_service = None
            service = FileDiscoveryService()
            expected = {'.stl', '.obj', '.3mf', '.form', '.idea'}
            assert service.allowed_extensions == expected

    def test_load_allowed_extensions_custom(self):
        """Test loading custom allowed extensions from environment"""
        with patch.dict(os.environ, {'ALLOWED_FILE_EXTENSIONS': 'stl,gcode,step'}, clear=True):
            # Reset the global singleton to pick up new environment variables
            file_configuration_service._file_config_service = None
            service = FileDiscoveryService()
            expected = {'.stl', '.gcode', '.step'}
            assert service.allowed_extensions == expected

    def test_load_extension_priority_default(self):
        """Test loading default extension priority"""
        with patch.dict(os.environ, {}, clear=True):
            # Reset the global singleton to pick up new environment variables
            file_configuration_service._file_config_service = None
            service = FileDiscoveryService()
            expected = {'.3mf': 0, '.form': 1, '.idea': 2, '.stl': 3, '.obj': 4}
            assert service.extension_priority == expected

    def test_load_extension_priority_custom(self):
        """Test loading custom extension priority from environment"""
        with patch.dict(os.environ, {'FILE_EXTENSION_PRIORITY': 'stl,3mf,obj'}, clear=True):
            # Reset the global singleton to pick up new environment variables
            file_configuration_service._file_config_service = None
            service = FileDiscoveryService()
            expected = {'.stl': 0, '.3mf': 1, '.obj': 2}
            assert service.extension_priority == expected

    def test_build_relevance_tokens(self):
        """Test building relevance tokens from job data"""
        tokens = self.service._build_relevance_tokens(self.mock_job)
        
        expected_tokens = {
            'tj123',          # from short_id
            'test-job',       # first 8 chars of id
            'test_model'      # stem of display_name
        }
        
        assert tokens == expected_tokens

    def test_build_relevance_tokens_with_missing_fields(self):
        """Test building relevance tokens when job has missing fields"""
        mock_job = Mock()
        mock_job.short_id = None
        mock_job.id = 'test-123'
        mock_job.display_name = None
        
        tokens = self.service._build_relevance_tokens(mock_job)
        expected_tokens = {'test-123'}  # Only id available
        assert tokens == expected_tokens

    def test_get_file_rank(self):
        """Test getting file extension priority rank"""
        # Reset singleton to ensure clean state
        file_configuration_service._file_config_service = None
        service = FileDiscoveryService()
        assert service._get_file_rank('test.3mf') == 0    # Highest priority
        assert service._get_file_rank('test.stl') == 3    # Lower priority
        assert service._get_file_rank('test.unknown') > 4  # Unknown extension

    def test_is_file_related_to_job_token_match(self):
        """Test file relatedness based on token matching"""
        tokens = {'tj123', 'test_model'}
        
        # Should match files containing tokens
        assert self.service._is_file_related_to_job('TJ123_final.stl', tokens, self.mock_job)
        assert self.service._is_file_related_to_job('test_model_v2.3mf', tokens, self.mock_job)
        
        # Should not match unrelated files
        assert not self.service._is_file_related_to_job('other_file.stl', tokens, self.mock_job)

    def test_is_file_related_to_job_original_filename(self):
        """Test file relatedness for original filename"""
        tokens = set()  # No tokens
        
        # Should always match original filename
        assert self.service._is_file_related_to_job('original.stl', tokens, self.mock_job)
        
        # Should not match other files when no tokens
        assert not self.service._is_file_related_to_job('other.stl', tokens, self.mock_job)

    def test_ensure_original_filename_included(self):
        """Test ensuring original filename is included in candidates"""
        candidates = [{'name': 'test.stl', 'mtime': 123}]
        
        # Should add original filename if not present
        result = self.service._ensure_original_filename_included(candidates, self.mock_job)
        assert len(result) == 2
        assert any(c['name'] == 'original.stl' for c in result)

    def test_ensure_original_filename_included_already_present(self):
        """Test original filename not duplicated if already present"""
        candidates = [
            {'name': 'original.stl', 'mtime': 123},
            {'name': 'test.stl', 'mtime': 124}
        ]
        
        result = self.service._ensure_original_filename_included(candidates, self.mock_job)
        assert len(result) == 2  # Should not add duplicate

    def test_sort_candidates_by_priority(self):
        """Test sorting candidates by priority, then mtime, then name"""
        # Reset singleton to ensure clean state
        file_configuration_service._file_config_service = None
        service = FileDiscoveryService()
        
        candidates = [
            {'name': 'old.stl', 'mtime': 100},      # .stl priority 3, old
            {'name': 'new.3mf', 'mtime': 200},      # .3mf priority 0, new
            {'name': 'medium.stl', 'mtime': 150},   # .stl priority 3, medium
        ]

        sorted_candidates = service._sort_candidates_by_priority(candidates)

        # Should be sorted by priority first (.3mf before .stl), then mtime desc
        expected_names = ['new.3mf', 'medium.stl', 'old.stl']
        actual_names = [c['name'] for c in sorted_candidates]
        assert actual_names == expected_names

    def test_discover_candidate_files_success(self):
        """Test successful file discovery"""
        # Reset singleton to ensure clean state
        file_configuration_service._file_config_service = None
        service = FileDiscoveryService()
        
        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / 'TJ123_model.stl').touch()
            (temp_path / 'TJ123_model.3mf').touch()
            (temp_path / 'unrelated.stl').touch()  # Should be filtered out

            # Update mock job file path
            self.mock_job.file_path = str(temp_path / 'TJ123_model.stl')

            result = service.discover_candidate_files(self.mock_job)

            # Should find related files plus original filename
            assert len(result.files) == 3  # 2 related files + original
            assert 'TJ123_model.stl' in result.files
            assert 'TJ123_model.3mf' in result.files
            assert 'original.stl' in result.files
    
            # Should recommend highest priority file (.3mf)
            assert result.recommended == 'TJ123_model.3mf'

    def test_discover_candidate_files_error_fallback(self):
        """Test fallback behavior when discovery fails"""
        # Mock job with invalid file path to trigger exception
        self.mock_job.file_path = '/nonexistent/path/test.stl'
        
        result = self.service.discover_candidate_files(self.mock_job)
        
        # Should return fallback with original filename
        assert result.files == ['original.stl']
        assert result.files_detailed == [{'name': 'original.stl', 'mtime': 0}]
        assert result.recommended == 'original.stl'

    def test_discover_candidate_files_no_original_filename(self):
        """Test fallback behavior when no original filename and error occurs"""
        # Mock job with no original filename and invalid path
        self.mock_job.original_filename = None
        self.mock_job.file_path = '/nonexistent/path/test.stl'
        
        result = self.service.discover_candidate_files(self.mock_job)
        
        # Should return empty fallback
        assert result.files == []
        assert result.files_detailed == []
        assert result.recommended is None

    def test_scan_directory_nonexistent(self):
        """Test scanning nonexistent directory returns empty list"""
        nonexistent_dir = Path('/nonexistent/directory')
        tokens = {'test'}
        
        candidates = self.service._scan_directory_for_candidates(nonexistent_dir, tokens, self.mock_job)
        assert candidates == []

    def test_scan_directory_filters_by_extension(self):
        """Test directory scanning filters by allowed extensions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with different extensions
            (temp_path / 'TJ123.stl').touch()      # Allowed
            (temp_path / 'TJ123.txt').touch()      # Not allowed
            (temp_path / 'TJ123.3mf').touch()      # Allowed
            
            tokens = {'tj123'}
            candidates = self.service._scan_directory_for_candidates(temp_path, tokens, self.mock_job)
            
            # Should only include allowed extensions
            candidate_names = [c['name'] for c in candidates]
            assert 'TJ123.stl' in candidate_names
            assert 'TJ123.3mf' in candidate_names
            assert 'TJ123.txt' not in candidate_names
