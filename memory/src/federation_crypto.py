"""
Cryptographic Memory Bundle Signing and Verification.

Provides HMAC-SHA256 digital signatures for TMEF memory bundles,
ensuring authenticity, tamper-proofing, and non-repudiation between federated agents.
"""
from __future__ import annotations

import hmac
import hashlib
import json
from typing import Dict, Any, List


DEFAULT_FEDERATION_SECRET = "threadline-federation-default-secret-v1"


def canonical_serialize(data: Dict[str, Any]) -> bytes:
    """
    Serializes a dictionary into canonical UTF-8 bytes:
    sorted keys, compact separators, excluding the signature field itself.
    """
    payload = {k: v for k, v in data.items() if k != "signature"}
    # Convert dates to ISO strings if present
    def default_encoder(o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if hasattr(o, "dict"):
            return o.dict()
        return str(o)

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=default_encoder,
        ensure_ascii=False
    )
    return serialized.encode("utf-8")


class FederationCryptoSigner:
    """
    Signs and verifies TMEF bundle payloads using HMAC-SHA256.
    """
    def __init__(self, secret_key: str = DEFAULT_FEDERATION_SECRET):
        self.secret_key = secret_key.encode("utf-8")

    def sign_bundle(self, bundle_dict: Dict[str, Any]) -> str:
        """Computes HMAC-SHA256 hexadecimal digest for bundle."""
        canonical_bytes = canonical_serialize(bundle_dict)
        signature = hmac.new(self.secret_key, canonical_bytes, hashlib.sha256).hexdigest()
        return signature

    def verify_bundle(self, bundle_dict: Dict[str, Any], signature: str) -> bool:
        """Verifies signature against bundle data using constant-time comparison."""
        if not signature:
            return False
        expected_sig = self.sign_bundle(bundle_dict)
        return hmac.compare_digest(expected_sig, signature)
