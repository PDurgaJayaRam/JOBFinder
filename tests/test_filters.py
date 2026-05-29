"""Unit tests for job filtering and URL building."""
import pytest
from agents.browser_agent.autonomous_agent import AutonomousAgent, _parse_posted_date


class TestBuildSearchUrl:
    """Tests for _build_search_url method."""

    def setup_method(self):
        self.agent = AutonomousAgent.__new__(AutonomousAgent)

    def test_naukri_url(self):
        url = self.agent._build_search_url("naukri", "Python Developer", "Hyderabad")
        assert "naukri.com" in url
        assert "Python-Developer" in url
        assert "Hyderabad" in url

    def test_indeed_url(self):
        url = self.agent._build_search_url("indeed", "Python Developer", "Hyderabad")
        assert "in.indeed.com" in url
        assert "q=" in url
        assert "l=" in url

    def test_linkedin_url(self):
        url = self.agent._build_search_url("linkedin", "Python Developer", "Hyderabad")
        assert "linkedin.com" in url
        assert "keywords=" in url

    def test_glassdoor_url(self):
        url = self.agent._build_search_url("glassdoor", "Python Developer", "Hyderabad")
        assert "glassdoor" in url
        assert "SRCH" in url

    def test_timesjobs_url(self):
        url = self.agent._build_search_url("timesjobs", "Python Developer", "Hyderabad")
        assert "timesjobs.com" in url
        assert "keywords" in url

    def test_foundit_url(self):
        url = self.agent._build_search_url("foundit", "Python Developer", "Hyderabad")
        assert "foundit.in" in url
        assert "query=" in url

    def test_url_encoding_special_chars(self):
        url = self.agent._build_search_url("indeed", "C# .NET", "New York")
        assert "%23" in url or "C%23" in url  # # should be encoded

    def test_unknown_portal_defaults_to_naukri(self):
        url = self.agent._build_search_url("unknown", "Python", "Delhi")
        assert "naukri.com" in url


class TestParsePostedDate:
    """Tests for _parse_posted_date module-level function."""

    def test_days_ago(self):
        from datetime import datetime, timedelta
        result = _parse_posted_date("3 days ago")
        assert result is not None
        expected = datetime.utcnow() - timedelta(days=3)
        assert abs((result - expected).total_seconds()) < 60

    def test_hours_ago(self):
        from datetime import datetime, timedelta
        result = _parse_posted_date("5 hours ago")
        assert result is not None
        expected = datetime.utcnow() - timedelta(hours=5)
        assert abs((result - expected).total_seconds()) < 60

    def test_today(self):
        from datetime import datetime
        result = _parse_posted_date("today")
        assert result is not None
        assert result.date() == datetime.utcnow().date()

    def test_none_input(self):
        assert _parse_posted_date(None) is None

    def test_empty_string(self):
        assert _parse_posted_date("") is None

    def test_invalid_format(self):
        assert _parse_posted_date("random text") is None


class TestFilterJobs:
    """Tests for _filter_jobs method."""

    def setup_method(self):
        self.agent = AutonomousAgent.__new__(AutonomousAgent)

    def test_filters_old_jobs(self):
        old_job = {
            "title": "Python Developer",
            "company": "TestCorp",
            "posted_text": "30 days ago",
        }
        recent_job = {
            "title": "Java Developer",
            "company": "TestCorp",
            "posted_text": "2 days ago",
        }
        result = self.agent._filter_jobs([old_job, recent_job], "Python", "Hyderabad", False)
        assert len(result) == 1
        assert result[0]["title"] == "Java Developer"

    def test_keeps_jobs_without_date(self):
        job = {"title": "Python Developer", "company": "TestCorp"}
        result = self.agent._filter_jobs([job], "Python", "Hyderabad", False)
        assert len(result) == 1

    def test_empty_list(self):
        assert self.agent._filter_jobs([], "Python", "Hyderabad", False) == []
