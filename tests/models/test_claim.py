"""Tests for Claim model."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.claim import Claim, Evidence


class TestClaim:
    """Test suite for Claim model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_claim_data = {
            "claim_id": "test-claim-id",
            "product_id": "test-product-id",
            "claim_type": "sustainability",
            "claim_text": "This product is eco-friendly",
            "confidence_label": "verified",
            "rationale": "Verified by third party",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def test_claim_initialization_with_valid_data(self):
        """Test Claim initialization with valid data."""
        claim = Claim(**self.valid_claim_data)
        
        assert claim.claim_id == "test-claim-id"
        assert claim.product_id == "test-product-id"
        assert claim.claim_type == "sustainability"
        assert claim.claim_text == "This product is eco-friendly"
        assert claim.confidence_label == "verified"
        assert claim.rationale == "Verified by third party"
        assert isinstance(claim.created_at, datetime)
        assert isinstance(claim.updated_at, datetime)

    def test_claim_initialization_with_minimal_required_fields(self):
        """Test Claim initialization with only required fields."""
        minimal_data = {
            "claim_id": "min-claim",
            "claim_type": "quality",
            "claim_text": "High quality product",
            "confidence_label": "unverified",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        claim = Claim(**minimal_data)
        
        assert claim.claim_id == "min-claim"
        assert claim.product_id is None
        assert claim.rationale is None

    def test_claim_product_id_optional(self):
        """Test that product_id can be None."""
        data = self.valid_claim_data.copy()
        data["product_id"] = None
        claim = Claim(**data)
        
        assert claim.product_id is None

    def test_claim_rationale_optional(self):
        """Test that rationale can be None."""
        data = self.valid_claim_data.copy()
        data["rationale"] = None
        claim = Claim(**data)
        
        assert claim.rationale is None

    def test_claim_verification_fields_when_set(self):
        """verified_by, verified_at, and verification_notes round-trip when present."""
        verifier_id = "00000000-0000-0000-0000-0000000000ab"
        verified_at = datetime(2024, 6, 15, 14, 30, 0)
        data = {
            **self.valid_claim_data,
            "verified_by": verifier_id,
            "verified_at": verified_at,
            "verification_notes": "Cross-checked with supplier audit.",
        }
        claim = Claim(**data)
        assert claim.verified_by == verifier_id
        assert claim.verified_at == verified_at
        assert claim.verification_notes == "Cross-checked with supplier audit."

    def test_claim_verified_by_defaults_to_none(self):
        claim = Claim(**self.valid_claim_data)
        assert claim.verified_by is None

    def test_claim_verified_at_defaults_to_none(self):
        claim = Claim(**self.valid_claim_data)
        assert claim.verified_at is None

    def test_claim_verification_notes_defaults_to_none(self):
        claim = Claim(**self.valid_claim_data)
        assert claim.verification_notes is None

    def test_claim_verified_at_accepts_iso_string(self):
        data = {
            **self.valid_claim_data,
            "verified_at": "2024-03-01T12:00:00",
        }
        claim = Claim(**data)
        assert claim.verified_at == datetime(2024, 3, 1, 12, 0, 0)

    def test_claim_verification_fields_serialization_roundtrip(self):
        data = {
            **self.valid_claim_data,
            "verified_by": "user-verifier-1",
            "verified_at": datetime(2024, 2, 2, 9, 0, 0),
            "verification_notes": "Approved",
        }
        dumped = Claim(**data).model_dump()
        again = Claim(**dumped)
        assert again.verified_by == "user-verifier-1"
        assert again.verified_at == datetime(2024, 2, 2, 9, 0, 0)
        assert again.verification_notes == "Approved"

    def test_claim_confidence_label_validation(self):
        """Test that confidence_label accepts only valid literals."""
        valid_labels = ["verified", "partially_verified", "unverified"]
        
        for label in valid_labels:
            data = self.valid_claim_data.copy()
            data["confidence_label"] = label
            claim = Claim(**data)
            assert claim.confidence_label == label

    def test_claim_confidence_label_invalid_value(self):
        """Test that invalid confidence_label raises ValidationError."""
        data = self.valid_claim_data.copy()
        data["confidence_label"] = "invalid_label"
        
        with pytest.raises(ValidationError) as exc_info:
            Claim(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("confidence_label",) for error in errors)

    def test_claim_required_fields_missing(self):
        """Test that missing required fields raises ValidationError."""
        required_fields = ["claim_id", "claim_type", "claim_text", "confidence_label", "created_at", "updated_at"]
        
        for field in required_fields:
            data = self.valid_claim_data.copy()
            del data[field]
            
            with pytest.raises(ValidationError) as exc_info:
                Claim(**data)
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == (field,) for error in errors)

    def test_claim_serialization(self):
        """Test Claim serialization to dict."""
        claim = Claim(**self.valid_claim_data)
        claim_dict = claim.model_dump()
        
        assert isinstance(claim_dict, dict)
        assert claim_dict["claim_id"] == "test-claim-id"
        assert claim_dict["claim_type"] == "sustainability"
        assert claim_dict["confidence_label"] == "verified"

    def test_claim_deserialization(self):
        """Test Claim deserialization from dict."""
        claim = Claim(**self.valid_claim_data)
        claim_dict = claim.model_dump()
        deserialized = Claim(**claim_dict)
        
        assert deserialized.claim_id == claim.claim_id
        assert deserialized.claim_type == claim.claim_type
        assert deserialized.confidence_label == claim.confidence_label


class TestEvidence:
    """Test suite for Evidence model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_evidence_data = {
            "evidence_id": "test-evidence-id",
            "stage_id": "test-stage-id",
            "claim_id": "test-claim-id",
            "type": "certificate",
            "issuer": "Test Certification Body",
            "date": "2024-01-01",
            "summary": "Test evidence summary",
            "file_reference": "certificate.pdf",
            "created_at": datetime.now(),
        }

    def test_evidence_initialization_with_valid_data(self):
        """Test Evidence initialization with valid data."""
        evidence = Evidence(**self.valid_evidence_data)
        
        assert evidence.evidence_id == "test-evidence-id"
        assert evidence.stage_id == "test-stage-id"
        assert evidence.claim_id == "test-claim-id"
        assert evidence.type == "certificate"
        assert evidence.issuer == "Test Certification Body"
        assert evidence.summary == "Test evidence summary"
        assert evidence.file_reference == "certificate.pdf"
        assert isinstance(evidence.created_at, datetime)

    def test_evidence_initialization_with_minimal_required_fields(self):
        """Test Evidence initialization with only required fields."""
        minimal_data = {
            "evidence_id": "min-evidence",
            "type": "document",
            "issuer": "Test Issuer",
            "created_at": datetime.now(),
        }
        evidence = Evidence(**minimal_data)
        
        assert evidence.evidence_id == "min-evidence"
        assert evidence.stage_id is None
        assert evidence.claim_id is None
        assert evidence.evidence_date is None
        assert evidence.summary is None
        assert evidence.file_reference is None

    def test_evidence_stage_id_optional(self):
        """Test that stage_id can be None."""
        data = self.valid_evidence_data.copy()
        data["stage_id"] = None
        evidence = Evidence(**data)
        
        assert evidence.stage_id is None

    def test_evidence_claim_id_optional(self):
        """Test that claim_id can be None."""
        data = self.valid_evidence_data.copy()
        data["claim_id"] = None
        evidence = Evidence(**data)
        
        assert evidence.claim_id is None

    def test_evidence_date_field_alias(self):
        """Test that 'date' field is aliased to 'evidence_date'."""
        from datetime import date
        
        data = {
            "evidence_id": "test-evidence",
            "type": "certificate",
            "issuer": "Test Issuer",
            "date": "2024-06-15",  # Using alias 'date'
            "created_at": datetime.now(),
        }
        evidence = Evidence(**data)
        
        # Should be accessible via evidence_date attribute
        assert evidence.evidence_date == date(2024, 6, 15)

    def test_evidence_date_optional(self):
        """Test that evidence_date can be None."""
        data = self.valid_evidence_data.copy()
        data["date"] = None
        evidence = Evidence(**data)
        
        assert evidence.evidence_date is None

    def test_evidence_summary_optional(self):
        """Test that summary can be None."""
        data = self.valid_evidence_data.copy()
        data["summary"] = None
        evidence = Evidence(**data)
        
        assert evidence.summary is None

    def test_evidence_file_reference_optional(self):
        """Test that file_reference can be None."""
        data = self.valid_evidence_data.copy()
        data["file_reference"] = None
        evidence = Evidence(**data)
        
        assert evidence.file_reference is None

    def test_evidence_required_fields_missing(self):
        """Test that missing required fields raises ValidationError."""
        required_fields = ["evidence_id", "type", "issuer", "created_at"]
        
        for field in required_fields:
            data = self.valid_evidence_data.copy()
            del data[field]
            
            with pytest.raises(ValidationError) as exc_info:
                Evidence(**data)
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == (field,) for error in errors)

    def test_evidence_serialization(self):
        """Test Evidence serialization to dict."""
        evidence = Evidence(**self.valid_evidence_data)
        evidence_dict = evidence.model_dump()
        
        assert isinstance(evidence_dict, dict)
        assert evidence_dict["evidence_id"] == "test-evidence-id"
        assert evidence_dict["type"] == "certificate"
        assert evidence_dict["issuer"] == "Test Certification Body"

    def test_evidence_deserialization(self):
        """Test Evidence deserialisation from dict."""
        evidence = Evidence(**self.valid_evidence_data)
        evidence_dict = evidence.model_dump()
        deserialized = Evidence(**evidence_dict)
        
        assert deserialized.evidence_id == evidence.evidence_id
        assert deserialized.type == evidence.type
        assert deserialized.issuer == evidence.issuer
        assert deserialized.file_reference == evidence.file_reference
