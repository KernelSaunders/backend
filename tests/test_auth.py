"""Tests for authentication module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi import HTTPException

from src.auth import get_current_user_id, get_current_user_role, require_verifier
from src.models.user import UserRole


class TestGetCurrentUserId:
    """Test suite for get_current_user_id function."""

    @pytest.mark.asyncio
    async def test_get_current_user_id_with_valid_token(self):
        """Test successful user ID extraction with valid Bearer token."""
        mock_user = Mock()
        mock_user.id = "test-user-id-123"
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = mock_user_response
        
        with patch("src.auth.get_client", return_value=mock_client):
            result = await get_current_user_id("Bearer valid-token-xyz")
        
        assert result == "test-user-id-123"
        mock_client.auth.get_user.assert_called_once_with("valid-token-xyz")

    @pytest.mark.asyncio
    async def test_get_current_user_id_without_bearer_prefix(self):
        """Test that missing 'Bearer ' prefix raises 401 HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id("InvalidFormat token-123")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid auth header"

    @pytest.mark.asyncio
    async def test_get_current_user_id_with_empty_authorization(self):
        """Test that empty authorization header raises 401 HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id("")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid auth header"

    @pytest.mark.asyncio
    async def test_get_current_user_id_with_bearer_only(self):
        """Test that 'Bearer ' without token raises 401 HTTPException."""
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = Exception("Invalid token")
        
        with patch("src.auth.get_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_id("Bearer ")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_get_current_user_id_with_invalid_token(self):
        """Test that invalid token raises 401 HTTPException."""
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = Exception("Token validation failed")
        
        with patch("src.auth.get_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_id("Bearer invalid-token")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
        mock_client.auth.get_user.assert_called_once_with("invalid-token")

    @pytest.mark.asyncio
    async def test_get_current_user_id_when_user_is_none(self):
        """Test that None user from Supabase raises 401 HTTPException."""
        mock_user_response = Mock()
        mock_user_response.user = None
        
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = mock_user_response
        
        with patch("src.auth.get_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_id("Bearer valid-but-no-user-token")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_get_current_user_id_with_expired_token(self):
        """Test that expired token raises 401 HTTPException."""
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = Exception("Token expired")
        
        with patch("src.auth.get_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_id("Bearer expired-token")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_get_current_user_id_with_malformed_token(self):
        """Test that malformed token raises 401 HTTPException."""
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = Exception("Malformed token")
        
        with patch("src.auth.get_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_id("Bearer malformed.token.xyz")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_get_current_user_id_token_extraction(self):
        """Test that Bearer prefix is correctly removed from token."""
        mock_user = Mock()
        mock_user.id = "user-abc-123"
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = mock_user_response
        
        with patch("src.auth.get_client", return_value=mock_client):
            await get_current_user_id("Bearer my-actual-token-string")
        
        # Verify the token passed to get_user does not include "Bearer "
        mock_client.auth.get_user.assert_called_once_with("my-actual-token-string")


class TestGetCurrentUserRole:
    """Test suite for get_current_user_role function."""

    @pytest.mark.asyncio
    async def test_get_current_user_role_with_verifier_role(self):
        """Test user with verifier role returns UserRole object."""
        from datetime import datetime
        
        mock_role = UserRole(
            role_id="role-123",
            user_id="user-123",
            role="verifier",
            created_at=datetime.now()
        )
        
        with patch("src.auth.select_by_field", return_value=[mock_role]):
            result = await get_current_user_role("user-123")
        
        assert result is not None
        assert result.role == "verifier"
        assert result.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_get_current_user_role_with_consumer_role(self):
        """Test user with consumer role returns UserRole object."""
        from datetime import datetime
        
        mock_role = UserRole(
            role_id="role-456",
            user_id="user-456",
            role="consumer",
            created_at=datetime.now()
        )
        
        with patch("src.auth.select_by_field", return_value=[mock_role]):
            result = await get_current_user_role("user-456")
        
        assert result is not None
        assert result.role == "consumer"
        assert result.user_id == "user-456"

    @pytest.mark.asyncio
    async def test_get_current_user_role_with_maintainer_role(self):
        """Test user with maintainer role returns UserRole object."""
        from datetime import datetime
        
        mock_role = UserRole(
            role_id="role-789",
            user_id="user-789",
            role="maintainer",
            created_at=datetime.now()
        )
        
        with patch("src.auth.select_by_field", return_value=[mock_role]):
            result = await get_current_user_role("user-789")
        
        assert result is not None
        assert result.role == "maintainer"
        assert result.user_id == "user-789"

    @pytest.mark.asyncio
    async def test_get_current_user_role_with_no_role(self):
        """Test user with no role returns None."""
        with patch("src.auth.select_by_field", return_value=None):
            result = await get_current_user_role("user-no-role")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_role_with_empty_roles_list(self):
        """Test user with empty roles list returns None."""
        with patch("src.auth.select_by_field", return_value=[]):
            result = await get_current_user_role("user-empty-roles")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_role_selects_first_role(self):
        """Test that first role is returned when user has multiple roles."""
        from datetime import datetime
        
        mock_role_1 = UserRole(
            role_id="role-1",
            user_id="user-multi",
            role="verifier",
            created_at=datetime.now()
        )
        mock_role_2 = UserRole(
            role_id="role-2",
            user_id="user-multi",
            role="consumer",
            created_at=datetime.now()
        )
        
        with patch("src.auth.select_by_field", return_value=[mock_role_1, mock_role_2]):
            result = await get_current_user_role("user-multi")
        
        assert result is not None
        assert result.role == "verifier"
        assert result.role_id == "role-1"

    @pytest.mark.asyncio
    async def test_get_current_user_role_calls_select_by_field_correctly(self):
        """Test that select_by_field is called with correct parameters."""
        with patch("src.auth.select_by_field", return_value=None) as mock_select:
            await get_current_user_role("test-user-id")
        
        mock_select.assert_called_once_with(UserRole, "user_id", "test-user-id")


class TestRequireVerifier:
    """Test suite for require_verifier function."""

    @pytest.mark.asyncio
    async def test_require_verifier_with_verifier_role(self):
        """Test that verifier role passes authorization."""
        from datetime import datetime
        
        mock_role = UserRole(
            role_id="role-123",
            user_id="user-123",
            role="verifier",
            created_at=datetime.now()
        )
        
        result = await require_verifier(mock_role)
        
        assert result == mock_role
        assert result.role == "verifier"

    @pytest.mark.asyncio
    async def test_require_verifier_with_consumer_role(self):
        """Test that consumer role raises 403 HTTPException."""
        from datetime import datetime
        
        mock_role = UserRole(
            role_id="role-456",
            user_id="user-456",
            role="consumer",
            created_at=datetime.now()
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await require_verifier(mock_role)
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access forbidden: verifier role required"

    @pytest.mark.asyncio
    async def test_require_verifier_with_maintainer_role(self):
        """Test that maintainer role raises 403 HTTPException."""
        from datetime import datetime
        
        mock_role = UserRole(
            role_id="role-789",
            user_id="user-789",
            role="maintainer",
            created_at=datetime.now()
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await require_verifier(mock_role)
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access forbidden: verifier role required"

    @pytest.mark.asyncio
    async def test_require_verifier_with_none_role(self):
        """Test that None role raises 403 HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            await require_verifier(None)
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access forbidden: verifier role required"

    @pytest.mark.asyncio
    async def test_require_verifier_returns_role_object(self):
        """Test that require_verifier returns the UserRole object on success."""
        from datetime import datetime
        
        mock_role = UserRole(
            role_id="role-999",
            user_id="user-999",
            role="verifier",
            created_at=datetime.now()
        )
        
        result = await require_verifier(mock_role)
        
        assert isinstance(result, UserRole)
        assert result.role_id == "role-999"
        assert result.user_id == "user-999"
        assert result.role == "verifier"


