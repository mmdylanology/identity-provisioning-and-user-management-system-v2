"""
Authentication and authorization utilities
"""
from fastapi import HTTPException, Header
from jose import jwt, JWTError
import httpx
from typing import Optional
from app.config import settings
import json

def get_keycloak_token(username: str, password: str) -> dict:
    """
    Authenticate with Keycloak and get tokens
    
    Returns:
        {
            "access_token": "eyJhbGc...",
            "refresh_token": "eyJhbGc...",
            "token_type": "Bearer",
            "expires_in": 300
        }
    """
    token_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
    
    data = {
        "client_id": settings.keycloak_client_id,
        "client_secret": settings.keycloak_client_secret,
        "grant_type": "password",
        "username": username,
        "password": password
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        raise HTTPException(status_code=500, detail="Authentication failed")

def refresh_keycloak_token(refresh_token: str) -> dict:
    """
    Refresh access token using refresh token
    
    Returns new access_token and refresh_token
    """
    token_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
    
    data = {
        "client_id": settings.keycloak_client_id,
        "client_secret": settings.keycloak_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

def get_jwks() -> dict:
    """Get Keycloak public keys for JWT verification"""
    jwks_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
    
    with httpx.Client() as client:
        response = client.get(jwks_url)
        response.raise_for_status()
        return response.json()

def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token
    
    Returns decoded token payload:
        {
            "sub": "user_id",
            "email": "user@example.com",
            "preferred_username": "username",
            "realm_access": {
                "roles": ["realm-admin", ...]
            }
        }
    """
    try:
        # Get public keys
        jwks = get_jwks()
        
        # Decode without verification first to get header
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the right key
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Unable to find appropriate key")
        
        # Decode and verify
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.keycloak_client_id,
            options={"verify_aud": False}  # Public client doesn't have audience
        )
        
        return payload
    
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def verify_bearer_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependency to verify Bearer token from Authorization header
    
    Usage:
        @router.get("/protected")
        def protected_route(token: dict = Depends(verify_bearer_token)):
            return {"user": token["preferred_username"]}
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    
    return decode_token(token)

def is_superadmin(token_payload: dict) -> bool:
    """
    Check if user has realm-admin role
    """
    roles = token_payload.get("realm_access", {}).get("roles", [])
    return "realm-admin" in roles

def require_superadmin(token_payload: dict):
    """
    Dependency to require realm-admin role
    
    Usage:
        @router.post("/admin-only")
        def admin_route(
            token: dict = Depends(verify_bearer_token),
            _: None = Depends(lambda t=token: require_superadmin(t))
        ):
            return {"message": "Admin access granted"}
    """
    if not is_superadmin(token_payload):
        raise HTTPException(status_code=403, detail="Requires realm-admin role")
