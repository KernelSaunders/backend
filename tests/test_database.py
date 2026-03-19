"""Tests for database module."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from pydantic import BaseModel

from src.database import (
    get_client,
    select_all,
    select_by_id,
    select_by_field,
    upsert_batch,
    insert_one,
    update_by_id,
    log_entity_change,
    log_claim_change,
)


# Test model for mock database operations
class TestModel(BaseModel):
    id: str
    name: str
    value: int


class TestGetClient:
    """Test suite for get_client function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        get_client.cache_clear()

    def teardown_method(self):
        """Clean up after each test method."""
        get_client.cache_clear()

    def test_get_client_returns_client(self):
        """Test that get_client returns a Supabase Client instance."""
        mock_settings = Mock()
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_key = "test-key-123"
        
        with patch("src.database.get_settings", return_value=mock_settings):
            with patch("src.database.create_client") as mock_create:
                mock_client = Mock()
                mock_create.return_value = mock_client
                
                result = get_client()
                
                assert result == mock_client
                mock_create.assert_called_once_with(
                    "https://test.supabase.co", 
                    "test-key-123"
                )

    def test_get_client_uses_settings(self):
        """Test that get_client uses settings from get_settings."""
        mock_settings = Mock()
        mock_settings.supabase_url = "https://custom.supabase.io"
        mock_settings.supabase_key = "custom-key-456"
        
        with patch("src.database.get_settings", return_value=mock_settings) as mock_get_settings:
            with patch("src.database.create_client") as mock_create:
                mock_create.return_value = Mock()
                
                get_client()
                
                mock_get_settings.assert_called_once()
                mock_create.assert_called_once_with(
                    "https://custom.supabase.io",
                    "custom-key-456"
                )

    def test_get_client_caching(self):
        """Test that get_client caches the client instance."""
        mock_settings = Mock()
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_key = "test-key"
        
        with patch("src.database.get_settings", return_value=mock_settings):
            with patch("src.database.create_client") as mock_create:
                mock_client = Mock()
                mock_create.return_value = mock_client
                
                # First call
                result1 = get_client()
                # Second call (should use cache)
                result2 = get_client()
                
                assert result1 == result2
                # create_client should only be called once due to caching
                assert mock_create.call_count == 1


class TestSelectAll:
    """Test suite for select_all function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = MagicMock()

    def test_select_all_returns_list_of_models(self):
        """Test that select_all returns a list of model instances."""
        mock_response = Mock()
        mock_response.data = [
            {"id": "1", "name": "Test1", "value": 100},
            {"id": "2", "name": "Test2", "value": 200},
        ]
        
        self.mock_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_all(TestModel)
        
        assert len(result) == 2
        assert isinstance(result[0], TestModel)
        assert result[0].id == "1"
        assert result[0].name == "Test1"
        assert result[1].id == "2"

    def test_select_all_uses_correct_table_name(self):
        """Test that select_all uses the model class name as table name."""
        mock_response = Mock()
        mock_response.data = []
        
        self.mock_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            select_all(TestModel)
        
        self.mock_client.table.assert_called_once_with("TestModel")

    def test_select_all_with_empty_response(self):
        """Test select_all when database returns empty list."""
        mock_response = Mock()
        mock_response.data = []
        
        self.mock_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_all(TestModel)
        
        assert result == []
        assert isinstance(result, list)

    def test_select_all_validates_response_data(self):
        """Test that select_all validates response data with TypeAdapter."""
        mock_response = Mock()
        mock_response.data = [
            {"id": "1", "name": "Valid", "value": 100}
        ]
        
        self.mock_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_all(TestModel)
        
        # Verify the model validation worked
        assert isinstance(result[0], TestModel)
        assert result[0].id == "1"
        assert result[0].value == 100


class TestSelectById:
    """Test suite for select_by_id function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = MagicMock()

    def test_select_by_id_returns_single_model(self):
        """Test that select_by_id returns a single model instance."""
        mock_response = Mock()
        mock_response.data = [{"id": "123", "name": "Test", "value": 999}]
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_by_id(TestModel, "id", "123")
        
        assert result is not None
        assert isinstance(result, TestModel)
        assert result.id == "123"
        assert result.name == "Test"

    def test_select_by_id_returns_none_when_not_found(self):
        """Test that select_by_id returns None when record not found."""
        mock_response = Mock()
        mock_response.data = []
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_by_id(TestModel, "id", "nonexistent")
        
        assert result is None

    def test_select_by_id_uses_correct_id_field(self):
        """Test that select_by_id uses the specified id_field parameter."""
        mock_response = Mock()
        mock_response.data = [{"id": "456", "name": "Test", "value": 100}]
        
        mock_table = self.mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value
        mock_eq.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            select_by_id(TestModel, "custom_id", "456")
        
        self.mock_client.table.assert_called_once_with("TestModel")
        mock_select.eq.assert_called_once_with("custom_id", "456")

    def test_select_by_id_validates_model(self):
        """Test that select_by_id validates response with model_validate."""
        mock_response = Mock()
        mock_response.data = [{"id": "789", "name": "Validated", "value": 555}]
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_by_id(TestModel, "id", "789")
        
        # Verify model validation worked correctly
        assert isinstance(result, TestModel)
        assert result.id == "789"
        assert result.value == 555


