"""Provider-specific tests for GeminiProvider — things that can only be
exercised at this layer (malformed input handling before any network call
is made), as opposed to test_interpret.py which tests orchestration behind
a FakeProvider.

Regression test for a real bug found during Phase 3 live gate testing:
base64.b64decode() ran outside the try/except and raised binascii.Error
uncaught, producing a raw 500 instead of the designed safe-fallback
behavior. No network call happens in this test — the decode fails before
the client would ever be used, so no API key or mocking is needed.
"""

from __future__ import annotations

from app.interpret.providers.gemini import GeminiProvider


def test_malformed_image_base64_returns_none_not_raises():
    provider = GeminiProvider(api_key="unused-no-network-call-reaches-this-point")
    result = provider.complete(
        system_prompt="system",
        context_text="test",
        image_base64="not-valid-base64-###",
        image_media_type="image/jpeg",
    )
    assert result is None
