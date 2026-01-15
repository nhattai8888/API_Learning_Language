"""Audit service placeholder"""


def audit_log(user, action: str, details: dict = None):
    # simple placeholder - in real app write to DB or external service
    print(f"AUDIT: user={user} action={action} details={details}")
