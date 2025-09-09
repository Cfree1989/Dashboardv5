"""
Tests for the error handling service.

This test suite covers:
- Error logging and classification
- Error severity assessment
- Recovery suggestions
- Error aggregation and reporting
- File operation error handling
- Metadata operation error handling
"""

import pytest
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone

from app.services.error_handling_service import (
    ErrorHandlingService,
    ErrorSeverity,
    ErrorCategory,
    FileOperationError,
    MetadataSyncError,
    get_error_handling_service
)


class TestErrorHandlingService:
    """Test cases for the ErrorHandlingService class."""
    
    @pytest.fixture
    def error_service(self):
        """Create a fresh error handling service for each test."""
        return ErrorHandlingService()
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger for testing."""
        with patch('app.services.error_handling_service.logger') as mock_logger:
            yield mock_logger
    
    def test_init(self, error_service):
        """Test service initialization."""
        assert error_service.error_counts == {}
        assert error_service.recent_errors == []
        assert error_service.max_recent_errors == 100
    
    def test_log_file_operation_error(self, error_service, mock_logger):
        """Test logging file operation errors."""
        error = FileNotFoundError("File not found")
        
        error_service.log_file_operation_error(
            operation="copy_file",
            error=error,
            file_path="/path/to/file.txt",
            job_id="123",
            context={"source": "/source/path"}
        )
        
        # Check that error was logged
        assert len(error_service.recent_errors) == 1
        error_info = error_service.recent_errors[0]
        assert error_info['operation'] == "copy_file"
        assert error_info['error_type'] == "FileNotFoundError"
        assert error_info['error_message'] == "File not found"
        assert error_info['file_path'] == "/path/to/file.txt"
        assert error_info['job_id'] == "123"
        assert error_info['context'] == {"source": "/source/path"}
        assert error_info['category'] == ErrorCategory.FILE_OPERATION.value
        
        # Check that error count was updated
        assert "file_operation:FileNotFoundError" in error_service.error_counts
        assert error_service.error_counts["file_operation:FileNotFoundError"] == 1
        
        # Check that logger was called
        mock_logger.error.assert_called()
    
    def test_log_metadata_sync_error(self, error_service, mock_logger):
        """Test logging metadata sync errors."""
        error = json.JSONDecodeError("Invalid JSON", "{}", 0)
        
        error_service.log_metadata_sync_error(
            error=error,
            job_id="123",
            metadata_path="/path/to/metadata.json",
            context={"operation": "load_metadata"}
        )
        
        # Check that error was logged
        assert len(error_service.recent_errors) == 1
        error_info = error_service.recent_errors[0]
        assert error_info['operation'] == "metadata_sync"
        assert error_info['error_type'] == "JSONDecodeError"
        assert error_info['job_id'] == "123"
        assert error_info['metadata_path'] == "/path/to/metadata.json"
        assert error_info['category'] == ErrorCategory.METADATA_SYNC.value
        
        # Check that error count was updated
        assert "metadata_sync:JSONDecodeError" in error_service.error_counts
        assert error_service.error_counts["metadata_sync:JSONDecodeError"] == 1
        
        # Check that logger was called
        mock_logger.error.assert_called()
    
    def test_handle_file_operation_with_error_handling_success(self, error_service):
        """Test successful file operation handling."""
        def successful_operation():
            return "success"
        
        success, error_msg = error_service.handle_file_operation_with_error_handling(
            operation="test_operation",
            file_path="/path/to/file.txt",
            operation_func=successful_operation
        )
        
        assert success is True
        assert error_msg is None
        assert len(error_service.recent_errors) == 0
    
    def test_handle_file_operation_with_error_handling_failure(self, error_service, mock_logger):
        """Test file operation handling with failure."""
        def failing_operation():
            raise PermissionError("Permission denied")
        
        success, error_msg = error_service.handle_file_operation_with_error_handling(
            operation="test_operation",
            file_path="/path/to/file.txt",
            operation_func=failing_operation
        )
        
        assert success is False
        assert "Permission denied" in error_msg
        assert len(error_service.recent_errors) == 1
        
        # Check that error was logged
        mock_logger.error.assert_called()
    
    def test_handle_metadata_operation_with_error_handling_success(self, error_service):
        """Test successful metadata operation handling."""
        def successful_operation():
            return "success"
        
        success, error_msg = error_service.handle_metadata_operation_with_error_handling(
            job_id="123",
            metadata_path="/path/to/metadata.json",
            operation_func=successful_operation
        )
        
        assert success is True
        assert error_msg is None
        assert len(error_service.recent_errors) == 0
    
    def test_handle_metadata_operation_with_error_handling_failure(self, error_service, mock_logger):
        """Test metadata operation handling with failure."""
        def failing_operation():
            raise OSError("No space left on device")
        
        success, error_msg = error_service.handle_metadata_operation_with_error_handling(
            job_id="123",
            metadata_path="/path/to/metadata.json",
            operation_func=failing_operation
        )
        
        assert success is False
        assert "No space left on device" in error_msg
        assert len(error_service.recent_errors) == 1
        
        # Check that error was logged
        mock_logger.error.assert_called()
    
    def test_get_error_summary(self, error_service):
        """Test error summary generation."""
        # Add some test errors
        error_service.log_file_operation_error(
            operation="test1",
            error=FileNotFoundError("File not found"),
            file_path="/path1"
        )
        error_service.log_file_operation_error(
            operation="test2",
            error=PermissionError("Permission denied"),
            file_path="/path2"
        )
        error_service.log_metadata_sync_error(
            error=json.JSONDecodeError("Invalid JSON", "{}", 0),
            job_id="123"
        )
        
        summary = error_service.get_error_summary()
        
        assert summary['total_errors'] == 3
        assert summary['error_counts']['file_operation:FileNotFoundError'] == 1
        assert summary['error_counts']['file_operation:PermissionError'] == 1
        assert summary['error_counts']['metadata_sync:JSONDecodeError'] == 1
        assert len(summary['recent_errors']) == 3
        assert summary['critical_errors'] == 1  # JSONDecodeError is CRITICAL severity
        assert summary['high_errors'] == 1  # PermissionError is HIGH severity
    
    def test_get_recovery_suggestions_file_operation(self, error_service):
        """Test recovery suggestions for file operation errors."""
        error_info = {
            'category': ErrorCategory.FILE_OPERATION.value,
            'error_message': 'Permission denied'
        }
        
        suggestions = error_service.get_recovery_suggestions(error_info)
        
        assert "Check file and directory permissions" in suggestions
        assert "Verify user has write access to the directory" in suggestions
        assert "Check if file is locked by another process" in suggestions
        assert "Check system logs for additional context" in suggestions
    
    def test_get_recovery_suggestions_metadata_sync(self, error_service):
        """Test recovery suggestions for metadata sync errors."""
        error_info = {
            'category': ErrorCategory.METADATA_SYNC.value,
            'error_message': 'Invalid JSON'
        }
        
        suggestions = error_service.get_recovery_suggestions(error_info)
        
        assert "Verify metadata file exists and is readable" in suggestions
        assert "Check JSON format validity" in suggestions
        assert "Run metadata integrity check" in suggestions
        assert "Consider regenerating metadata from job data" in suggestions
    
    def test_assess_file_error_severity(self, error_service):
        """Test file error severity assessment."""
        # Critical errors
        disk_full_error = OSError("Disk full")
        severity = error_service._assess_file_error_severity(disk_full_error, "copy_file")
        assert severity == ErrorSeverity.CRITICAL
        
        # High severity errors
        permission_error = PermissionError("Permission denied")
        severity = error_service._assess_file_error_severity(permission_error, "copy_file")
        assert severity == ErrorSeverity.HIGH
        
        # Medium severity errors
        not_found_error = FileNotFoundError("No such file or directory")
        severity = error_service._assess_file_error_severity(not_found_error, "copy_file")
        assert severity == ErrorSeverity.MEDIUM
        
        # Low severity errors
        generic_error = ValueError("Generic error")
        severity = error_service._assess_file_error_severity(generic_error, "copy_file")
        assert severity == ErrorSeverity.LOW
    
    def test_assess_metadata_error_severity(self, error_service):
        """Test metadata error severity assessment."""
        # Critical errors
        corruption_error = json.JSONDecodeError("Invalid JSON", "{}", 0)
        severity = error_service._assess_metadata_error_severity(corruption_error)
        assert severity == ErrorSeverity.CRITICAL
        
        # High severity errors
        permission_error = PermissionError("Permission denied")
        severity = error_service._assess_metadata_error_severity(permission_error)
        assert severity == ErrorSeverity.HIGH
        
        # Medium severity errors
        not_found_error = FileNotFoundError("No such file or directory")
        severity = error_service._assess_metadata_error_severity(not_found_error)
        assert severity == ErrorSeverity.MEDIUM
        
        # Low severity errors
        generic_error = ValueError("Generic error")
        severity = error_service._assess_metadata_error_severity(generic_error)
        assert severity == ErrorSeverity.LOW
    
    def test_recent_errors_limit(self, error_service):
        """Test that recent errors are limited to max_recent_errors."""
        error_service.max_recent_errors = 3
        
        # Add more errors than the limit
        for i in range(5):
            error_service.log_file_operation_error(
                operation=f"test_{i}",
                error=ValueError(f"Error {i}"),
                file_path=f"/path/{i}"
            )
        
        # Should only keep the most recent 3
        assert len(error_service.recent_errors) == 3
        assert error_service.recent_errors[0]['operation'] == "test_2"
        assert error_service.recent_errors[1]['operation'] == "test_3"
        assert error_service.recent_errors[2]['operation'] == "test_4"
    
    def test_format_error_message(self, error_service):
        """Test error message formatting."""
        error_info = {
            'operation': 'copy_file',
            'file_path': '/path/to/file.txt',
            'error_message': 'Permission denied',
            'job_id': '123'
        }
        
        message = error_service._format_error_message(error_info)
        expected = "copy_file failed for /path/to/file.txt: Permission denied (Job: 123)"
        assert message == expected
    
    def test_format_error_message_metadata(self, error_service):
        """Test error message formatting for metadata errors."""
        error_info = {
            'operation': 'metadata_sync',
            'metadata_path': '/path/to/metadata.json',
            'error_message': 'Invalid JSON',
            'job_id': '123'
        }
        
        message = error_service._format_error_message(error_info)
        expected = "metadata_sync failed for /path/to/metadata.json: Invalid JSON (Job: 123)"
        assert message == expected


class TestCustomExceptions:
    """Test cases for custom exception classes."""
    
    def test_file_operation_error(self):
        """Test FileOperationError creation and attributes."""
        error = FileOperationError(
            message="Test error",
            operation="copy_file",
            file_path="/path/to/file.txt",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.FILE_OPERATION,
            context={"source": "/source/path"}
        )
        
        assert str(error) == "Test error"
        assert error.operation == "copy_file"
        assert error.file_path == "/path/to/file.txt"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.FILE_OPERATION
        assert error.context == {"source": "/source/path"}
        assert isinstance(error.timestamp, datetime)
        assert error.traceback is not None
    
    def test_metadata_sync_error(self):
        """Test MetadataSyncError creation and attributes."""
        error = MetadataSyncError(
            message="Test metadata error",
            job_id="123",
            metadata_path="/path/to/metadata.json",
            context={"operation": "load_metadata"}
        )
        
        assert str(error) == "Test metadata error"
        assert error.job_id == "123"
        assert error.metadata_path == "/path/to/metadata.json"
        assert error.context == {"operation": "load_metadata"}
        assert isinstance(error.timestamp, datetime)
        assert error.traceback is not None


class TestGlobalService:
    """Test cases for the global error handling service."""
    
    def test_get_error_handling_service_singleton(self):
        """Test that get_error_handling_service returns a singleton."""
        service1 = get_error_handling_service()
        service2 = get_error_handling_service()
        
        assert service1 is service2
        assert isinstance(service1, ErrorHandlingService)
    
    def test_global_service_functionality(self):
        """Test that the global service works correctly."""
        service = get_error_handling_service()
        
        # Clear any existing errors
        service.recent_errors.clear()
        service.error_counts.clear()
        
        # Test logging an error
        service.log_file_operation_error(
            operation="test_operation",
            error=FileNotFoundError("File not found"),
            file_path="/path/to/file.txt"
        )
        
        assert len(service.recent_errors) == 1
        assert service.recent_errors[0]['operation'] == "test_operation"


class TestErrorHandlingIntegration:
    """Integration tests for error handling with real file operations."""
    
    @pytest.fixture
    def error_service(self):
        """Create a fresh error handling service for each test."""
        return ErrorHandlingService()
    
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file for testing."""
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("test content")
        return file_path
    
    def test_file_operation_with_real_error(self, error_service, temp_file):
        """Test error handling with a real file operation error."""
        # Try to copy to a non-existent directory
        non_existent_dir = temp_file.parent / "non_existent" / "file.txt"
        
        import shutil
        success, error_msg = error_service.handle_file_operation_with_error_handling(
            operation="copy_file",
            file_path=str(temp_file),
            operation_func=lambda: shutil.copy2(temp_file, non_existent_dir)
        )
        
        assert success is False
        assert ("No such file or directory" in error_msg or 
                "Parent directory" in error_msg or 
                "The system cannot find the path specified" in error_msg)
        assert len(error_service.recent_errors) == 1
    
    def test_metadata_operation_with_real_error(self, error_service, tmp_path):
        """Test error handling with a real metadata operation error."""
        # Try to read a non-existent JSON file
        non_existent_file = tmp_path / "non_existent.json"
        
        def read_json():
            import json
            with open(non_existent_file, 'r') as f:
                return json.load(f)
        
        success, error_msg = error_service.handle_metadata_operation_with_error_handling(
            job_id="123",
            metadata_path=str(non_existent_file),
            operation_func=read_json
        )
        
        assert success is False
        assert "No such file or directory" in error_msg
        assert len(error_service.recent_errors) == 1
