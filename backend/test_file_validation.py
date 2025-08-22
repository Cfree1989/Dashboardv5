#!/usr/bin/env python3
"""
Test script for enhanced file validation features

This script tests the comprehensive file validation implemented in Task 8.
"""

import os
import tempfile
import struct
from app.services.infrastructure.file_configuration_service import get_file_configuration_service


def create_test_files():
    """Create test files for validation testing"""
    test_files = {}
    
    # Create ASCII STL file
    ascii_stl = """solid test
facet normal 0 0 1
    outer loop
        vertex 0 0 0
        vertex 1 0 0
        vertex 0 1 0
    endloop
endfacet
endsolid test"""
    test_files['valid_ascii.stl'] = ascii_stl.encode('utf-8')
    
    # Create binary STL file
    header = b'Binary STL file header' + b'\x00' * 60  # 80 bytes
    triangle_count = b'\x01\x00\x00\x00'  # 1 triangle, little endian
    binary_stl = header + triangle_count + b'\x00' * 50  # Add some data
    test_files['valid_binary.stl'] = binary_stl
    
    # Create OBJ file
    obj_content = """# OBJ file
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
f 1 2 3"""
    test_files['valid.obj'] = obj_content.encode('utf-8')
    
    # Create 3MF file (ZIP with 3MF content)
    zip_header = b'PK\x03\x04'  # ZIP signature
    content = zip_header + b'[Content_Types].xml' + b'\x00' * 100
    test_files['valid.3mf'] = content
    
    # Create invalid files
    test_files['invalid.txt'] = b'This is not a 3D file'
    test_files['empty.stl'] = b''
    test_files['tiny.stl'] = b'123'
    
    # Create executable file (should be rejected)
    test_files['malicious.exe'] = b'MZ' + b'\x00' * 100
    
    return test_files


