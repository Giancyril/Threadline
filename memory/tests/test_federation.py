"""
Unit tests for Cross-Agent Memory Federation components:
- TMEF bundle serialization
- Cryptographic HMAC-SHA256 signature and tamper detection
- Privacy scrubbing and PII redaction
- 3-way merge conflict resolution
"""
import pytest
from datetime import datetime, timezone
from memory.src.federation_schemas import TMEFBundle, AgentManifest, ExportedMemoryItem
from memory.src.federation_crypto import FederationCryptoSigner, canonical_serialize
from memory.src.privacy_scrubber import PrivacyScrubber
from memory.src.federation_merger import FederationMergeResolver


def test_crypto_signer_and_tamper_detection():
    signer = FederationCryptoSigner("test-secret-key-123")
    
    payload = {
        "bundle_id": "bnd_001",
        "format_version": "1.0",
        "memory_count": 1,
        "memories": [{"memory_id": "m1", "content": "User prefers dark mode"}]
    }
    
    sig = signer.sign_bundle(payload)
    assert len(sig) == 64  # SHA-256 hex string
    
    # Valid signature check
    assert signer.verify_bundle(payload, sig) is True
    
    # Tampered payload check
    tampered_payload = dict(payload)
    tampered_payload["memory_count"] = 2
    assert signer.verify_bundle(tampered_payload, sig) is False
    
    # Invalid signature check
    assert signer.verify_bundle(payload, "invalid_sig_abc123") is False


def test_privacy_scrubber():
    scrubber = PrivacyScrubber()
    text = (
        "Contact me at alice.dev@company.org or +1 415 555 2671. "
        "Secret token is sk-proj-abcdef1234567890abcdef123456 on IP 192.168.1.10."
    )
    
    cleaned, stats = scrubber.scrub_text(text)
    assert "[REDACTED_EMAIL]" in cleaned
    assert "[REDACTED_PHONE]" in cleaned
    assert "[REDACTED_API_KEY]" in cleaned
    assert "[REDACTED_IP]" in cleaned
    assert "alice.dev@company.org" not in cleaned
    assert stats["email"] == 1
    assert stats["api_key"] == 1


def test_federation_merge_resolver():
    resolver = FederationMergeResolver()
    
    local_memories = [
        {"id": "loc_1", "content": "User prefers concise answers", "category": "preferences"},
        {"id": "loc_2", "content": "Working on Python backend", "category": "projects"}
    ]
    
    bundle = TMEFBundle(
        bundle_id="bundle_test_1",
        source_agent=AgentManifest(agent_id="ag_mobile", agent_name="MobileAgent"),
        memory_count=3,
        memories=[
            # Exact duplicate -> should be skipped
            ExportedMemoryItem(memory_id="rem_1", content="User prefers concise answers", category="preferences", created_at="2026-09-01T00:00:00Z"),
            # Contradiction with change signal -> should be flagged
            ExportedMemoryItem(memory_id="rem_2", content="User no longer wants concise answers, switched to long essays", category="preferences", created_at="2026-09-02T00:00:00Z"),
            # New unique memory -> should be imported
            ExportedMemoryItem(memory_id="rem_3", content="Loves dark theme on mobile interface", category="preferences", created_at="2026-09-03T00:00:00Z")
        ]
    )
    
    merged, result = resolver.reconcile_bundle(bundle, local_memories, strategy="auto")
    
    assert result.total_received == 3
    assert result.skipped_duplicates == 1
    assert result.contradictions_flagged >= 1
    assert result.imported_count >= 1
    assert any(m.get("content") == "Loves dark theme on mobile interface" for m in merged)