class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""

    @pytest.mark.asyncio
    async def test_full_authentication_flow_for_verifier(self):
        """Test complete authentication flow from token to verifier role."""
        from datetime import datetime
        
        # Mock user extraction
        mock_user = Mock()
        mock_user.id = "user-verifier-123"
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = mock_user_response
        
        # Mock role retrieval
        mock_role = UserRole(
            role_id="role-v-123",
            user_id="user-verifier-123",
            role="verifier",
            created_at=datetime.now()
        )
        
        with patch("src.auth.get_client", return_value=mock_client):
            with patch("src.auth.select_by_field", return_value=[mock_role]):
                # Step 1: Get user ID from token
                user_id = await get_current_user_id("Bearer valid-token")
                assert user_id == "user-verifier-123"
                
                # Step 2: Get user role
                role = await get_current_user_role(user_id)
                assert role is not None
                assert role.role == "verifier"
                
                # Step 3: Verify user has verifier role
                verified_role = await require_verifier(role)
                assert verified_role.role == "verifier"

    @pytest.mark.asyncio
    async def test_full_authentication_flow_for_consumer_blocked(self):
        """Test that consumer is blocked from verifier-only endpoints."""
        from datetime import datetime
        
        # Mock user extraction
        mock_user = Mock()
        mock_user.id = "user-consumer-456"
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = mock_user_response
        
        # Mock role retrieval
        mock_role = UserRole(
            role_id="role-c-456",
            user_id="user-consumer-456",
            role="consumer",
            created_at=datetime.now()
        )
        
        with patch("src.auth.get_client", return_value=mock_client):
            with patch("src.auth.select_by_field", return_value=[mock_role]):
                # Step 1: Get user ID from token
                user_id = await get_current_user_id("Bearer valid-token")
                assert user_id == "user-consumer-456"
                
                # Step 2: Get user role
                role = await get_current_user_role(user_id)
                assert role is not None
                assert role.role == "consumer"
                
                # Step 3: Verify user is blocked from verifier-only access
                with pytest.raises(HTTPException) as exc_info:
                    await require_verifier(role)
                
                assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_full_authentication_flow_for_user_without_role(self):
        """Test that user without role is blocked from verifier-only endpoints."""
        from datetime import datetime
        
        # Mock user extraction
        mock_user = Mock()
        mock_user.id = "user-norole-789"
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = mock_user_response
        
        with patch("src.auth.get_client", return_value=mock_client):
            with patch("src.auth.select_by_field", return_value=None):
                # Step 1: Get user ID from token
                user_id = await get_current_user_id("Bearer valid-token")
                assert user_id == "user-norole-789"
                
                # Step 2: Get user role (returns None)
                role = await get_current_user_role(user_id)
                assert role is None
                
                # Step 3: Verify user is blocked from verifier-only access
                with pytest.raises(HTTPException) as exc_info:
                    await require_verifier(role)
                
                assert exc_info.value.status_code == 403
