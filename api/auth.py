from fastapi import Header, HTTPException
from config import settings

def verify_admin(x_admin_token: str = Header(...)):
    """Verify admin authentication token"""
    if x_admin_token != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return x_admin_token
