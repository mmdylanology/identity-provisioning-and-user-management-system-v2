# IAM Admin Portal V2

A modern Identity and Access Management (IAM) administrative portal built with React, FastAPI, and Keycloak. This application provides a comprehensive interface for managing users, roles, and groups with full REST API support.

## 🏗️ Architecture

The application uses a microservices architecture with three main components:

- **Frontend**: React 18 + Vite (Port 3001)
- **Backend**: FastAPI REST API (Port 8001)
- **Keycloak**: Identity Provider (Port 8082)

All services run in Docker containers and communicate over a private Docker network (`iam-net-v2`).

## ✨ Features

### User Management
- ✅ Create, read, update, and delete users
- ✅ Assign multiple roles to users during creation
- ✅ Add users to multiple groups during creation
- ✅ Edit user roles and groups after creation
- ✅ Search and filter users
- ✅ Reset user passwords
- ✅ Enable/disable user accounts

### Role Management
- ✅ Create and delete realm roles
- ✅ Assign/remove roles from users
- ✅ View all roles with descriptions
- ✅ Track role assignments per user

### Group Management
- ✅ Create and delete groups
- ✅ Add/remove users from groups
- ✅ View group memberships
- ✅ Organize users by teams

### Authentication & Authorization
- ✅ JWT-based authentication
- ✅ Automatic token refresh
- ✅ Role-based access control (RBAC)
- ✅ Protected routes
- ✅ Session management with 5-minute token expiry

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- macOS, Linux, or Windows with WSL2

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd iam-admin-portal/v2-api-version
   ```

2. **Configure environment variables**
   
   The `.env` file is already configured with default values:
   ```env
   keycloak_url=http://keycloak:8080
   keycloak_realm=iam-realm-v2
   keycloak_client_id=iam-api-v2
   keycloak_client_secret=your-secret-here
   keycloak_admin_username=admin
   keycloak_admin_password=admin
   jwt_algorithm=RS256
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

4. **Bootstrap Keycloak (First time only)**
   ```bash
   python bootstrap_keycloak.py
   ```
   
   This script creates:
   - Realm: `iam-realm-v2`
   - Client: `iam-api-v2` with client secret
   - Roles: `realm-admin`, `user-manager`, `viewer`
   - Groups: `admins`, `analysts`, `developers`
   - Users: `admin` (realm-admin), `john` (user-manager)

5. **Access the application**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs
   - Keycloak Admin: http://localhost:8082

### Default Credentials

**Admin User:**
- Username: `admin`
- Password: `admin123`
- Role: `realm-admin`

**Regular User:**
- Username: `john`
- Password: `password123`
- Role: `user-manager`

**Keycloak Admin Console:**
- Username: `admin`
- Password: `admin`

## 📡 API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/login
User login with credentials

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 300,
  "user": {
    "id": "b7be5e54-954b-4bcb-a9f5-373374898b74",
    "username": "admin",
    "email": "admin@example.com",
    "name": "Admin User",
    "realm_access": {
      "roles": ["realm-admin", "offline_access"]
    }
  }
}
```

#### POST /api/v1/auth/refresh
Refresh expired access token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 300,
  "user": {
    "id": "b7be5e54-954b-4bcb-a9f5-373374898b74",
    "username": "admin",
    "email": "admin@example.com",
    "name": "Admin User",
    "realm_access": {
      "roles": ["realm-admin", "offline_access"]
    }
  }
}
```

### User Management Endpoints

#### GET /api/v1/users
List all users with optional search

**Query Parameters:**
- `search` (optional): Search by username, email, first/last name

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "users": [
    {
      "id": "b7be5e54-954b-4bcb-a9f5-373374898b74",
      "username": "admin",
      "email": "admin@example.com",
      "firstName": "Admin",
      "lastName": "User",
      "enabled": true,
      "emailVerified": false
    }
  ],
  "total": 1
}
```

#### POST /api/v1/users
Create new user with roles and groups (requires realm-admin)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "firstName": "New",
  "lastName": "User",
  "password": "password123",
  "roles": ["viewer", "user-manager"],
  "groups": ["analysts", "developers"],
  "enabled": true
}
```

