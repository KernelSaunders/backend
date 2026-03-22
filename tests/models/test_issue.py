"""Tests for Issue models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.issue import IssueReports, ChangeLog


class TestIssueReports:
    """Test suite for IssueReports model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_issue_data = {
            "issue_id": "test-issue-id",
            "product_id": "test-product-id",
            "reported_by": "user-123",
            "type": "claim_false",
            "description": "This claim appears to be incorrect",
            "status": "open",
            "resolution_note": None,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 2, 12, 0, 0),
        }

    def test_issue_report_initialization_with_valid_data(self):
        """Test IssueReports initialization with valid data."""
        issue = IssueReports(**self.valid_issue_data)
        
        assert issue.issue_id == "test-issue-id"
        assert issue.product_id == "test-product-id"
        assert issue.reported_by == "user-123"
        assert issue.type == "claim_false"
        assert issue.description == "This claim appears to be incorrect"
        assert issue.status == "open"
        assert issue.resolution_note is None
        assert issue.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert issue.updated_at == datetime(2024, 1, 2, 12, 0, 0)

    def test_issue_report_initialization_with_minimal_required_fields(self):
        """Test IssueReports initialization with only required fields."""
        minimal_data = {
            "issue_id": "min-issue-id",
            "type": "other",
            "description": "Minimal issue",
            "created_at": datetime.now(),
        }
        issue = IssueReports(**minimal_data)
        
        assert issue.issue_id == "min-issue-id"
        assert issue.product_id is None
        assert issue.reported_by is None
        assert issue.type == "other"
        assert issue.description == "Minimal issue"
        assert issue.status == "open"  # Default value
        assert issue.resolution_note is None
        assert issue.created_at is not None
        assert issue.updated_at is None

    def test_issue_report_status_default_value(self):
        """Test that status defaults to 'open'."""
        data = {
            "issue_id": "test-id",
            "type": "data_incorrect",
            "description": "Test",
            "created_at": datetime.now(),
        }
        issue = IssueReports(**data)
        assert issue.status == "open"

    def test_issue_report_type_validation_all_valid_types(self):
        """Test that type accepts all valid literal values."""
        valid_types = ["claim_false", "evidence_missing", "data_incorrect", "other"]
        
        for issue_type in valid_types:
            data = {
                "issue_id": f"test-{issue_type}",
                "type": issue_type,
                "description": "Test description",
                "created_at": datetime.now(),
            }
            issue = IssueReports(**data)
            assert issue.type == issue_type

    def test_issue_report_type_invalid_value(self):
        """Test that invalid type raises ValidationError."""
        invalid_data = {
            "issue_id": "test-id",
            "type": "invalid_type",
            "description": "Test",
            "created_at": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IssueReports(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("type",) for error in errors)

    def test_issue_report_status_validation_all_valid_statuses(self):
        """Test that status accepts all valid literal values."""
        valid_statuses = ["open", "under_review", "resolved", "rejected"]
        
        for status in valid_statuses:
            data = {
                "issue_id": f"test-{status}",
                "type": "other",
                "description": "Test",
                "status": status,
                "created_at": datetime.now(),
            }
            issue = IssueReports(**data)
            assert issue.status == status

    def test_issue_report_status_invalid_value(self):
        """Test that invalid status raises ValidationError."""
        invalid_data = {
            "issue_id": "test-id",
            "type": "other",
            "description": "Test",
            "status": "invalid_status",
            "created_at": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IssueReports(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("status",) for error in errors)

    def test_issue_report_product_id_optional(self):
        """Test that product_id can be None."""
        data = {
            "issue_id": "test-id",
            "product_id": None,
            "type": "other",
            "description": "Test",
            "created_at": datetime.now(),
        }
        issue = IssueReports(**data)
        assert issue.product_id is None

    def test_issue_report_reported_by_optional_for_anonymous(self):
        """Test that reported_by can be None (anonymous reports)."""
        data = {
            "issue_id": "test-id",
            "reported_by": None,
            "type": "other",
            "description": "Anonymous report",
            "created_at": datetime.now(),
        }
        issue = IssueReports(**data)
        assert issue.reported_by is None

    def test_issue_report_resolution_note_optional(self):
        """Test that resolution_note can be None."""
        data = {
            "issue_id": "test-id",
            "type": "other",
            "description": "Test",
            "resolution_note": None,
            "created_at": datetime.now(),
        }
        issue = IssueReports(**data)
        assert issue.resolution_note is None

    def test_issue_report_updated_at_optional(self):
        """Test that updated_at can be None."""
        data = {
            "issue_id": "test-id",
            "type": "other",
            "description": "Test",
            "created_at": datetime.now(),
            "updated_at": None,
        }
        issue = IssueReports(**data)
        assert issue.updated_at is None

    def test_issue_report_required_fields_missing_issue_id(self):
        """Test that missing issue_id raises ValidationError."""
        invalid_data = {
            "type": "other",
            "description": "Test",
            "created_at": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IssueReports(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("issue_id",) for error in errors)

    def test_issue_report_required_fields_missing_type(self):
        """Test that missing type raises ValidationError."""
        invalid_data = {
            "issue_id": "test-id",
            "description": "Test",
            "created_at": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IssueReports(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("type",) for error in errors)

    def test_issue_report_required_fields_missing_description(self):
        """Test that missing description raises ValidationError."""
        invalid_data = {
            "issue_id": "test-id",
            "type": "other",
            "created_at": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IssueReports(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("description",) for error in errors)

    def test_issue_report_required_fields_missing_created_at(self):
        """Test that missing created_at raises ValidationError."""
        invalid_data = {
            "issue_id": "test-id",
            "type": "other",
            "description": "Test",
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IssueReports(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("created_at",) for error in errors)

    def test_issue_report_serialization(self):
        """Test IssueReports serialization to dict."""
        issue = IssueReports(**self.valid_issue_data)
        issue_dict = issue.model_dump()
        
        assert isinstance(issue_dict, dict)
        assert issue_dict["issue_id"] == "test-issue-id"
        assert issue_dict["type"] == "claim_false"
        assert issue_dict["status"] == "open"
        assert isinstance(issue_dict["created_at"], datetime)

    def test_issue_report_deserialization(self):
        """Test IssueReports deserialization from dict."""
        issue = IssueReports(**self.valid_issue_data)
        issue_dict = issue.model_dump()
        deserialized = IssueReports(**issue_dict)
        
        assert deserialized.issue_id == issue.issue_id
        assert deserialized.type == issue.type
        assert deserialized.status == issue.status
        assert deserialized.description == issue.description

    def test_issue_report_with_resolution(self):
        """Test IssueReports with resolution details."""
        data = {
            "issue_id": "resolved-issue",
            "type": "claim_false",
            "description": "False claim detected",
            "status": "resolved",
            "resolution_note": "Claim has been corrected",
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 5),
        }
        issue = IssueReports(**data)
        
        assert issue.status == "resolved"
        assert issue.resolution_note == "Claim has been corrected"
        assert issue.updated_at > issue.created_at


class TestChangeLog:
    """Test suite for ChangeLog model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_changelog_data = {
            "log_id": "log-123",
            "entity_type": "product",
            "entity_id": "product-456",
            "changed_by": "user-789",
            "change_summary": "Updated product description",
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
        }

    def test_changelog_initialization_with_valid_data(self):
        """Test ChangeLog initialization with valid data."""
        log = ChangeLog(**self.valid_changelog_data)
        
        assert log.log_id == "log-123"
        assert log.entity_type == "product"
        assert log.entity_id == "product-456"
        assert log.changed_by == "user-789"
        assert log.change_summary == "Updated product description"
        assert log.timestamp == datetime(2024, 1, 1, 12, 0, 0)

    def test_changelog_initialization_with_minimal_required_fields(self):
        """Test ChangeLog initialization with only required fields."""
        minimal_data = {
            "log_id": "min-log",
            "entity_type": "claim",
            "entity_id": "claim-123",
            "change_summary": "Created claim",
            "timestamp": datetime.now(),
        }
        log = ChangeLog(**minimal_data)
        
        assert log.log_id == "min-log"
        assert log.entity_type == "claim"
        assert log.changed_by is None

    def test_changelog_entity_type_validation_all_valid_types(self):
        """Test that entity_type accepts all valid literal values."""
        valid_entity_types = [
            "product",
            "stage",
            "claim",
            "evidence",
            "input_share",
            "mission",
        ]
        
        for entity_type in valid_entity_types:
            data = {
                "log_id": f"log-{entity_type}",
                "entity_type": entity_type,
                "entity_id": f"{entity_type}-123",
                "change_summary": f"Updated {entity_type}",
                "timestamp": datetime.now(),
            }
            log = ChangeLog(**data)
            assert log.entity_type == entity_type

    def test_changelog_entity_type_invalid_value(self):
        """Test that invalid entity_type raises ValidationError."""
        invalid_data = {
            "log_id": "log-123",
            "entity_type": "invalid_entity",
            "entity_id": "entity-123",
            "change_summary": "Test",
            "timestamp": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChangeLog(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("entity_type",) for error in errors)

    def test_changelog_changed_by_optional(self):
        """Test that changed_by can be None (system changes)."""
        data = {
            "log_id": "log-123",
            "entity_type": "product",
            "entity_id": "product-456",
            "changed_by": None,
            "change_summary": "Automated update",
            "timestamp": datetime.now(),
        }
        log = ChangeLog(**data)
        assert log.changed_by is None

    def test_changelog_required_fields_missing_log_id(self):
        """Test that missing log_id raises ValidationError."""
        invalid_data = {
            "entity_type": "product",
            "entity_id": "product-123",
            "change_summary": "Test",
            "timestamp": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChangeLog(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("log_id",) for error in errors)

    def test_changelog_required_fields_missing_entity_type(self):
        """Test that missing entity_type raises ValidationError."""
        invalid_data = {
            "log_id": "log-123",
            "entity_id": "entity-123",
            "change_summary": "Test",
            "timestamp": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChangeLog(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("entity_type",) for error in errors)

    def test_changelog_required_fields_missing_entity_id(self):
        """Test that missing entity_id raises ValidationError."""
        invalid_data = {
            "log_id": "log-123",
            "entity_type": "product",
            "change_summary": "Test",
            "timestamp": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChangeLog(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("entity_id",) for error in errors)

    def test_changelog_change_summary_optional_defaults_to_none(self):
        """change_summary is optional on the model; omitted means None."""
        data = {
            "log_id": "log-123",
            "entity_type": "product",
            "entity_id": "product-123",
            "timestamp": datetime.now(),
        }
        log = ChangeLog(**data)
        assert log.change_summary is None

    def test_changelog_change_summary_dict_payload(self):
        """change_summary accepts JSON-shaped dict (e.g. DB JSONB rows)."""
        summary = {
            "action": "verified",
            "old_confidence": "unverified",
            "new_confidence": "verified",
            "notes": "Evidence reviewed",
        }
        data = {
            "log_id": "log-jsonb-1",
            "entity_type": "claim",
            "entity_id": "claim-789",
            "change_summary": summary,
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
        }
        log = ChangeLog(**data)
        assert log.change_summary == summary
        assert isinstance(log.change_summary, dict)
        assert log.change_summary["action"] == "verified"

    def test_changelog_change_summary_nested_dict(self):
        """Nested structures in change_summary are preserved."""
        summary = {
            "action": "updated",
            "old": {"name": "A", "category": "food"},
            "new": {"name": "B", "category": "food"},
        }
        log = ChangeLog(
            log_id="log-nested",
            entity_type="product",
            entity_id="p-1",
            change_summary=summary,
            timestamp=datetime(2024, 5, 5, 0, 0, 0),
        )
        assert log.change_summary["old"]["name"] == "A"
        assert log.change_summary["new"]["name"] == "B"

    def test_changelog_change_summary_dict_serialization_roundtrip(self):
        summary = {"action": "confidence_updated", "old_confidence": "partially_verified"}
        log = ChangeLog(
            log_id="log-rt",
            entity_type="claim",
            entity_id="c-1",
            change_summary=summary,
            timestamp=datetime(2024, 1, 2, 0, 0, 0),
        )
        restored = ChangeLog(**log.model_dump())
        assert restored.change_summary == summary
        assert isinstance(restored.change_summary, dict)

    def test_changelog_required_fields_missing_timestamp(self):
        """Test that missing timestamp raises ValidationError."""
        invalid_data = {
            "log_id": "log-123",
            "entity_type": "product",
            "entity_id": "product-123",
            "change_summary": "Test",
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChangeLog(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("timestamp",) for error in errors)

    def test_changelog_serialization(self):
        """Test ChangeLog serialization to dict."""
        log = ChangeLog(**self.valid_changelog_data)
        log_dict = log.model_dump()
        
        assert isinstance(log_dict, dict)
        assert log_dict["log_id"] == "log-123"
        assert log_dict["entity_type"] == "product"
        assert log_dict["entity_id"] == "product-456"
        assert isinstance(log_dict["timestamp"], datetime)

    def test_changelog_deserialization(self):
        """Test ChangeLog deserialization from dict."""
        log = ChangeLog(**self.valid_changelog_data)
        log_dict = log.model_dump()
        deserialized = ChangeLog(**log_dict)
        
        assert deserialized.log_id == log.log_id
        assert deserialized.entity_type == log.entity_type
        assert deserialized.entity_id == log.entity_id
        assert deserialized.change_summary == log.change_summary
        assert deserialized.timestamp == log.timestamp

    def test_changelog_timestamp_handling(self):
        """Test ChangeLog timestamp is properly stored."""
        now = datetime(2024, 6, 15, 10, 30, 45)
        data = {
            "log_id": "log-time",
            "entity_type": "stage",
            "entity_id": "stage-123",
            "change_summary": "Time test",
            "timestamp": now,
        }
        log = ChangeLog(**data)
        
        assert log.timestamp == now
        assert log.timestamp.year == 2024
        assert log.timestamp.month == 6
        assert log.timestamp.day == 15
