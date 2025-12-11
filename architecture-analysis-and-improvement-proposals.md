# Multi-Service Architecture Analysis & Recommendations
## Production vs POC Comparison with AWS Kubernetes Cost Analysis

**Author**: AI Architecture Team  
**Date**: December 11, 2025  
**Version**: 1.0  
**Status**: Proposal for Review

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [POC Architecture Review](#poc-architecture-review)
4. [Gap Analysis](#gap-analysis)
5. [Proposed Solutions](#proposed-solutions)
6. [Cost Analysis (AWS + Kubernetes)](#cost-analysis-aws--kubernetes)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Risk Assessment](#risk-assessment)
9. [Recommendations](#recommendations)

---

## Executive Summary

### Current Landscape

| Component | Production Frontend | Production IAM Service | POC (v2-api-version) |
|-----------|-------------------|----------------------|---------------------|
| **Technology** | React 19 + Vite + TypeScript | NestJS 11 + TypeScript + Fastify | FastAPI + Nginx + Keycloak |
| **Auth Pattern** | Client-side JWT refresh | Keycloak integration via service | Centralized API gateway with JWT validation |
| **Architecture** | Direct multi-service calls | Modular CQRS with guards | 3-layer (Nginx → FastAPI → Keycloak) |
| **Multi-tenancy** | Header-based (x-country-code, x-business-unit) | AsyncLocalStorage tenant context | None |
| **Service Communication** | REST (3+ backend services) | REST + Circuit breaker | REST proxy pattern |

### Key Findings

✅ **POC Advantages**:
- Centralized authentication reduces per-service complexity
- Single entry point simplifies frontend integration
- Nginx reverse proxy eliminates CORS issues

❌ **POC Limitations**:
- Only wraps Keycloak Admin API (1 service)
- No multi-tenancy support
- No rate limiting, caching, or observability

🎯 **Recommendation**: **Hybrid Architecture** - Extend production NestJS IAM service to act as an API Gateway while preserving CQRS patterns and multi-tenancy capabilities.

---

## Current State Analysis

### 1. Production Frontend (serhafen-portal-web)

**Stack**: React 19, Vite, TypeScript, TanStack Query, Zustand

#### ✅ Strengths
- Modern React ecosystem with excellent DX
- Client-side state management (Zustand for auth, React Query for server state)
- Automatic token refresh (15 mins before expiry)
- Role-based access control (RBAC) with RoleGuard components
- Server-side pagination and filtering
- i18n support (Spanish/English)
- 75% test coverage threshold

#### ❌ Weaknesses
- **No reverse proxy** - Direct calls to multiple backends
  ```typescript
  // src/lib/config.ts
  VITE_IAM_SERVICE: 'http://localhost:8080'
  VITE_CUSTOM_DECLARATION_SERVICE: 'http://localhost:8081'
  VITE_MOCK_ENDPOINT: '...'
  ```
- **CORS complexity** - Each service must configure CORS independently
- **No centralized rate limiting** - Vulnerable to abuse
- **No request/response logging** - Limited audit trail
- **No WebSocket gateway** - REST-only communication

#### Architecture Diagram
```
┌─────────────────────────────────────────┐
│   React SPA (serhafen-portal-web)      │
│   - Zustand (auth state)               │
│   - React Query (server state)         │
│   - JWT refresh (client-managed)       │
└─────────────────┬───────────────────────┘
                  │ Direct HTTP calls
        ┌─────────┼─────────┬─────────────┐
        ▼         ▼         ▼             ▼
    ┌─────┐  ┌─────────┐ ┌──────┐   ┌──────┐
    │ IAM │  │ Customs │ │ Mock │   │ ... │
    │ :80 │  │ :8081   │ │ Svc  │   │ Svc │
    └─────┘  └─────────┘ └──────┘   └──────┘
      Each service handles:
      - CORS configuration
      - JWT validation
      - Rate limiting
      - Logging
```

**Pain Points**:
1. Frontend knows about all backend URLs
2. Adding a new service requires frontend config changes
3. No centralized monitoring or rate limiting
4. Each service duplicates auth/CORS logic

---

### 2. Production IAM Service (iam-service)

**Stack**: NestJS 11, Fastify, TypeORM, PostgreSQL, Keycloak

#### ✅ Strengths

**Architecture Patterns**:
- ✅ **CQRS** - Separate query/command modules for read/write operations
- ✅ **Multi-tenancy** - AsyncLocalStorage for tenant context propagation
  ```typescript
  // Tenant context extracted from headers
  x-business-unit: SERHAFEN
  x-country-code: CL
  ```
- ✅ **Circuit breaker** - Resilient HTTP client with Opossum
- ✅ **Contract-first** - OpenAPI spec → DTOs with validation
- ✅ **Error handling** - Custom exception filters with structured responses
- ✅ **Logging** - Pino with context propagation (MDC-like)
- ✅ **Health checks** - Terminus for readiness/liveness probes
- ✅ **Modular design** - Feature-based modules (users, roles, auth)

**Security**:
- ✅ **JWT validation** - RolesGuard with RS256 signature verification
- ✅ **Role-based authorization** - `@Roles('SUPERADMIN')` decorator
- ✅ **Request interception** - Logs all incoming requests

**Infrastructure**:
- ✅ **OpenTelemetry** - Distributed tracing support
- ✅ **SNS/SQS** - Event-driven messaging
- ✅ **Migrations** - Safe parallel execution with advisory locks

#### ❌ Weaknesses
- **Not an API gateway** - Only handles IAM-specific endpoints
- **No request routing** - Doesn't proxy to other services
- **Limited observability** - No centralized metrics dashboard
- **No rate limiting** - Vulnerable to DDoS

#### Architecture Diagram
```
┌──────────────────────────────────────────────┐
│        NestJS IAM Service (Port 3000)       │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  TenantContextMiddleware               │ │
│  │  - Extracts x-business-unit            │ │
│  │  - Extracts x-country-code             │ │
│  │  - AsyncLocalStorage propagation       │ │
│  └────────────────────────────────────────┘ │
│                    │                         │
│         ┌──────────┴──────────┬─────────┐  │
│         ▼                     ▼         ▼   │
│  ┌───────────┐   ┌──────────────┐  ┌─────┐ │
│  │   Auth    │   │    Users     │  │Roles│ │
│  │  Module   │   │   Module     │  │ Mod │ │
│  │           │   │              │  │     │ │
│  │ - Login   │   │ - List Users │  │ - List│ │
│  │ - Refresh │   │ - Add User   │  │ Roles│ │
│  │ - Google  │   │ - Edit User  │  └─────┘ │
│  │   OAuth   │   │              │          │
│  └─────┬─────┘   └──────┬───────┘          │
│        │                │                   │
│        └────────┬───────┘                   │
│                 ▼                           │
│      ┌──────────────────────┐              │
│      │   RolesGuard         │              │
│      │   - JWT validation   │              │
│      │   - Role checking    │              │
│      └──────────────────────┘              │
│                 │                           │
│                 ▼                           │
│      ┌──────────────────────┐              │
│      │  KeycloakService     │              │
│      │  - Token exchange    │              │
│      │  - User management   │              │
│      └──────────┬───────────┘              │
│                 │                           │
└─────────────────┼───────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │   Keycloak     │
         │  (Port 8082)   │
         │ NewCustomsRealm│
         └────────────────┘
```

**Key Features**:
1. **Contract-first development** - OpenAPI specs generate DTOs
2. **Multi-tenant by design** - All queries scoped to tenant
3. **Resilient HTTP** - Circuit breaker prevents cascade failures
4. **Production-ready** - Health checks, structured logging, error handling

---

### 3. POC Architecture (v2-api-version)

**Stack**: FastAPI, Nginx, Keycloak, Docker Compose

#### ✅ Strengths
- **Centralized authentication** - All JWT validation in one place
- **Single entry point** - `/api/*` proxied through Nginx
- **No CORS issues** - Nginx handles cross-origin requests
- **Token refresh** - Automatic 5-minute expiry with refresh
- **RBAC** - realm-admin role checking

#### ❌ Weaknesses
- **Single-service focus** - Only wraps Keycloak Admin API
- **No multi-tenancy** - No business unit or country filtering
- **No rate limiting** - Open to abuse
- **No caching** - Every request hits Keycloak
- **No observability** - No metrics, tracing, or logging aggregation
- **No WebSocket support** - REST-only
- **No audit logging** - No track of user actions

#### Architecture Diagram
```
┌────────────────────────────────────────────┐
│    React Frontend (Port 3001)             │
│    - Calls /api/* endpoints               │
└──────────────────┬─────────────────────────┘
                   │ HTTP
                   ▼
         ┌─────────────────────┐
         │   Nginx (Port 80)   │
         │   Reverse Proxy     │
         │                     │
         │  location /api/ {   │
         │    proxy_pass       │
         │    http://backend:  │
         │    8000;            │
         │  }                  │
         └──────────┬──────────┘
                    │
                    ▼
      ┌─────────────────────────────┐
      │  FastAPI Gateway (Port 8000)│
      │                             │
      │  ┌────────────────────────┐ │
      │  │   auth.py              │ │
      │  │   - decode_token()     │ │
      │  │   - verify_bearer()    │ │
      │  │   - JWKS validation    │ │
      │  └────────────────────────┘ │
      │               │              │
      │               ▼              │
      │  ┌────────────────────────┐ │
      │  │   routes/              │ │
      │  │   - users.py           │ │
      │  │   - roles.py           │ │
      │  │   - groups.py          │ │
      │  │   All use Depends()    │ │
      │  └────────────────────────┘ │
      └──────────────┬──────────────┘
                     │
                     ▼
            ┌────────────────┐
            │   Keycloak     │
            │  (Port 8082)   │
            │ Admin REST API │
            └────────────────┘
```

**Key Learnings**:
1. API gateway pattern simplifies frontend
2. Centralized JWT validation reduces duplication
3. Nginx layer provides caching, compression potential
4. Need to extend to multiple backend services

---

## Gap Analysis

### Feature Comparison Matrix

| Feature | Production Frontend | Production IAM | POC | Target State |
|---------|---------------------|----------------|-----|--------------|
| **Authentication** | ✅ Client-managed JWT | ✅ Keycloak integration | ✅ Centralized gateway | ✅ Gateway-managed |
| **Authorization** | ✅ Frontend guards | ✅ RolesGuard decorator | ✅ realm-admin check | ✅ RBAC middleware |
| **Multi-tenancy** | ✅ Headers (client) | ✅ AsyncLocalStorage | ❌ None | ✅ Context propagation |
| **API Gateway** | ❌ None | ❌ None | ⚠️ Single service | ✅ Multi-service proxy |
| **Rate Limiting** | ❌ None | ❌ None | ❌ None | ✅ Gateway-level |
| **Caching** | ✅ React Query (5min) | ❌ None | ❌ None | ✅ Redis + CDN |
| **Logging** | ✅ Console + toast | ✅ Pino (structured) | ❌ Basic | ✅ Centralized (ELK) |
| **Tracing** | ❌ None | ✅ OpenTelemetry | ❌ None | ✅ Distributed tracing |
| **Health Checks** | ❌ None | ✅ Terminus | ❌ None | ✅ All services |
| **Circuit Breaker** | ❌ None | ✅ Opossum | ❌ None | ✅ Gateway + services |
| **WebSocket** | ❌ None | ❌ None | ❌ None | ✅ Gateway support |
| **Metrics** | ❌ None | ❌ None | ❌ None | ✅ Prometheus |
| **Service Discovery** | ❌ Hardcoded URLs | ❌ N/A | ❌ Docker network | ✅ Kubernetes DNS |
| **Load Balancing** | ❌ None | ❌ None | ❌ None | ✅ K8s Service |
| **TLS/SSL** | ⚠️ Client-side | ⚠️ Dev only | ❌ None | ✅ Ingress + mTLS |
| **Audit Logging** | ❌ None | ❌ None | ❌ None | ✅ Structured events |
| **Request Validation** | ✅ class-validator | ✅ class-validator | ⚠️ Pydantic | ✅ Gateway + service |
| **Response Compression** | ❌ None | ❌ None | ⚠️ Nginx | ✅ Gateway-wide |
| **CORS** | ⚠️ Per-service | ✅ app.enableCors() | ✅ Nginx | ✅ Gateway-managed |
| **API Versioning** | ✅ /v0/* | ✅ /v0/* | ✅ /v0/* | ✅ Gateway routing |

### Critical Gaps

#### 1. **No Centralized API Gateway** (HIGH PRIORITY)
- Frontend makes direct calls to 3+ backend services
- Each service must implement auth, CORS, rate limiting
- No single point for cross-cutting concerns

#### 2. **No Rate Limiting** (MEDIUM PRIORITY)
- Vulnerable to DDoS attacks
- No per-user or per-IP throttling
- No cost control for external API calls

#### 3. **No Centralized Logging & Monitoring** (MEDIUM PRIORITY)
- Frontend logs to console only
- IAM service uses Pino (good!) but no aggregation
- No distributed tracing across services

#### 4. **No Caching Layer** (MEDIUM PRIORITY)
- React Query provides client caching only
- No server-side cache (Redis)
- Keycloak Admin API called on every request

#### 5. **No WebSocket Support** (LOW PRIORITY)
- No real-time features (notifications, live updates)
- Polling-only for dynamic data

---

## Proposed Solutions

### Solution 1: Extend NestJS IAM Service as API Gateway (RECOMMENDED)

**Approach**: Transform production IAM service into a full-fledged API gateway that proxies to all backend services.

#### Architecture Diagram
```
┌────────────────────────────────────────────────────────┐
│          React Frontend (Port 3000)                   │
│          - All calls to /api/*                         │
└──────────────────────┬─────────────────────────────────┘
                       │ HTTPS
                       ▼
         ┌─────────────────────────────┐
         │   AWS ALB/Ingress           │
         │   - TLS termination         │
         │   - Path-based routing      │
         └─────────────┬───────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│     NestJS API Gateway (Enhanced IAM Service)           │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Gateway Middleware Stack                   │ │
│  │  1. TenantContextMiddleware                        │ │
│  │  2. JwtAuthMiddleware (validates all requests)     │ │
│  │  3. RateLimitMiddleware (per-user/IP throttling)   │ │
│  │  4. RequestLoggingInterceptor                      │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│       ┌──────────────────┼──────────────────┐           │
│       ▼                  ▼                  ▼            │
│  ┌─────────┐      ┌──────────┐      ┌───────────┐      │
│  │  Auth   │      │  Proxy   │      │  Proxy    │      │
│  │ Module  │      │ Module   │      │  Module   │      │
│  │         │      │          │      │           │      │
│  │ /auth/* │      │ /customs/*│     │ /mawbs/*  │      │
│  │ (local) │      │ (proxy)  │      │ (proxy)   │      │
│  └─────────┘      └────┬─────┘      └─────┬─────┘      │
│                        │                   │             │
│                  Circuit│Breaker      Circuit│Breaker    │
│                        │                   │             │
└────────────────────────┼───────────────────┼─────────────┘
                         │                   │
                         ▼                   ▼
              ┌──────────────────┐  ┌─────────────────┐
              │  Customs Service │  │  MAWB Service   │
              │   (Port 8081)    │  │  (Port 8082)    │
              └──────────────────┘  └─────────────────┘
```

#### Implementation Steps

**Phase 1: Core Gateway Features (Week 1-2)**

1. **JWT Middleware** - Global authentication
   ```typescript
   // src/shared/middleware/jwt-auth.middleware.ts
   @Injectable()
   export class JwtAuthMiddleware implements NestMiddleware {
     constructor(
       private readonly jwtService: JwtService,
       private readonly configService: ConfigService,
     ) {}

     async use(req: Request, res: Response, next: NextFunction) {
       const token = this.extractToken(req);
       if (!token) {
         throw new UnauthorizedException('Missing authorization token');
       }

       try {
         // Validate JWT using Keycloak public key (JWKS)
         const payload = await this.jwtService.verifyAsync(token, {
           publicKey: await this.getKeycloakPublicKey(),
         });
         
         req['user'] = payload;
         next();
       } catch (error) {
         throw new UnauthorizedException('Invalid token');
       }
     }

     private extractToken(req: Request): string | null {
       const authHeader = req.headers.authorization;
       return authHeader?.replace('Bearer ', ') ?? null;
     }

     private async getKeycloakPublicKey(): Promise<string> {
       // Fetch JWKS from Keycloak and cache
       const jwksUrl = `${this.configService.get('KEYCLOAK_BASE_URL')}/realms/${this.configService.get('KEYCLOAK_REALM')}/protocol/openid-connect/certs`;
       // ... fetch and parse JWKS
     }
   }
   ```

2. **Proxy Module** - Dynamic service routing
   ```typescript
   // src/gateway/proxy/proxy.module.ts
   @Module({
     imports: [HttpModule],
     providers: [ProxyService],
     controllers: [ProxyController],
   })
   export class ProxyModule {}

   // src/gateway/proxy/proxy.service.ts
   @Injectable()
   export class ProxyService {
     private readonly serviceRegistry = new Map<string, string>([
       ['customs', process.env.CUSTOMS_SERVICE_URL],
       ['mawbs', process.env.MAWB_SERVICE_URL],
       ['hawbs', process.env.HAWB_SERVICE_URL],
     ]);

     async proxyRequest(
       serviceName: string,
       path: string,
       method: string,
       body?: any,
       headers?: Record<string, string>,
     ): Promise<any> {
       const baseUrl = this.serviceRegistry.get(serviceName);
       if (!baseUrl) {
         throw new NotFoundException(`Service ${serviceName} not found`);
       }

       const url = `${baseUrl}${path}`;
       
       // Use circuit breaker for resilience
       return this.circuitBreakerClient.request(method, url, body, headers);
     }
   }

   // src/gateway/proxy/proxy.controller.ts
   @Controller()
   export class ProxyController {
     @All('/customs/*')
     async proxyCustoms(@Req() req: Request) {
       const path = req.url.replace('/customs', '');
       return this.proxyService.proxyRequest('customs', path, req.method, req.body, req.headers);
     }

     @All('/mawbs/*')
     async proxyMawbs(@Req() req: Request) {
       const path = req.url.replace('/mawbs', '');
       return this.proxyService.proxyRequest('mawbs', path, req.method, req.body, req.headers);
     }
   }
   ```

3. **Rate Limiting** - Protect against abuse
   ```typescript
   // src/shared/middleware/rate-limit.middleware.ts
   import { ThrottlerModule } from '@nestjs/throttler';

   @Module({
     imports: [
       ThrottlerModule.forRoot({
         ttl: 60, // 60 seconds
         limit: 100, // 100 requests per minute per user
       }),
     ],
   })
   export class AppModule {}
   ```

**Phase 2: Observability (Week 3)**

4. **Request/Response Logging**
   ```typescript
   // Already have RequestInterceptor, enhance it:
   @Injectable()
   export class EnhancedRequestInterceptor implements NestInterceptor {
     intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
       const request = context.switchToHttp().getRequest();
       const startTime = Date.now();

       return next.handle().pipe(
         tap((data) => {
           const duration = Date.now() - startTime;
           this.logger.log({
             method: request.method,
             url: request.url,
             user: request.user?.preferred_username,
             tenant: request.tenantContext,
             duration,
             statusCode: 200,
           });
         }),
         catchError((error) => {
           const duration = Date.now() - startTime;
           this.logger.error({
             method: request.method,
             url: request.url,
             user: request.user?.preferred_username,
             tenant: request.tenantContext,
             duration,
             error: error.message,
             statusCode: error.status,
           });
           throw error;
         }),
       );
     }
   }
   ```

5. **Metrics Collection**
   ```typescript
   // Add Prometheus metrics
   import { PrometheusModule } from '@willsoto/nestjs-prometheus';

   @Module({
     imports: [
       PrometheusModule.register({
         path: '/metrics',
         defaultMetrics: {
           enabled: true,
         },
       }),
     ],
   })
   export class AppModule {}

   // Custom metrics
   @Injectable()
   export class MetricsService {
     private readonly httpRequestDuration = new Histogram({
       name: 'http_request_duration_seconds',
       help: 'Duration of HTTP requests in seconds',
       labelNames: ['method', 'route', 'status'],
     });

     recordRequest(method: string, route: string, status: number, duration: number) {
       this.httpRequestDuration.labels(method, route, status.toString()).observe(duration / 1000);
     }
   }
   ```

**Phase 3: Caching & Performance (Week 4)**

6. **Redis Caching**
   ```typescript
   // src/shared/cache/cache.module.ts
   import { CacheModule } from '@nestjs/cache-manager';
   import * as redisStore from 'cache-manager-redis-store';

   @Module({
     imports: [
       CacheModule.registerAsync({
         isGlobal: true,
         useFactory: (configService: ConfigService) => ({
           store: redisStore,
           host: configService.get('REDIS_HOST'),
           port: configService.get('REDIS_PORT'),
           ttl: 300, // 5 minutes
         }),
         inject: [ConfigService],
       }),
     ],
   })
   export class SharedModule {}

   // Usage in service
   @Injectable()
   export class UsersService {
     constructor(@Inject(CACHE_MANAGER) private cacheManager: Cache) {}

     @Cacheable('users')
     async listUsers(tenantContext: TenantContext): Promise<User[]> {
       // Cache key includes tenant for isolation
       const cacheKey = `users:${tenantContext.businessUnit}:${tenantContext.countryCode}`;
       const cached = await this.cacheManager.get(cacheKey);
       if (cached) return cached;

       const users = await this.fetchFromKeycloak();
       await this.cacheManager.set(cacheKey, users, 300);
       return users;
     }
   }
   ```

#### Pros
✅ Leverages existing NestJS infrastructure  
✅ Preserves multi-tenancy and CQRS patterns  
✅ TypeScript end-to-end  
✅ Built-in health checks, logging, OpenTelemetry  
✅ Familiar stack for team  
✅ Can migrate incrementally (add proxy modules one service at a time)

#### Cons
❌ More complex than dedicated gateway (Kong, Nginx)  
❌ Node.js overhead vs. Nginx (but Fastify is fast!)  
❌ Need to implement caching, rate limiting ourselves  
❌ Harder to scale independently from IAM logic

#### Estimated Effort
- **Development**: 3-4 weeks (1 developer)
- **Testing**: 1 week
- **Deployment**: 1 week
- **Total**: 5-6 weeks

---

### Solution 2: Kong API Gateway + Production Services (ALTERNATIVE)

**Approach**: Deploy Kong as a standalone API gateway in Kubernetes.

#### Architecture Diagram
```
┌─────────────────────────────────────────┐
│      React Frontend (Port 3000)        │
└─────────────────┬───────────────────────┘
                  │ HTTPS
                  ▼
      ┌───────────────────────┐
      │   AWS ALB/Ingress     │
      │   - TLS termination   │
      └───────────┬───────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│          Kong API Gateway                   │
│                                             │
│  ┌────────────────────────────────────────┐│
│  │  Plugins Stack                         ││
│  │  1. JWT Authentication                 ││
│  │  2. Rate Limiting (Redis)              ││
│  │  3. Request Logging                    ││
│  │  4. Response Transformer               ││
│  │  5. Correlation ID                     ││
│  └────────────────────────────────────────┘│
│                    │                        │
│   ┌────────────────┼────────────────┐      │
│   ▼                ▼                ▼       │
│  /auth/*      /customs/*        /mawbs/*    │
└───┬────────────┬─────────────────┬──────────┘
    │            │                 │
    ▼            ▼                 ▼
┌────────┐  ┌──────────┐  ┌──────────────┐
│  IAM   │  │ Customs  │  │ MAWB Service │
│Service │  │ Service  │  │              │
└────────┘  └──────────┘  └──────────────┘
```

#### Implementation Steps

1. **Deploy Kong**
   ```yaml
   # k8s/kong-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: kong
   spec:
     replicas: 3
     template:
       spec:
         containers:
         - name: kong
           image: kong:3.4
           env:
           - name: KONG_DATABASE
             value: "postgres"
           - name: KONG_PG_HOST
             value: "postgres.default.svc.cluster.local"
           ports:
           - containerPort: 8000  # Proxy
           - containerPort: 8001  # Admin API
   ```

2. **Configure Routes**
   ```bash
   # Add IAM service route
   curl -i -X POST http://kong-admin:8001/services \
     --data name=iam-service \
     --data url=http://iam-service.default.svc.cluster.local:3000

   curl -i -X POST http://kong-admin:8001/services/iam-service/routes \
     --data paths[]=/auth \
     --data paths[]=/users \
     --data paths[]=/roles

   # Add Customs service route
   curl -i -X POST http://kong-admin:8001/services \
     --data name=customs-service \
     --data url=http://customs-service.default.svc.cluster.local:8081

   curl -i -X POST http://kong-admin:8001/services/customs-service/routes \
     --data paths[]=/customs
   ```

3. **Enable JWT Plugin**
   ```bash
   curl -i -X POST http://kong-admin:8001/plugins \
     --data name=jwt \
     --data config.secret_is_base64=false \
     --data config.key_claim_name=kid
   ```

4. **Enable Rate Limiting**
   ```bash
   curl -i -X POST http://kong-admin:8001/plugins \
     --data name=rate-limiting \
     --data config.minute=100 \
     --data config.policy=redis \
     --data config.redis_host=redis.default.svc.cluster.local
   ```

#### Pros
✅ Battle-tested, production-grade gateway  
✅ Rich plugin ecosystem (70+ plugins)  
✅ High performance (Nginx + Lua)  
✅ Declarative configuration (Kong decK)  
✅ Scales independently  
✅ Admin UI available (Kong Manager)  
✅ Can add WebSocket, gRPC support easily

#### Cons
❌ New technology to learn and maintain  
❌ Adds complexity to infrastructure  
❌ Costs: Kong Enterprise ($$$) or OSS (free but limited)  
❌ Requires PostgreSQL for config storage  
❌ Team unfamiliar with Lua for custom plugins

#### Estimated Effort
- **Infrastructure Setup**: 1 week
- **Route Configuration**: 1 week
- **Plugin Testing**: 1 week
- **Migration**: 2 weeks
- **Total**: 5 weeks

---

### Solution 3: Nginx Ingress + Service Mesh (FUTURE-PROOF)

**Approach**: Use Kubernetes Ingress for routing + Istio service mesh for advanced features.

#### Architecture Diagram
```
┌────────────────────────────────────────┐
│     React Frontend (Static S3/CDN)    │
└────────────────┬───────────────────────┘
                 │ HTTPS
                 ▼
       ┌──────────────────────┐
       │   AWS ALB            │
       │   - TLS termination  │
       └──────────┬───────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │  Kubernetes Ingress (Nginx)     │
    │  - Path-based routing           │
    │  - Rate limiting (annotations)  │
    └──────────────┬──────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌────────┐  ┌───────────┐  ┌──────────┐
│ IAM Svc│  │ Customs   │  │ MAWB Svc │
│        │  │ Service   │  │          │
│ Istio  │  │ Istio     │  │ Istio    │
│ Sidecar│  │ Sidecar   │  │ Sidecar  │
└────────┘  └───────────┘  └──────────┘

┌────────────────────────────────────────┐
│         Istio Control Plane            │
│  - Mutual TLS (mTLS)                   │
│  - Distributed tracing (Jaeger)        │
│  - Circuit breaking                    │
│  - Request routing & retries           │
│  - Telemetry (Prometheus + Grafana)    │
└────────────────────────────────────────┘
```

#### Implementation Steps

1. **Install Istio**
   ```bash
   istioctl install --set profile=production -y
   ```

2. **Enable Sidecar Injection**
   ```bash
   kubectl label namespace default istio-injection=enabled
   ```

3. **Configure Ingress Gateway**
   ```yaml
   apiVersion: networking.istio.io/v1beta1
   kind: Gateway
   metadata:
     name: api-gateway
   spec:
     selector:
       istio: ingressgateway
     servers:
     - port:
         number: 443
         name: https
         protocol: HTTPS
       tls:
         mode: SIMPLE
         credentialName: api-tls-secret
       hosts:
       - api.serhafen.com
   ```

4. **Configure Virtual Services**
   ```yaml
   apiVersion: networking.istio.io/v1beta1
   kind: VirtualService
   metadata:
     name: iam-service
   spec:
     hosts:
     - api.serhafen.com
     gateways:
     - api-gateway
     http:
     - match:
       - uri:
           prefix: /auth
       - uri:
           prefix: /users
       route:
       - destination:
           host: iam-service.default.svc.cluster.local
           port:
             number: 3000
       retries:
         attempts: 3
         perTryTimeout: 2s
       timeout: 10s
   ```

5. **Enable JWT Authentication**
   ```yaml
   apiVersion: security.istio.io/v1beta1
   kind: RequestAuthentication
   metadata:
     name: jwt-auth
   spec:
     jwtRules:
     - issuer: "http://keycloak:8082/realms/NewCustomsRealm"
       jwksUri: "http://keycloak:8082/realms/NewCustomsRealm/protocol/openid-connect/certs"
   ```

6. **Configure Rate Limiting**
   ```yaml
   apiVersion: networking.istio.io/v1beta1
   kind: EnvoyFilter
   metadata:
     name: rate-limit
   spec:
     configPatches:
     - applyTo: HTTP_FILTER
       match:
         context: GATEWAY
       patch:
         operation: INSERT_BEFORE
         value:
           name: envoy.filters.http.local_ratelimit
           typed_config:
             "@type": type.googleapis.com/udpa.type.v1.TypedStruct
             type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
             value:
               stat_prefix: http_local_rate_limiter
               token_bucket:
                 max_tokens: 100
                 tokens_per_fill: 100
                 fill_interval: 60s
   ```

#### Pros
✅ Cloud-native, Kubernetes-native  
✅ Service mesh provides mTLS, observability, circuit breaking  
✅ Zero code changes to services  
✅ Best-in-class observability (Kiali, Jaeger, Grafana)  
✅ Scales with Kubernetes  
✅ Future-proof for microservices growth

#### Cons
❌ Steep learning curve (Istio complexity)  
❌ Resource overhead (sidecar per pod)  
❌ Debugging complexity  
❌ Overkill for current 3-4 services  
❌ Requires dedicated ops expertise

#### Estimated Effort
- **Istio Setup**: 2 weeks
- **Configuration**: 2 weeks
- **Testing & Tuning**: 2 weeks
- **Team Training**: 1 week
- **Total**: 7 weeks

---

## Cost Analysis (AWS + Kubernetes)

### Assumptions
- **Region**: US-East-1 (Northern Virginia)
- **Traffic**: 1M requests/day, 30M/month
- **Services**: 4 backend services (IAM, Customs, MAWB, Mock)
- **High Availability**: Multi-AZ deployment
- **Data Transfer**: 100GB/month outbound

### Solution 1: NestJS API Gateway (RECOMMENDED)

#### Infrastructure Costs

| Component | Spec | Unit Cost | Qty | Monthly Cost |
|-----------|------|-----------|-----|--------------|
| **EKS Cluster** | Control plane | $0.10/hour | 1 | $73 |
| **EC2 (Gateway)** | t3.medium (2 vCPU, 4GB) | $0.0416/hour | 3 | $90 |
| **EC2 (IAM Service)** | t3.medium | $0.0416/hour | 3 | $90 |
| **EC2 (Other Services)** | t3.small (2 vCPU, 2GB) | $0.0208/hour | 9 (3x3) | $135 |
| **Redis (ElastiCache)** | cache.t3.micro | $0.017/hour | 1 | $12 |
| **RDS PostgreSQL** | db.t3.medium | $0.068/hour | 1 | $50 |
| **Application Load Balancer** | ALB | $0.0225/hour + $0.008/LCU | 1 | $22 |
| **NAT Gateway** | Data processing | $0.045/hour + $0.045/GB | 2 | $65 + $4.5 = $70 |
| **Data Transfer Out** | Internet | $0.09/GB | 100GB | $9 |
| **CloudWatch Logs** | 10GB/month | $0.50/GB | 10GB | $5 |
| **Secrets Manager** | 5 secrets | $0.40/secret | 5 | $2 |

**Subtotal**: $558/month

#### Storage Costs

| Component | Spec | Monthly Cost |
|-----------|------|--------------|
| EBS Volumes (100GB per node x 15) | gp3 $0.08/GB | $120 |
| S3 (Frontend static assets) | 5GB | $0.12 |
| RDS Storage (50GB) | gp3 $0.115/GB | $5.75 |

**Subtotal**: $126/month

#### Observability Costs

| Component | Spec | Monthly Cost |
|-----------|------|--------------|
| Prometheus (self-hosted on K8s) | t3.small | Included |
| Grafana (self-hosted on K8s) | t3.small | Included |
| ELK Stack (OpenSearch) | t3.medium.search x 2 | $100 |

**Subtotal**: $100/month

**Total Monthly Cost**: **$784/month** (~$9,400/year)

---

### Solution 2: Kong API Gateway

#### Additional Costs vs Solution 1

| Component | Spec | Monthly Cost |
|-----------|------|--------------|
| Kong OSS (3 pods) | t3.medium | Included (same EC2) |
| Kong Database (PostgreSQL) | db.t3.small | $35 |
| Kong Enterprise License | Per-node (optional) | $0 (using OSS) |

**Total Monthly Cost**: **$819/month** (~$9,828/year)

**Delta vs Solution 1**: +$35/month (+4.5%)

---

### Solution 3: Nginx Ingress + Istio

#### Additional Costs vs Solution 1

| Component | Spec | Monthly Cost |
|-----------|------|--------------|
| Istio Control Plane | t3.medium x 2 | $60 |
| Istio Sidecar Overhead | +256MB per pod | ~$40 (extra EC2) |
| Istio Observability (Kiali, Jaeger) | t3.small x 2 | Included |

**Total Monthly Cost**: **$884/month** (~$10,608/year)

**Delta vs Solution 1**: +$100/month (+12.7%)

---

### Cost-Benefit Analysis

| Solution | Monthly Cost | Annual Cost | Performance | Complexity | Scalability | Recommendation |
|----------|--------------|-------------|-------------|------------|-------------|----------------|
| **Solution 1: NestJS Gateway** | $784 | $9,408 | ⭐⭐⭐⭐ | ⭐⭐⭐ (Medium) | ⭐⭐⭐⭐ | ✅ **BEST VALUE** |
| **Solution 2: Kong** | $819 | $9,828 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (High) | ⭐⭐⭐⭐⭐ | ⚠️ Overkill for now |
| **Solution 3: Istio** | $884 | $10,608 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (Very High) | ⭐⭐⭐⭐⭐ | ❌ Too complex |

### Cost Optimization Tips

1. **Use Spot Instances** for non-critical workloads (save 70%)
   ```yaml
   # k8s node group config
   instanceType: t3.medium
   capacityType: SPOT
   ```
   **Savings**: ~$150/month

2. **Horizontal Pod Autoscaling** - Scale down during off-hours
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: api-gateway
   spec:
     minReplicas: 2  # During off-hours
     maxReplicas: 10
     targetCPUUtilizationPercentage: 70
   ```
   **Savings**: ~$50/month

3. **Use AWS Fargate** for gateway pods (pay-per-use)
   - No need to manage EC2 instances
   - Auto-scaling included
   **Savings**: ~$100/month (for variable traffic)

4. **CloudFront CDN** for frontend
   - Cache static assets
   - Reduce ALB load
   **Savings**: ~$20/month on data transfer

5. **Reserved Instances** for RDS (1-year commitment)
   - 40% discount on database
   **Savings**: ~$20/month

**Optimized Cost**: **$444/month** (~$5,328/year) 🎯

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Set up API Gateway core with JWT authentication

**Tasks**:
- [ ] Create `gateway` module in NestJS IAM service
- [ ] Implement JWT middleware (Keycloak JWKS validation)
- [ ] Implement tenant context propagation
- [ ] Add health check endpoints
- [ ] Deploy to staging environment

**Deliverables**:
- Working JWT authentication for all requests
- Health checks passing
- Swagger documentation updated

**Success Metrics**:
- 100% of requests validated
- <50ms JWT validation overhead
- 99.9% uptime

---

### Phase 2: Service Proxy (Weeks 3-4)

**Goal**: Proxy requests to backend services

**Tasks**:
- [ ] Create proxy service with circuit breaker
- [ ] Implement route configuration (Customs, MAWB services)
- [ ] Add request/response logging
- [ ] Add correlation IDs for tracing
- [ ] Update frontend to call gateway only

**Deliverables**:
- Proxy working for Customs service
- Proxy working for MAWB service
- Circuit breaker tested (simulate failures)
- Frontend using `/api/*` routes only

**Success Metrics**:
- <100ms proxy overhead
- Circuit breaker opens on 50% error rate
- 100% of frontend calls routed through gateway

---

### Phase 3: Rate Limiting & Caching (Weeks 5-6)

**Goal**: Add performance and security features

**Tasks**:
- [ ] Integrate Redis ElastiCache
- [ ] Implement rate limiting (per-user, per-IP)
- [ ] Implement response caching (GET endpoints)
- [ ] Add cache invalidation logic
- [ ] Load testing with 10K req/sec

**Deliverables**:
- Rate limiting active (100 req/min per user)
- Cache hit rate >60% for read endpoints
- Load test passing

**Success Metrics**:
- 0 rate limit violations in prod
- Cache hit rate >60%
- Avg response time <200ms

---

### Phase 4: Observability (Weeks 7-8)

**Goal**: Full monitoring and alerting

**Tasks**:
- [ ] Deploy Prometheus + Grafana
- [ ] Create dashboards (request rate, latency, errors)
- [ ] Integrate OpenTelemetry distributed tracing
- [ ] Set up CloudWatch alarms
- [ ] Create runbooks for common issues

**Deliverables**:
- 10+ Grafana dashboards
- Distributed tracing working
- PagerDuty alerts configured
- Runbooks in Confluence

**Success Metrics**:
- Mean time to detect (MTTD) <5 minutes
- Mean time to resolve (MTTR) <30 minutes
- 99.9% availability

---

### Phase 5: Production Rollout (Weeks 9-10)

**Goal**: Migrate production traffic to gateway

**Tasks**:
- [ ] Blue-green deployment setup
- [ ] Gradual traffic migration (10% → 50% → 100%)
- [ ] Monitor error rates and latency
- [ ] Rollback plan tested
- [ ] Post-deployment review

**Deliverables**:
- 100% of production traffic on gateway
- Zero downtime migration
- Performance metrics within SLA

**Success Metrics**:
- 0 incidents during migration
- Latency <200ms (P95)
- Error rate <0.1%

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **JWT validation overhead** | Medium | High | Use Keycloak JWKS caching, benchmark before rollout |
| **Circuit breaker false positives** | Medium | Medium | Tune thresholds based on staging data |
| **Redis single point of failure** | Low | High | Use ElastiCache with Multi-AZ replication |
| **Proxy latency** | Medium | High | Use Fastify (fastest Node.js framework), load test |
| **Memory leaks in gateway** | Low | Critical | Extensive load testing, memory profiling |
| **Tenant context lost** | Low | Critical | Integration tests for all request flows |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Team unfamiliar with gateway patterns** | High | Medium | 2-week training period, pair programming |
| **Increased infrastructure costs** | Medium | Medium | Use Spot instances, HPA for autoscaling |
| **Migration downtime** | Low | Critical | Blue-green deployment, gradual rollout |
| **Monitoring gaps** | Medium | High | Pre-deploy dashboards, runbooks |
| **Third-party service outages** | Low | High | Circuit breakers, graceful degradation |

### Security Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **JWT token leakage** | Low | Critical | Use HTTPS everywhere, short token TTL (5 min) |
| **Rate limit bypass** | Medium | High | Use Redis for distributed rate limiting |
| **DDoS attack** | Medium | Critical | AWS Shield, CloudFront, rate limiting |
| **Unauthorized access** | Low | Critical | Strict RBAC, audit logging |

---

## Recommendations

### 🏆 Primary Recommendation: Solution 1 (NestJS API Gateway)

**Rationale**:
1. **Fastest time to market** - Leverages existing NestJS codebase
2. **Best cost-performance** - $784/month, lowest operational overhead
3. **Team expertise** - Team already proficient in NestJS/TypeScript
4. **Incremental migration** - Can add proxy modules one service at a time
5. **Preserves multi-tenancy** - No need to rebuild tenant context logic

**When to Migrate to Kong/Istio**:
- When serving >10M requests/day (performance bottleneck)
- When managing >10 backend services (operational complexity)
- When needing advanced features (gRPC, WebSocket at scale)
- When ops team has dedicated service mesh expertise

---

### 📋 Action Items (Next 2 Weeks)

**Week 1**:
1. **Architecture Review** - Present this document to stakeholders
2. **POC Validation** - Test NestJS proxy with 1 service (Customs)
3. **Cost Approval** - Get budget sign-off for $784/month
4. **Team Training** - NestJS middleware, circuit breakers, caching

**Week 2**:
5. **Development Kickoff** - Assign tasks to team
6. **Infrastructure Setup** - Provision Redis, update K8s configs
7. **CI/CD Pipeline** - Update GitHub Actions for gateway deployment
8. **Monitoring Setup** - Deploy Prometheus + Grafana to staging

---

### 🔮 Future Enhancements (6-12 Months)

1. **GraphQL Gateway** - Consolidate multiple REST calls into single GraphQL query
2. **WebSocket Support** - Real-time notifications, live updates
3. **Edge Caching** - CloudFront with Lambda@Edge for dynamic content
4. **API Versioning** - Support /v1/* and /v2/* simultaneously
5. **Multi-Region** - Deploy to EU for GDPR compliance
6. **Service Mesh Migration** - Consider Istio when >10 services

---

### 📊 Success Metrics (6 Months Post-Deployment)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Availability** | 99.5% | 99.9% | CloudWatch uptime |
| **Latency (P95)** | 500ms | <200ms | Prometheus histogram |
| **Error Rate** | 1% | <0.1% | Gateway logs |
| **Cache Hit Rate** | 0% | >60% | Redis metrics |
| **Cost per Request** | $0.0005 | <$0.0003 | AWS Cost Explorer |
| **MTTR** | 60 min | <30 min | PagerDuty |
| **Developer Velocity** | N/A | +30% | Story points/sprint |

---

## Conclusion

**The POC (v2-api-version) successfully demonstrates the API gateway pattern** with centralized authentication and single entry point. However, it's limited to a single service (Keycloak Admin API) and lacks production-ready features like multi-tenancy, rate limiting, and observability.

**Production systems have a strong foundation** with NestJS IAM service implementing CQRS, multi-tenancy, circuit breakers, and structured logging. The frontend is well-architected but makes direct calls to multiple backends, creating operational complexity.

**Extending the production NestJS IAM service as an API gateway is the optimal path forward**:
- Fastest time to market (5-6 weeks)
- Lowest cost ($784/month, optimizable to $444/month)
- Leverages existing team expertise
- Preserves multi-tenancy and CQRS patterns
- Incremental migration path

**Kong and Istio are viable alternatives** for future scale (>10 services, >10M req/day) but introduce unnecessary complexity and cost for current needs.

---

## Appendix

### A. Frontend Configuration Changes

**Before** (Direct service calls):
```typescript
// src/lib/config.ts
export const Endpoints = {
  login: `${iamService}/v0/auth/login`,
  listMawbs: `${customsDeclarationService}/v0/mawbs`,
  hawbs: `${customsDeclarationService}/v0/hawbs`,
  // ... 10+ hardcoded URLs
};
```

**After** (Gateway-only):
```typescript
// src/lib/config.ts
const API_GATEWAY = import.meta.env.VITE_API_GATEWAY_URL;

export const Endpoints = {
  login: `${API_GATEWAY}/auth/login`,
  listMawbs: `${API_GATEWAY}/mawbs`,
  hawbs: `${API_GATEWAY}/hawbs`,
  // Single entry point
};
```

---

### B. Example Kubernetes Manifests

**Gateway Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  labels:
    app: api-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: gateway
        image: your-registry/api-gateway:v1.0.0
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: production
        - name: REDIS_HOST
          value: redis.default.svc.cluster.local
        - name: KEYCLOAK_BASE_URL
          value: http://keycloak.default.svc.cluster.local:8082
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /actuator/liveness
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/readiness
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
```

**HorizontalPodAutoscaler**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

### C. Monitoring Queries

**Prometheus Queries**:
```promql
# Request rate by service
sum(rate(http_requests_total[5m])) by (service)

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# Latency (P95)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Circuit breaker state
circuit_breaker_state{service="customs"} # 0=closed, 1=open, 2=half-open

# Cache hit rate
sum(rate(redis_cache_hits[5m])) / (sum(rate(redis_cache_hits[5m])) + sum(rate(redis_cache_misses[5m])))
```

**CloudWatch Alarms**:
```yaml
# High error rate
MetricName: 5xxErrors
Threshold: 10
EvaluationPeriods: 2
ComparisonOperator: GreaterThanThreshold
AlarmActions:
  - arn:aws:sns:us-east-1:123456789012:pagerduty

# High latency
MetricName: TargetResponseTime
Statistic: p95
Threshold: 500ms
```

---

### D. References

1. **NestJS Documentation**: https://docs.nestjs.com
2. **Fastify Performance**: https://fastify.dev/benchmarks
3. **Kong Gateway**: https://konghq.com/products/kong-gateway
4. **Istio Service Mesh**: https://istio.io/latest/docs
5. **AWS EKS Pricing**: https://aws.amazon.com/eks/pricing
6. **Keycloak Admin REST API**: https://www.keycloak.org/docs-api/latest/rest-api
7. **OpenTelemetry**: https://opentelemetry.io/docs
8. **Circuit Breaker Pattern**: https://martinfowler.com/bliki/CircuitBreaker.html

---

**Document Status**: ✅ Ready for Review  
**Last Updated**: December 11, 2025  
**Next Review**: After stakeholder feedback
