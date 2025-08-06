# type: ignore
import io


def test_event_logging_on_submit(client, token):
    # Submit job
    data = {
        'student_name': 'Charlie',
        'student_email': 'charlie@example.com',
        'discipline': 'Eng',
        'class_number': '303',
        'printer': 'Prusa',
        'color': 'Green',
        'material': 'Filament',
        'file': (io.BytesIO(b'model data'), 'model.stl')
    }
    resp = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp.status_code == 201
    job = resp.get_json()
    job_id = job['id']

    # Retrieve events
    resp_events = client.get(
        f'/api/v1/jobs/{job_id}/events',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp_events.status_code == 200
    events = resp_events.get_json()
    assert len(events) == 1
    evt = events[0]
    assert evt['job_id'] == job_id
    assert evt['event_type'] == 'JobCreated'