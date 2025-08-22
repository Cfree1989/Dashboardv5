from __future__ import annotations
import os
from pathlib import Path
import shutil
from typing import Optional
import logging

from app.business_logic.shared_services.error_handling_service import get_error_handling_service, FileOperationError

logger = logging.getLogger(__name__)

# STATUS_TO_DIR constant moved to atomic_file_service.py to avoid duplication
# This file now serves as a legacy compatibility layer only

# All deprecated functions have been removed:
# - move_authoritative: Replaced by atomic_move_authoritative in atomic_file_service.py
# - _update_metadata_file: Helper function for deprecated move_authoritative
# - _storage_root_from_path: Helper function for deprecated move_authoritative

# This file is now empty and can be removed once all imports are updated
# to use atomic_file_service.py directly