**Response (201):**
```json
{
  "user_id": "5e7c4920-98d8-49d2-8528-f8648ac82603",
  "message": "User created successfully"
}
```

#### GET /api/v1/users/{user_id}
Get user details by ID

**Response (200):**
```json
{
  "id": "b7be5e54-954b-4bcb-a9f5-373374898b74",
  "username": "admin",
  "email": "admin@example.com",
  "firstName": "Admin",
  "lastName": "User",
  "enabled": true,
  "emailVerified": false
}
```

#### PUT /api/v1/users/{user_id}
Update user information (requires realm-admin)

**Request:**
```json
{
  "email": "newemail@example.com",
  "firstName": "NewFirst",
  "lastName": "NewLast",
  "enabled": false
}
```

**Response (200):**
```json
{
  "message": "User updated successfully"
}
```

#### DELETE /api/v1/users/{user_id}
Delete user (requires realm-admin)

**Response:** 204 No Content

#### GET /api/v1/users/{user_id}/roles
Get user's assigned roles

**Response (200):**
```json
{
  "roles": [
    {
      "id": "role-uuid",
      "name": "realm-admin",
      "description": "Realm administrator with full access"
    }
  ]
}
```

#### GET /api/v1/users/{user_id}/groups
Get user's group memberships

**Response (200):**
```json
{
  "groups": [
    {
      "id": "group-uuid",
      "name": "admins",
      "path": "/admins"
    }
  ]
}
```

#### PUT /api/v1/users/{user_id}/password
Reset user password (requires realm-admin)

**Request:**
```json
{
  "password": "newpassword123",
  "temporary": false
}
```

**Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

### Role Management Endpoints

#### GET /api/v1/roles
List all realm roles

**Response (200):**
```json
{
  "roles": [
    {
      "id": "role-uuid",
      "name": "realm-admin",
      "description": "Realm administrator with full access",
      "composite": false
    },
    {
      "id": "role-uuid-2",
      "name": "viewer",
      "description": "Read-only access",
      "composite": false
    }
  ],
  "total": 2
}
```

#### POST /api/v1/roles
Create new realm role (requires realm-admin)

**Request:**
```json
{
  "name": "custom-role",
  "description": "Custom role description"
}
```

**Response (201):**
```json
{
  "message": "Role created successfully",
  "role_name": "custom-role"
}
```

#### DELETE /api/v1/roles/{role_name}
Delete realm role (requires realm-admin)

**Response:** 204 No Content

#### POST /api/v1/users/{user_id}/roles
Assign roles to user (requires realm-admin)

**Request:**
```json
{
  "roles": ["viewer", "user-manager"]
}
```

**Response (200):**
```json
{
  "message": "Roles assigned successfully"
}
```

#### DELETE /api/v1/users/{user_id}/roles
Remove roles from user (requires realm-admin)

**Request:**
```json
{
  "roles": ["viewer"]
}
```

**Response (200):**
```json
{
  "message": "Roles removed successfully"
}
```

### Group Management Endpoints

#### GET /api/v1/groups
List all groups

**Response (200):**
```json
{
  "groups": [
    {
      "id": "group-uuid",
      "name": "admins",
      "path": "/admins"
    },
    {
      "id": "group-uuid-2",
      "name": "developers",
      "path": "/developers"
    }
  ],
  "total": 2
}
```

#### POST /api/v1/groups
Create new group (requires realm-admin)

**Request:**
```json
{
  "name": "new-team"
}
```

**Response (201):**
```json
{
  "group_id": "group-uuid",
  "message": "Group created successfully"
}
```

#### DELETE /api/v1/groups/{group_id}
Delete group (requires realm-admin)

**Response:** 204 No Content

