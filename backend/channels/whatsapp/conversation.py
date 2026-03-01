"""Multi-turn WhatsApp onboarding conversation — SBI YONO-style flow.

Manages per-phone conversation state for the 8-step digital account opening:
  1. initiate  →  ask name
  2. name      →  ask Aadhaar
  3. aadhaar   →  validate (Verhoeff) + send OTP
  4. otp       →  verify OTP → show eKYC
  5. confirm   →  ask PAN
  6. pan       →  verify PAN + AML
  7. video_kyc →  simulated video KYC
  8. complete  →  account created
"""

import random
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

SESSION_TIMEOUT = 900  # 15 minutes
MAX_OTP_ATTEMPTS = 3

# ---------------------------------------------------------------------------
# Verhoeff checksum (used by UIDAI for Aadhaar numbers)
# ---------------------------------------------------------------------------
_VERHOEFF_D = [
    [0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0],
]
_VERHOEFF_P = [
    [0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8],
]
_VERHOEFF_INV = [0,4,3,2,1,5,6,7,8,9]


def validate_verhoeff(number: str) -> bool:
    """Validate a number string using the Verhoeff checksum algorithm."""
    c = 0
    for i, digit in enumerate(reversed(number)):
        if not digit.isdigit():
            return False
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][int(digit)]]
    return c == 0


def validate_aadhaar(raw: str) -> tuple[bool, str]:
    """Validate an Aadhaar number (12 digits + Verhoeff checksum).

    Returns (is_valid, cleaned_number_or_error_message).
    """
    cleaned = raw.replace(" ", "").replace("-", "")
    if not cleaned.isdigit():
        return False, "Aadhaar number must contain only digits."
    if len(cleaned) != 12:
        return False, "Aadhaar number must be exactly 12 digits."
    if cleaned[0] == "0" or cleaned[0] == "1":
        return False, "Aadhaar number cannot start with 0 or 1."
    if not validate_verhoeff(cleaned):
        return False, "Aadhaar number failed checksum validation."
    return True, cleaned


def validate_pan(raw: str) -> tuple[bool, str]:
    """Validate PAN format: 5 letters + 4 digits + 1 letter."""
    cleaned = raw.strip().upper()
    if len(cleaned) != 10:
        return False, "PAN must be exactly 10 characters (e.g., ABCDE1234F)."
    if not (cleaned[:5].isalpha() and cleaned[5:9].isdigit() and cleaned[9].isalpha()):
        return False, "Invalid PAN format. Expected: ABCDE1234F."
    return True, cleaned


# ---------------------------------------------------------------------------
# Conversation state
# ---------------------------------------------------------------------------
@dataclass
class OnboardingSession:
    phone: str
    step: str = "name"           # current step
    name: str = ""
    aadhaar: str = ""
    otp: str = ""
    otp_attempts: int = 0
    pan: str = ""
    created_at: float = field(default_factory=time.time)
    # Generated eKYC data
    dob: str = ""
    address: str = ""
    gender: str = ""
    account_number: str = ""
    card_number: str = ""

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > SESSION_TIMEOUT


# In-memory sessions: phone → OnboardingSession
_sessions: dict[str, OnboardingSession] = {}

# Trigger words that start an onboarding conversation
ONBOARDING_TRIGGERS = {
    "open account", "new account", "account open", "account kholna",
    "khata kholna", "savings account", "onboarding", "i want to open",
    "open a bank account", "naya khata", "account banana",
}


def is_onboarding_trigger(message: str) -> bool:
    """Check if a message is requesting account opening."""
    msg = message.lower().strip()
    return any(trigger in msg for trigger in ONBOARDING_TRIGGERS)


def has_active_session(phone: str) -> bool:
    """Check if a phone number has an active onboarding session."""
    phone = _normalize_phone(phone)
    session = _sessions.get(phone)
    if session and not session.is_expired:
        return True
    if session and session.is_expired:
        del _sessions[phone]
    return False


def start_session(phone: str) -> OnboardingSession:
    """Start a new onboarding session for a phone number."""
    phone = _normalize_phone(phone)
    session = OnboardingSession(phone=phone)
    _sessions[phone] = session
    logger.info("Onboarding session started for %s", phone)
    return session


def get_session(phone: str) -> Optional[OnboardingSession]:
    """Get the active session for a phone, or None."""
    phone = _normalize_phone(phone)
    session = _sessions.get(phone)
    if session and session.is_expired:
        del _sessions[phone]
        return None
    return session


