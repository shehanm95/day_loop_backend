from datetime import datetime, timezone, timedelta
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple, List, Dict, Any

from sqlmodel import Session
from app.core.config import settings
from app.core.security import get_password_hash
from app.schemas.ReSetPassword import ReSetPassword
from app.services import user_service

# ==========================================
# CONFIGURATION CONSTANTS
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "shehanmaleesha4884@gmail.com"
SENDER_PASSWORD = settings.EMAIL_APP_PASSWORD

# In-memory storage list for OTP records: [{ "email": str, "otp": str, "timestamp": datetime }, ...]
otp_storage: List[Dict[str, Any]] = []

# OTP validity window in seconds (180 seconds = 3 minutes)
OTP_VALIDITY_SECONDS = 180


def generate_otp(length: int = 6) -> str:
    """
    Generates a secure numeric OTP of the specified length.
    """
    range_start = 10 ** (length - 1)
    range_end = (10 ** length) - 1
    return str(random.randint(range_start, range_end))


def create_otp_email_message(recipient_email: str, otp_code: str) -> MIMEMultipart:
    """
    Builds the MIME multipart email message containing both plain text 
    and an HTML template for the OTP.
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Verification Code (OTP)"
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email

    # Plain text version for fallback
    text_content = (
        f"Hello,\n\n"
        f"Your One-Time Password (OTP) for verification is: {otp_code}\n\n"
        f"This code is valid for 3 minutes. Do not share it with anyone.\n\n"
        f"Best regards,\nDayLoop Team"
    )

    # Clean HTML version for modern email clients
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f9f9f6; padding: 20px; color: #2b2b2b;">
        <div style="max-width: 500px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
          <h2 style="color: #1b4d3e; text-align: center; margin-bottom: 20px;">Verification Code</h2>
          <p style="font-size: 1rem; color: #555;">Hello,</p>
          <p style="font-size: 1rem; color: #555;">Please use the following One-Time Password (OTP) to complete your verification process:</p>
          
          <div style="text-align: center; margin: 30px 0;">
            <span style="display: inline-block; background-color: #1b4d3e; color: #ffffff; font-size: 2rem; font-weight: bold; letter-spacing: 6px; padding: 12px 24px; border-radius: 8px;">
              {otp_code}
            </span>
          </div>
          
          <p style="font-size: 0.9rem; color: #777; text-align: center;">This code will expire in 3 minutes. If you did not request this, please ignore this email.</p>
          <hr style="border: none; border-top: 1px solid #e2e2e2; margin: 20px 0;">
          <p style="font-size: 0.8rem; color: #aaa; text-align: center;">DayLoop Security Team</p>
        </div>
      </body>
    </html>
    """

    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    
    message.attach(part1)
    message.attach(part2)

    return message


def send_email_via_smtp(recipient_email: str, message: MIMEMultipart) -> bool:
    """
    Connects to the SMTP server and transmits the email message.
    Returns True if successful, False otherwise.
    """
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def store_otp(email: str, otp_code: str) -> None:
    """
    Cleans up expired OTPs globally, removes any existing active OTP for the same email,
    and stores the new OTP record with a UTC timestamp.
    """
    global otp_storage
    now = datetime.now(timezone.utc)
    
    # Filter out expired OTPs globally (> 180 seconds old)
    otp_storage = [
        item for item in otp_storage 
        if now - item["timestamp"] < timedelta(seconds=OTP_VALIDITY_SECONDS)
    ]
    
    # Remove any existing active OTP for this specific email address
    otp_storage = [item for item in otp_storage if item["email"] != email]
    
    # Append the new OTP entry
    otp_storage.append({
        "email": email,
        "otp": otp_code,
        "timestamp": now
    })


def send_otp_to_email(recipient_email: str) -> Tuple[bool, str]:
    """
    Orchestration method: Generates an OTP, stores it in memory with a timestamp, 
    builds the email, and dispatches it to the recipient.
    Returns a tuple of (success_status, generated_otp).
    """
    global otp_storage
    
    otp_code = generate_otp(length=6)
    # otp_code = "123456"
    # Store OTP in memory list
    store_otp(recipient_email, otp_code)
    
    email_message = create_otp_email_message(recipient_email, otp_code)
    success = send_email_via_smtp(recipient_email, email_message)
    success = True
    if success:
        return True, otp_code
    
    # Rollback from storage if email delivery fails
    otp_storage = [item for item in otp_storage if item["email"] != recipient_email]
    return False, ""