class TestSelectByField:
    """Test suite for select_by_field function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = MagicMock()

    def test_select_by_field_returns_list_of_models(self):
        """Test that select_by_field returns a list of model instances."""
        mock_response = Mock()
        mock_response.data = [
            {"id": "1", "name": "Match1", "value": 100},
            {"id": "2", "name": "Match2", "value": 100},
        ]
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_by_field(TestModel, "value", "100")
        
        assert len(result) == 2
        assert all(isinstance(item, TestModel) for item in result)
        assert result[0].name == "Match1"
        assert result[1].name == "Match2"

    def test_select_by_field_uses_correct_field_and_value(self):
        """Test that select_by_field filters by the correct field and value."""
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = self.mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value
        mock_eq.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            select_by_field(TestModel, "name", "TestName")
        
        self.mock_client.table.assert_called_once_with("TestModel")
        mock_select.eq.assert_called_once_with("name", "TestName")

    def test_select_by_field_with_empty_response(self):
        """Test select_by_field when no records match the filter."""
        mock_response = Mock()
        mock_response.data = []
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_by_field(TestModel, "name", "NonExistent")
        
        assert result == []
        assert isinstance(result, list)

    def test_select_by_field_validates_response_data(self):
        """Test that select_by_field validates response data."""
        mock_response = Mock()
        mock_response.data = [
            {"id": "1", "name": "Valid1", "value": 50},
            {"id": "2", "name": "Valid2", "value": 50},
        ]
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = select_by_field(TestModel, "value", "50")
        
        # Verify validation worked
        assert all(isinstance(item, TestModel) for item in result)
        assert all(item.value == 50 for item in result)


class TestUpsertBatch:
    """Test suite for upsert_batch function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = MagicMock()

    def test_upsert_batch_with_empty_records(self):
        """Test that upsert_batch returns 0 for empty records."""
        with patch("src.database.get_client", return_value=self.mock_client):
            result = upsert_batch("TestTable", [])
        
        assert result == 0
        self.mock_client.table.assert_not_called()

    def test_upsert_batch_with_records_below_batch_size(self):
        """Test upsert_batch with records less than batch_size."""
        records = [
            {"id": "1", "name": "Test1"},
            {"id": "2", "name": "Test2"},
        ]
        
        mock_response = Mock()
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = upsert_batch("TestTable", records, batch_size=500)
        
        assert result == 2
        self.mock_client.table.assert_called_once_with("TestTable")
        self.mock_client.table.return_value.upsert.assert_called_once_with(records)

    def test_upsert_batch_with_records_exceeding_batch_size(self):
        """Test upsert_batch with records exceeding batch_size."""
        # Create 1200 records with batch size of 500
        records = [{"id": str(i), "name": f"Test{i}"} for i in range(1200)]
        
        mock_response = Mock()
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = upsert_batch("TestTable", records, batch_size=500)
        
        assert result == 1200
        # Should be called 3 times: 500, 500, 200
        assert self.mock_client.table.return_value.upsert.call_count == 3

    def test_upsert_batch_uses_correct_table_name(self):
        """Test that upsert_batch uses the provided table_name."""
        records = [{"id": "1", "name": "Test"}]
        
        mock_response = Mock()
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            upsert_batch("CustomTable", records)
        
        self.mock_client.table.assert_called_with("CustomTable")

    def test_upsert_batch_returns_total_count(self):
        """Test that upsert_batch returns the total number of upserted records."""
        records = [{"id": str(i), "name": f"Test{i}"} for i in range(750)]
        
        mock_response = Mock()
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = upsert_batch("TestTable", records, batch_size=500)
        
        # Should upsert 500 + 250 = 750 total
        assert result == 750

    def test_upsert_batch_with_custom_batch_size(self):
        """Test upsert_batch with a custom batch_size parameter."""
        records = [{"id": str(i), "name": f"Test{i}"} for i in range(150)]
        
        mock_response = Mock()
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = upsert_batch("TestTable", records, batch_size=50)
        
        assert result == 150
        # Should be called 3 times: 50, 50, 50
        assert self.mock_client.table.return_value.upsert.call_count == 3


