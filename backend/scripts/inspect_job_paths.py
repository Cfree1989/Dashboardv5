#!/usr/bin/env python3
import sys
import json
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage", "message": "inspect_job_paths.py <job_id>"}))
        return 1

    job_id = sys.argv[1]

    try:
        from app import create_app
        from app.models import Job
    except Exception as e:
        print(json.dumps({"error": "import_failure", "message": str(e)}))
        return 1

    app = create_app()
    with app.app_context():
        job = Job.query.get(job_id)
        if not job:
            print(json.dumps({"error": "job_not_found", "job_id": job_id}))
            return 0

        db_file_path = job.file_path
        db_file_resolved = str(Path(db_file_path).resolve()) if db_file_path else None
        metadata_path = job.metadata_path

        meta = {}
        if metadata_path and Path(metadata_path).exists():
            try:
                meta = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
            except Exception as e:
                meta = {"read_error": str(e)}

        meta_file_path = meta.get("file_path") if isinstance(meta, dict) else None
        meta_status = meta.get("status") if isinstance(meta, dict) else None

        meta_resolved = None
        try:
            if meta_file_path:
                meta_resolved = str(Path(meta_file_path).resolve())
        except Exception:
            meta_resolved = None

        result = {
            "job_id": job.id,
            "status": job.status,
            "db_file_path": db_file_path,
            "db_file_path_resolved": db_file_resolved,
            "metadata_path": metadata_path,
            "exists_db_file": bool(db_file_path and Path(db_file_path).exists()),
            "exists_metadata_file": bool(metadata_path and Path(metadata_path).exists()),
            "meta_file_path": meta_file_path,
            "meta_file_path_resolved": meta_resolved,
            "meta_status": meta_status,
        }

        print(json.dumps(result))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())


