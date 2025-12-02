"""
Keycloak Admin API wrapper
"""
import httpx
from typing import List, Optional, Dict, Any
from app.config import settings
import json

def _admin_token() -> str:
    """Get admin access token"""
    token_url = f"{settings.keycloak_url}/realms/master/protocol/openid-connect/token"
    data = {
        "client_id": "admin-cli",
        "grant_type": "password",
        "username": settings.keycloak_admin_user,
        "password": settings.keycloak_admin_password,
    }
    with httpx.Client() as client:
        r = client.post(token_url, data=data)
        r.raise_for_status()
        return r.json()["access_token"]

def _admin_headers() -> dict:
    """Get headers with admin token"""
    token = _admin_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

# ============= USER MANAGEMENT =============

def list_users(search: Optional[str] = None) -> List[dict]:
    """List all users in realm"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users"
    headers = _admin_headers()
    params = {"search": search} if search else {}
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

def get_user(user_id: str) -> dict:
    """Get user by ID"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def create_user(
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    enabled: bool = True,
    email_verified: bool = True,
    attributes: Optional[dict] = None
) -> str:
    """
    Create new user
    Returns user ID
    """
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users"
    
    payload = {
        "username": username,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": enabled,
        "emailVerified": email_verified,
        "requiredActions": []
    }
    
    if attributes:
        payload["attributes"] = attributes
    
    headers = _admin_headers()
    headers["Content-Type"] = "application/json"
    
    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload)
        
        if response.status_code not in (201, 409):
            response.raise_for_status()
        
        # Get user ID
        users = client.get(url, headers=headers, params={"username": username}).json()
        if not users:
            raise RuntimeError("User not found after creation")
        
        return users[0]["id"]

def update_user(user_id: str, user_data: dict) -> None:
    """Update user"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.put(url, headers=headers, json=user_data)
        response.raise_for_status()

def delete_user(user_id: str) -> None:
    """Delete user"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.delete(url, headers=headers)
        if response.status_code not in (204, 404):
            response.raise_for_status()

def set_user_password(user_id: str, password: str, temporary: bool = False) -> None:
    """Set user password"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/reset-password"
    
    payload = {
        "type": "password",
        "value": password,
        "temporary": temporary
    }
    
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.put(url, headers=headers, json=payload)
        response.raise_for_status()

# ============= ROLE MANAGEMENT =============

def list_realm_roles() -> List[dict]:
    """Get all realm roles"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def get_realm_role(role_name: str) -> dict:
    """Get realm role by name"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles/{role_name}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def create_realm_role(role_name: str, description: Optional[str] = None) -> None:
    """Create new realm role"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles"
    
    payload = {"name": role_name}
    if description:
        payload["description"] = description
    
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload)
        if response.status_code not in (201, 409):
            response.raise_for_status()

def delete_realm_role(role_name: str) -> None:
    """Delete realm role"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles/{role_name}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.delete(url, headers=headers)
        if response.status_code not in (204, 404):
            response.raise_for_status()

def get_user_roles(user_id: str) -> List[dict]:
    """Get user's realm roles"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/role-mappings/realm"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def assign_roles_to_user(user_id: str, role_names: List[str]) -> None:
    """Assign realm roles to user"""
    if not role_names:
        return
    
    headers = _admin_headers()
    roles = []
    
    with httpx.Client() as client:
        # Fetch role objects
        for role_name in role_names:
            if not role_name:
                continue
            try:
                role_url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles/{role_name}"
                r = client.get(role_url, headers=headers)
                if r.status_code == 200:
                    roles.append(r.json())
            except Exception:
                continue
        
        if not roles:
            return
        
        # Assign roles
        url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/role-mappings/realm"
        response = client.post(url, headers=headers, json=roles)
        
        if response.status_code not in (204, 409):
            response.raise_for_status()

def remove_roles_from_user(user_id: str, role_names: List[str]) -> None:
    """Remove realm roles from user"""
    if not role_names:
        return
    
    headers = _admin_headers()
    roles = []
    
    with httpx.Client() as client:
        # Fetch role objects
        for role_name in role_names:
            try:
                role_url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles/{role_name}"
                r = client.get(role_url, headers=headers)
                if r.status_code == 200:
                    roles.append(r.json())
            except Exception:
                continue
        
        if not roles:
            return
        
        # Remove roles
        url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/role-mappings/realm"
        response = client.delete(url, headers=headers, json=roles)
        
        if response.status_code not in (204, 404):
            response.raise_for_status()

# ============= GROUP MANAGEMENT =============

def list_groups() -> List[dict]:
    """Get all groups"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/groups"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def get_group(group_id: str) -> dict:
    """Get group by ID"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/groups/{group_id}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def create_group(group_name: str) -> str:
    """
    Create new group
    Returns group ID
    """
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/groups"
    
    payload = {"name": group_name}
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload)
        
        if response.status_code not in (201, 409):
            response.raise_for_status()
        
        # Get group ID
        groups = client.get(url, headers=headers).json()
        for group in groups:
            if group["name"] == group_name:
                return group["id"]
        
        raise RuntimeError("Group not found after creation")

def delete_group(group_id: str) -> None:
    """Delete group"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/groups/{group_id}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.delete(url, headers=headers)
        if response.status_code not in (204, 404):
            response.raise_for_status()

def get_user_groups(user_id: str) -> List[dict]:
    """Get user's groups"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/groups"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def add_user_to_group(user_id: str, group_id: str) -> None:
    """Add user to group"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/groups/{group_id}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.put(url, headers=headers)
        if response.status_code not in (204, 409):
            response.raise_for_status()

def remove_user_from_group(user_id: str, group_id: str) -> None:
    """Remove user from group"""
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/groups/{group_id}"
    headers = _admin_headers()
    
    with httpx.Client() as client:
        response = client.delete(url, headers=headers)
        if response.status_code not in (204, 404):
            response.raise_for_status()
