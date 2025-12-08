# Keycloak Staging Configuration Issues - Technical Report

**Date:** December 8, 2025  
**Environment:** Staging (EKS Cluster)  
**Prepared by:** IAM Service Team

---

## Executive Summary

We successfully resolved critical API failures in the staging environment by implementing proper Keycloak hostname configuration. However, this fix introduced a secondary issue with admin console access that requires a documented workaround.

**Current Status:**
- ✅ **All IAM Service APIs working in staging** (PRIMARY GOAL ACHIEVED)
- ⚠️ **Admin UI requires manual configuration toggle** (Known limitation with documented workaround)

---

## Problem 1: IAM Service APIs Returning 500 Errors (RESOLVED ✅)

### Symptoms
- All IAM service endpoints returning HTTP 500 errors in staging
- APIs: List Users, List Roles, Update User - all failing
- Error logs showed connection/authentication issues with Keycloak

### Root Causes Identified

#### Issue 1.1: IAM Service Using Public URL for Admin API Calls
**Problem:**
- IAM service was configured to call Keycloak at: `https://api.serhafen-staging.andinolabs.tech`
- This is the public API gateway URL
- Keycloak Admin API paths are NOT exposed through the public ingress (correct for security)
- Result: IAM service couldn't reach Keycloak Admin APIs

**Configuration Before:**
```yaml
# IAM Service Secret
KEYCLOAK_BASE_URL: https://api.serhafen-staging.andinolabs.tech
```

**Solution Implemented:**
```yaml
# IAM Service Secret  
KEYCLOAK_BASE_URL: http://keycloak-service.keycloak
```

**Why This Works:**
- Uses internal Kubernetes service DNS
- Pod-to-pod communication within the cluster
- Bypasses the public ingress
- Keycloak Admin API accessible internally
- No security compromise (still not exposed publicly)

#### Issue 1.2: Keycloak Not Configured with Canonical Hostname
**Problem:**
- Keycloak was not configured with a canonical (official) hostname
- JWT tokens had inconsistent issuer claims
- Token validation failing because issuer URL didn't match expected value
- OIDC discovery endpoints returning inconsistent URLs

**Technical Explanation:**
When Keycloak issues JWT tokens, it includes an `iss` (issuer) field:
```json
{
  "iss": "https://some-inconsistent-url/realms/NewCustomsRealm",
  "sub": "user-id",
  "exp": 1234567890
}
```

Without a canonical hostname:
- Tokens issued from pod IP: `iss: "http://10.0.1.45/realms/..."`
- Tokens issued from service: `iss: "http://keycloak-service/realms/..."`
- Tokens issued from ingress: `iss: "https://api.serhafen-staging.andinolabs.tech/realms/..."`

IAM service expects: `iss: "https://api.serhafen-staging.andinolabs.tech/realms/NewCustomsRealm"`

**Result:** Token validation fails with mismatched issuer

**Configuration Before:**
```yaml
# Keycloak ConfigMap
KC_DB: postgres
KC_HEALTH_ENABLED: "true"
KC_METRICS_ENABLED: "true"
KC_PROXY: edge
KC_HOSTNAME_STRICT: "false"
KC_HOSTNAME_STRICT_HTTPS: "false"
# KC_HOSTNAME_URL: NOT SET ❌
```

**Solution Implemented:**
```yaml
# Keycloak ConfigMap
KC_HOSTNAME_URL: https://api.serhafen-staging.andinolabs.tech
```

**Why This Works:**
- Sets the canonical (official) hostname for all Keycloak operations
- All JWT tokens now have consistent issuer: `https://api.serhafen-staging.andinolabs.tech`
- OIDC discovery URLs are consistent
- Token validation succeeds
- Industry best practice for production deployments

### Actions Taken to Resolve Problem 1

1. **Updated IAM Service Secret** (namespace: `serhafen`)
   ```bash
   kubectl edit secret iam-service-secret -n serhafen
   # Changed: KEYCLOAK_BASE_URL from public URL to internal service URL
   ```

2. **Updated Keycloak ConfigMap** (namespace: `keycloak`)
   ```bash
   kubectl edit configmap keycloak-config -n keycloak
   # Added: KC_HOSTNAME_URL=https://api.serhafen-staging.andinolabs.tech
   ```

3. **Restarted Both Deployments**
   ```bash
   kubectl rollout restart deployment/keycloak -n keycloak
   kubectl rollout restart deployment/iam-service -n serhafen
   ```

