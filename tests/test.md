# Test Architecture Documentation

## Overview

This document outlines the test architecture that has been set up for the backend project. The test suite uses pytest as the testing framework and follows best practices for organizing and structuring tests.


### Test Results Summary (Last Run: Mar 24, 2026)

Environment: Windows, Python 3.12, pytest 8.x (local run).

```
407 collected | 407 passed | ~4.2s
```

To reproduce: `pytest tests/routers/test_missions.py tests/routers/test_missions_schemas.py -v`

### Fully implemented features (green on last run)
- **Model Validation Tests** — Pydantic models (`tests/models/`)
- **Product Router Tests** — Endpoints including traceability, missions listing on products, evidence, stages, verify/unverify/confidence, verification history, validation errors (`test_products.py` / `test_products_schemas.py`)
- **Issues Router Tests** — Parametrised `IssueCreate.type` literals; current handling of non-UUID `product_id` (`test_issues.py` / `test_issues_schemas.py`)
- **Auth** — `src.auth` helpers and router guards (`test_auth.py`, `routers/test_auth.py`)
- **Users Router** — `GET /users/me/role` (`routers/test_users.py`)
- **Database Operations** — Database helper layer (`test_database.py`)
- **Configuration** — Settings env-file behaviour and FRONTEND_URL-only scenario (`test_config.py`)
- **App wiring & CLI** — Lifespan, CORS, route mounts (`test_main_app.py`), `run.main`, `scripts/demo` smoke (`test_run.py`, `test_scripts_demo.py`)
- **Test infrastructure** — Shared fixtures and isolation (`conftest.py`, `test_conftest.py`); suite hygiene (e.g. DB fixture naming)

## Test Structure

The test suite is organized to mirror the source code structure:

```
tests/
├── conftest.py
├── test_auth.py
├── test_config.py
├── test_conftest.py
├── test_database.py
├── test_main_app.py
├── test_run.py
├── test_scripts_demo.py
├── models/
│   ├── test_claim.py
│   ├── test_issue.py
│   ├── test_product.py
│   └── test_user.py
└── routers/
    ├── test_auth.py
    ├── test_issues.py
    ├── test_issues_schemas.py
    ├── test_missions.py
    ├── test_missions_schemas.py
    ├── test_products.py
    ├── test_products_schemas.py
    └── test_users.py
```

## Test Files and Coverage

### 1. `conftest.py` - Shared Test Fixtures

Contains reusable pytest fixtures available to all test files:
- **`client`**: FastAPI Test client for making HTTP requests
- **`mock_supabase_client`**: Mock Supabase client for testing without database calls
- **`test_settings`**: Test configuration settings

**Tests for conftest.py** (13 tests in `test_conftest.py`):
- Client fixture creation and functionality
- Real settings loaded from .env file
- Environment file existence validation
- Mock Supabase client behavior
- Test settings isolation from production environment
- Fixture independence verification

### 2. `test_config.py` - Configuration Tests

**Test Classes:**
- `TestSettings`: Tests for the Settings configuration class
  - Default value initialisation
  - Environment variable loading
  - Field validation for supabase_url, supabase_key, and port
  
- `TestGetSettings`: Tests for the get_settings function
  - Instance creation
  - LRU caching behavior
  - Singleton pattern verification

### 3. `test_database.py` - Database Module Tests

**Test Classes:**
- `TestGetClient`: Tests for Supabase client creation
  - Client instance creation
  - Settings usage
  - Cache verification

- `TestSelectAll`: Tests for selecting all records
  - Model list returns
  - Table name resolution
  - Empty response handling
  - Data validation

- `TestSelectById`: Tests for selecting by ID
  - Single record retrieval
  - Not found scenarios (returns None)
  - ID field parameter usage
  - Model validation

- `TestSelectByField`: Tests for field-based filtering
  - Multiple record retrieval
  - Field and value filtering
  - Empty results handling
  - Data validation

- `TestUpsertBatch`: Tests for batch upsert operations
  - Empty records handling
  - Batch size boundaries
  - Multiple batch processing
  - Table name usage
  - Return count verification
  - Custom batch size

