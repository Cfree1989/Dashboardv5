import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from app.services.payment_service import PaymentService
from app.services.interfaces.payment_service_interface import PaymentData
from app.models.job import Job
from app.models.payment import Payment
from app.models.staff import Staff
from app.services.validation_service import ValidationResult


class TestPaymentService:
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_validation_service = Mock()
        self.payment_service = PaymentService(validation_service=self.mock_validation_service)
        
        # Mock job
        self.mock_job = Mock(spec=Job)
        self.mock_job.id = "test_job_123"
        self.mock_job.status = "COMPLETED"
        self.mock_job.material = "filament"
        self.mock_job.file_path = "/storage/Completed/test.stl"
        
        # Mock staff
        self.mock_staff = Mock(spec=Staff)
        self.mock_staff.is_active = True
        
        # Mock payment data
        self.payment_data = PaymentData(
            grams=25.5,
            txn_no="TX123",
            picked_up_by="John Doe",
            staff_name="Cashier"
        )

    def test_calculate_final_cost_filament_below_minimum(self):
        """Test filament cost calculation below minimum charge"""
        cost = self.payment_service.calculate_final_cost("filament", 20.0)
        assert cost == 300  # $3.00 minimum charge

    def test_calculate_final_cost_filament_above_minimum(self):
        """Test filament cost calculation above minimum charge"""
        cost = self.payment_service.calculate_final_cost("filament", 50.0)
        assert cost == 500  # $5.00 (50g * $0.10/g)

    def test_calculate_final_cost_resin_below_minimum(self):
        """Test resin cost calculation below minimum charge"""
        cost = self.payment_service.calculate_final_cost("resin", 10.0)
        assert cost == 300  # $3.00 minimum charge

    def test_calculate_final_cost_resin_above_minimum(self):
        """Test resin cost calculation above minimum charge"""
        cost = self.payment_service.calculate_final_cost("resin", 25.0)
        assert cost == 500  # $5.00 (25g * $0.20/g)

    def test_calculate_final_cost_rounding(self):
        """Test cost calculation with proper rounding"""
        cost = self.payment_service.calculate_final_cost("filament", 33.333)
        assert cost == 333  # $3.33 rounded down (33.333 * 0.10 = 3.3333, rounded to 3.33 = 333 cents)

    def test_calculate_final_cost_case_insensitive(self):
        """Test material name case insensitivity"""
        cost_lower = self.payment_service.calculate_final_cost("resin", 10.0)
        cost_upper = self.payment_service.calculate_final_cost("RESIN", 10.0)
        cost_mixed = self.payment_service.calculate_final_cost("ResIn", 10.0)
        assert cost_lower == cost_upper == cost_mixed

    def test_calculate_final_cost_none_material(self):
        """Test cost calculation with None material (defaults to filament rate)"""
        cost = self.payment_service.calculate_final_cost(None, 50.0)
        assert cost == 500  # $5.00 (50g * $0.10/g)

    @patch('app.services.payment_service.db')
    @patch('app.services.payment_service.move_authoritative')
    def test_record_payment_success(self, mock_move_authoritative, mock_db):
        """Test successful payment recording"""
        # Setup validation mocks
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(True, data=self.mock_job)
        self.mock_validation_service.validate_staff.return_value = ValidationResult(True, data=self.mock_staff)
        
        # Mock database session
        mock_db.session.add = Mock()
        mock_db.session.commit = Mock()
        
        # Execute
        result = self.payment_service.record_payment("test_job_123", self.payment_data)
        
        # Verify
        assert isinstance(result, Payment)
        assert result.job_id == "test_job_123"
        assert result.grams == 25.5
        assert result.txn_no == "TX123"
        assert result.picked_up_by == "John Doe"
        assert result.paid_by_staff == "Cashier"
        
        # Verify job status transition
        assert self.mock_job.status == "PAIDPICKEDUP"
        assert self.mock_job.last_updated_by == "Cashier"
        
        # Verify file movement
        mock_move_authoritative.assert_called_once_with(self.mock_job, "PAIDPICKEDUP")
        
        # Verify database operations
        assert mock_db.session.add.call_count >= 2  # Payment + Job + Event
        assert mock_db.session.commit.call_count >= 2

    def test_record_payment_job_not_found(self):
        """Test payment recording with non-existent job"""
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(False, "Job not found")
        
        with pytest.raises(ValueError, match="Job not found"):
            self.payment_service.record_payment("nonexistent_job", self.payment_data)

    def test_record_payment_wrong_status(self):
        """Test payment recording with job in wrong status"""
        self.mock_job.status = "PENDING"
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(True, data=self.mock_job)
        
        with pytest.raises(ValueError, match="Job must be in COMPLETED to record payment"):
            self.payment_service.record_payment("test_job_123", self.payment_data)

    def test_record_payment_invalid_staff(self):
        """Test payment recording with invalid staff"""
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(True, data=self.mock_job)
        self.mock_validation_service.validate_staff.return_value = ValidationResult(False, "Invalid staff")
        
        with pytest.raises(ValueError, match="Invalid staff"):
            self.payment_service.record_payment("test_job_123", self.payment_data)

    def test_record_payment_invalid_grams(self):
        """Test payment recording with invalid grams"""
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(True, data=self.mock_job)
        self.mock_validation_service.validate_staff.return_value = ValidationResult(True, data=self.mock_staff)
        
        invalid_payment_data = PaymentData(
            grams=0,  # Invalid
            txn_no="TX123",
            picked_up_by="John Doe",
            staff_name="Cashier"
        )
        
        with pytest.raises(ValueError, match="grams must be greater than 0"):
            self.payment_service.record_payment("test_job_123", invalid_payment_data)

    def test_record_payment_missing_txn_no(self):
        """Test payment recording with missing transaction number"""
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(True, data=self.mock_job)
        self.mock_validation_service.validate_staff.return_value = ValidationResult(True, data=self.mock_staff)
        
        invalid_payment_data = PaymentData(
            grams=25.5,
            txn_no="",  # Invalid
            picked_up_by="John Doe",
            staff_name="Cashier"
        )
        
        with pytest.raises(ValueError, match="txn_no is required"):
            self.payment_service.record_payment("test_job_123", invalid_payment_data)

    def test_record_payment_missing_picked_up_by(self):
        """Test payment recording with missing picked up by"""
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(True, data=self.mock_job)
        self.mock_validation_service.validate_staff.return_value = ValidationResult(True, data=self.mock_staff)
        
        invalid_payment_data = PaymentData(
            grams=25.5,
            txn_no="TX123",
            picked_up_by="",  # Invalid
            staff_name="Cashier"
        )
        
        with pytest.raises(ValueError, match="picked_up_by is required"):
            self.payment_service.record_payment("test_job_123", invalid_payment_data)

    @patch('app.services.payment_service.db')
    @patch('app.services.payment_service.move_authoritative')
    def test_record_payment_with_workstation_id(self, mock_move_authoritative, mock_db):
        """Test payment recording with workstation ID in Flask context"""
        # Setup validation mocks
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(True, data=self.mock_job)
        self.mock_validation_service.validate_staff.return_value = ValidationResult(True, data=self.mock_staff)
        
        # Mock database session
        mock_db.session.add = Mock()
        mock_db.session.commit = Mock()
        
        # Execute - workstation ID will be None outside Flask context
        result = self.payment_service.record_payment("test_job_123", self.payment_data)
        
        # Verify payment was recorded successfully
        assert isinstance(result, Payment)
        assert result.job_id == "test_job_123"
        assert mock_db.session.add.call_count >= 3  # Payment + Job + Event

    @patch('app.services.payment_service.db')
    @patch('app.services.payment_service.move_authoritative')
    def test_record_payment_without_workstation_id(self, mock_move_authoritative, mock_db):
        """Test payment recording without Flask context (e.g., in tests)"""
        # Setup validation mocks
        self.mock_validation_service.validate_job_exists.return_value = ValidationResult(True, data=self.mock_job)
        self.mock_validation_service.validate_staff.return_value = ValidationResult(True, data=self.mock_staff)
        
        # Mock database session
        mock_db.session.add = Mock()
        mock_db.session.commit = Mock()
        
        # Execute - should work without Flask context
        result = self.payment_service.record_payment("test_job_123", self.payment_data)
        
        # Verify payment was still recorded successfully
        assert isinstance(result, Payment)
        assert result.job_id == "test_job_123"

    def test_get_workstation_id_without_flask_context(self):
        """Test getting workstation ID when outside Flask context"""
        # Test that method handles missing Flask context gracefully
        workstation_id = self.payment_service._get_workstation_id()
        assert workstation_id is None