### Result: Problem 1 RESOLVED ✅

**Verification:**
- List Users API: ✅ Working
- List Roles API: ✅ Working  
- Update User API: ✅ Working
- Token validation: ✅ Working
- OIDC flows: ✅ Working

**Security Maintained:**
- ✅ Keycloak Admin API remains unexposed publicly
- ✅ Only authorized pods can access Admin API (internal cluster communication)
- ✅ Public ingress only exposes required OIDC endpoints

---

## Problem 2: Admin UI No Longer Accessible via Port-Forward (ONGOING ⚠️)

### Symptoms
After fixing Problem 1, a new issue emerged:
- Cannot access Keycloak Admin Console via `kubectl port-forward`
- Previously worked: `kubectl port-forward svc/keycloak-service 8080:80 -n keycloak` → `http://localhost:8080`
- Now returns: Browser errors, redirects to staging URL, 404 errors

### Root Cause

**The Fix for Problem 1 Introduced This Issue:**

When `KC_HOSTNAME_URL` is set to the canonical hostname, Keycloak enforces it for ALL requests, including Admin UI:

1. Developer runs: `kubectl port-forward svc/keycloak-service 8080:80 -n keycloak`
2. Browser accesses: `http://localhost:8080`
3. Keycloak sees the request hostname: `localhost`
4. Keycloak checks: "This is not my canonical hostname (`api.serhafen-staging.andinolabs.tech`)"
5. Keycloak redirects: `https://api.serhafen-staging.andinolabs.tech/admin`
6. Public ingress returns: **404 Not Found** (Admin UI paths not exposed, correctly)

**Why This Happens:**
- Canonical hostname configuration is global in Keycloak
- Applies to all interfaces: public APIs, admin UI, realms
- Keycloak prioritizes security and consistency over convenience
- This is expected behavior, not a bug

### Attempted Solutions (Unsuccessful ❌)

#### Attempt 1: Set Admin-Specific Hostname URL
**What We Tried:**
```yaml
KC_HOSTNAME_URL: https://api.serhafen-staging.andinolabs.tech
KC_HOSTNAME_ADMIN_URL: http://localhost:8080
```

**Result:** ❌ Failed
- Still redirected to canonical URL
- Admin URL setting didn't override the main hostname behavior

#### Attempt 2: Use Custom Admin Hostname with /etc/hosts
**What We Tried:**
```yaml
KC_HOSTNAME_URL: https://api.serhafen-staging.andinolabs.tech
KC_HOSTNAME_ADMIN: admin-keycloak.internal.local
```

Added to `/etc/hosts`:
```
127.0.0.1 admin-keycloak.internal.local
```

Accessed: `http://admin-keycloak.internal.local:8080`

**Result:** ❌ Failed
- Browser errors: "URL can't be shown" (Safari)
- Port doubling issue: Generated URLs like `http://admin-keycloak.internal.local:8080:8080`
- Hostname resolution issues in Safari

#### Attempt 3: Various Port and Configuration Combinations
**What We Tried:**
- Different port numbers
- With/without port in hostname config
- Different browsers
- Direct pod port-forwarding

**Result:** ❌ All Failed
- Hostname enforcement too strict
- Configuration complexity didn't resolve core issue

### Current Working Solution (Manual Toggle)

**Process for Admin UI Access:**

**Step 1: Disable Hostname Enforcement**
```bash
# Edit ConfigMap
kubectl edit configmap keycloak-config -n keycloak

# Comment out hostname configuration
# KC_HOSTNAME_URL: https://api.serhafen-staging.andinolabs.tech

# Restart Keycloak
kubectl rollout restart deployment/keycloak -n keycloak
kubectl rollout status deployment/keycloak -n keycloak
```

**Step 2: Access Admin UI**
```bash
# Port-forward
kubectl port-forward svc/keycloak-service 8080:80 -n keycloak

# Access in browser
http://localhost:8080
```

**Step 3: Re-enable Hostname Enforcement (When Done)**
```bash
# Edit ConfigMap
kubectl edit configmap keycloak-config -n keycloak

# Uncomment hostname configuration
KC_HOSTNAME_URL: https://api.serhafen-staging.andinolabs.tech

# Restart Keycloak
kubectl rollout restart deployment/keycloak -n keycloak
```

**Important Notes:**
- ⚠️ While hostname is disabled, staging APIs may have token validation issues
- ⏱️ Keycloak restart takes ~30-60 seconds
- 📝 Document when hostname is disabled in team chat
- 🔄 Always re-enable after admin work is complete

