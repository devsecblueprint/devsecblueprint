"""The walkthrough announcement scan must be registered with the scheduler."""

from fastapi.testclient import TestClient

from app.main import app


def test_announcement_scan_job_is_scheduled():
    with TestClient(app):
        job = app.state.scheduler.get_job("announcement_scan")
        assert job is not None
        assert job.max_instances == 1
        assert job.coalesce is True
        # Default interval is 5 minutes
        assert job.trigger.interval.total_seconds() == 5 * 60
        assert job.func.__name__ == "run_announcement_scan"