class TestInsertOne:
    """Test suite for insert_one function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = MagicMock()

    def test_insert_one_returns_inserted_record(self):
        """Test that insert_one returns the inserted record."""
        record = {"id": "123", "name": "Test"}
        mock_response = Mock()
        mock_response.data = [{"id": "123", "name": "Test", "created_at": "2024-01-01"}]
        
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = insert_one("TestTable", record)
        
        assert result == {"id": "123", "name": "Test", "created_at": "2024-01-01"}
        self.mock_client.table.assert_called_once_with("TestTable")
        self.mock_client.table.return_value.insert.assert_called_once_with(record)

    def test_insert_one_uses_correct_table(self):
        """Test that insert_one uses the correct table name."""
        record = {"data": "test"}
        mock_response = Mock()
        mock_response.data = [record]
        
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            insert_one("CustomTable", record)
        
        self.mock_client.table.assert_called_once_with("CustomTable")


class TestUpdateById:
    """Test suite for update_by_id function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = MagicMock()

    def test_update_by_id_returns_updated_record(self):
        """Test that update_by_id returns the updated record."""
        updates = {"name": "Updated"}
        mock_response = Mock()
        mock_response.data = [{"id": "123", "name": "Updated"}]
        
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = update_by_id("TestTable", "id", "123", updates)
        
        assert result == {"id": "123", "name": "Updated"}
        self.mock_client.table.assert_called_once_with("TestTable")
        self.mock_client.table.return_value.update.assert_called_once_with(updates)

    def test_update_by_id_uses_correct_id_field(self):
        """Test that update_by_id uses the correct id field."""
        updates = {"status": "active"}
        mock_response = Mock()
        mock_response.data = [{"custom_id": "abc", "status": "active"}]
        
        mock_table = self.mock_client.table.return_value
        mock_update = mock_table.update.return_value
        mock_eq = mock_update.eq.return_value
        mock_eq.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            update_by_id("TestTable", "custom_id", "abc", updates)
        
        mock_update.eq.assert_called_once_with("custom_id", "abc")

    def test_update_by_id_returns_empty_dict_when_not_found(self):
        """Test that update_by_id returns empty dict when no record found."""
        updates = {"name": "Updated"}
        mock_response = Mock()
        mock_response.data = []
        
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            result = update_by_id("TestTable", "id", "nonexistent", updates)
        
        assert result == {}