---

## Why The Long-Term Solutions Don't Work

### Option: Expose Admin UI via Separate Ingress
**Why Not Implemented:**

```yaml
# Would require creating:
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: keycloak-admin-ingress
  annotations:
    # IP whitelisting required
    alb.ingress.kubernetes.io/inbound-cidrs: "OFFICE_IP/32"
spec:
  rules:
    - host: admin.serhafen-staging.andinolabs.tech
```

**Challenges:**
1. **DNS Configuration:** Need to create new DNS record in Route53
2. **Certificate Management:** Need separate SSL certificate or update existing
3. **Security Risk:** Admin UI exposed to internet (even with IP whitelisting)
4. **Cost:** Additional ingress resources, potential additional ALB
5. **Maintenance:** More infrastructure to manage
6. **Not Urgent:** Admin access needed infrequently

**Decision:** Not worth the complexity for infrequent admin access needs

### Option: VPN-Based Access
**Why Not Implemented:**

**Challenges:**
1. **Infrastructure Required:** AWS Client VPN or Site-to-Site VPN setup
2. **Cost:** VPN endpoint charges (~$0.10/hour + data transfer)
3. **Complexity:** VPN client configuration for all team members
4. **Time Investment:** Setup and maintenance overhead
5. **Current Access:** Manual toggle works sufficiently well

**Decision:** Overkill for current team size and access frequency

---