### 3a. `test_auth.py` - Authentication Module Tests

Unit tests for authentication helpers in `src.auth`, including extracting user IDs from `Authorization: Bearer ...`,
resolving user roles, and verifier/role-guard logic.

### 3b. `test_main_app.py` - FastAPI App Wiring Tests

Verifies application wiring:
- lifespan startup calls the database client initializer (`get_client`)
- CORS middleware is registered with `allow_origins` matching `settings.frontend_url`
- routers are mounted on expected path prefixes (`/products`, `/missions`, `/users`, `/issues`)

### 3c. `test_run.py` - CLI Entrypoint Tests

Checks `run.main()` calls `uvicorn.run()` with the correct app import path and the port sourced from `get_settings()`.

### 3d. `test_scripts_demo.py` - Demo Script Smoke Tests

Validates that `scripts/demo.py` loads the demo module and calls `select_all()` for each supported model,
printing expected headings for non-empty and empty results.

### 4. `test_claim.py` - Claim Model Tests

**Test Classes:**
- `TestClaim`: Tests for the Claim model
  - Valid data initialisation
  - Minimal required fields
  - Optional fields (product_id, rationale)
  - Confidence label validation (verified, partially_verified, unverified)
  - Invalid confidence label rejection
  - Required field validation
  - Serialisation/deserialisation

- `TestEvidence`: Tests for the Evidence model
  - Valid data initialisation
  - Minimal required fields
  - Optional fields (stage_id, claim_id, evidence_date, summary, file_reference)
  - Field alias testing (date → evidence_date)
  - Required field validation
  - Serialisation/deserialisation

### 4a. `test_issue.py` - Issue Report and ChangeLog Model Tests

**Test Classes:**
- `TestIssueReport`: Tests for the IssueReport model 
  - Valid data initialisation
  - Minimal required fields
  - Status default value ("open")
  - Type validation (bug, feature_request, data_quality, other)
  - Status validation (open, in_progress, resolved, closed)
  - Invalid literal value rejection
  - Optional fields (product_id, reported_by, resolution_note, updated_at)
  - Required field validation for all fields
  - Serialisation/deserialisation
  - Resolution handling

- `TestChangeLog`: Tests for the ChangeLog model 
  - Valid data initialisation
  - Minimal required fields
  - Entity type validation (product, claim, evidence, issue, user)
  - Invalid entity type rejection
  - Optional fields (changed_by)
  - Required field validation for all fields
  - Serialisation/deserialisation
  - Timestamp handling

### 5. `test_product.py` - Product Models Tests

**Test Classes:**
- `TestProduct`: Tests for the Product model
  - Valid data initialisation
  - Minimal required fields
  - Category validation (food, luxury, supplements, other)
  - Invalid category rejection
  - Optional fields (brand, description, image)
  - Required field validation
  - Serialisation/deserialisation

- `TestStage`: Tests for the Stage model
  - Valid data initialisation
  - Minimal required fields
  - Optional fields (product_id, location fields, dates, description, sequence_order, created_at)
  - Required field validation
  - Serialisation/deserialisation

- `TestInputShare`: Tests for the InputShare model
  - Valid data initialisation
  - Minimal required fields
  - Optional fields (product_id, percentage, notes)
  - Decimal type validation for percentage
  - Required field validation
  - Serialisation/deserialisation
### 6. `test_user.py` - User Models Tests

**Test Classes:**
- `TestQuestMission`: Tests for the QuestMission model
  - Valid data initialisation
  - Minimal required fields
  - Tier validation (basic, intermediate, advanced)
  - Grading type validation (auto, manual)
  - Optional fields (product_id, answer_key, explanation_link)
  - Invalid literal value rejection
  - Required field validation
  - Serialisation/deserialisation

- `TestUserProgress`: Tests for the UserProgress model
  - Valid data initialisation
  - Minimal required fields
  - Default value for completed field (False)
  - Optional fields (score, attempts, completed_at)
  - Required field validation
  - Serialisation/deserialisation