def test_file_validation():
    """Test comprehensive file validation"""
    print("Testing Enhanced File Validation (Task 8)")
    print("=" * 50)
    
    # Get file configuration service
    file_config = get_file_configuration_service()
    
    # Create test files
    test_files = create_test_files()
    
    # Test results
    results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    def run_test(test_name, test_func):
        """Run a test and record results"""
        results['total'] += 1
        try:
            test_func()
            print(f"✅ {test_name}")
            results['passed'] += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            results['failed'] += 1
    
    # Test 1: Valid ASCII STL
    def test_valid_ascii_stl():
        content = test_files['valid_ascii.stl']
        is_valid, error = file_config.validate_file_header(content, 'test.stl')
        assert is_valid, f"Valid ASCII STL should pass: {error}"
    
    run_test("Valid ASCII STL", test_valid_ascii_stl)
    
    # Test 2: Valid Binary STL
    def test_valid_binary_stl():
        content = test_files['valid_binary.stl']
        is_valid, error = file_config.validate_file_header(content, 'test.stl')
        assert is_valid, f"Valid binary STL should pass: {error}"
    
    run_test("Valid Binary STL", test_valid_binary_stl)
    
    # Test 3: Valid OBJ
    def test_valid_obj():
        content = test_files['valid.obj']
        is_valid, error = file_config.validate_file_header(content, 'test.obj')
        assert is_valid, f"Valid OBJ should pass: {error}"
    
    run_test("Valid OBJ", test_valid_obj)
    
    # Test 4: Valid 3MF
    def test_valid_3mf():
        content = test_files['valid.3mf']
        is_valid, error = file_config.validate_file_header(content, 'test.3mf')
        assert is_valid, f"Valid 3MF should pass: {error}"
    
    run_test("Valid 3MF", test_valid_3mf)
    
    # Test 5: Invalid file type
    def test_invalid_file_type():
        content = test_files['invalid.txt']
        is_valid, error = file_config.validate_file_header(content, 'test.txt')
        # For unknown extensions, we do basic validation but don't reject
        # The file extension validation happens separately
        assert is_valid, f"Unknown file type should pass basic validation: {error}"
    
    run_test("Invalid File Type", test_invalid_file_type)
    
    # Test 6: Empty file
    def test_empty_file():
        content = test_files['empty.stl']
        is_valid, error = file_config.validate_file_header(content, 'test.stl')
        assert not is_valid, "Empty file should fail"
        assert "File is empty" in error
    
    run_test("Empty File", test_empty_file)
    
    # Test 7: Tiny file
    def test_tiny_file():
        content = test_files['tiny.stl']
        is_valid, error = file_config.validate_file_header(content, 'test.stl')
        assert not is_valid, "Tiny file should fail"
        assert "too small for header validation" in error
    
    run_test("Tiny File", test_tiny_file)
    
    # Test 8: Malicious executable
    def test_malicious_executable():
        content = test_files['malicious.exe']
        is_valid, error = file_config.validate_file_header(content, 'test.unknown')
        assert not is_valid, "Executable file should fail"
        assert "executable" in error
    
    run_test("Malicious Executable", test_malicious_executable)
    
    # Test 9: Filename security validation
    def test_filename_security():
        # Test path traversal
        is_valid, error = file_config.validate_filename_security('../test.stl')
        assert not is_valid, "Path traversal should fail"
        assert "Path traversal attempt detected" in error
        
        # Test dangerous characters
        is_valid, error = file_config.validate_filename_security('test*.stl')
        assert not is_valid, "Dangerous characters should fail"
        assert "Dangerous character" in error
        
        # Test reserved names
        is_valid, error = file_config.validate_filename_security('CON.stl')
        assert not is_valid, "Reserved filename should fail"
        assert "Reserved filename" in error
        
        # Test valid filename
        is_valid, error = file_config.validate_filename_security('test.stl')
        assert is_valid, f"Valid filename should pass: {error}"
    
    run_test("Filename Security", test_filename_security)
    
    # Test 10: File size validation
    def test_file_size_validation():
        # Test valid size
        assert file_config.validate_file_size(1024), "1KB should be valid"
        assert file_config.validate_file_size(50 * 1024 * 1024), "50MB should be valid"
        
        # Test too small
        assert not file_config.validate_file_size(512), "512B should be too small"
        error = file_config.get_file_size_validation_error(512)
        assert "too small" in error
        
        # Test too large
        assert not file_config.validate_file_size(100 * 1024 * 1024), "100MB should be too large"
        error = file_config.get_file_size_validation_error(100 * 1024 * 1024)
        assert "too large" in error
    
    run_test("File Size Validation", test_file_size_validation)
    
    # Test 11: Filename sanitization
    def test_filename_sanitization():
        # Test normal filename
        assert file_config.sanitize_filename('test.stl') == 'test.stl'
        
        # Test dangerous characters
        assert file_config.sanitize_filename('test/file.stl') == 'test_file.stl'
        assert file_config.sanitize_filename('test\\file.stl') == 'test_file.stl'
        assert file_config.sanitize_filename('test:file.stl') == 'test_file.stl'
        
        # Test leading/trailing characters
        assert file_config.sanitize_filename('.test.stl.') == 'test.stl'
        assert file_config.sanitize_filename(' test.stl ') == 'test.stl'
        
        # Test empty filename
        assert file_config.sanitize_filename('') == 'unnamed_file'
    
    run_test("Filename Sanitization", test_filename_sanitization)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Test Summary:")
    print(f"  Total: {results['total']}")
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Success Rate: {results['passed']/results['total']*100:.1f}%")
    
    if results['failed'] == 0:
        print("\n🎉 All tests passed! Enhanced file validation is working correctly.")
    else:
        print(f"\n⚠️  {results['failed']} tests failed. Please review the implementation.")
    
    return results['failed'] == 0


if __name__ == '__main__':
    success = test_file_validation()
    exit(0 if success else 1)