def end_session(phone: str) -> None:
    """Remove the session for a phone number."""
    phone = _normalize_phone(phone)
    _sessions.pop(phone, None)


def _normalize_phone(phone: str) -> str:
    phone = phone.strip().replace(" ", "")
    if not phone.startswith("+"):
        # Handle numbers already starting with country code 91
        if phone.startswith("91") and len(phone) > 10:
            phone = "+" + phone
        else:
            phone = "+91" + phone.lstrip("0")
    return phone


# ---------------------------------------------------------------------------
# Step handlers — each returns the reply message string
# ---------------------------------------------------------------------------
_ADDRESSES = [
    "Flat 402, Koregaon Park, Pune 411001",
    "B-12, Andheri West, Mumbai 400058",
    "House 7, Sector 22, Gurgaon 122015",
    "303, MG Road, Bengaluru 560001",
    "A-45, Salt Lake, Kolkata 700091",
    "16, Anna Nagar, Chennai 600040",
]

_DOBS = [
    "15-Mar-1990", "22-Jul-1988", "03-Nov-1995",
    "18-Jan-1992", "09-Sep-1985", "27-Dec-1997",
]


def generate_otp() -> str:
    """Generate a random 6-digit OTP."""
    return str(random.randint(100000, 999999))


def handle_step(session: OnboardingSession, message: str) -> tuple[str, bool]:
    """Process the current step and return (reply_message, is_complete).

    The caller is responsible for sending the reply via WhatsApp and calling
    the appropriate agents for event emission.
    """
    step = session.step
    msg = message.strip()

    if step == "name":
        return _handle_name(session, msg)
    elif step == "aadhaar":
        return _handle_aadhaar(session, msg)
    elif step == "otp":
        return _handle_otp(session, msg)
    elif step == "confirm_ekyc":
        return _handle_confirm_ekyc(session, msg)
    elif step == "pan":
        return _handle_pan(session, msg)
    elif step == "video_kyc":
        return _handle_video_kyc(session, msg)
    else:
        return "Session error. Please type 'open account' to start again.", True


def _handle_name(session: OnboardingSession, msg: str) -> tuple[str, bool]:
    if len(msg) < 2 or not any(c.isalpha() for c in msg):
        return (
            "Please enter a valid full name (at least 2 characters).\n"
            "Example: Prateem Mehta",
            False,
        )
    session.name = msg.title()
    session.step = "aadhaar"
    return (
        f"Thank you, {session.name}! 🙏\n\n"
        f"Now please share your *12-digit Aadhaar number* for eKYC verification.\n\n"
        f"🔒 Your data is encrypted and processed per UIDAI guidelines."
    ), False


def _handle_aadhaar(session: OnboardingSession, msg: str) -> tuple[str, bool]:
    valid, result = validate_aadhaar(msg)
    if not valid:
        return f"❌ {result}\n\nPlease enter a valid 12-digit Aadhaar number.", False

    session.aadhaar = result
    session.otp = generate_otp()
    session.otp_attempts = 0
    session.step = "otp"

    masked = f"XXXX XXXX {result[-4:]}"
    phone_last4 = session.phone[-4:] if len(session.phone) >= 4 else "XXXX"

    return (
        f"📱 Verifying your Aadhaar ({masked}) via UIDAI...\n\n"
        f"✅ Aadhaar found! An OTP has been sent to your registered mobile ending in *XX{phone_last4[-2:]}*.\n\n"
        f"🔑 Your OTP is: *{session.otp}*\n"
        f"_(In a real bank, this comes via SMS. For this demo, we send it here on WhatsApp.)_\n\n"
        f"Please enter the 6-digit OTP to proceed."
    ), False


