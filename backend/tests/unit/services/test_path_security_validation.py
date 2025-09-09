import pytest
from app.services.infrastructure.file_configuration_service import get_file_configuration_service


def test_directory_traversal_prevention_blocks_malicious_paths():
    config = get_file_configuration_service()

    malicious_paths = [
        '../../../etc/passwd',
        '..\\..\\..\\windows\\system32\\config',
        '/etc/passwd',
        'C:\\Windows\\System32\\config\\sam',
        '../../secret_file.txt',
        'storage/../../../sensitive_data',
        'storage/Uploaded/../../outside_storage.txt',
        '/absolute/path/outside/storage',
        'storage/Uploaded/file.txt/../../../escape',
    ]

    for path in malicious_paths:
        is_valid, error = config.validate_path_security(path)
        assert not is_valid, f"Path should be blocked: {path} (error={error})"


def test_valid_paths_within_storage_are_allowed():
    config = get_file_configuration_service()

    valid_paths = [
        'storage/Uploaded/valid_file.stl',
        'storage/Pending/student_project.3mf',
        'storage/Completed/finished_job.obj',
        'storage/ReadyToPrint/ready_file.stl',
    ]

    for path in valid_paths:
        is_valid, error = config.validate_path_security(path)
        assert is_valid, f"Valid storage path blocked: {path} (error={error})"


