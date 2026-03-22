from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.auth import get_current_user_role, require_maintainer, require_verifier
from src.models.user import UserRole

# test minimal backend 
def create_test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/verifier-only")
    async def verifier_only(_role: UserRole = Depends(require_verifier)):
        return {"status": "ok"}

    @app.get("/maintainer-only")
    async def maintainer_only(_role: UserRole = Depends(require_maintainer)):
        return {"status": "ok"}

    return app


class TestRoleGuards:
    def setup_method(self):
        self.app = create_test_app()
        self.client = TestClient(self.app)

    def teardown_method(self):
        self.app.dependency_overrides.clear()

    def test_verifier_route_rejects_default_consumer(self):
        # No stored role should behave like the default consumer role
        async def override_user_role():
            return None

        self.app.dependency_overrides[get_current_user_role] = override_user_role

        response = self.client.get("/verifier-only")

        assert response.status_code == 403

    def test_maintainer_route_allows_maintainer(self):
        # Maintainers should pass routes protected with the maintainer guard
        async def override_user_role():
            return UserRole(
                role_id="660e8400-e29b-41d4-a716-446655440000",
                user_id="550e8400-e29b-41d4-a716-446655440000",
                role="maintainer",
                created_at=datetime.now(),
            )

        self.app.dependency_overrides[get_current_user_role] = override_user_role

        response = self.client.get("/maintainer-only")

        assert response.status_code == 200
