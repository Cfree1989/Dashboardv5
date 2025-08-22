# backend/app/utils/file_utils.py
from pathlib import Path
import os
from typing import Optional, Tuple
from app.services.infrastructure.file_configuration_service import get_file_configuration_service

class FileUtils:
    @staticmethod
    def validate_storage_path(file_path: str) -> bool:
        """Validate file path is within storage root"""
        root = Path(os.environ.get('STORAGE_PATH', 'storage')).resolve()
        target = Path(file_path).resolve()
        return str(target).startswith(str(root))
    
    @staticmethod
    def get_storage_root() -> Path:
        """Get configured storage root path"""
        return Path(os.environ.get('STORAGE_PATH', 'storage'))
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> Path:
        """Ensure directory exists, create if it doesn't"""
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension from path"""
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def is_valid_file_type(file_path: str, allowed_extensions: list) -> bool:
        """Check if file has allowed extension"""
        extension = FileUtils.get_file_extension(file_path)
        return extension in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def is_valid_file_type_configured(file_path: str) -> bool:
        """Check if file has allowed extension using centralized configuration"""
        file_config = get_file_configuration_service()
        return file_config.is_allowed_extension(file_path)
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get safe filename by removing dangerous characters"""
        # Remove or replace dangerous characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        safe_filename = ''.join(c for c in filename if c in safe_chars)
        
        # Ensure filename doesn't start with a dot
        if safe_filename.startswith('.'):
            safe_filename = 'file' + safe_filename
            
        return safe_filename or 'unnamed_file'
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """Get file size in bytes, return None if file doesn't exist"""
        try:
            return Path(file_path).stat().st_size
        except (FileNotFoundError, OSError):
            return None
    
    @staticmethod
    def split_path_components(file_path: str) -> Tuple[str, str, str]:
        """Split path into directory, filename (without extension), and extension"""
        path = Path(file_path)
        directory = str(path.parent)
        filename = path.stem
        extension = path.suffix
        return directory, filename, extension
    
    @staticmethod
    def join_paths(*paths: str) -> str:
        """Join multiple path components safely"""
        return str(Path(*paths))
    
    @staticmethod
    def normalize_path(file_path: str) -> str:
        """Normalize path separators for current OS"""
        return str(Path(file_path))
