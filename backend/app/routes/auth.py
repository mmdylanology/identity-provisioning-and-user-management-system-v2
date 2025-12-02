"""
Authentication endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.auth import (
    get_keycloak_token,
    refresh_keycloak_token,
    verify_bearer_token,
    decode_token
)

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class RefreshRequest(BaseModel):
    refresh_token: str

class UserInfo(BaseModel):
    sub: str
    email: str
    preferred_username: str
    roles: list

@router.post("/auth/login")
def login(credentials: LoginRequest):
    """
    Authenticate user and return JWT tokens
    
    **Request Body:**
    ```json
    {
        "username": "malik",
        "password": "password123"
    }
    ```
    
    **Response:**
    ```json
    {
        "access_token": "eyJhbGc...",
        "refresh_token": "eyJhbGc...",
        "token_type": "bearer",
        "expires_in": 300,
        "user": {...}
    }
    ```
    """
    try:
        token_data = get_keycloak_token(credentials.username, credentials.password)
        
        # Decode token to get user info
        user_data = decode_token(token_data["access_token"])
        
        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_type": "bearer",
            "expires_in": token_data["expires_in"],
            "user": {
                "id": user_data.get("sub"),
                "username": user_data.get("preferred_username"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "realm_access": user_data.get("realm_access")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.post("/auth/refresh")
def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token
    
    **Request Body:**
    ```json
    {
        "refresh_token": "eyJhbGc..."
    }
    ```
    
    **Response:**
    ```json
    {
        "access_token": "eyJhbGc...",
        "refresh_token": "eyJhbGc...",
        "token_type": "bearer",
        "expires_in": 300
    }
    ```
    """
    try:
        token_data = refresh_keycloak_token(request.refresh_token)
        
        # Decode token to get user info
        user_data = decode_token(token_data["access_token"])
        
        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_type": "bearer",
            "expires_in": token_data["expires_in"],
            "user": {
                "id": user_data.get("sub"),
                "username": user_data.get("preferred_username"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "realm_access": user_data.get("realm_access")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

@router.get("/auth/me", response_model=UserInfo)
def get_current_user(token: dict = Depends(verify_bearer_token)):
    """
    Get current user information from token
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Response:**
    ```json
    {
        "sub": "cc0fb4c2-134d-4d2c-a5b5-6fb6217cdfc9",
        "email": "malik@example.com",
        "preferred_username": "malik",
        "roles": ["realm-admin", "default-roles-newcustomsrealm"]
    }
    ```
    """
    return UserInfo(
        sub=token.get("sub", ""),
        email=token.get("email", ""),
        preferred_username=token.get("preferred_username", ""),
        roles=token.get("realm_access", {}).get("roles", [])
    )

@router.post("/auth/logout")
def logout(token: dict = Depends(verify_bearer_token)):
    """
    Logout user (client should delete tokens)
    
    Note: This is a client-side operation. The client should:
    1. Delete access_token from storage
    2. Delete refresh_token from storage
    3. Redirect to login page
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Response:**
    ```json
    {
        "message": "Logged out successfully"
    }
    ```
    """
    # In a full implementation, you could revoke the token with Keycloak
    # For now, client-side deletion is sufficient
    return {"message": "Logged out successfully. Please delete tokens from client."}