## Technical Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Public Internet                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS
                             ▼
                   ┌─────────────────┐
                   │   AWS ALB       │
                   │  (Internet-     │
                   │   facing)       │
                   └────────┬────────┘
                            │
                            │ Ingress Rules
                            │ /iam-service/* → IAM Service
                            │ /realms/* → Keycloak (OIDC only)
                            │ ❌ /admin/* NOT exposed
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────┐                    ┌──────────────────┐
│  IAM Service  │                    │    Keycloak      │
│   (Pod)       │                    │     (Pod)        │
│               │                    │                  │
│ Port: 3000    │───────────────────▶│ Port: 80         │
│               │  Internal Call     │                  │
│ KEYCLOAK_     │  (Pod-to-Pod)      │ KC_HOSTNAME_URL: │
│ BASE_URL:     │  http://keycloak-  │ https://api.     │
│ http://       │  service.keycloak  │ serhafen-staging │
│ keycloak-     │                    │ .andinolabs.tech │
│ service.      │                    │                  │
│ keycloak      │                    │ Issues tokens    │
│               │                    │ with iss:        │
│ Validates     │                    │ "https://api..." │
│ tokens with   │                    │                  │
│ iss check     │                    │ ❌ Admin UI      │
└───────────────┘                    │   blocked for    │
                                     │   localhost      │
                                     └──────────────────┘
                                              │
                                              │ Port-forward
                                              │ (kubectl)
                                              ▼
                                     ┌──────────────────┐
                                     │  Developer's     │
                                     │  Laptop          │
                                     │  localhost:8080  │
                                     │                  │
                                     │  ❌ Redirected   │
                                     │  to canonical    │
                                     │  hostname        │
                                     └──────────────────┘

Legend:
✅ Working path
❌ Blocked/Not working
→ Communication flow
```

---

## Configuration Reference

### Before Changes (Original State)
**IAM Service Secret:**
```yaml
KEYCLOAK_BASE_URL: https://api.serhafen-staging.andinolabs.tech  # ❌ Wrong
```

**Keycloak ConfigMap:**
```yaml
KC_DB: postgres
KC_HEALTH_ENABLED: "true"
KC_METRICS_ENABLED: "true"
KC_PROXY: edge
KC_HOSTNAME_STRICT: "false"
KC_HOSTNAME_STRICT_HTTPS: "false"
# KC_HOSTNAME_URL: NOT SET  # ❌ Missing
```

**Result:** 
- ❌ APIs failing with 500 errors
- ✅ Admin UI accessible via port-forward

---

### After Changes (Current Production State)
**IAM Service Secret:**
```yaml
KEYCLOAK_BASE_URL: http://keycloak-service.keycloak  # ✅ Fixed
```

**Keycloak ConfigMap:**
```yaml
KC_DB: postgres
KC_HEALTH_ENABLED: "true"
KC_METRICS_ENABLED: "true"
KC_PROXY: edge
KC_HOSTNAME_STRICT: "false"
KC_HOSTNAME_STRICT_HTTPS: "false"
KC_HOSTNAME_URL: https://api.serhafen-staging.andinolabs.tech  # ✅ Added
```

**Result:**
- ✅ All APIs working perfectly
- ⚠️ Admin UI requires manual toggle for access

---

## Testing and Verification

### API Tests Performed (All Passing ✅)

**1. List Users API**
```bash
curl -X GET "https://api.serhafen-staging.andinolabs.tech/iam-service/v0/users?page=1&size=10" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Country-Code: AG"
```
**Status:** ✅ 200 OK - Returns paginated user list

**2. List Roles API**
```bash
curl -X GET "https://api.serhafen-staging.andinolabs.tech/iam-service/v0/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Country-Code: AG"
```
**Status:** ✅ 200 OK - Returns available roles

**3. Update User API**
```bash
curl -X PATCH "https://api.serhafen-staging.andinolabs.tech/iam-service/v0/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Country-Code: AG" \
  -H "Content-Type: application/json" \
  -d '{"firstName": "Updated", "lastName": "Name"}'
```
**Status:** ✅ 200 OK - User updated successfully

**4. Token Validation**
- ✅ JWT tokens contain correct issuer claim
- ✅ IAM service successfully validates tokens
- ✅ OIDC discovery endpoints return consistent URLs
- ✅ Token refresh flows working

---

## Impact Assessment

### Positive Impacts ✅
1. **All staging APIs operational** - Primary business requirement met
2. **Production-ready configuration** - Follows Keycloak best practices
3. **Improved security** - Admin API not exposed publicly
4. **Consistent token validation** - No more intermittent auth failures
5. **Stable OIDC flows** - Frontend authentication working reliably

### Trade-offs ⚠️
1. **Admin UI access requires manual steps** - Additional 2-3 minutes to toggle config
2. **Cannot debug production issues instantly** - Need to disable hostname first
3. **Potential for mistakes** - Forgetting to re-enable hostname after admin work

### Risk Mitigation
- ✅ **Documented procedure** - Clear steps for admin access
- ✅ **Infrequent need** - Admin UI access needed ~1-2 times per week
- ✅ **Quick recovery** - If hostname left disabled, just edit and restart
- ✅ **Monitoring in place** - API health checks will alert if issues occur

---

## Recommendations

### Short-term (Current Approach) ✅
**Continue using manual toggle for admin access**

**Pros:**
- Zero infrastructure cost
- Zero additional complexity
- Works reliably
- Adequate for current team size

**Cons:**
- Manual process
- 2-3 minute overhead

**Recommended For:** Current situation (small team, infrequent admin access)

---

### Medium-term (If Admin Access Frequency Increases)
**Implement admin ingress with IP whitelisting**

**When to Consider:**
- Admin access needed >5 times per week
- Multiple team members need simultaneous access
- Debugging production issues becomes more frequent

**Requirements:**
- Office/VPN static IP addresses
- DNS record: `admin.serhafen-staging.andinolabs.tech`
- SSL certificate update
- Ingress configuration with IP whitelist

**Estimated Effort:** 4-6 hours implementation + testing

---

### Long-term (Enterprise Production)
**Implement VPN-based access**

**When to Consider:**
- Multiple environments (dev, staging, prod)
- Larger team (10+ engineers)
- Compliance requirements
- Need for audit trails

**Requirements:**
- AWS Client VPN setup
- Internal ALB for Keycloak
- VPN client distribution
- Documentation and training

**Estimated Effort:** 2-3 days implementation + ongoing maintenance

---

## Comparison with Industry Standards

### How Other Companies Handle This

**Option 1: Bastion Host (Common)**
- SSH jump server in private subnet
- Port-forward through bastion
- Similar manual process to our approach

**Option 2: VPN (Enterprise)**
- Corporate VPN required for all internal access
- Higher security, higher cost
- Common in large enterprises

**Option 3: Separate Admin Ingress (Common)**
- Admin UI on different subdomain
- IP whitelisting at ALB/WAF level
- Common in mid-size companies

**Option 4: No Admin UI Access (Rare)**
- Everything via API/CLI
- Infrastructure as Code only
- Very rare, mostly in highly automated environments

**Our Approach (Manual Toggle):**
- Uncommon but valid for small teams
- Trade-off: convenience vs complexity
- Appropriate for current scale

---

## Lessons Learned

### Technical Insights
1. **Canonical hostname is critical** for JWT token validation in distributed systems
2. **Keycloak's hostname enforcement is global** - affects all interfaces
3. **Internal service communication** should use cluster DNS, not public URLs
4. **Security and convenience** often require trade-offs

### Process Improvements
1. **Test configuration changes** in non-production first (if available)
2. **Document trade-offs** before implementing changes
3. **Have rollback plan** for any production config changes
4. **Consider downstream impacts** of security improvements

### Team Communication
1. **Technical limitations** should be explained to stakeholders upfront
2. **Document workarounds** clearly for team members
3. **Regular review** of manual processes to identify automation opportunities

---

## Appendix A: Glossary

**Canonical Hostname:** The official, authoritative hostname for a service. All URLs and references use this hostname for consistency.

**JWT (JSON Web Token):** A secure token containing user identity and claims, used for authentication.

**Issuer (iss) Claim:** Field in JWT token indicating which service issued the token. Must match expected value for validation to succeed.

**OIDC (OpenID Connect):** Authentication protocol built on OAuth 2.0, used by Keycloak.

**Pod-to-Pod Communication:** Direct network communication between containers in Kubernetes cluster, using internal cluster DNS.

**Port-Forward:** Kubectl command that creates a tunnel from local machine to a pod/service in Kubernetes.

**Ingress:** Kubernetes resource that manages external access to services, typically HTTP/HTTPS.

**ConfigMap:** Kubernetes resource for storing configuration data as key-value pairs.

**Keycloak Admin API:** REST API for managing Keycloak configuration, users, roles, etc.

---

## Appendix B: Quick Reference Commands

### Check Current Configuration
```bash
# View Keycloak ConfigMap
kubectl get configmap keycloak-config -n keycloak -o yaml

# View IAM Service Secret (base64 encoded)
kubectl get secret iam-service-secret -n serhafen -o yaml

# Check pod status
kubectl get pods -n keycloak
kubectl get pods -n serhafen
```

### Admin UI Access (Full Procedure)
```bash
# Step 1: Disable hostname
kubectl edit configmap keycloak-config -n keycloak
# Comment out: KC_HOSTNAME_URL

# Step 2: Restart
kubectl rollout restart deployment/keycloak -n keycloak
kubectl rollout status deployment/keycloak -n keycloak

# Step 3: Port-forward
kubectl port-forward svc/keycloak-service 8080:80 -n keycloak

# Step 4: Access
# Open browser: http://localhost:8080

# Step 5: When done, re-enable hostname
kubectl edit configmap keycloak-config -n keycloak
# Uncomment: KC_HOSTNAME_URL: https://api.serhafen-staging.andinolabs.tech

# Step 6: Restart
kubectl rollout restart deployment/keycloak -n keycloak
```

### Test APIs
```bash
# Get token
TOKEN=$(curl -X POST "https://api.serhafen-staging.andinolabs.tech/realms/NewCustomsRealm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=newcustoms" \
  -d "username=admin" \
  -d "password=PASSWORD" | jq -r '.access_token')

# Test List Users
curl -X GET "https://api.serhafen-staging.andinolabs.tech/iam-service/v0/users?page=1&size=10" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Country-Code: AG"

# Test List Roles  
curl -X GET "https://api.serhafen-staging.andinolabs.tech/iam-service/v0/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Country-Code: AG"
```

---

## Appendix C: Timeline

**December 7, 2025 (Saturday)**
- 🔴 Issue discovered: All IAM APIs returning 500 errors
- 🔍 Investigation: Identified two root causes
- ✅ Fix 1: Changed IAM service to use internal Keycloak URL
- ✅ Fix 2: Added canonical hostname to Keycloak config
- ✅ Result: All APIs working
- ⚠️ New issue: Admin UI no longer accessible

**December 8, 2025 (Sunday - Today)**
- 🔍 Investigation: Admin UI redirect issue
- ❌ Attempt 1: KC_HOSTNAME_ADMIN_URL - Failed
- ❌ Attempt 2: Custom hostname with /etc/hosts - Failed
- ❌ Attempt 3: Various config combinations - Failed
- ✅ Solution: Documented manual toggle process
- 📝 Created this comprehensive report

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 8, 2025 | IAM Team | Initial report creation |

---

## Contact Information

**For Questions About This Report:**
- IAM Service Team
- Kubernetes/Infrastructure Team

**For Production Issues:**
- Follow incident response procedures
- Check API monitoring dashboard
- Review staging logs: `kubectl logs -n serhafen deployment/iam-service`

---

**End of Report**
