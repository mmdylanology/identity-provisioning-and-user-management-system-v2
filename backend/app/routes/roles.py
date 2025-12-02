"""
Role management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.auth import verify_bearer_token, require_superadmin
from app import keycloak_admin

router = APIRouter()

class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    composite: bool = False

class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total: int

class RoleCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class RoleAssignRequest(BaseModel):
    roles: List[str]

@router.get("/roles", response_model=RoleListResponse)
def list_roles(token: dict = Depends(verify_bearer_token)):
    """
    List all realm roles
    
    **Requires:** Valid Bearer token
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Response:**
    ```json
    {
        "roles": [
            {
                "id": "role_id",
                "name": "realm-admin",
                "description": "Realm administrator",
                "composite": false
            }
        ],
        "total": 3
    }
    ```
    """
    try:
        roles = keycloak_admin.list_realm_roles()
        
        role_list = [
            RoleResponse(
                id=role["id"],
                name=role["name"],
                description=role.get("description"),
                composite=role.get("composite", False)
            )
            for role in roles
        ]
        
        return RoleListResponse(roles=role_list, total=len(role_list))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list roles: {str(e)}")

@router.post("/roles", status_code=201)
def create_role(
    role: RoleCreateRequest,
    token: dict = Depends(verify_bearer_token)
):
    """
    Create new realm role
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Request Body:**
    ```json
    {
        "name": "custom-role",
        "description": "Custom role description"
    }
    ```
    
    **Response:**
    ```json
    {
        "message": "Role created successfully",
        "role_name": "custom-role"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.create_realm_role(role.name, role.description)
        
        return {
            "message": "Role created successfully",
            "role_name": role.name
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create role: {str(e)}")

@router.delete("/roles/{role_name}", status_code=204)
def delete_role(
    role_name: str,
    token: dict = Depends(verify_bearer_token)
):
    """
    Delete realm role
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `role_name`: Name of the role to delete
    
    **Response:** 204 No Content
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.delete_realm_role(role_name)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete role: {str(e)}")

@router.post("/users/{user_id}/roles")
def assign_roles(
    user_id: str,
    role_assign: RoleAssignRequest,
    token: dict = Depends(verify_bearer_token)
):
    """
    Assign roles to user
    
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
        "roles": ["developer", "manager"]
    }
    ```
    
    **Response:**
    ```json
    {
        "message": "Roles assigned successfully"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.assign_roles_to_user(user_id, role_assign.roles)
        
        return {"message": "Roles assigned successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign roles: {str(e)}")

@router.delete("/users/{user_id}/roles")
def remove_roles(
    user_id: str,
    role_assign: RoleAssignRequest,
    token: dict = Depends(verify_bearer_token)
):
    """
    Remove roles from user
    
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
        "roles": ["developer"]
    }
    ```
    
    **Response:**
    ```json
    {
        "message": "Roles removed successfully"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.remove_roles_from_user(user_id, role_assign.roles)
        
        return {"message": "Roles removed successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove roles: {str(e)}")
