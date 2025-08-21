import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime
import os

from app.services.orchestration.job_orchestration_service import (
    JobOrchestrationService, 
    JobApprovalData, 
    JobRejectionData
)
from app.business_logic.shared_services.validation_service import ValidationService, ValidationResult
from app.business_logic.shared_services.response_service import ResponseService
from app.models.job import Job
from app.models.staff import Staff
from app.models.event import Event
from app import create_app


class TestJobApprovalData:
    """Test JobApprovalData data class"""
    
    def test_job_approval_data_creation(self):
        """Test creating JobApprovalData with all parameters"""
        data = JobApprovalData(
            staff_name="John Doe",
            weight_g=25.5,
            time_hours=2.0,
            authoritative_filename="test.stl",
            printer_override="Prusa MK4S"
        )
        
        assert data.staff_name == "John Doe"
        assert data.weight_g == 25.5
        assert data.time_hours == 2.0
        assert data.authoritative_filename == "test.stl"
        assert data.printer_override == "Prusa MK4S"
    
    def test_job_approval_data_minimal(self):
        """Test creating JobApprovalData with minimal parameters"""
        data = JobApprovalData(
            staff_name="John Doe",
            weight_g=25.5,
            time_hours=2.0
        )
        
        assert data.staff_name == "John Doe"
        assert data.weight_g == 25.5
        assert data.time_hours == 2.0
        assert data.authoritative_filename is None
        assert data.printer_override is None


class TestJobRejectionData:
    """Test JobRejectionData data class"""
    
    def test_job_rejection_data_creation(self):
        """Test creating JobRejectionData with all parameters"""
        data = JobRejectionData(
            staff_name="John Doe",
            reasons=["Poor quality", "Wrong material"],
            custom_reason="Additional custom reason"
        )
        
        assert data.staff_name == "John Doe"
        assert data.reasons == ["Poor quality", "Wrong material"]
        assert data.custom_reason == "Additional custom reason"
    
    def test_job_rejection_data_minimal(self):
        """Test creating JobRejectionData with minimal parameters"""
        data = JobRejectionData(
            staff_name="John Doe",
            reasons=["Poor quality"]
        )
        
        assert data.staff_name == "John Doe"
        assert data.reasons == ["Poor quality"]
        assert data.custom_reason is None


