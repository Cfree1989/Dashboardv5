# type: ignore


def test_diag_requires_auth(client):
    resp = client.get('/api/v1/_diag')
    assert resp.status_code == 401


def test_diag_with_token_returns_expected_fields(client, token):
    resp = client.get('/api/v1/_diag', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'db_engine' in data
    assert 'db_url_sanitized' in data
    assert 'migration_head' in data
    assert 'job_counts_by_status' in data
    assert isinstance(data['job_counts_by_status'], dict)
    assert 'app_env' in data


def test_admin_audit_report_basic(client, token, app, tmp_path):
    import os
    # Use empty storage to start
    os.environ['STORAGE_PATH'] = str(tmp_path)
    # Create a stray orphan file
    (tmp_path / 'Uploaded').mkdir(parents=True, exist_ok=True)
    orphan = tmp_path / 'Uploaded' / 'orphan.stl'
    orphan.write_text('x')

    # Request audit report
    resp = client.get('/api/v1/admin/audit/report', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'report_generated_at' in data
    # Orphan should be flagged
    assert any(str(orphan.resolve()) == p for p in data.get('orphaned_files', []))


def test_admin_delete_orphaned_file(client, token, app, tmp_path):
    import os
    os.environ['STORAGE_PATH'] = str(tmp_path)
    # Create orphan
    (tmp_path / 'Uploaded').mkdir(parents=True, exist_ok=True)
    orphan = tmp_path / 'Uploaded' / 'z.stl'
    orphan.write_text('x')
    # Delete via API
    resp = client.delete(
        '/api/v1/admin/audit/orphaned-file',
        json={'file_path': str(orphan), 'staff_name': 'Admin User'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert not orphan.exists()


def test_admin_delete_stale_file(client, token, app, tmp_path):
    import os
    os.environ['STORAGE_PATH'] = str(tmp_path)
    # Create stale file (in ReadyToPrint) while job authoritative is elsewhere
    (tmp_path / 'ReadyToPrint').mkdir(parents=True, exist_ok=True)
    stale = tmp_path / 'ReadyToPrint' / 'z.stl'
    stale.write_text('x')
    resp = client.delete(
        '/api/v1/admin/audit/stale-file',
        json={'file_path': str(stale), 'staff_name': 'Admin User'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert not stale.exists()