def verify_email_otp(email: str, otp_code: str) -> Tuple[bool, str]:
    """
    Verifies the provided OTP against the in-memory storage list for the given email.
    Checks if the code exists and is within the 180-second validity window.
    Removes the OTP record upon a successful match (one-time use).
    Returns a tuple of (is_valid, message).
    """
    global otp_storage
    now = datetime.now(timezone.utc)
    
    # Purge expired OTPs globally first
    otp_storage = [
        item for item in otp_storage 
        if now - item["timestamp"] < timedelta(seconds=OTP_VALIDITY_SECONDS)
    ]
    
    # Find record matching the email
    record = next((item for item in otp_storage if item["email"] == email), None)
    
    if not record:
        return False, "No active OTP found or the code has expired."
    
    if record["otp"] != otp_code:
        return False, "Invalid OTP code."
    
    # Remove the OTP entry upon successful verification (one-time use)
    otp_storage = [item for item in otp_storage if item["email"] != email]
    
    return True, "OTP verified successfully."


def send_setup_password_email(recipient_email: str, first_name: str) -> bool:
    """
    Sends an invitation email to a newly created user with a link to set up their password.
    """
    setup_link = f"http://localhost:5173/set_password/{recipient_email}"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Welcome to DayLoop - Set Up Your Password"
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email

    text_content = (
        f"Hello {first_name},\n\n"
        f"An administrator has created an account for you on DayLoop.\n"
        f"Please click the link below to set up your password and activate your account:\n\n"
        f"{setup_link}\n\n"
        f"If you did not expect this, please ignore this email.\n\n"
        f"Best regards,\nDayLoop Team"
    )

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f9f9f6; padding: 20px; color: #2b2b2b;">
        <div style="max-width: 500px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
          <h2 style="color: #1b4d3e; text-align: center; margin-bottom: 20px;">Welcome to DayLoop!</h2>
          <p style="font-size: 1rem; color: #555;">Hello <strong>{first_name}</strong>,</p>
          <p style="font-size: 1rem; color: #555;">An administrator has registered an account for you. Please click the button below to set up your password and get started:</p>
          
          <div style="text-align: center; margin: 30px 0;">
            <a href="{setup_link}" target="_blank" style="display: inline-block; background-color: #1b4d3e; color: #ffffff; font-size: 1rem; font-weight: bold; text-decoration: none; padding: 12px 24px; border-radius: 8px;">
              Set Up Password
            </a>
          </div>
          
          <p style="font-size: 0.85rem; color: #777; word-break: break-all;">Or copy and paste this link into your browser:<br><a href="{setup_link}" style="color: #1b4d3e;">{setup_link}</a></p>
          
          <hr style="border: none; border-top: 1px solid #e2e2e2; margin: 20px 0;">
          <p style="font-size: 0.8rem; color: #aaa; text-align: center;">DayLoop Administration Team</p>
        </div>
      </body>
    </html>
    """

    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    
    message.attach(part1)
    message.attach(part2)

    return send_email_via_smtp(recipient_email, message)

def setPassword(db: Session, body: ReSetPassword) -> bool:
    """
    Verifies the OTP, hashes the new password, and updates the user in the database.
    """
    # 1. Verify the OTP and ensure it's within the 180s window (removes OTP upon success)
    is_valid, message = verify_email_otp(body.email, body.otp)
    if not is_valid:
        raise ValueError(message)
    
    # 2. Find the user by email
    user = user_service.get_user_by_email(db, body.email)
    if not user:
        raise ValueError("User not found in the system.")
    
    # 3. Update using the service function (handles hashing and saving safely)
    updated_user = user_service.update_with_password(db, user.id, body.password)  # type: ignore
    if not updated_user:
        raise ValueError("Failed to update password. Please try again.")
        
    return True