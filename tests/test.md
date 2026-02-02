# Test Architecture Documentation

## Overview

This document outlines the test architecture that has been set up for the backend project. The test suite uses **pytest** as the testing framework and follows best practices for organizing and structuring tests.

## mplementation Status

| Test File | Total Tests | Implemented | Status |
|-----------|-------------|-------------|---------|
| `test_config.py` | 13 | 0 |  Placeholder |
| `test_database.py` | 24 | 0 |  Placeholder |
| `test_claim.py` | 22 | 0 |  Placeholder |
| `test_product.py` | 30 | 0 |  Placeholder |
| `test_user.py` | 27 | 0 |  Placeholder |
| `test_products.py` | 41 | 19 |  46% Complete |
| **Total** | **157** | **19** | **12% Complete** |

### Fully Implemented Features 
- **Product ID Search Feature** (13 tests) - Complete end-to-end testing
- **UUID Validation Utility** (6 tests) - Comprehensive format validation

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

#### `TestValidateUuid`: Tests for UUID validation utility (6 tests)
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

#### `TestGetProducts`: Tests for GET /products endpoint (5 tests)
- List of products return
- Empty database handling
- select_all function call verification
- 200 status code
- Response structure validation

#### `TestGetProduct`: **PRODUCT ID SEARCH FEATURE** (13 tests) 

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

#### `TestGetProductTraceability`: Tests for GET /products/{product_id}/traceability endpoint (13 tests) - PLACEHOLDER
- Valid ID traceability retrieval
- 400 status for invalid UUID
- 404 status for product not found
- Stages inclusion and sorting by sequence_order
- Input shares inclusion
- Claims with evidence inclusion
- 200 status code
- ProductTraceability schema validation
- Empty claims/stages/input_shares handling

#### `TestClaimWithEvidence`: Tests for ClaimWithEvidence model (2 tests) - PLACEHOLDER
- Initialization
- Serialization

#### `TestProductTraceability`: Tests for ProductTraceability model (2 tests) - PLACEHOLDER
- Initialization
- Serialization

**Setup/Teardown:**
- TestClient instance is created in setup_method for API testing
- Mock fixtures configured per test class

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

### Completed Tests
The following test suites are **fully implemented and ready to run**:

1. **`TestValidateUuid`** (6 tests) - UUID validation for product searches
2. **`TestGetProduct`** (13 tests) - Complete product ID search feature testing

### Tests Requiring Implementation
For each test marked with `# TODO: Implement test`, you should:

1. **Arrange**: Set up the test data and mocks
2. **Act**: Execute the code being tested
3. **Assert**: Verify the expected behavior using pytest assertions

### Example Test Implementation Pattern:
all router tests
pytest tests/routers/

# Run only product ID search tests
pytest tests/routers/test_products.py::TestGetProduct -v

# Run UUID validation tests
pytest tests/routers/test_products.py::TestValidateUuid -v

# Run specific test method
pytest tests/routers/test_products.py::TestGetProduct::test_get_product_with_valid_id -v

# Run with coverage for product search feature
pytest --cov=src.routers.products tests/routers/test_products.py

# Run with detailed output
pytest tests/routers/test_products.py -v -s

# Run and stop on first failure
pytest tests/routers/test_products.py -x
```

### Running Product Search Tests with Coverage Report

```bash
# Generate HTML coverage report for product router
pytest --cov=src.routers.products --cov-report=html tests/routers/test_products.py

# View coverage in terminal
pytest --cov=src.routers.products --cov-report=term-missing tests/routers/test_products.py

## Product ID Search Feature - Testing Summary

### Feature Description
The product ID search feature allows users to enter a product UUID and retrieve the corresponding product from the database. This is implemented via the `GET /products/{product_id}` endpoint.

### Test Coverage Statistics
- **Total Tests**: 19 (6 UUID validation + 13 product search)
- **Implementation Status**: 100% complete
- **Key Areas Covered**:
  - UUID format validation (valid and invalid formats)
  - Successful product retrieval
  - Product not found scenarios
  - Database interaction verification
  - Response structure validation
  - Edge cases (minimal data, case sensitivity)
  - Error handling (database errors, malformed inputs)
  - Performance (single query verification)
  - Security (validation before database access)

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


## Test Configuration

The `pytest.ini` file in the project root contains pytest configuration settings.

## Best Practices to Follow

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Mock External Dependencies**: Use mocks for database calls, API requests, etc.
3. **Clear Assertions**: Use descriptive assertion messages when needed
4. **Coverage**: Aim for high code coverage, especially for critical business logic
5. **Edge Cases**: Test boundary conditions, empty inputs, and error scenarios
6. **DRY Principle**: Use fixtures and helper functions to avoid duplication

## Notes

- Product ID search tests are fully implemented and ready to run
- Mock objects are set up in fixtures but need to be configured in individual tests (except product search)
- Consider adding integration tests that use a test database
- Consider adding parametrized tests for testing multiple similar scenarios

---

##  Quick Reference Guide

### Product ID Search Feature Tests

#### Running the Tests
```bash
# Run all product search tests
pytest tests/routers/test_products.py::TestGetProduct -v

# Run a specific test
pytest tests/routers/test_products.py::TestGetProduct::test_get_product_with_valid_id -v

# Run with coverage
pytest --cov=src.routers.products --cov-report=term-missing tests/routers/test_products.py::TestGetProduct
```

#### Test Categories

| Category | Test Count | Purpose |
|----------|-----------|---------|
| UUID Validation | 6 | Ensure only valid UUIDs reach database |
| Basic Search | 2 | Test successful product retrieval |
| Error Handling | 3 | Test 400/404 responses |
| Database Integration | 2 | Verify correct database calls |
| Edge Cases | 3 | Test minimal data, case sensitivity |
| Performance | 1 | Verify single query optimization |
| Response Validation | 2 | Check response structure |

#### Key Test Scenarios

**Happy Path:**
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