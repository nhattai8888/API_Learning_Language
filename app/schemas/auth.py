from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from app.core.enums import IdentityType

class RegisterEmailRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: Optional[str] = None

class RegisterPhoneRequest(BaseModel):
    phone: str  # E.164 recommended
    display_name: Optional[str] = None

class LoginEmailRequest(BaseModel):
    email: EmailStr
    password: str
    device_id: Optional[str] = None
    device_fingerprint: Optional[str] = None

class LoginPhoneStartRequest(BaseModel):
    phone: str
    device_id: Optional[str] = None
    device_fingerprint: Optional[str] = None

class OtpVerifyRequest(BaseModel):
    otp_id: str
    code: str
    device_id: Optional[str] = None
    trust_device: bool = False

class RefreshRequest(BaseModel):
    refresh_token: str

class ForgotPasswordStartRequest(BaseModel):
    identity_type: IdentityType
    value: str  # email or phone

class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AuthUser(BaseModel):
    user_id: str
    display_name: Optional[str] = None

class LogoutRequest(BaseModel):
    refresh_token: str
    all_sessions: bool = False  # optional: logout all devices

class MeResponse(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []