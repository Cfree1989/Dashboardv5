import os
import json

# Set up environment
os.environ['TESTING'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'

from app import create_app
from app.business_logic.shared_services.response_service import ResponseService, ErrorCategory, ErrorCode

def test_error_formats():
    """Test the standardized error response formats"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Standardized Error Response Formats")
        print("=" * 50)
        
        # Test 1: Validation Error
        print("\n1. Testing Validation Error:")
        response = ResponseService.validation_error(
            message="Invalid input provided",
            error_code=ErrorCode.INVALID_INPUT.value,
            field="email"
        )
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        # Test 2: Not Found Error
        print("\n2. Testing Not Found Error:")
        response = ResponseService.not_found(
            resource="User",
            error_code=ErrorCode.RESOURCE_NOT_FOUND.value
        )
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        # Test 3: Server Error
        print("\n3. Testing Server Error:")
        response = ResponseService.server_error(
            message="Database connection failed",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR.value
        )
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        # Test 4: Conflict Error
        print("\n4. Testing Conflict Error:")
        response = ResponseService.conflict(
            message="Resource already exists",
            error_code=ErrorCode.RESOURCE_CONFLICT.value
        )
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        # Test 5: Business Error
        print("\n5. Testing Business Error:")
        response = ResponseService.business_error(
            message="Insufficient permissions",
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION.value
        )
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        # Test 6: File Operation Error
        print("\n6. Testing File Operation Error:")
        response = ResponseService.file_operation_error(
            message="Failed to upload file",
            details={"file_size": "10MB", "max_size": "5MB"}
        )
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        # Test 7: Database Error
        print("\n7. Testing Database Error:")
        response = ResponseService.database_error(
            message="Connection timeout",
            details={"operation": "INSERT", "table": "jobs"}
        )
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        # Test 8: Success Response
        print("\n8. Testing Success Response:")
        response = ResponseService.success({
            "message": "Operation completed successfully",
            "data": {"id": 123, "status": "active"}
        })
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        print("\n✅ All error format tests completed!")

if __name__ == "__main__":
    test_error_formats()
