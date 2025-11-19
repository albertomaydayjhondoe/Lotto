import os
import time
import requests
import pytest

BASE_URL = os.getenv('ORQUESTADOR_URL', 'https://api.example.com')
TOKEN = os.getenv('ORQUESTADOR_TOKEN', 'changeme')

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}


def test_create_and_poll_job_lifecycle():
    """Simple POC test: create a job and poll for status transitions.

    This is a skeleton test: the test expects a POST /jobs to accept job creation
    and a GET /jobs/{id} to return job status. The environment must point to
    a running Orquestador (or a mocked server).
    """

    payload = {
        'job_type': 'cut',
        'params': {'video_asset_id': None},
        'dedup_key': f'test-cut-{int(time.time())}'
    }

    resp = requests.post(f"{BASE_URL}/jobs", json=payload, headers=headers)
    assert resp.status_code in (200, 201)
    job = resp.json()
    job_id = job.get('id')
    assert job_id

    # poll for a small number of seconds for status change
    status = job.get('status')
    for _ in range(10):
        r = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        assert r.status_code == 200
        j = r.json()
        if j.get('status') in ('success', 'failed', 'cancelled'):
            status = j.get('status')
            break
        time.sleep(1)

    # At least ensure job reached a terminal or running state within timeframe
    assert status in ('running', 'success', 'failed', 'cancelled')