def _handle_otp(session: OnboardingSession, msg: str) -> tuple[str, bool]:
    cleaned = msg.replace(" ", "")

    if cleaned != session.otp:
        session.otp_attempts += 1
        remaining = MAX_OTP_ATTEMPTS - session.otp_attempts
        if remaining <= 0:
            end_session(session.phone)
            return (
                "❌ Too many incorrect attempts. Session expired.\n\n"
                "Please type *open account* to start again."
            ), True
        return (
            f"❌ Invalid OTP. Please try again.\n"
            f"You have {remaining} attempt(s) remaining.\n\n"
            f"🔑 Reminder — your OTP is: *{session.otp}*"
        ), False

    # OTP verified — generate mock eKYC data
    session.dob = random.choice(_DOBS)
    session.address = random.choice(_ADDRESSES)
    session.gender = "Male" if random.random() > 0.5 else "Female"
    session.step = "confirm_ekyc"

    masked_aadhaar = f"XXXX XXXX {session.aadhaar[-4:]}"
    return (
        f"✅ OTP Verified! eKYC data retrieved from UIDAI:\n\n"
        f"📋 *Name:* {session.name}\n"
        f"📅 *DOB:* {session.dob}\n"
        f"🏠 *Address:* {session.address}\n"
        f"👤 *Gender:* {session.gender}\n"
        f"🪪 *Aadhaar:* {masked_aadhaar}\n"
        f"📷 *Photo:* Matched ✅\n\n"
        f"Is this information correct? Reply *YES* to confirm or *NO* to retry."
    ), False


def _handle_confirm_ekyc(session: OnboardingSession, msg: str) -> tuple[str, bool]:
    if msg.upper() in ("NO", "N", "NAHI", "NHIN"):
        end_session(session.phone)
        return (
            "No problem. Please type *open account* to restart the process "
            "with correct details."
        ), True

    if msg.upper() not in ("YES", "Y", "HA", "HAAN", "HAA"):
        return "Please reply *YES* to confirm or *NO* to retry.", False

    session.step = "pan"
    return (
        "Great! eKYC confirmed. ✅\n\n"
        "Now please share your *PAN number* for income tax linkage.\n"
        "_(Format: ABCDE1234F)_"
    ), False


def _handle_pan(session: OnboardingSession, msg: str) -> tuple[str, bool]:
    valid, result = validate_pan(msg)
    if not valid:
        return f"❌ {result}\n\nPlease enter a valid PAN number.", False

    session.pan = result
    session.step = "video_kyc"

    return (
        f"✅ *PAN Verified!*\n"
        f"Name match: {session.name} ↔ {session.name.upper()} ✅\n\n"
        f"🔍 Running AML/Sanctions screening...\n"
        f"✅ No adverse findings. Risk score: LOW (12/100)\n"
        f"• OFAC: Clear ✅\n"
        f"• UN Sanctions: Clear ✅\n"
        f"• RBI Defaulter List: Clear ✅\n\n"
        f"📹 *Final step: Video KYC*\n"
        f"In a real process, you'd connect with a bank officer via video call.\n"
        f"For this demo, we'll simulate the verification.\n\n"
        f"Reply *PROCEED* to complete Video KYC."
    ), False


def _handle_video_kyc(session: OnboardingSession, msg: str) -> tuple[str, bool]:
    if msg.upper() not in ("PROCEED", "YES", "OK", "Y", "CONTINUE"):
        return "Reply *PROCEED* to complete Video KYC.", False

    # Generate account details
    session.account_number = f"{random.randint(1000,9999)}-{random.randint(10000000,99999999)}"
    session.card_number = f"XXXX-XXXX-XXXX-{random.randint(1000,9999)}"
    session.step = "complete"

    video_kyc_msg = (
        "📹 *Video KYC in progress...*\n\n"
        f"✅ Liveness detected (confidence: 97%)\n"
        f"✅ Face matched with Aadhaar photo (94% match)\n"
        f"✅ Document verification: Aadhaar + PAN originals confirmed\n\n"
        f"*Video KYC: APPROVED* ✅\n\n"
        f"⏳ Creating your account..."
    )

    # Account creation message will be sent separately after agents run
    account_msg = (
        f"🎉 *Congratulations, {session.name}!*\n"
        f"Your BNB Digital Savings Account is now *ACTIVE!*\n\n"
        f"🏦 *Account Details:*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Account No: {session.account_number}\n"
        f"IFSC: BNBN0001234\n"
        f"Branch: Koregaon Park, Pune\n"
        f"Account Type: Insta Plus Savings\n\n"
        f"💳 *Virtual Debit Card:*\n"
        f"Card No: {session.card_number}\n"
        f"Valid: 03/26 – 03/31\n\n"
        f"📧 Welcome kit sent to your email.\n"
        f"📱 Download BNB Mobile App to start banking.\n\n"
        f"Thank you for choosing *Bharat National Bank!* 🙏"
    )

    return video_kyc_msg + "\n\n" + account_msg, True