- `TestUserRole`: Tests for the UserRole model
  - Valid data initialisation
  - Minimal required fields
  - Role validation (consumer, verifier, maintainer)
  - Invalid role rejection
  - Optional fields (user_id, role)
  - Required field validation
  - Serialisation/deserialisation

### 6a. `routers/test_auth.py` - Role Guard Dependency Tests

Mounts a minimal FastAPI app to verify that verifier and maintainer guards accept/reject based on the returned `UserRole`.

### 6b. `routers/test_users.py` - Users Router Tests

Validates `GET /users/me/role` resolves to `consumer` when no stored role exists,
and returns the assigned role when present.

### 6c. `routers/test_issues.py` - Issues Router Tests

Covers issues creation (`POST /issues`) including `IssueCreate.type` literal handling and current UUID validation policy,
plus list/update behavior protected by verifier permissions.

### 6d. `routers/test_missions.py` - Missions Router Tests

Targets mission **attempt** endpoints: UUID validation, answer normalisation, comparison against mission `options`, HTTP status branches (404/400/422/500 where mocked), and direct unit-style calls. **Status:** suite is in place but **was failing** on the last full run (see summary above); fix by aligning implementation with tests or updating mocks/expectations after API changes.

### 6e. `routers/test_*_schemas.py` - Schema Unit Tests

Pure request/response schema validation for:
- products/stages/claims/evidence (`test_products_schemas.py`)
- issues (`test_issues_schemas.py`)
- missions attempt input/output (`test_missions_schemas.py`) — **`MissionAttemptOut` cases were failing** on the last run; confirm schema fields and `model_dump` shape match the router responses.

### 7. `test_products.py` - Products Router Tests

This suite covers the full products API surface exercised in the codebase:
endpoint UUID validation, traceability, missions listing, evidence drill-down,
stage/claim/evidence creation, claim verification (`verify`/`unverify`) and confidence updates,
and verification history branching.

**Test Classes:**

#### `TestValidateUuid`: Tests for UUID validation utility (6 tests - COMPLETE)
The UUID validator is a critical component for the product ID search feature, ensuring that only valid UUID formats reach the database layer.