class TestJobOrchestrationService:
    """Test JobOrchestrationService business logic"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing with proper configuration"""
        # Set test environment variables
        os.environ['TESTING'] = 'true'
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    @pytest.fixture
    def mock_validation_service(self):
        """Create a mock validation service"""
        mock = Mock(spec=ValidationService)
        return mock
    
    @pytest.fixture
    def mock_response_service(self):
        """Create a mock response service"""
        mock = Mock(spec=ResponseService)
        return mock
    
    @pytest.fixture
    def service(self, mock_validation_service, mock_response_service):
        """Create JobOrchestrationService with mocked dependencies"""
        # Mock the individual services that the orchestration service uses
        with patch('app.services.orchestration.job_orchestration_service.JobApprovalService') as mock_approval, \
             patch('app.services.orchestration.job_orchestration_service.JobStatusService') as mock_status, \
             patch('app.services.orchestration.job_orchestration_service.JobTransitionService') as mock_transition, \
             patch('app.services.orchestration.job_orchestration_service.JobAdminService') as mock_admin, \
             patch('app.services.orchestration.job_orchestration_service.JobNotesService') as mock_notes, \
             patch('app.services.orchestration.job_orchestration_service.JobLockingService') as mock_locking, \
             patch('app.services.orchestration.job_orchestration_service.JobEventService') as mock_events:
            
            # Create mock service instances
            mock_approval_instance = Mock()
            mock_status_instance = Mock()
            mock_transition_instance = Mock()
            mock_admin_instance = Mock()
            mock_notes_instance = Mock()
            mock_locking_instance = Mock()
            mock_events_instance = Mock()
            
            # Configure the mock constructors to return our instances
            mock_approval.return_value = mock_approval_instance
            mock_status.return_value = mock_status_instance
            mock_transition.return_value = mock_transition_instance
            mock_admin.return_value = mock_admin_instance
            mock_notes.return_value = mock_notes_instance
            mock_locking.return_value = mock_locking_instance
            mock_events.return_value = mock_events_instance
            
            # Create the orchestration service
            service = JobOrchestrationService()
            
            # Store the mock instances for test access
            service.mock_approval = mock_approval_instance
            service.mock_status = mock_status_instance
            service.mock_transition = mock_transition_instance
            service.mock_admin = mock_admin_instance
            service.mock_notes = mock_notes_instance
            service.mock_locking = mock_locking_instance
            service.mock_events = mock_events_instance
            
            return service
    
    @pytest.fixture
    def mock_job(self):
        """Create a mock job without using spec to avoid Flask context issues"""
        job = Mock()
        job.id = "test-job-123"
        job.status = "UPLOADED"
        job.material = "PLA"
        job.color = "True Black"
        job.printer = "Prusa MK4S"
        job.file_path = "/storage/Uploaded/test-file.stl"
        job.display_name = "test-file.stl"
        job.metadata_path = "/storage/Uploaded/test-file.stl.metadata.json"
        return job
    
    @pytest.fixture
    def mock_staff(self):
        """Create a mock staff member"""
        staff = Mock(spec=Staff)
        staff.name = "John Doe"
        staff.is_active = True
        return staff
    
    def test_service_initialization(self, service):
        """Test service initialization with all business logic services"""
        # Verify all business logic services are initialized
        assert hasattr(service, 'approval')
        assert hasattr(service, 'status')
        assert hasattr(service, 'transition')
        assert hasattr(service, 'admin')
        assert hasattr(service, 'notes')
        assert hasattr(service, 'locking')
        assert hasattr(service, 'events')
    
    def test_approve_job_delegation(self, service, mock_job):
        """Test approve_job delegates to JobApprovalService"""
        # Setup
        approval_data = JobApprovalData(
            staff_name="John Doe",
            weight_g=25.5,
            time_hours=2.0
        )
        service.mock_approval.approve_job.return_value = mock_job
        
        # Execute
        result = service.approve_job("test-job-123", approval_data)
        
        # Verify
        assert result == mock_job
        service.mock_approval.approve_job.assert_called_once_with("test-job-123", approval_data, None)
    
    def test_reject_job_delegation(self, service, mock_job):
        """Test reject_job delegates to JobApprovalService"""
        # Setup
        rejection_data = JobRejectionData(
            staff_name="John Doe",
            reasons=["Poor quality"]
        )
        service.mock_approval.reject_job.return_value = mock_job
        
        # Execute
        result = service.reject_job("test-job-123", rejection_data)
        
        # Verify
        assert result == mock_job
        service.mock_approval.reject_job.assert_called_once_with("test-job-123", rejection_data, None)
    
    def test_transition_status_delegation(self, service, mock_job):
        """Test transition_status delegates to JobTransitionService"""
        # Setup
        service.mock_transition.transition_status.return_value = mock_job
        
        # Execute
        result = service.transition_status("test-job-123", "PRINTING", "John Doe")
        
        # Verify
        assert result == mock_job
        service.mock_transition.transition_status.assert_called_once_with("test-job-123", "PRINTING", "John Doe", None)
    
    def test_lock_job_delegation(self, service, mock_job):
        """Test lock_job delegates to JobLockingService"""
        # Setup
        from app.business_logic.shared_services.job_locking_service import JobLockData
        lock_data = JobLockData(workstation_id="workstation-123")
        service.mock_locking.lock_job.return_value = mock_job
        
        # Execute
        result = service.lock_job("test-job-123", lock_data)
        
        # Verify
        assert result == mock_job
        service.mock_locking.lock_job.assert_called_once_with("test-job-123", lock_data)
    
    def test_unlock_job_delegation(self, service, mock_job):
        """Test unlock_job delegates to JobLockingService"""
        # Setup
        from app.business_logic.shared_services.job_locking_service import JobLockData
        lock_data = JobLockData(workstation_id="workstation-123")
        service.mock_locking.unlock_job.return_value = mock_job
        
        # Execute
        result = service.unlock_job("test-job-123", lock_data)
        
        # Verify
        assert result == mock_job
        service.mock_locking.unlock_job.assert_called_once_with("test-job-123", lock_data)
    
    def test_append_note_delegation(self, service, mock_job):
        """Test append_note delegates to JobNotesService"""
        # Setup
        from app.business_logic.admin_operations.job_notes_service import JobNoteData
        note_data = JobNoteData(staff_name="John Doe", text="Test note")
        service.mock_notes.append_note.return_value = mock_job
        
        # Execute
        result = service.append_note("test-job-123", note_data)
        
        # Verify
        assert result == mock_job
        service.mock_notes.append_note.assert_called_once_with("test-job-123", note_data, None)
    
    def test_delete_job_delegation(self, service, mock_job):
        """Test delete_job delegates to JobAdminService"""
        # Setup
        from app.business_logic.admin_operations.job_admin_service import JobDeleteData
        delete_data = JobDeleteData(staff_name="John Doe")
        service.mock_admin.delete_job.return_value = mock_job
        
        # Execute
        result = service.delete_job("test-job-123", delete_data)
        
        # Verify
        assert result == mock_job
        service.mock_admin.delete_job.assert_called_once_with("test-job-123", delete_data, None)
    
    def test_log_event_delegation(self, service):
        """Test log_event delegates to JobEventService"""
        # Setup
        mock_event = Mock()
        service.mock_events.log_event.return_value = mock_event
        
        # Execute
        result = service.log_event("test-job-123", "JobCreated", {"test": True}, "John Doe")
        
        # Verify
        assert result == mock_event
        service.mock_events.log_event.assert_called_once_with("test-job-123", "JobCreated", {"test": True}, "John Doe", None)
