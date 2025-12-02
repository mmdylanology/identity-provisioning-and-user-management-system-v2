"""
Bootstrap script to initialize Keycloak with realm, users, roles, and groups
"""
import os
import sys
import time
import httpx

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def wait_for_keycloak():
    """Wait for Keycloak to be ready"""
    print("Waiting for Keycloak to be ready...")
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            response = httpx.get(f"{settings.keycloak_url}/health/ready", timeout=5.0)
            if response.status_code == 200:
                print("Keycloak is ready!")
                return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"Attempt {i+1}/{max_retries}: Keycloak not ready yet, retrying in {retry_interval}s...")
                time.sleep(retry_interval)
            else:
                print(f"Failed to connect to Keycloak after {max_retries} attempts")
                return False
    
    return False

def get_admin_token():
    """Get admin access token"""
    data = {
        "username": settings.keycloak_admin_user,
        "password": settings.keycloak_admin_password,
        "grant_type": "password",
        "client_id": "admin-cli"
    }
    
    response = httpx.post(
        f"{settings.keycloak_url}/realms/master/protocol/openid-connect/token",
        data=data,
        timeout=10.0
    )
    response.raise_for_status()
    return response.json()["access_token"]

def create_realm(token):
    """Create iam-realm if it doesn't exist"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check if realm exists
    response = httpx.get(
        f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}",
        headers=headers,
        timeout=10.0
    )
    
    if response.status_code == 200:
        print(f"Realm '{settings.keycloak_realm}' already exists")
        return
    
    # Create realm
    realm_data = {
        "realm": settings.keycloak_realm,
        "enabled": True,
        "displayName": "IAM Realm",
        "accessTokenLifespan": 300,
        "refreshTokenMaxReuse": 0,
        "ssoSessionIdleTimeout": 1800,
        "ssoSessionMaxLifespan": 36000
    }
    
    response = httpx.post(
        f"{settings.keycloak_url}/admin/realms",
        headers=headers,
        json=realm_data,
        timeout=10.0
    )
    
    if response.status_code == 201:
        print(f"Created realm '{settings.keycloak_realm}'")
    else:
        print(f"Failed to create realm: {response.text}")

def create_client(token):
    """Create iam-api client if it doesn't exist"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get clients
    response = httpx.get(
        f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/clients",
        headers=headers,
        params={"clientId": settings.keycloak_client_id},
        timeout=10.0
    )
    
    if response.status_code == 200 and len(response.json()) > 0:
        print(f"Client '{settings.keycloak_client_id}' already exists")
        return
    
    # Create client
    client_data = {
        "clientId": settings.keycloak_client_id,
        "enabled": True,
        "publicClient": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": True,
        "standardFlowEnabled": True,
        "secret": settings.keycloak_client_secret,
        "redirectUris": ["*"],
        "webOrigins": ["*"]
    }
    
    response = httpx.post(
        f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/clients",
        headers=headers,
        json=client_data,
        timeout=10.0
    )
    
    if response.status_code == 201:
        print(f"Created client '{settings.keycloak_client_id}'")
    else:
        print(f"Failed to create client: {response.text}")

def create_roles(token):
    """Create realm roles"""
    headers = {"Authorization": f"Bearer {token}"}
    
    roles = [
        {"name": "realm-admin", "description": "Realm administrator with full access"},
        {"name": "user-manager", "description": "Can manage users"},
        {"name": "viewer", "description": "Read-only access"}
    ]
    
    for role in roles:
        # Check if role exists
        response = httpx.get(
            f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles/{role['name']}",
            headers=headers,
            timeout=10.0
        )
        
        if response.status_code == 200:
            print(f"Role '{role['name']}' already exists")
            continue
        
        # Create role
        response = httpx.post(
            f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles",
            headers=headers,
            json=role,
            timeout=10.0
        )
        
        if response.status_code == 201:
            print(f"Created role '{role['name']}'")
        else:
            print(f"Failed to create role '{role['name']}': {response.text}")

