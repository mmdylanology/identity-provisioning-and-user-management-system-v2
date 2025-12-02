"""
Group management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.auth import verify_bearer_token, require_superadmin
from app import keycloak_admin

router = APIRouter()

class GroupResponse(BaseModel):
    id: str
    name: str
    path: str

class GroupListResponse(BaseModel):
    groups: List[GroupResponse]
    total: int

class GroupCreateRequest(BaseModel):
    name: str

class GroupAssignRequest(BaseModel):
    group_id: str

@router.get("/groups", response_model=GroupListResponse)
def list_groups(token: dict = Depends(verify_bearer_token)):
    """
    List all groups
    
    **Requires:** Valid Bearer token
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Response:**
    ```json
    {
        "groups": [
            {
                "id": "group_id",
                "name": "ml-team",
                "path": "/ml-team"
            }
        ],
        "total": 2
    }
    ```
    """
    try:
        groups = keycloak_admin.list_groups()
        
        group_list = [
            GroupResponse(
                id=group["id"],
                name=group["name"],
                path=group.get("path", f"/{group['name']}")
            )
            for group in groups
        ]
        
        return GroupListResponse(groups=group_list, total=len(group_list))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list groups: {str(e)}")

@router.post("/groups", status_code=201)
def create_group(
    group: GroupCreateRequest,
    token: dict = Depends(verify_bearer_token)
):
    """
    Create new group
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Request Body:**
    ```json
    {
        "name": "new-team"
    }
    ```
    
    **Response:**
    ```json
    {
        "group_id": "new_group_id",
        "message": "Group created successfully"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        group_id = keycloak_admin.create_group(group.name)
        
        return {
            "group_id": group_id,
            "message": "Group created successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")

@router.delete("/groups/{group_id}", status_code=204)
def delete_group(
    group_id: str,
    token: dict = Depends(verify_bearer_token)
):
    """
    Delete group
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `group_id`: Keycloak group ID
    
    **Response:** 204 No Content
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.delete_group(group_id)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete group: {str(e)}")

@router.put("/users/{user_id}/groups/{group_id}")
def add_user_to_group(
    user_id: str,
    group_id: str,
    token: dict = Depends(verify_bearer_token)
):
    """
    Add user to group
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `user_id`: Keycloak user ID
    - `group_id`: Keycloak group ID
    
    **Response:**
    ```json
    {
        "message": "User added to group successfully"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.add_user_to_group(user_id, group_id)
        
        return {"message": "User added to group successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add user to group: {str(e)}")

@router.delete("/users/{user_id}/groups/{group_id}")
def remove_user_from_group(
    user_id: str,
    group_id: str,
    token: dict = Depends(verify_bearer_token)
):
    """
    Remove user from group
    
    **Requires:** Bearer token with realm-admin role
    
    **Headers:**
    ```
    Authorization: Bearer eyJhbGc...
    ```
    
    **Path Parameters:**
    - `user_id`: Keycloak user ID
    - `group_id`: Keycloak group ID
    
    **Response:**
    ```json
    {
        "message": "User removed from group successfully"
    }
    ```
    """
    # Check if user is superadmin
    require_superadmin(token)
    
    try:
        keycloak_admin.remove_user_from_group(user_id, group_id)
        
        return {"message": "User removed from group successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove user from group: {str(e)}")
