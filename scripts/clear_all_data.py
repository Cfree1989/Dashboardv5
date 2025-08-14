"""
Dev script: Clear all jobs, events, and payments. Use with caution.

Usage:
  - python scripts/clear_all_data.py --confirm
  - docker-compose exec backend python scripts/clear_all_data.py --confirm
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _ensure_backend_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parent
    # Container layout: /app/app exists
    if (repo_root / "app").exists() and (repo_root / "app" / "__init__.py").exists():
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        return
    # Host layout: backend/app exists
    backend_dir = repo_root / "backend"
    if (backend_dir / "app").exists() and (backend_dir / "app" / "__init__.py").exists():
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        return
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


_ensure_backend_on_path()

from app import create_app, db  # type: ignore  # noqa: E402
from app.models.job import Job  # type: ignore  # noqa: E402
from app.models.event import Event  # type: ignore  # noqa: E402
from app.models.payment import Payment  # type: ignore  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clear all jobs, events, and payments (dev-only)")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    return parser.parse_args()


def main() -> int:
    if "DATABASE_URL" not in os.environ:
        print("❌ DATABASE_URL not set. Run inside backend container or set env var.")
        return 1

    args = parse_args()
    if not args.confirm:
        print("This will delete ALL jobs, events, and payments. Type 'DELETE ALL' to confirm:")
        try:
            confirmation = input().strip()
        except KeyboardInterrupt:
            return 1
        if confirmation != "DELETE ALL":
            print("Cancelled.")
            return 0

    app = create_app()
    with app.app_context():
        jobs = Job.query.count()
        events = Event.query.count()
        payments = Payment.query.count()
        print(f"Before: jobs={jobs}, events={events}, payments={payments}")

        deleted_jobs = 0
        deleted_events = 0
        deleted_payments = 0

        # Order: payments -> events -> jobs (respect FK constraints)
        deleted_payments = Payment.query.delete(synchronize_session=False)
        db.session.commit()

        deleted_events = Event.query.delete(synchronize_session=False)
        db.session.commit()

        deleted_jobs = Job.query.delete(synchronize_session=False)
        db.session.commit()

        print("✅ Deleted:")
        print(f"  jobs: {deleted_jobs}")
        print(f"  events: {deleted_events}")
        print(f"  payments: {deleted_payments}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