#### PUT /api/v1/users/{user_id}/groups/{group_id}
Add user to group (requires realm-admin)

**Response (200):**
```json
{
  "message": "User added to group successfully"
}
```

#### DELETE /api/v1/users/{user_id}/groups/{group_id}
Remove user from group (requires realm-admin)

**Response (200):**
```json
{
  "message": "User removed from group successfully"
}
```

### Error Responses

All endpoints may return the following error codes:

- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: Insufficient permissions (realm-admin required)
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

**Error Response Format:**
```json
{
  "detail": "Error message description"
}
```

**Full API documentation available at:** http://localhost:8001/docs

## 🎨 Frontend Features

### Navigation
- Clean, responsive navbar with dark background
- Bright white navigation links with cyan hover effects
- User info display (username) in bold white
- Quick logout button
- Smooth transitions and visual feedback

### Login Page
- Simple, centered login form
- Email/password authentication
- Error message display
- Automatic redirect to dashboard on success

### Dashboard
- Overview statistics cards
- Total users, roles, and groups count
- Quick navigation to management pages
- Clean, card-based layout

### User Management Page
- **List View**:
  - Searchable user table
  - Display: username, email, first name, last name, enabled status
  - Edit and delete actions per user
  
- **Create User Form**:
  - Basic info: username, email, first/last name, password
  - Multi-select dropdown for roles (hold Ctrl/Cmd)
  - Multi-select dropdown for groups (optional, hold Ctrl/Cmd)
  - Real-time display of selected roles and groups
  - Enable/disable account checkbox
  
- **Edit User Form**:
  - Update basic info (email, first/last name, enabled status)
  - View and modify assigned roles
  - View and modify group memberships
  - Username is read-only (cannot be changed)
  - Smart update: only changes modified roles/groups

### Role Management Page
- View all available realm roles
- Create custom roles with descriptions
- Delete roles (with confirmation)
- Filter out system roles from display

### Group Management Page
- View all groups
- Create new groups for organizing users
- Delete groups (with confirmation)
- Manage group memberships

### UI/UX Features
- Modal dialogs for create/edit operations
- Confirmation prompts for destructive actions (delete)
- Error message display with red alerts
- Success feedback on operations
- Responsive design
- Loading states
- Clean, modern styling with cards and tables

## 🔧 Configuration

### Environment Variables

All configuration is managed through the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `keycloak_url` | Internal Keycloak URL for backend | `http://keycloak:8080` |
| `keycloak_realm` | Keycloak realm name | `iam-realm-v2` |
| `keycloak_client_id` | Client ID for API authentication | `iam-api-v2` |
| `keycloak_client_secret` | Client secret (generated during bootstrap) | Set by bootstrap script |
| `keycloak_admin_username` | Keycloak admin console username | `admin` |
| `keycloak_admin_password` | Keycloak admin console password | `admin` |
| `jwt_algorithm` | JWT signing algorithm | `RS256` |

### Port Configuration

| Service | Internal Port | Exposed Port | Description |
|---------|--------------|--------------|-------------|
| Frontend | 80 | 3001 | React app served by nginx |
| Backend | 8000 | 8001 | FastAPI REST API |
| Keycloak | 8080 | 8082 | Keycloak admin UI |

### Docker Network

All services communicate over `iam-net-v2` bridge network:
- Frontend → Backend: `http://backend:8000`
- Backend → Keycloak: `http://keycloak:8080`
- Browser → Frontend: `http://localhost:3001`
- Browser → Keycloak: `http://localhost:8082` (admin only)

## 🔐 Authentication Flow

1. **Login**
   - User submits credentials to `/api/v1/auth/login`
   - Backend validates with Keycloak using client credentials
   - Keycloak returns JWT access token and refresh token
   - Backend decodes token, extracts user info
   - Returns tokens + user data to frontend
   - Frontend stores in localStorage

2. **API Requests**
   - Frontend includes `Authorization: Bearer <token>` header
   - Backend validates JWT signature using Keycloak JWKS public keys
   - Backend checks user roles for authorization (realm-admin required for admin operations)
   - Request processed and response returned