- **`test_validate_uuid_with_valid_uuid`**: Validates that standard UUID format is accepted
- **`test_validate_uuid_with_valid_uuid_different_format`**: Tests multiple valid UUID variations including edge cases (all zeros, all F's, mixed case)
- **`test_validate_uuid_with_invalid_uuid`**: Ensures invalid UUIDs raise HTTPException with 400 status
- **`test_validate_uuid_with_invalid_uuid_formats`**: Comprehensive testing of various invalid formats:
  - Too short UUIDs
  - Too long UUIDs
  - Missing hyphens
  - Invalid characters
  - Empty strings
  - Malformed strings
- **`test_validate_uuid_with_custom_field_name`**: Verifies custom field names appear in error messages for better debugging
- **`test_validate_uuid_returns_value_on_success`**: Confirms the validator returns the original value when valid

#### `TestGetProducts`: Tests for GET /products endpoint (5 tests - COMPLETE)
- List of products return
- Empty database handling
- select_all function call verification
- 200 status code
- Response structure validation

#### `TestGetProduct`: **PRODUCT ID SEARCH FEATURE** (14 tests - COMPLETE) 

This is the core test suite for the product ID search functionality that allows users to search for products by entering a product ID. **All tests are fully implemented with comprehensive coverage.**

**Feature Coverage:**

1. **Basic Product Search by ID:**
   - **`test_get_product_with_valid_id`**: Tests successful product retrieval with valid UUID
     - Mocks database response
     - Verifies 200 status code
     - Confirms correct product data returned
     - Validates database call with correct parameters
   
   - **`test_get_product_search_by_id_returns_correct_product`**: Deep validation of returned product data
     - Verifies all product fields are correctly returned
     - Checks product_id, name, category, brand, description, image
     - Ensures data integrity throughout the request/response cycle

2. **UUID Validation in Search:**
   - **`test_get_product_with_invalid_uuid`**: Tests multiple invalid UUID formats
     - Tests: "invalid-uuid", "12345", "not-a-uuid-at-all", truncated UUIDs, empty strings
     - Verifies 400 status code for all invalid formats
     - Confirms error message contains "Invalid product_id format"
   
   - **`test_get_product_validates_uuid_before_database_query`**: Security and performance test
     - Ensures UUID validation occurs before database access
     - Verifies database is never queried with invalid UUIDs
     - Prevents unnecessary database load from malformed requests

3. **Product Not Found Handling:**
   - **`test_get_product_not_found`**: Tests 404 response for non-existent products
     - Mocks database returning None
     - Verifies 404 status code
     - Confirms "Product not found" error message
     - Validates database was queried with correct ID

4. **Database Interaction Testing:**
   - **`test_get_product_calls_select_by_id`**: Verifies correct database function usage
     - Confirms select_by_id is called with Product model
     - Validates "product_id" field name parameter
     - Ensures correct UUID is passed to database layer
   
   - **`test_get_product_search_performance_single_query`**: Performance validation
     - Confirms only one database query per search
     - Prevents N+1 query problems
     - Ensures efficient database usage

5. **Multiple Product Search Testing:**
   - **`test_get_product_with_different_valid_uuids`**: Tests search with multiple products
     - Tests three different valid UUIDs
     - Verifies each returns correct product
     - Ensures search works consistently across different IDs

6. **Edge Cases and Data Variations:**
   - **`test_get_product_with_minimal_data`**: Tests products with minimal/optional fields
     - Validates search works with products having only required fields
     - Confirms null values are properly handled (brand, description, image)
     - Ensures robustness with incomplete data
   
   - **`test_get_product_case_sensitive_uuid_search`**: UUID case handling
     - Tests both lowercase and uppercase UUIDs
     - Verifies case-insensitive UUID handling
     - Ensures consistent behavior regardless of input case

7. **Response Structure Validation:**
   - **`test_get_product_response_structure`**: Comprehensive response validation
     - Verifies all expected fields are present in response
     - Checks: product_id, name, category, brand, description, image, created_at, updated_at
     - Ensures API contract compliance

8. **Error Handling:**
   - **`test_get_product_handles_database_errors_gracefully`**: Database error scenarios
     - Tests behavior when database connection fails
     - Ensures exceptions are properly propagated
     - Validates error handling robustness

**Test Fixtures:**
- Mock Product with full data including all optional fields
- Valid UUID constant (550e8400-e29b-41d4-a716-446655440000)
- TestClient instance for HTTP request simulation

**Mocking Strategy:**
- `@patch("src.routers.products.select_by_id")` for database isolation
- Mock responses configured per test case
- Call verification to ensure correct database interactions

#### `TestGetProductTraceability`: Tests for GET /products/{product_id}/traceability endpoint (13 tests - COMPLETE)
- Valid ID traceability retrieval
- 400 status for invalid UUID
- 404 status for product not found
- Stages inclusion and sorting by sequence_order
- Input shares inclusion
- Claims with evidence inclusion
- 200 status code
- ProductTraceability schema validation
- Empty claims/stages/input_shares handling

#### `TestClaimWithEvidence`: Tests for ClaimWithEvidence model (2 tests - COMPLETE)
- initialisation
- Serialisation

#### `TestProductTraceability`: Tests for ProductTraceability model (2 tests - COMPLETE)
- initialisation
- Serialisation

## Testing Patterns Used

### 1. **Class-Based Organization**
Tests are organized into classes that group related functionality, making tests easier to understand and maintain.

### 2. **Setup and Teardown Methods**
- `setup_method()`: Runs before each test method to set up test fixtures
- `teardown_method()`: Runs after each test method to clean up resources (e.g., clearing caches)

### 3. **Descriptive Test Names**
All test methods follow the naming pattern: `test_<component>_<scenario>` with clear docstrings explaining what is being tested.

### 4. **Test Data Fixtures**
Valid test data is created in `setup_method()` to be reused across tests, reducing duplication.

### 5. **Mocking Strategy**
- Uses `unittest.mock` for mocking Supabase clients and external dependencies
- Shared mock fixtures defined in `conftest.py`

### 6. **Validation Testing**
Tests cover:
- Valid data scenarios
- Invalid data rejection
- Optional vs required fields
- Type validation (Literal types, Decimal, dates)
- Edge cases (empty lists, None values)

## Product ID Search Feature - Testing Summary

### Feature Description
The product ID search feature allows users to enter a product UUID and retrieve the corresponding product from the database. This is implemented via the `GET /products/{product_id}` endpoint.

### Quality Assurance
The extensive test suite ensures:
1. **Reliability**: All happy path and error scenarios are covered
2. **Security**: Invalid inputs are rejected before reaching the database
3. **Performance**: Single query per request is verified
4. **Robustness**: Edge cases and error conditions are handled
5. **Maintainability**: Well-structured tests with clear documentation

## Running Tests

To run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run all tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_config.py -v
pytest tests/models/test_issue.py -v

# Run specific test class
pytest tests/test_config.py::TestSettings -v

# Run specific test method
pytest tests/test_config.py::TestSettings::test_settings_initialisation_with_defaults -v

# Run all model tests
pytest tests/models/ -v

# Run all router tests
pytest tests/routers/ -v

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Run with verbose output and show local variables on failure
pytest tests/ -vv -l
```


## Test Configuration

Test configuration is managed through:
- **`pytest.ini`**: pytest configuration settings in the project root
- **`.env`**: Environment variables for Supabase connection (not in version control)
- **`.env.example`**: Template for required environment variables
- **`conftest.py`**: Shared fixtures and test setup

### Environment Setup
Before running tests, ensure you have a `.env` file with:
```
SUPABASE_URL=your-project-url
SUPABASE_KEY=your-anon-key
PORT=8000
```

## Best Practices Followed

1. ** Test Isolation**: Each test is independent and doesn't rely on other tests
2. ** Mock External Dependencies**: Mocks for database calls, API requests, etc.
3. ** Clear Assertions**: Descriptive assertion messages and clear test names
4. ** High Coverage**: code coverage on models and core business logic
5. ** Edge Cases**: Boundary conditions, empty inputs, and error scenarios tested
6. ** DRY Principle**: Fixtures and helper functions used to avoid duplication
7. ** Comprehensive Documentation**: All tests documented with clear descriptions
8. ** CI/CD Integration**: Automated testing in GitHub Actions workflow

## CI/CD Integration

The test suite is integrated into the GitHub Actions CI/CD pipeline:

```yaml
# Tests run on every push and pull request
- Model tests with coverage reporting
- Router tests with endpoint validation  
- Database tests with mock client
- Configuration tests with environment validation
- Code formatting and linting checks
- Type checking with mypy


#### Test Scenarios

**good Path:**
```python
# Valid UUID  Returns product with 200 status
test_get_product_with_valid_id
test_get_product_search_by_id_returns_correct_product
```

**Error Scenarios:**
```python
# Invalid UUID  400 Bad Request
test_get_product_with_invalid_uuid
test_get_product_validates_uuid_before_database_query

# Product not found  404 Not Found
test_get_product_not_found
```

**Edge Cases:**
```python
# Products with minimal data
test_get_product_with_minimal_data

# Case insensitive UUID handling
test_get_product_case_sensitive_uuid_search

# Multiple different products
test_get_product_with_different_valid_uuids
```

### Debugging Failed Tests

If tests fail, use these commands for detailed debugging:

```bash
# Show detailed output including print statements
pytest tests/routers/test_products.py::TestGetProduct -v -s

# Show local variables on failure
pytest tests/routers/test_products.py::TestGetProduct -v -l

# Drop into debugger on failure
pytest tests/routers/test_products.py::TestGetProduct -v --pdb

# Show detailed traceback
pytest tests/routers/test_products.py::TestGetProduct -v --tb=long
```