def create_groups(token):
    """Create groups"""
    headers = {"Authorization": f"Bearer {token}"}
    
    groups = ["admins", "developers", "analysts"]
    
    for group_name in groups:
        # Create group
        response = httpx.post(
            f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/groups",
            headers=headers,
            json={"name": group_name},
            timeout=10.0
        )
        
        if response.status_code == 201:
            print(f"Created group '{group_name}'")
        elif response.status_code == 409:
            print(f"Group '{group_name}' already exists")
        else:
            print(f"Failed to create group '{group_name}': {response.text}")

def create_users(token):
    """Create test users"""
    headers = {"Authorization": f"Bearer {token}"}
    
    users = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "firstName": "Admin",
            "lastName": "User",
            "enabled": True,
            "password": "admin123",
            "roles": ["realm-admin"]
        },
        {
            "username": "john",
            "email": "john@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "enabled": True,
            "password": "password123",
            "roles": ["user-manager"]
        }
    ]
    
    for user_data in users:
        password = user_data.pop("password")
        roles = user_data.pop("roles")
        
        # Check if user exists
        response = httpx.get(
            f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users",
            headers=headers,
            params={"username": user_data["username"], "exact": "true"},
            timeout=10.0
        )
        
        if response.status_code == 200 and len(response.json()) > 0:
            print(f"User '{user_data['username']}' already exists")
            user_id = response.json()[0]["id"]
        else:
            # Create user
            response = httpx.post(
                f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users",
                headers=headers,
                json=user_data,
                timeout=10.0
            )
            
            if response.status_code != 201:
                print(f"Failed to create user '{user_data['username']}': {response.text}")
                continue
            
            print(f"Created user '{user_data['username']}'")
            
            # Get user ID from location header
            user_id = response.headers["Location"].split("/")[-1]
        
        # Set password
        password_data = {
            "type": "password",
            "value": password,
            "temporary": False
        }
        
        response = httpx.put(
            f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/reset-password",
            headers=headers,
            json=password_data,
            timeout=10.0
        )
        
        if response.status_code == 204:
            print(f"Set password for '{user_data['username']}'")
        
        # Assign roles
        for role_name in roles:
            # Get role
            response = httpx.get(
                f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/roles/{role_name}",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"Role '{role_name}' not found")
                continue
            
            role_data = response.json()
            
            # Assign role
            response = httpx.post(
                f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/role-mappings/realm",
                headers=headers,
                json=[{"id": role_data["id"], "name": role_data["name"]}],
                timeout=10.0
            )
            
            if response.status_code == 204:
                print(f"Assigned role '{role_name}' to '{user_data['username']}'")

def main():
    """Main bootstrap function"""
    print("=" * 60)
    print("Keycloak Bootstrap Script")
    print("=" * 60)
    
    # Wait for Keycloak
    if not wait_for_keycloak():
        print("ERROR: Keycloak is not ready. Exiting.")
        sys.exit(1)
    
    try:
        # Get admin token
        print("\n1. Getting admin token...")
        token = get_admin_token()
        print("✓ Admin token obtained")
        
        # Create realm
        print("\n2. Creating realm...")
        create_realm(token)
        
        # Create client
        print("\n3. Creating client...")
        create_client(token)
        
        # Create roles
        print("\n4. Creating roles...")
        create_roles(token)
        
        # Create groups
        print("\n5. Creating groups...")
        create_groups(token)
        
        # Create users
        print("\n6. Creating users...")
        create_users(token)
        
        print("\n" + "=" * 60)
        print("Bootstrap completed successfully!")
        print("=" * 60)
        print("\nTest credentials:")
        print("  Admin user: admin / admin123")
        print("  Regular user: john / password123")
        print("\nYou can now access:")
        print("  Frontend: http://localhost:3000")
        print("  Backend API: http://localhost:8001")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: Bootstrap failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