3. **Token Refresh**
   - Access tokens expire after 5 minutes (300 seconds)
   - Axios interceptor catches 401 responses
   - Automatically calls `/api/v1/auth/refresh` with refresh token
   - New access token obtained and original request retried
   - Transparent to user experience

4. **Logout**
   - Clears tokens from localStorage
   - Redirects to login page
   - Token becomes invalid (no server-side invalidation needed)

## 🔄 Complete System Flow & Architecture

### Service Communication Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Browser (End User)                          │
│                        http://localhost:3001                         │
└────────────┬──────────────────────────────────────┬──────────────────┘
             │                                      │
             │ HTTP Requests                        │ (Optional)
             │                                      │ Admin Console Access
             ▼                                      ▼
┌─────────────────────────────┐         ┌──────────────────────────────┐
│   Frontend (React + Nginx)  │         │  Keycloak Admin Console      │
│   Container: iam-frontend-v2│         │  http://localhost:8082       │
│   Port: 80 (internal)       │         │  (Exposed for admin only)    │
│   Exposed: 3001             │         └──────────────────────────────┘
└────────────┬────────────────┘
             │
             │ Proxied API calls
             │ /api/v1/* → backend:8000
             ▼
┌─────────────────────────────┐
│  Backend (FastAPI)          │
│  Container: iam-backend-v2  │
│  Port: 8000 (internal)      │
│  Exposed: 8001              │
└────────────┬────────────────┘
             │
             │ Admin API calls
             │ http://keycloak:8080
             ▼
┌─────────────────────────────┐
│  Keycloak (Identity Server) │
│  Container: kc-v2           │
│  Port: 8080 (internal)      │
│  Exposed: 8082 (optional)   │
└─────────────────────────────┘

All services connected via Docker network: iam-net-v2
```

### Detailed Flow Explanation

#### 1. **Frontend to Backend Communication**

**User Login Flow:**
```
1. User opens http://localhost:3001 → Browser
2. React app loads from nginx (port 80 internal)
3. User enters credentials on login page
4. Frontend sends: POST /api/v1/auth/login
   ├─ nginx receives request at port 80
   ├─ nginx.conf proxies: /api/* → http://backend:8000/api/*
   └─ Request reaches FastAPI backend
```

**API Requests:**
```
Frontend (axios) → nginx → backend:8000
   - All /api/v1/* requests go through nginx proxy
   - nginx adds proper headers
   - Internal Docker network resolution: backend = iam-backend-v2 container
```

#### 2. **Backend to Keycloak Communication**

**Login Process (Backend Internal):**
```
1. Backend receives login request
2. Backend calls Keycloak Token Endpoint:
   POST http://keycloak:8080/realms/iam-realm-v2/protocol/openid-connect/token
   ├─ Uses client_credentials grant
   ├─ Sends: client_id, client_secret, username, password
   └─ Keycloak validates credentials

3. Keycloak responds with:
   ├─ access_token (JWT, 5 min expiry)
   ├─ refresh_token (longer expiry)
   └─ token metadata

4. Backend decodes JWT to extract user info:
   ├─ User ID, username, email, name
   ├─ Realm roles (realm-admin, user-manager, etc.)
   └─ Other claims

5. Backend returns to frontend:
   {
     "access_token": "...",
     "refresh_token": "...",
     "user": { id, username, email, roles }
   }
```

**Admin Operations (Backend to Keycloak):**
```
When creating/updating users/roles/groups:

1. Backend gets admin token:
   POST http://keycloak:8080/realms/master/protocol/openid-connect/token
   ├─ Uses admin credentials (admin/admin)
   └─ Gets master realm admin token

2. Backend calls Keycloak Admin REST API:
   POST http://keycloak:8080/admin/realms/iam-realm-v2/users
   ├─ Includes admin token in Authorization header
   ├─ Sends user data
   └─ Keycloak creates user

3. Backend wraps response and returns to frontend
```

**Token Validation:**
```
For every protected API request:

1. Frontend sends: Authorization: Bearer <access_token>

2. Backend extracts token

3. Backend validates JWT:
   ├─ Gets Keycloak JWKS (public keys):
   │  GET http://keycloak:8080/realms/iam-realm-v2/protocol/openid-connect/certs
   ├─ Verifies signature using public key
   ├─ Checks expiration
   ├─ Validates issuer, audience
   └─ Extracts claims

4. If valid → Process request
   If invalid/expired → Return 401

5. Frontend intercepts 401:
   ├─ Calls /api/v1/auth/refresh with refresh_token
   ├─ Gets new access_token
   └─ Retries original request
```

#### 3. **Keycloak Exposure & Security**

**Current Configuration (Port 8082 Exposed):**
```
Keycloak is accessible from host machine:
- URL: http://localhost:8082
- Purpose: Admin console access for configuration
- Users can access: 
  ├─ Admin console (admin/admin)
  ├─ Account console
  └─ Direct token endpoints (not recommended)

Pros:
✅ Easy administration
✅ Can configure realm settings via GUI
✅ Debug authentication issues
✅ View users/roles/groups directly

Cons:
⚠️ Exposed to network (development only)
⚠️ End users could theoretically access directly
⚠️ Not production-ready
```

**Production Configuration (Not Exposed):**
```yaml
# docker-compose.yml - Remove ports section
keycloak:
  image: quay.io/keycloak/keycloak:24.0.3
  container_name: kc-v2
  # ports:              ← REMOVE THIS
  #   - "8082:8080"     ← REMOVE THIS
  networks:
    - iam-net-v2
```

**When Keycloak is NOT Exposed:**
```
Keycloak only accessible within Docker network:

✅ Better Security:
   - No external access to Keycloak
   - Only backend can communicate
   - End users never interact with Keycloak directly

✅ True API Gateway Pattern:
   Browser → Frontend → Backend → Keycloak
   Backend acts as sole gateway

❌ Trade-offs:
   - Cannot access admin console from browser
   - Must use CLI for configuration
   - Harder to debug authentication

Alternative Admin Access:
1. Docker exec into backend container
2. Use Keycloak Admin CLI (kcadm.sh)
3. Or expose temporarily for admin tasks
```

#### 4. **End User Perspective**

**What End Users See:**
```
1. Frontend Only:
   - URL: http://localhost:3001
   - Modern React UI
   - Login form, dashboard, management pages
   
2. Never See:
   - Backend API endpoint (http://localhost:8001)
   - Keycloak server (http://localhost:8082)
   - Docker containers
   - JWT tokens (except in console.log for debugging)

3. User Experience:
   ├─ Enter credentials → Login form
   ├─ Automatic token refresh → Seamless
   ├─ Role-based UI → See only what they can access
   └─ Logout → Clear and simple
```

**What Happens Behind the Scenes:**
```
User Action: "Click Login"
↓
Frontend: Collect username/password
↓
Frontend: POST /api/v1/auth/login via axios
↓
Nginx: Proxy to backend:8000
↓
Backend: Validate with Keycloak
↓
Keycloak: Check credentials, generate tokens
↓
Backend: Decode token, extract user info
↓
Frontend: Store tokens, redirect to dashboard
↓
Frontend: Fetch user-specific data
↓
Backend: Validate token for each request
↓
User: Sees personalized dashboard

All of this happens in ~500ms, transparent to user
```

#### 5. **Network Isolation & Security Layers**

**Docker Network Boundaries:**
```
iam-net-v2 (bridge network)
├─ iam-frontend-v2 (nginx + React)
│  ├─ Internal: Port 80
│  ├─ External: Port 3001
│  └─ Can talk to: backend, keycloak
│
├─ iam-backend-v2 (FastAPI)
│  ├─ Internal: Port 8000
│  ├─ External: Port 8001
│  └─ Can talk to: keycloak
│
└─ kc-v2 (Keycloak)
   ├─ Internal: Port 8080
   ├─ External: Port 8082 (optional)
   └─ Isolated from direct external access
```

**Security Layers:**
```
Layer 1: Network Isolation
├─ Services use internal DNS (backend, keycloak)
├─ External access only through exposed ports
└─ Docker network provides isolation

Layer 2: Authentication (Keycloak)
├─ Username/password validation
├─ JWT token generation
├─ Token expiration (5 minutes)
└─ Refresh token rotation

Layer 3: Authorization (Backend)
├─ JWT signature validation
├─ Role checking (realm-admin required)
├─ RBAC enforcement
└─ API endpoint protection

Layer 4: Frontend Protection
├─ Route guards (ProtectedRoute, AdminRoute)
├─ UI element hiding based on roles
├─ Token storage in localStorage
└─ Automatic token refresh
```

#### 6. **Data Flow Examples**

**Example 1: Create User (Superadmin)**
```
1. Admin clicks "Create User" button
   └─ Frontend shows modal form

2. Admin fills form: username, email, roles, groups
   └─ Frontend: formData = { username: "alice", roles: ["viewer"], ... }

3. Admin clicks "Create"
   └─ Frontend: POST /api/v1/users with access_token

4. Nginx proxies to backend:8000
   └─ Request: Authorization: Bearer eyJhbGc...

5. Backend validates token:
   ├─ Verify JWT signature with Keycloak public key
   ├─ Check realm_access.roles includes "realm-admin"
   └─ If not admin → Return 403 Forbidden

6. Backend gets admin token from Keycloak
   └─ POST http://keycloak:8080/realms/master/protocol/openid-connect/token

7. Backend creates user in Keycloak:
   └─ POST http://keycloak:8080/admin/realms/iam-realm-v2/users
   └─ Returns user_id

8. Backend assigns roles (if specified):
   └─ POST http://keycloak:8080/admin/realms/.../users/{id}/role-mappings/realm

9. Backend adds to groups (if specified):
   └─ PUT http://keycloak:8080/admin/realms/.../users/{id}/groups/{group_id}

10. Backend returns success to frontend
    └─ { user_id: "...", message: "User created successfully" }

11. Frontend shows success message, refreshes user list
```

**Example 2: Regular User Views Dashboard**
```
1. John (user-manager) logs in
   └─ Gets token with roles: ["user-manager"]

2. John's dashboard loads
   └─ Frontend: GET /api/v1/users/{john_id}/roles

3. Backend validates token → Valid, not realm-admin
   └─ Allows viewing own roles only

4. Backend fetches from Keycloak:
   └─ GET http://keycloak:8080/admin/realms/.../users/{john_id}/role-mappings

5. Returns: { roles: [{ name: "user-manager", ... }] }

6. John sees:
   ├─ Dashboard link only (no Users/Roles/Groups)
   ├─ Personal info card
   ├─ Roles: user-manager
   └─ Groups: (any assigned groups)

7. If John tries: http://localhost:3001/users
   └─ AdminRoute component: Checks isSuperAdmin() → false
   └─ Shows "Access Denied" page
```

#### 7. **Token Lifecycle**

```
Token Creation (Login):
├─ User logs in
├─ Keycloak generates access_token (RS256 JWT)
├─ Token contains:
│  ├─ exp: Expiration timestamp (now + 300 seconds)
│  ├─ iat: Issued at timestamp
│  ├─ sub: User ID
│  ├─ preferred_username: "admin"
│  ├─ email: "admin@example.com"
│  ├─ realm_access: { roles: ["realm-admin"] }
│  └─ signature (signed with Keycloak private key)
└─ Frontend stores in localStorage

Token Usage (Every API Call):
├─ Frontend includes: Authorization: Bearer <token>
├─ Backend extracts token
├─ Backend fetches Keycloak public keys (cached)
├─ Backend verifies signature → Valid/Invalid
├─ Backend checks exp → Not expired/Expired
└─ Backend extracts user_id, roles from claims

Token Refresh (Before Expiry):
├─ Token expires in 5 minutes
├─ Axios interceptor catches 401 response
├─ Calls: POST /api/v1/auth/refresh { refresh_token: "..." }
├─ Backend: POST to Keycloak with refresh_token
├─ Keycloak: Validates refresh_token, issues new access_token
├─ Backend: Decodes new token, returns with user data
├─ Frontend: Updates localStorage
└─ Frontend: Retries original request with new token

Token Expiration:
├─ Access token: 5 minutes (short-lived for security)
├─ Refresh token: Much longer (hours/days)
├─ After refresh token expires → Must login again
└─ Logout clears both tokens immediately
```

### Why This Architecture?

**Benefits:**
1. **Separation of Concerns**
   - Frontend: Pure UI/UX
   - Backend: Business logic + API gateway
   - Keycloak: Identity management only

2. **Security**
   - Keycloak hidden behind backend (optional)
   - JWT validation on every request
   - Role-based access control
   - Short-lived tokens

3. **Scalability**
   - Each service can scale independently
   - Stateless backend (JWT validation)
   - Keycloak handles user storage

4. **Maintainability**
   - Clear service boundaries
   - Standard protocols (OAuth2/OIDC)
   - Easy to add features

**Production Recommendations:**
- Remove Keycloak port exposure (8082)
- Add HTTPS/TLS to all services
- Use external PostgreSQL for Keycloak
- Implement rate limiting
- Add API gateway (Kong/Traefik)
- Enable Keycloak production mode
- Configure proper CORS origins
- Set up monitoring/logging

## Testing

### Manual API Testing

```bash
# Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Use token
curl -X GET http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📁 Project Structure

```
v2-api-version/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration settings from .env
│   │   ├── auth.py              # JWT authentication & validation
│   │   ├── keycloak_admin.py   # Keycloak Admin API wrapper
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py          # Login & token refresh endpoints
│   │       ├── users.py         # User CRUD & role/group management
│   │       ├── roles.py         # Role management endpoints
│   │       └── groups.py        # Group management endpoints
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── axios.js         # API client with auto token refresh
│   │   ├── components/
│   │   │   ├── Layout.jsx       # Main layout with navbar
│   │   │   └── ProtectedRoute.jsx # Route protection wrapper
│   │   ├── context/
│   │   │   └── AuthContext.jsx  # Authentication state management
│   │   ├── pages/
│   │   │   ├── Login.jsx        # Login page
│   │   │   ├── Dashboard.jsx    # Dashboard with stats
│   │   │   ├── Users.jsx        # User management with roles/groups
│   │   │   ├── Roles.jsx        # Role management
│   │   │   └── Groups.jsx       # Group management
│   │   ├── App.jsx              # React Router setup
│   │   ├── index.css            # Global styles
│   │   └── main.jsx             # React entry point
│   ├── package.json             # Node dependencies
│   ├── nginx.conf               # Nginx reverse proxy config
│   └── Dockerfile               # Multi-stage build
├── bootstrap_keycloak.py        # Initial Keycloak setup script
├── docker-compose.yml           # Docker orchestration
├── .env                         # Environment variables
└── README.md
```

## Troubleshooting

### Keycloak not starting
Check logs: `docker-compose logs keycloak`

### Backend can't reach Keycloak
Ensure using internal URL: `http://keycloak:8080`

### Frontend 401 errors
Check token expiration and refresh mechanism

### CORS errors
Verify CORS origins in `backend/app/main.py`

## Next Steps

- [ ] Add unit tests
- [ ] Add API documentation with Swagger/OpenAPI
- [ ] Implement rate limiting
- [ ] Add logging and monitoring
- [ ] Deploy to production with HTTPS
- [ ] Add user profile management
- [ ] Implement password reset flow
- [ ] Add group membership UI in user details