class TestLogEntityChange:
    """Test suite for log_entity_change function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = MagicMock()

    def test_log_entity_change_inserts_record(self):
        """Test that log_entity_change inserts a change record."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        change_summary = {"action": "updated", "field": "name"}
        
        with patch("src.database.get_client", return_value=self.mock_client):
            log_entity_change("Product", "prod-123", "user-456", change_summary)
        
        self.mock_client.table.assert_called_once_with("ChangeLog")
        
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        assert call_args["entity_type"] == "Product"
        assert call_args["entity_id"] == "prod-123"
        assert call_args["changed_by"] == "user-456"
        assert call_args["change_summary"] == change_summary

    def test_log_entity_change_with_different_entity_types(self):
        """Test log_entity_change with various entity types."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        entity_types = ["Claim", "Evidence", "Stage", "Mission"]
        
        with patch("src.database.get_client", return_value=self.mock_client):
            for entity_type in entity_types:
                log_entity_change(entity_type, "id-123", "user-789", {"action": "test"})
        
        # Should be called once for each entity type
        assert self.mock_client.table.return_value.insert.call_count == len(entity_types)


class TestLogClaimChange:
    """Test suite for log_claim_change function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = MagicMock()

    def test_log_claim_change_with_all_parameters(self):
        """Test log_claim_change with all parameters provided."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            log_claim_change(
                claim_id="claim-123",
                changed_by="user-456",
                action="verified",
                old_confidence="unverified",
                new_confidence="verified",
                notes="Looks good",
                old_verified=False,
                new_verified=True,
            )
        
        self.mock_client.table.assert_called_once_with("ChangeLog")
        
        # Verify the insert was called with correct structure
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        assert call_args["entity_type"] == "Claim"
        assert call_args["entity_id"] == "claim-123"
        assert call_args["changed_by"] == "user-456"
        assert call_args["change_summary"]["action"] == "verified"
        assert call_args["change_summary"]["old_confidence"] == "unverified"
        assert call_args["change_summary"]["new_confidence"] == "verified"
        assert call_args["change_summary"]["notes"] == "Looks good"
        assert call_args["change_summary"]["old_verified_status"] is False
        assert call_args["change_summary"]["new_verified_status"] is True

    def test_log_claim_change_with_minimal_parameters(self):
        """Test log_claim_change with only required parameters."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            log_claim_change(
                claim_id="claim-789",
                changed_by="user-999",
                action="updated",
            )
        
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        assert call_args["entity_type"] == "Claim"
        assert call_args["entity_id"] == "claim-789"
        assert call_args["changed_by"] == "user-999"
        assert call_args["change_summary"]["action"] == "updated"
        # Should not include optional fields
        assert "old_confidence" not in call_args["change_summary"]
        assert "notes" not in call_args["change_summary"]
        assert "old_verified_status" not in call_args["change_summary"]

    def test_log_claim_change_with_confidence_only(self):
        """Test log_claim_change with confidence change."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            log_claim_change(
                claim_id="claim-abc",
                changed_by="user-xyz",
                action="confidence_updated",
                old_confidence="uncertain",
                new_confidence="likely",
            )
        
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        assert call_args["change_summary"]["old_confidence"] == "uncertain"
        assert call_args["change_summary"]["new_confidence"] == "likely"
        assert "notes" not in call_args["change_summary"]

    def test_log_claim_change_with_notes_only(self):
        """Test log_claim_change with notes provided."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            log_claim_change(
                claim_id="claim-def",
                changed_by="user-ghi",
                action="reviewed",
                notes="Needs more evidence",
            )
        
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        assert call_args["change_summary"]["notes"] == "Needs more evidence"

    def test_log_claim_change_with_verified_status_change(self):
        """Test log_claim_change with verified status change."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            log_claim_change(
                claim_id="claim-jkl",
                changed_by="user-mno",
                action="unverified",
                old_verified=True,
                new_verified=False,
            )
        
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        assert call_args["change_summary"]["old_verified_status"] is True
        assert call_args["change_summary"]["new_verified_status"] is False

    def test_log_claim_change_with_old_verified_false(self):
        """Test log_claim_change handles old_verified=False correctly."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            log_claim_change(
                claim_id="claim-pqr",
                changed_by="user-stu",
                action="verified",
                old_verified=False,
                new_verified=True,
            )
        
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        # Should include verified status even when old_verified is False
        assert "old_verified_status" in call_args["change_summary"]
        assert call_args["change_summary"]["old_verified_status"] is False

    def test_log_claim_change_jsonb_summary_structure(self):
        """Test that log_claim_change creates correct JSONB summary structure."""
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch("src.database.get_client", return_value=self.mock_client):
            log_claim_change(
                claim_id="claim-test",
                changed_by="user-test",
                action="test_action",
                old_confidence="a",
                new_confidence="b",
                notes="test note",
                old_verified=True,
                new_verified=False,
            )
        
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        summary = call_args["change_summary"]
        
        # Verify it's a dict (will be stored as JSONB)
        assert isinstance(summary, dict)
        assert "action" in summary
        assert len(summary) == 6  # action + 5 other fields
