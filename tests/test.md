# Test Architecture Documentation

## Overview

This document outlines the test architecture that has been set up for the backend project. The test suite uses **pytest** as the testing framework and follows best practices for organizing and structuring tests.

## Test Structure

The test suite is organized to mirror the source code structure:

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_config.py              # Tests for config module
├── test_database.py            # Tests for database module
├── models/
│   ├── test_claim.py          # Tests for Claim and Evidence models
│   ├── test_product.py        # Tests for Product, Stage, and InputShare models
│   └── test_user.py           # Tests for QuestMission, UserProgress, and UserRole models
└── routers/
    └── test_products.py       # Tests for products router endpoints
```

## Test Files and Coverage

### 1. `conftest.py` - Shared Test Fixtures

Contains reusable pytest fixtures available to all test files:
- **`client`**: FastAPI TestClient for making HTTP requests to the app
- **`mock_supabase_client`**: Mock Supabase client for testing without database calls
- **`test_settings`**: Test configuration settings

### 2. `test_config.py` - Configuration Tests

**Test Classes:**
- `TestSettings`: Tests for the Settings configuration class
  - Default value initialization
  - Environment variable loading
  - Field validation for supabase_url, supabase_key, and port
  
- `TestGetSettings`: Tests for the get_settings function
  - Instance creation
  - LRU caching behavior
  - Singleton pattern verification

**Setup/Teardown:**
- Each test method clears the LRU cache to ensure test isolation

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

### 4. `test_claim.py` - Claim Model Tests

**Test Classes:**
- `TestClaim`: Tests for the Claim model
  - Valid data initialization
  - Minimal required fields
  - Optional fields (product_id, rationale)
  - Confidence label validation (verified, partially_verified, unverified)
  - Invalid confidence label rejection
  - Required field validation
  - Serialization/deserialization

- `TestEvidence`: Tests for the Evidence model
  - Valid data initialization
  - Minimal required fields
  - Optional fields (stage_id, claim_id, evidence_date, summary, file_reference)
  - Field alias testing (date → evidence_date)
  - Required field validation
  - Serialization/deserialization

**Setup/Teardown:**
- Valid test data dictionaries are created in setup_method

### 5. `test_product.py` - Product Models Tests

**Test Classes:**
- `TestProduct`: Tests for the Product model
  - Valid data initialization
  - Minimal required fields
  - Category validation (food, luxury, supplements, other)
  - Invalid category rejection
  - Optional fields (brand, description, image)
  - Required field validation
  - Serialization/deserialization

- `TestStage`: Tests for the Stage model
  - Valid data initialization
  - Minimal required fields
  - Optional fields (product_id, location fields, dates, description, sequence_order, created_at)
  - Required field validation
  - Serialization/deserialization

- `TestInputShare`: Tests for the InputShare model
  - Valid data initialization
  - Minimal required fields
  - Optional fields (product_id, percentage, notes)
  - Decimal type validation for percentage
  - Required field validation
  - Serialization/deserialization

**Setup/Teardown:**
- Valid test data dictionaries with proper types (datetime, date, Decimal) are created in setup_method

### 6. `test_user.py` - User Models Tests

**Test Classes:**
- `TestQuestMission`: Tests for the QuestMission model
  - Valid data initialization
  - Minimal required fields
  - Tier validation (basic, intermediate, advanced)
  - Grading type validation (auto, manual)
  - Optional fields (product_id, answer_key, explanation_link)
  - Invalid literal value rejection
  - Required field validation
  - Serialization/deserialization

- `TestUserProgress`: Tests for the UserProgress model
  - Valid data initialization
  - Minimal required fields
  - Default value for completed field (False)
  - Optional fields (score, attempts, completed_at)
  - Required field validation
  - Serialization/deserialization

- `TestUserRole`: Tests for the UserRole model
  - Valid data initialization
  - Minimal required fields
  - Role validation (consumer, verifier, maintainer)
  - Invalid role rejection
  - Optional fields (user_id, role)
  - Required field validation
  - Serialization/deserialization

**Setup/Teardown:**
- Valid test data dictionaries are created in setup_method

### 7. `test_products.py` - Products Router Tests

**Test Classes:**
- `TestValidateUuid`: Tests for UUID validation utility
  - Valid UUID acceptance
  - Invalid UUID rejection with HTTPException
  - Custom field name in error messages
  - Return value verification

- `TestGetProducts`: Tests for GET /products endpoint
  - List of products return
  - Empty database handling
  - select_all function call verification
  - 200 status code
  - Response structure validation

- `TestGetProduct`: Tests for GET /products/{product_id} endpoint
  - Valid ID product retrieval
  - 400 status for invalid UUID
  - 404 status for not found
  - select_by_id function call verification
  - 200 status code
  - Response structure validation

- `TestGetProductTraceability`: Tests for GET /products/{product_id}/traceability endpoint
  - Valid ID traceability retrieval
  - 400 status for invalid UUID
  - 404 status for product not found
  - Stages inclusion and sorting by sequence_order
  - Input shares inclusion
  - Claims with evidence inclusion
  - 200 status code
  - ProductTraceability schema validation
  - Empty claims/stages/input_shares handling

- `TestClaimWithEvidence`: Tests for ClaimWithEvidence model
  - Initialization
  - Serialization

- `TestProductTraceability`: Tests for ProductTraceability model
  - Initialization
  - Serialization

**Setup/Teardown:**
- TestClient instance is created in setup_method for API testing

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

## Next Steps for Implementation

For each test marked with `# TODO: Implement test`, you should:

1. **Arrange**: Set up the test data and mocks
2. **Act**: Execute the code being tested
3. **Assert**: Verify the expected behavior using pytest assertions

## Running Tests

To run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run specific test class
pytest tests/test_config.py::TestSettings

# Run specific test method
pytest tests/test_config.py::TestSettings::test_settings_initialization_with_defaults

# Run with coverage
pytest --cov=src tests/

# Run with verbose output
pytest -v
```

