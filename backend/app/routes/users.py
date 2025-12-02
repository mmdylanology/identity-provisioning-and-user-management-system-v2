"""
User management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.auth import verify_bearer_token, require_superadmin
from app import keycloak_admin

router = APIRouter()

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    firstName: str
    lastName: str
    enabled: bool
    emailVerified: bool

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    firstName: str
    lastName: str
    password: str
    roles: Optional[List[str]] = []
    groups: Optional[List[str]] = []
    enabled: bool = True

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    enabled: Optional[bool] = None

class PasswordResetRequest(BaseModel):
    password: str
    temporary: bool = False

@router.get("/users", response_model=UserListResponse)
def list_users(
    search: Optional[str] = Query(None, description="Search by username or email"),
    token: dict = Depends(verify_bearer_token)
):
    """
    List all users in realm
    
    **Requires:** Valid Bearer token
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Query Parameters:**
    - `search` (optional): Search term for filtering users
    
    **Response:**
    ```json
    {
        "users": [
            {
                "id": "abc123",
                "username": "malik",
                "email": "malik@example.com",
                "firstName": "Malik",
                "lastName": "Khan",
                "enabled": true,
                "emailVerified": true
            }
        ],
        "total": 1
    }
    ```
    """
    try:
        users = keycloak_admin.list_users(search=search)
        
        user_list = [
            UserResponse(
                id=user["id"],
                username=user.get("username", ""),
                email=user.get("email", ""),
                firstName=user.get("firstName", ""),
                lastName=user.get("lastName", ""),
                enabled=user.get("enabled", False),
                emailVerified=user.get("emailVerified", False)
            )
            for user in users
        ]
        
        return UserListResponse(users=user_list, total=len(user_list))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    token: dict = Depends(verify_bearer_token)
):
    """
    Get user by ID
    
    **Requires:** Valid Bearer token
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `user_id`: Keycloak user ID
    
    **Response:**
    ```json
    {
        "id": "abc123",
        "username": "malik",
        "email": "malik@example.com",
        "firstName": "Malik",
        "lastName": "Khan",
        "enabled": true,
        "emailVerified": true
    }
    ```
    """
    try:
        user = keycloak_admin.get_user(user_id)
        
        return UserResponse(
            id=user["id"],
            username=user.get("username", ""),
            email=user.get("email", ""),
            firstName=user.get("firstName", ""),
            lastName=user.get("lastName", ""),
            enabled=user.get("enabled", False),
            emailVerified=user.get("emailVerified", False)
        )
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"User not found: {str(e)}")

@router.post("/users", status_code=201)
def create_user(
    user: UserCreateRequest,
    token: dict = Depends(verify_bearer_token)
):
    """
    Create new user
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Request Body:**
    ```json
    {
        "username": "johndoe",
        "email": "john@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "password": "secure123",
        "roles": ["developer"],
        "groups": ["ml-team"],
        "enabled": true
    }
    ```
    
    **Response:**
    ```json
    {
        "user_id": "new_user_id_123",
        "message": "User created successfully"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        # Create user
        user_id = keycloak_admin.create_user(
            username=user.username,
            email=user.email,
            first_name=user.firstName,
            last_name=user.lastName,
            enabled=user.enabled
        )
        
        # Set password
        keycloak_admin.set_user_password(user_id, user.password, temporary=False)
        
        # Assign roles
        if user.roles:
            keycloak_admin.assign_roles_to_user(user_id, user.roles)
        
        # Add to groups
        if user.groups:
            all_groups = keycloak_admin.list_groups()
            group_map = {g["name"]: g["id"] for g in all_groups}
            
            for group_name in user.groups:
                if group_name in group_map:
                    keycloak_admin.add_user_to_group(user_id, group_map[group_name])
        
        return {
            "user_id": user_id,
            "message": "User created successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    user_update: UserUpdateRequest,
    token: dict = Depends(verify_bearer_token)
):
    """
    Update user information
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `user_id`: Keycloak user ID
    
    **Request Body:**
    ```json
    {
        "email": "newemail@example.com",
        "firstName": "NewFirst",
        "lastName": "NewLast",
        "enabled": false
    }
    ```
    
    **Response:**
    ```json
    {
        "message": "User updated successfully"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        # Get current user data
        current_user = keycloak_admin.get_user(user_id)
        
        # Update only provided fields
        if user_update.email is not None:
            current_user["email"] = user_update.email
        if user_update.firstName is not None:
            current_user["firstName"] = user_update.firstName
        if user_update.lastName is not None:
            current_user["lastName"] = user_update.lastName
        if user_update.enabled is not None:
            current_user["enabled"] = user_update.enabled
        
        # Update user
        keycloak_admin.update_user(user_id, current_user)
        
        return {"message": "User updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    token: dict = Depends(verify_bearer_token)
):
    """
    Delete user
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `user_id`: Keycloak user ID
    
    **Response:** 204 No Content
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.delete_user(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@router.put("/users/{user_id}/password")
def reset_password(
    user_id: str,
    password_reset: PasswordResetRequest,
    token: dict = Depends(verify_bearer_token)
):
    """
    Reset user password
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `user_id`: Keycloak user ID
    
    **Request Body:**
    ```json
    {
        "password": "newpassword123",
        "temporary": false
    }
    ```
    
    **Response:**
    ```json
    {
        "message": "Password reset successfully"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.set_user_password(
            user_id,
            password_reset.password,
            temporary=password_reset.temporary
        )
        
        return {"message": "Password reset successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset password: {str(e)}")

@router.get("/users/{user_id}/roles")
def get_user_roles(
    user_id: str,
    token: dict = Depends(verify_bearer_token)
):
    """
    Get user's roles
    
    **Requires:** Valid Bearer token
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `user_id`: Keycloak user ID
    
    **Response:**
    ```json
    {
        "roles": [
            {
                "id": "role_id",
                "name": "realm-admin",
                "description": "Realm admin role"
            }
        ]
    }
    ```
    """
    try:
        roles = keycloak_admin.get_user_roles(user_id)
        return {"roles": roles}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user roles: {str(e)}")

@router.get("/users/{user_id}/groups")
def get_user_groups(
    user_id: str,
    token: dict = Depends(verify_bearer_token)
):
    """
    Get user's groups
    
    **Requires:** Valid Bearer token
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `user_id`: Keycloak user ID
    
    **Response:**
    ```json
    {
        "groups": [
            {
                "id": "group_id",
                "name": "ml-team",
                "path": "/ml-team"
            }
        ]
    }
    ```
    """
    try:
        groups = keycloak_admin.get_user_groups(user_id)
        return {"groups": groups}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user groups: {str(e)}")
