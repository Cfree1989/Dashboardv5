"""
Dev script: Generate simple mock jobs directly via Flask app context.

Usage examples:
  - python scripts/generate_mock_data.py --count 10 --email demo@example.com
  - python scripts/generate_mock_data.py --uploaded 5 --pending 3 --completed 2 --email demo@example.com

Requirements:
  - Set DATABASE_URL in environment (same as backend). Run inside backend container for convenience:
      docker-compose exec backend python scripts/generate_mock_data.py --count 10
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path
from typing import Dict


def _ensure_backend_on_path() -> None:
    """Ensure Python can import the Flask 'app' package.

    Handles both local host (repo root has ./backend/app) and container (code mounted at /app with /app/app).
    """
    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parent
    # Container: /app/app exists
    if (repo_root / "app").exists() and (repo_root / "app" / "__init__.py").exists():
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        return
    # Host: backend/app exists
    backend_dir = repo_root / "backend"
    if (backend_dir / "app").exists() and (backend_dir / "app" / "__init__.py").exists():
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        return
    # Fallback: add repo root just in case
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


_ensure_backend_on_path()

from app import create_app, db  # type: ignore  # noqa: E402
from app.models.job import Job  # type: ignore  # noqa: E402
from app.models.event import Event  # type: ignore  # noqa: E402
from app.services.infrastructure.file_configuration_service import get_file_configuration_service  # type: ignore  # noqa: E402


def _create_placeholder_files(storage_root: Path, status_dir: str, filename: str) -> tuple[Path, Path]:
    target_dir = storage_root / status_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / filename
    meta_path = target_dir / f"{file_path.stem}_metadata.json"
    if not file_path.exists():
        file_path.write_text("placeholder", encoding="utf-8")
    if not meta_path.exists():
        meta_path.write_text("{}", encoding="utf-8")
    return file_path, meta_path


def _status_to_dir(status: str) -> str:
    mapping = {
        "UPLOADED": "Uploaded",
        "PENDING": "Pending",
        "READYTOPRINT": "ReadyToPrint",
        "PRINTING": "Printing",
        "COMPLETED": "Completed",
        "PAIDPICKEDUP": "PaidPickedUp",
        "ARCHIVED": "Archived",
        "REJECTED": "Rejected",
    }
    return mapping.get(status, "Uploaded")


def create_jobs(counts: Dict[str, int], email: str) -> Dict[str, int]:
    created_by_status: Dict[str, int] = {k: 0 for k in counts.keys()}
    storage_root = Path(os.environ.get("STORAGE_PATH", "storage")).resolve()

    for status, requested in counts.items():
        for idx in range(requested):
            job_id = uuid.uuid4().hex
            short = job_id[:8]
            # Use centralized file configuration to get a valid extension
            file_config = get_file_configuration_service()
            extension = list(file_config.allowed_extensions)[0]  # Use first allowed extension
            filename = f"Mock_{short}{extension}"
            status_dir = _status_to_dir(status)
            file_path, meta_path = _create_placeholder_files(storage_root, status_dir, filename)

            job = Job(
                id=job_id,
                short_id=short,
                student_name=f"Mock Student {short}",
                student_email=email,
                discipline="Engineering",
                class_number="ENGR 1010",
                original_filename=filename,
                display_name=filename,
                file_path=str(file_path),
                metadata_path=str(meta_path),
                printer="Prusa MK4S",
                color="Gray",
                material="Filament",
                status=status,
            )
            db.session.add(job)
            db.session.flush()
            db.session.add(Event(job_id=job.id, event_type="JobCreated", details={}, triggered_by="dev-script", workstation_id="dev"))
            db.session.commit()
            created_by_status[status] += 1

    return created_by_status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate simple mock jobs (dev-only)")
    parser.add_argument("--count", type=int, default=0, help="Total UPLOADED jobs to create (quick path)")
    parser.add_argument("--uploaded", type=int, default=0, help="UPLOADED jobs")
    parser.add_argument("--pending", type=int, default=0, help="PENDING jobs")
    parser.add_argument("--ready", type=int, default=0, help="READYTOPRINT jobs")
    parser.add_argument("--printing", type=int, default=0, help="PRINTING jobs")
    parser.add_argument("--completed", type=int, default=0, help="COMPLETED jobs")
    parser.add_argument("--paid", type=int, default=0, help="PAIDPICKEDUP jobs")
    parser.add_argument("--email", type=str, default="cfree3@lsu.edu", help="Email for all jobs")
    return parser.parse_args()


def main() -> int:
    if "DATABASE_URL" not in os.environ:
        print("❌ DATABASE_URL not set. Run inside backend container or set env var.")
        return 1

    args = parse_args()
    counts = {
        "UPLOADED": args.count if args.count else args.uploaded,
        "PENDING": args.pending,
        "READYTOPRINT": args.ready,
        "PRINTING": args.printing,
        "COMPLETED": args.completed,
        "PAIDPICKEDUP": args.paid,
    }
    # Remove zero entries for cleaner output
    counts = {k: v for k, v in counts.items() if v and v > 0}
    if not counts:
        print("Nothing to create. Use --count or per-status flags.")
        return 0

    app = create_app()
    with app.app_context():
        result = create_jobs(counts, args.email)
        total = sum(result.values())
        print("✅ Created jobs:")
        for k, v in result.items():
            if v:
                print(f"  {k}: {v}")
        print(f"Total: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


