import hashlib
import hmac
import json

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.repositories import booking_repository, payment_repository

settings = get_settings()


def verify_paystack_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Paystack signs the raw request body with HMAC-SHA512, keyed with your
    secret key (not a separate webhook secret) — the signature arrives in
    the X-Paystack-Signature header."""
    if not signature_header or not settings.paystack_secret_key:
        return False

    computed = hmac.new(
        settings.paystack_secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    # constant-time comparison — a naive `==` here leaks timing information
    # an attacker could use to guess the correct signature byte by byte.
    return hmac.compare_digest(computed, signature_header)


def verify_flutterwave_signature(signature_header: str | None) -> bool:
    """Flutterwave does NOT use HMAC — it sends back the exact secret hash
    you configured in your dashboard, in the verif-hash header. Verification
    is a direct (constant-time) string comparison, not a computed digest."""
    if not signature_header or not settings.flutterwave_webhook_secret_hash:
        return False

    return hmac.compare_digest(signature_header, settings.flutterwave_webhook_secret_hash)


async def process_paystack_webhook(db: AsyncSession, raw_body: bytes, signature_header: str | None) -> None:
    if not verify_paystack_signature(raw_body, signature_header):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    payload = json.loads(raw_body)
    event = payload.get("event")
    reference = payload.get("data", {}).get("reference")

    if event != "charge.success" or not reference:
        return  # not a success event we care about — accept and no-op

    await _confirm_payment_by_reference(db, reference)


async def process_flutterwave_webhook(db: AsyncSession, raw_body: bytes, signature_header: str | None) -> None:
    if not verify_flutterwave_signature(signature_header):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    payload = json.loads(raw_body)
    status_value = payload.get("data", {}).get("status")
    reference = payload.get("data", {}).get("tx_ref")

    if status_value != "successful" or not reference:
        return

    await _confirm_payment_by_reference(db, reference)


async def _confirm_payment_by_reference(db: AsyncSession, provider_reference: str) -> None:
    payment = await payment_repository.get_payment_by_reference(db, provider_reference)
    if not payment:
        # Reference we don't recognize — log and ignore rather than error,
        # since providers retry webhooks and an unknown reference isn't
        # actionable on our end.
        return

    if payment.status == "success":
        # Idempotency: providers retry webhooks (network blips, timeouts on
        # their end reading our 200). Re-processing an already-confirmed
        # payment must be a safe no-op, not a duplicate booking confirmation
        # or double-counted revenue.
        return

    await payment_repository.mark_payment_status(db, payment, "success")

    booking = await booking_repository.get_booking_by_id(db, payment.booking_id)
    if booking and booking.status == "pending":
        await booking_repository.update_booking_status(db, booking, "confirmed")