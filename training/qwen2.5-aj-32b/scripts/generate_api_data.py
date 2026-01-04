#!/usr/bin/env python3
"""
API Development Training Data Generator
Target: ~200 examples for REST APIs, GraphQL, webhooks, API design
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for API development and integration.
You help with REST API design, GraphQL, webhooks, API security, and integration patterns."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

API_TASKS = [
    {
        "instruction": "Test REST API endpoint with curl",
        "command": "curl -X GET http://localhost:8000/api/users -H 'Accept: application/json' -H 'Authorization: Bearer $TOKEN' | jq",
        "explanation": "GET request with auth header, pipes to jq for formatting"
    },
    {
        "instruction": "Send POST request with JSON body",
        "command": "curl -X POST http://localhost:8000/api/users -H 'Content-Type: application/json' -d '{\"name\": \"John\", \"email\": \"john@example.com\"}'",
        "explanation": "POST with JSON content type and body"
    },
    {
        "instruction": "Test API with HTTPie",
        "command": "http POST localhost:8000/api/users name=John email=john@example.com Authorization:'Bearer token'",
        "explanation": "HTTPie provides cleaner syntax than curl"
    },
    {
        "instruction": "Generate OpenAPI documentation",
        "command": "openapi-generator generate -i openapi.yaml -g python-fastapi -o ./generated",
        "explanation": "Generates FastAPI server stub from OpenAPI spec"
    },
    {
        "instruction": "Validate OpenAPI specification",
        "command": "openapi-generator validate -i openapi.yaml",
        "explanation": "Checks spec for errors and warnings"
    },
    {
        "instruction": "Start GraphQL Playground",
        "command": "npx graphql-playground",
        "explanation": "Interactive GraphQL IDE for testing queries"
    },
    {
        "instruction": "Introspect GraphQL schema",
        "command": "npx graphql get-schema --endpoint http://localhost:4000/graphql --output schema.graphql",
        "explanation": "Downloads schema from running server"
    },
    {
        "instruction": "Test webhook endpoint locally",
        "command": "ngrok http 8000",
        "explanation": "Creates public URL to tunnel to local server"
    },
    {
        "instruction": "Load test API endpoint",
        "command": "hey -n 1000 -c 100 -m GET http://localhost:8000/api/users",
        "explanation": "Sends 1000 requests with 100 concurrent connections"
    },
    {
        "instruction": "Mock API server from OpenAPI spec",
        "command": "prism mock openapi.yaml",
        "explanation": "Starts mock server that returns example responses"
    },
    {
        "instruction": "Send PUT request to update resource",
        "command": "curl -X PUT http://localhost:8000/api/users/1 -H 'Content-Type: application/json' -d '{\"name\": \"Updated\"}'",
        "explanation": "PUT request for full resource update"
    },
    {
        "instruction": "Send PATCH request for partial update",
        "command": "curl -X PATCH http://localhost:8000/api/users/1 -H 'Content-Type: application/json' -d '{\"email\": \"new@example.com\"}'",
        "explanation": "PATCH for partial resource modification"
    },
    {
        "instruction": "Delete resource with curl",
        "command": "curl -X DELETE http://localhost:8000/api/users/1 -H 'Authorization: Bearer $TOKEN' -w '%{http_code}'",
        "explanation": "DELETE request showing response status code"
    },
    {
        "instruction": "Upload file via API",
        "command": "curl -X POST http://localhost:8000/api/upload -F 'file=@document.pdf' -F 'description=My file'",
        "explanation": "Multipart form upload with file and metadata"
    },
    {
        "instruction": "Download file from API",
        "command": "curl -OJ http://localhost:8000/api/files/123/download -H 'Authorization: Bearer $TOKEN'",
        "explanation": "Downloads file using server-provided filename"
    },
    {
        "instruction": "Test API with verbose output",
        "command": "curl -v http://localhost:8000/api/health",
        "explanation": "Shows full request/response headers and body"
    },
    {
        "instruction": "Send request with custom headers",
        "command": "curl http://localhost:8000/api/data -H 'X-Request-ID: abc123' -H 'X-Api-Version: 2'",
        "explanation": "Adds custom tracking and versioning headers"
    },
    {
        "instruction": "Follow API redirects",
        "command": "curl -L http://localhost:8000/api/redirect",
        "explanation": "Follows 301/302 redirects automatically"
    },
    {
        "instruction": "Save API response to file",
        "command": "curl -o response.json http://localhost:8000/api/data",
        "explanation": "Writes response body to file"
    },
    {
        "instruction": "Test API with timeout",
        "command": "curl --connect-timeout 5 --max-time 30 http://localhost:8000/api/slow",
        "explanation": "Sets connection and total timeout limits"
    },
    {
        "instruction": "Send GraphQL query with curl",
        "command": "curl -X POST http://localhost:4000/graphql -H 'Content-Type: application/json' -d '{\"query\": \"{ users { id name } }\"}'",
        "explanation": "Posts GraphQL query as JSON"
    },
    {
        "instruction": "Send GraphQL mutation",
        "command": "curl -X POST http://localhost:4000/graphql -H 'Content-Type: application/json' -d '{\"query\": \"mutation { createUser(name: \\\"John\\\") { id } }\"}'",
        "explanation": "GraphQL mutation via HTTP POST"
    },
    {
        "instruction": "Generate TypeScript types from OpenAPI",
        "command": "npx openapi-typescript openapi.yaml -o types.ts",
        "explanation": "Creates TypeScript interfaces from API spec"
    },
    {
        "instruction": "Generate API client from OpenAPI",
        "command": "openapi-generator generate -i openapi.yaml -g typescript-axios -o ./client",
        "explanation": "Creates Axios client from OpenAPI spec"
    },
    {
        "instruction": "Start Swagger UI for API docs",
        "command": "docker run -p 8080:8080 -e SWAGGER_JSON=/api/openapi.yaml -v $(pwd):/api swaggerapi/swagger-ui",
        "explanation": "Serves interactive API documentation"
    },
    {
        "instruction": "Test API rate limiting",
        "command": "for i in {1..100}; do curl -s -o /dev/null -w '%{http_code}\\n' http://localhost:8000/api/data; done | sort | uniq -c",
        "explanation": "Sends rapid requests to trigger rate limiting"
    },
    {
        "instruction": "Test WebSocket connection",
        "command": "websocat ws://localhost:8000/ws",
        "explanation": "Interactive WebSocket client for testing"
    },
    {
        "instruction": "Replay HTTP traffic",
        "command": "mitmproxy -r captured.flow --replay-client",
        "explanation": "Replays captured HTTP requests for testing"
    },
    {
        "instruction": "Benchmark API with wrk",
        "command": "wrk -t12 -c400 -d30s http://localhost:8000/api/users",
        "explanation": "High-performance HTTP benchmark tool"
    },
    {
        "instruction": "Test gRPC service",
        "command": "grpcurl -plaintext localhost:50051 list",
        "explanation": "Lists available gRPC services"
    },
    {
        "instruction": "Call gRPC method",
        "command": "grpcurl -plaintext -d '{\"name\": \"John\"}' localhost:50051 user.UserService/CreateUser",
        "explanation": "Invokes gRPC method with JSON payload"
    },
    {
        "instruction": "Generate gRPC code from proto",
        "command": "protoc --python_out=. --grpc_python_out=. service.proto",
        "explanation": "Compiles Protocol Buffers to Python"
    },
    {
        "instruction": "Test API authentication flow",
        "command": "TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -d 'username=user&password=pass' | jq -r .token) && curl -H \"Authorization: Bearer $TOKEN\" http://localhost:8000/api/me",
        "explanation": "Login and use token in subsequent request"
    },
    {
        "instruction": "Test OAuth2 token endpoint",
        "command": "curl -X POST http://localhost:8000/oauth/token -d 'grant_type=client_credentials&client_id=app&client_secret=secret'",
        "explanation": "Requests OAuth2 access token"
    },
    {
        "instruction": "Test API with cookies",
        "command": "curl -c cookies.txt -b cookies.txt http://localhost:8000/api/session",
        "explanation": "Saves and sends cookies across requests"
    },
    {
        "instruction": "Send request with basic auth",
        "command": "curl -u username:password http://localhost:8000/api/protected",
        "explanation": "HTTP Basic authentication"
    },
    {
        "instruction": "Test API CORS preflight",
        "command": "curl -X OPTIONS http://localhost:8000/api/data -H 'Origin: http://example.com' -H 'Access-Control-Request-Method: POST' -v",
        "explanation": "Simulates browser CORS preflight request"
    },
    {
        "instruction": "Generate Postman collection from OpenAPI",
        "command": "openapi2postmanv2 -s openapi.yaml -o collection.json",
        "explanation": "Creates Postman collection for API testing"
    },
    {
        "instruction": "Run Postman collection tests",
        "command": "newman run collection.json -e environment.json --reporters cli,htmlextra",
        "explanation": "Executes Postman tests with HTML report"
    },
    {
        "instruction": "Start mock GraphQL server",
        "command": "npx graphql-faker schema.graphql",
        "explanation": "Creates mock server with fake data"
    },
    {
        "instruction": "Profile API response time",
        "command": "curl -w '@curl-format.txt' -o /dev/null -s http://localhost:8000/api/data",
        "explanation": "Shows detailed timing breakdown"
    },
    {
        "instruction": "Test server-sent events",
        "command": "curl -N http://localhost:8000/api/events",
        "explanation": "Streams SSE events from server"
    },
    {
        "instruction": "Compress request body",
        "command": "curl -X POST http://localhost:8000/api/data -H 'Content-Encoding: gzip' --data-binary @<(echo '{\"large\": \"data\"}' | gzip)",
        "explanation": "Sends gzip-compressed request body"
    },
    {
        "instruction": "Test API with retry",
        "command": "curl --retry 3 --retry-delay 2 http://localhost:8000/api/flaky",
        "explanation": "Automatically retries failed requests"
    },
    {
        "instruction": "Monitor API with httpstat",
        "command": "httpstat http://localhost:8000/api/health",
        "explanation": "Visual HTTP timing statistics"
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "instruction": "Create REST API with FastAPI",
        "language": "python",
        "code": """from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="User API",
    version="1.0.0",
    description="User management API"
)

security = HTTPBearer()

# Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

# Simulated database
users_db: dict[int, dict] = {}
next_id = 1

# Dependency for authentication
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "valid-token":  # Replace with real validation
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

# Endpoints
@app.get("/api/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    token: str = Depends(verify_token)
):
    \"\"\"List all users with pagination.\"\"\"
    users = list(users_db.values())[skip:skip + limit]
    return users

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, token: str = Depends(verify_token)):
    \"\"\"Create a new user.\"\"\"
    global next_id
    user_dict = {
        "id": next_id,
        "name": user.name,
        "email": user.email,
        "created_at": datetime.utcnow()
    }
    users_db[next_id] = user_dict
    next_id += 1
    return user_dict

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, token: str = Depends(verify_token)):
    \"\"\"Get user by ID.\"\"\"
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, token: str = Depends(verify_token)):
    \"\"\"Partially update a user.\"\"\"
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user.model_dump(exclude_unset=True)
    users_db[user_id].update(update_data)
    return users_db[user_id]

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, token: str = Depends(verify_token)):
    \"\"\"Delete a user.\"\"\"
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]""",
        "explanation": "Complete REST API with CRUD, validation, auth, pagination"
    },
    {
        "instruction": "Implement rate limiting middleware",
        "language": "python",
        "code": """from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
from typing import Dict, Tuple

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        request_count, window_start = self.clients[client_ip]
        
        # Reset window if minute has passed
        if current_time - window_start > 60:
            request_count = 0
            window_start = current_time
        
        if request_count >= self.requests_per_minute:
            remaining = 60 - (current_time - window_start)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(int(remaining)),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_start + 60))
                }
            )
        
        self.clients[client_ip] = (request_count + 1, window_start)
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self.requests_per_minute - request_count - 1)
        return response

app = FastAPI()
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)""",
        "explanation": "Simple in-memory rate limiter, use Redis for distributed"
    },
    {
        "instruction": "Create GraphQL API with Strawberry",
        "language": "python",
        "code": """import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI
from typing import List, Optional
from datetime import datetime

# Types
@strawberry.type
class User:
    id: int
    name: str
    email: str
    created_at: datetime
    posts: List["Post"]

@strawberry.type
class Post:
    id: int
    title: str
    content: str
    author_id: int
    author: User

# Input types
@strawberry.input
class CreateUserInput:
    name: str
    email: str

@strawberry.input
class CreatePostInput:
    title: str
    content: str
    author_id: int

# Simulated data
users_db = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com", "created_at": datetime.now()}
}
posts_db = {
    1: {"id": 1, "title": "Hello", "content": "World", "author_id": 1}
}

# Resolvers
def get_user_posts(user_id: int) -> List[Post]:
    return [Post(**p, author=get_user(p["author_id"])) 
            for p in posts_db.values() if p["author_id"] == user_id]

def get_user(user_id: int) -> Optional[User]:
    if user_id not in users_db:
        return None
    user = users_db[user_id]
    return User(**user, posts=get_user_posts(user_id))

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        return [get_user(uid) for uid in users_db]
    
    @strawberry.field
    def user(self, id: int) -> Optional[User]:
        return get_user(id)
    
    @strawberry.field
    def posts(self) -> List[Post]:
        return [Post(**p, author=get_user(p["author_id"])) for p in posts_db.values()]

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: CreateUserInput) -> User:
        new_id = max(users_db.keys()) + 1
        users_db[new_id] = {
            "id": new_id,
            "name": input.name,
            "email": input.email,
            "created_at": datetime.now()
        }
        return get_user(new_id)

schema = strawberry.Schema(query=Query, mutation=Mutation)

app = FastAPI()
app.include_router(GraphQLRouter(schema), prefix="/graphql")""",
        "explanation": "GraphQL API with types, queries, mutations, relationships"
    },
    {
        "instruction": "Implement webhook handler with signature verification",
        "language": "python",
        "code": """import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Literal
import json

app = FastAPI()

WEBHOOK_SECRET = "your-webhook-secret"  # From environment

class WebhookPayload(BaseModel):
    event: Literal["user.created", "user.updated", "user.deleted"]
    data: dict
    timestamp: str

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    \"\"\"Verify HMAC-SHA256 webhook signature.\"\"\"
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.post("/webhooks/users")
async def handle_user_webhook(
    request: Request,
    x_webhook_signature: str = Header(..., alias="X-Webhook-Signature")
):
    \"\"\"Handle incoming webhooks with signature verification.\"\"\"
    body = await request.body()
    
    # Verify signature
    if not verify_signature(body, x_webhook_signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        payload = WebhookPayload(**json.loads(body))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    
    # Handle event
    handlers = {
        "user.created": handle_user_created,
        "user.updated": handle_user_updated,
        "user.deleted": handle_user_deleted,
    }
    
    handler = handlers.get(payload.event)
    if handler:
        await handler(payload.data)
    
    return {"status": "ok"}

async def handle_user_created(data: dict):
    print(f"User created: {data}")

async def handle_user_updated(data: dict):
    print(f"User updated: {data}")

async def handle_user_deleted(data: dict):
    print(f"User deleted: {data}")""",
        "explanation": "Secure webhook handler with HMAC signature verification"
    },
    {
        "instruction": "Write OpenAPI specification",
        "language": "yaml",
        "code": """openapi: 3.0.3
info:
  title: User Management API
  version: 1.0.0
  description: API for managing users
  contact:
    email: api@example.com

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: http://localhost:8000/v1
    description: Development

paths:
  /users:
    get:
      summary: List users
      operationId: listUsers
      tags: [Users]
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
        '401':
          $ref: '#/components/responses/Unauthorized'
      security:
        - bearerAuth: []
    
    post:
      summary: Create user
      operationId: createUser
      tags: [Users]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          description: Email already exists
      security:
        - bearerAuth: []

  /users/{userId}:
    parameters:
      - name: userId
        in: path
        required: true
        schema:
          type: string
          format: uuid
    
    get:
      summary: Get user by ID
      operationId: getUser
      tags: [Users]
      responses:
        '200':
          description: User details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          $ref: '#/components/responses/NotFound'
      security:
        - bearerAuth: []

components:
  schemas:
    User:
      type: object
      required: [id, name, email, createdAt]
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        email:
          type: string
          format: email
        createdAt:
          type: string
          format: date-time
    
    CreateUser:
      type: object
      required: [name, email]
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        email:
          type: string
          format: email
    
    Pagination:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer
    
    Error:
      type: object
      properties:
        code:
          type: string
        message:
          type: string

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT""",
        "explanation": "Complete OpenAPI 3.0 spec with schemas, responses, security"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Design RESTful API for e-commerce platform",
        "steps": [
            "Identify resources: products, categories, users, orders, cart",
            "Define URL structure following REST conventions",
            "Plan authentication (JWT) and authorization (roles)",
            "Design response envelope: {data, meta, errors}",
            "Define error format: {code, message, details}",
            "Plan pagination: cursor-based for lists",
            "Design filtering and sorting query params",
            "Create OpenAPI specification",
            "Define rate limiting strategy",
            "Plan versioning approach (URL path: /v1/)",
            "Design webhook events for order status",
            "Document API with examples",
            "Create Postman/Bruno collection",
            "Generate client SDKs from spec"
        ]
    },
    {
        "instruction": "Implement API versioning strategy",
        "steps": [
            "Choose versioning approach (URL path vs header vs query param)",
            "URL path recommended: /api/v1/resource",
            "Create version-specific routers/controllers",
            "Share common logic between versions",
            "Document breaking changes per version",
            "Set deprecation timeline (6+ months)",
            "Add deprecation warnings in responses (Deprecation header)",
            "Create version migration guide",
            "Set up monitoring for old version usage",
            "Implement sunset header for deprecated versions",
            "Redirect very old versions to docs",
            "Maintain at most 2-3 active versions"
        ]
    },
    {
        "instruction": "Add comprehensive error handling to API",
        "steps": [
            "Define error response schema: {code, message, details, requestId}",
            "Create error code taxonomy (AUTH_001, VALIDATION_002, etc.)",
            "Implement global exception handler",
            "Map exceptions to HTTP status codes",
            "Add request ID to all responses for tracing",
            "Never expose stack traces in production",
            "Log full error details server-side",
            "Provide actionable error messages",
            "Include links to documentation in errors",
            "Handle validation errors with field-level details",
            "Test error scenarios in integration tests",
            "Document all error codes in API docs"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is REST and RESTful API design?",
        "answer": "REST (Representational State Transfer) is architectural style for web APIs. Principles: stateless (no server-side sessions), uniform interface (standard HTTP methods), resource-based URLs. HTTP methods: GET (read), POST (create), PUT/PATCH (update), DELETE (remove). Good URL design: /users (collection), /users/{id} (item), /users/{id}/posts (sub-resource). Use nouns not verbs. Status codes: 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Server Error. Return JSON with consistent structure."
    },
    {
        "question": "What is GraphQL and when should I use it?",
        "answer": "GraphQL is query language for APIs where clients request exactly the data they need. Single endpoint, typed schema, introspection. Benefits: no over/under-fetching, strongly typed, self-documenting. Use when: complex data requirements, multiple clients needing different data, rapid iteration. REST better for: simple CRUD, caching important, simpler to implement. GraphQL concepts: Query (read), Mutation (write), Subscription (real-time), Types, Resolvers. Tools: Apollo, Strawberry, graphql-yoga."
    },
    {
        "question": "How do I handle API authentication?",
        "answer": "Common approaches: API keys (simple but less secure), JWT tokens (stateless, include claims), OAuth 2.0 (delegated auth, third-party). JWT flow: login → get token → include in Authorization: Bearer <token>. Store tokens securely (httpOnly cookies or secure storage). Short-lived access tokens + refresh tokens. Validate tokens on every request. For service-to-service: API keys or mTLS. Never send credentials in URLs. Use HTTPS always."
    },
    {
        "question": "What are webhooks?",
        "answer": "Webhooks are HTTP callbacks - server pushes data to client when events occur. Alternative to polling. Example: payment processor notifies your server when payment completes. Implementation: register callback URL, receive POST with event data, verify signature, respond quickly (< 5s). Best practices: verify signatures (HMAC), return 2xx quickly, process async, handle retries (idempotency), log everything. Retry logic: exponential backoff on failure."
    },
    {
        "question": "What are HTTP status codes?",
        "answer": "Status codes indicate request outcome. 2xx Success: 200 OK, 201 Created, 204 No Content. 3xx Redirect: 301 Moved Permanently, 302 Found, 304 Not Modified. 4xx Client Error: 400 Bad Request, 401 Unauthorized (unauthenticated), 403 Forbidden (no permission), 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 429 Too Many Requests. 5xx Server Error: 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable. Use specific codes - helps debugging and client handling."
    },
    {
        "question": "What is API versioning?",
        "answer": "Versioning manages breaking changes. Strategies: URL path (/v1/users), query param (?version=1), custom header (X-API-Version: 1), Accept header (Accept: application/vnd.api.v1+json). URL versioning most common - simple, visible, cacheable. Maintain multiple versions during migration. Deprecation headers warn clients. Document sunset dates. Best practice: design to avoid versioning (additive changes only). Version when truly breaking: renamed fields, changed behavior, removed endpoints."
    },
    {
        "question": "What is content negotiation?",
        "answer": "Content negotiation: server returns different formats based on client preference. Accept header specifies desired format: Accept: application/json, application/xml. Server responds with Content-Type header. Common: JSON (default), XML, MessagePack, Protocol Buffers. Implementation: check Accept header, return appropriate format. Quality values for preference: Accept: application/json;q=1.0, application/xml;q=0.5. Return 406 Not Acceptable if format unsupported. Most APIs JSON-only now."
    },
    {
        "question": "What is API documentation?",
        "answer": "Documentation crucial for API adoption. Standards: OpenAPI/Swagger (most common), AsyncAPI (events), API Blueprint. Auto-generate from code or write spec first. Include: endpoints, methods, parameters, request/response examples, authentication, errors. Tools: Swagger UI, Redoc, Stoplight, Postman. Interactive docs let users try API. Keep docs versioned with code. Test that examples work. Good docs reduce support burden significantly."
    },
    {
        "question": "What is request validation?",
        "answer": "Validation ensures request data meets requirements before processing. Validate: data types, required fields, string lengths, number ranges, formats (email, UUID), enums. Server-side validation mandatory (client bypass possible). Return 400 with specific error details. Libraries: Pydantic (Python), Zod/Yup (JS), FluentValidation (.NET). Schema validation from OpenAPI spec. Sanitize inputs (prevent injection). Early validation fails fast, saves resources. Include field name and expected format in errors."
    },
    {
        "question": "What is CORS?",
        "answer": "CORS (Cross-Origin Resource Sharing) controls which domains can access API from browsers. Same-origin policy blocks cross-domain requests by default. Server sends headers: Access-Control-Allow-Origin, Allow-Methods, Allow-Headers. Preflight OPTIONS request for complex requests. Configuration: specific origins (secure), wildcard * (public APIs without auth). With credentials: must specify exact origin. Common issue: forgot to handle OPTIONS, wrong origin. Not needed for server-to-server."
    },
    {
        "question": "What are query parameters vs path parameters?",
        "answer": "Path parameters identify specific resource: /users/{id}, /posts/{postId}/comments/{commentId}. Query parameters filter, sort, paginate: /users?role=admin&sort=name&page=2. Path: required for resource identification, part of URL structure. Query: optional, for modifying request. Guidelines: use path for identity, query for filtering. Arrays in query: ?ids=1,2,3 or ?ids=1&ids=2. Complex filters: consider POST with body. Document all parameters with types and defaults."
    },
    {
        "question": "What are idempotent API operations?",
        "answer": "Idempotent: multiple identical requests have same effect as single request. GET, PUT, DELETE should be idempotent. POST typically not (creates new resource each time). Importance: safe retries on network failures, client simplicity. Implementation: use unique IDs for creation, check existence before delete. Idempotency keys: client sends unique key, server tracks processed requests. Example header: Idempotency-Key: abc-123. Important for payment APIs - prevents double charges."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "What is API rate limiting and how do I implement it?",
        "answer": "Rate limiting controls request frequency to prevent abuse and ensure fair usage. Algorithms: fixed window (X per minute), sliding window (smoother), token bucket (allows bursts), leaky bucket (constant rate). Implementation: track requests per client (IP, API key, user), store in Redis for distributed systems. Response headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset. Return 429 Too Many Requests when exceeded. Consider different limits per endpoint, user tier. Use Retry-After header."
    },
    {
        "question": "How do I design APIs for backward compatibility?",
        "answer": "Additive changes are safe: new fields, new endpoints, new optional params. Breaking changes: removing fields, changing types, renaming, changing behavior. Strategies: always add, never remove (deprecate instead), version when breaking changes unavoidable. Use nullable types, default values. Deprecation: mark in docs, add headers, monitor usage, sunset after grace period. Contract testing catches breaks. Feature flags for gradual rollout. API versioning as last resort."
    },
    {
        "question": "What is HATEOAS in REST APIs?",
        "answer": "HATEOAS (Hypermedia As The Engine Of Application State): responses include links to related actions/resources. Level 3 of Richardson Maturity Model. Example: GET /orders/123 returns {id, status, _links: {self, cancel, items}}. Benefits: discoverable API, client doesn't hardcode URLs, server can change URLs. Rarely fully implemented - most APIs are level 2 (resources + HTTP verbs). Consider for complex workflows, public APIs. JSON:API and HAL are formats supporting HATEOAS."
    },
    {
        "question": "How do I handle pagination in APIs?",
        "answer": "Offset pagination: ?page=2&limit=20. Simple but problematic with large datasets (skip is slow) and inconsistent with live data. Cursor pagination: ?after=abc123&limit=20. Cursor encodes position (usually ID or timestamp). Consistent with changing data, efficient for large datasets. Return: {data, nextCursor, prevCursor, hasMore}. Keyset pagination similar, uses last seen values. For infinite scroll: cursor. For page numbers: offset with max limit. Include total count only if cheap to compute."
    },
    {
        "question": "What is API gateway and why use it?",
        "answer": "API gateway sits between clients and services. Functions: routing, authentication, rate limiting, caching, request transformation, monitoring, load balancing. Products: Kong, AWS API Gateway, Azure API Management, Traefik. Benefits: centralized concerns, microservice abstraction, protocol translation. Patterns: aggregate multiple services, request/response transformation, circuit breaker. Considerations: single point of failure, added latency. Can implement: SSL termination, API versioning, request validation."
    },
    {
        "question": "How do I handle errors in APIs?",
        "answer": "Consistent error format: {error: {code: 'VALIDATION_ERROR', message: 'Invalid email', details: [{field: 'email', issue: 'format'}]}}. Use appropriate status codes. Include enough detail to fix issue. Never expose stack traces, internal paths, or sensitive info. Log full error server-side with request ID. Return request ID for support correlation. Document all error codes. Distinguish client errors (4xx) from server errors (5xx). Localize error messages for i18n."
    },
    {
        "question": "What is API caching?",
        "answer": "Caching reduces load and latency. HTTP caching: Cache-Control header (max-age, no-cache, private), ETag for validation. CDN caching for public data. Application caching: Redis/Memcached for computed data, response caching. Cache strategies: cache-aside, write-through, write-behind. Cache invalidation: TTL-based, event-driven. Cache key design includes: endpoint, params, user (if personal). Avoid caching: authenticated user data at CDN, frequently changing data, POST requests."
    },
    {
        "question": "How do I design APIs for microservices?",
        "answer": "Internal APIs: may use gRPC for performance, not REST. Service discovery: Consul, Kubernetes DNS. Circuit breaker: Polly, resilience4j - prevent cascade failures. Distributed tracing: correlate requests across services. API contracts: OpenAPI, protobuf schemas. Versioning between services. Event-driven: async communication for decoupling. BFF pattern: separate API per client type. Aggregate APIs: single call triggers multiple services. Monitor: latency, error rates per service."
    },
    {
        "question": "What is OAuth 2.0 and OpenID Connect?",
        "answer": "OAuth 2.0: authorization framework for delegated access. Flows: Authorization Code (web apps), Client Credentials (service-to-service), PKCE (mobile/SPA). Terms: resource owner, client, authorization server, resource server. Tokens: access token (short-lived), refresh token (long-lived). OpenID Connect: identity layer on OAuth. ID token contains user info (JWT). Scopes define permissions. Use established libraries - don't implement yourself. Common providers: Auth0, Okta, Azure AD."
    },
    {
        "question": "How do I implement real-time APIs?",
        "answer": "Options: WebSocket (bidirectional, persistent), Server-Sent Events (server push, simpler), Long polling (fallback). WebSocket: full-duplex, lower overhead after handshake. SSE: text-only, auto-reconnect, simpler. Use cases: chat, notifications, live updates, collaborative editing. Implementation: Socket.io, SignalR, native WebSocket. Consider: connection limits, horizontal scaling (sticky sessions or pub/sub), reconnection logic, heartbeats. Alternative: webhooks for server-to-server."
    },
    {
        "question": "What is API mocking and testing?",
        "answer": "Mocking: simulate API for development/testing. Tools: WireMock, Prism, MSW (Mock Service Worker). Contract testing: verify API matches spec - Pact, Dredd. Integration tests: actual API calls in test environment. Load testing: k6, Locust, Apache JMeter. Test: happy path, error cases, edge cases, auth, rate limits. API test automation in CI/CD. Mock external dependencies. Snapshot testing for response structure. Generate tests from OpenAPI spec."
    },
    {
        "question": "How do I handle large file uploads in APIs?",
        "answer": "Challenges: memory, timeout, resume support. Solutions: multipart upload (chunks), presigned URLs (direct to storage), streaming. Presigned URL flow: client requests URL → server generates S3/Blob URL → client uploads directly. Benefits: offload bandwidth from API server. Multipart: upload in parts, server reassembles. Implement: progress tracking, resume capability, validation after upload. Size limits: reject early based on Content-Length. Virus scanning before processing."
    },
]

# =============================================================================
# ERROR SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "API returning 500 Internal Server Error",
        "error_type": "server_error",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Check server logs for stack trace",
                "Look for unhandled exceptions",
                "Verify database connections",
                "Check external service dependencies",
                "Review recent deployments",
                "Check memory/CPU usage"
            ],
            "common_causes": [
                "Unhandled null/undefined",
                "Database connection timeout",
                "External service down",
                "Out of memory",
                "Configuration error"
            ],
            "best_practice": "Never return raw errors to client, log and return generic message"
        }
    },
    {
        "instruction": "Return user password in API response",
        "error_type": "security_violation",
        "response": {
            "status": "blocked",
            "reason": "Exposing passwords is a critical security vulnerability",
            "proper_approach": [
                "Never store plain text passwords",
                "Never include password in response models",
                "Use separate models for input/output",
                "Audit all serialization code"
            ],
            "example": "UserResponse should exclude password field, use Pydantic's exclude"
        }
    },
    {
        "instruction": "API experiencing high latency",
        "error_type": "performance",
        "response": {
            "status": "optimize",
            "diagnosis": [
                "Add timing middleware to identify slow endpoints",
                "Check database query performance (EXPLAIN)",
                "Profile code for CPU bottlenecks",
                "Check N+1 query problems",
                "Review external API call times"
            ],
            "solutions": [
                "Add database indexes",
                "Implement caching (Redis)",
                "Use connection pooling",
                "Paginate large responses",
                "Make external calls async",
                "Use background jobs for slow operations"
            ]
        }
    },
    {
        "instruction": "API CORS error from browser",
        "error_type": "cors_misconfiguration",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Verify Access-Control-Allow-Origin header is set",
                "Check OPTIONS preflight handling",
                "Ensure allowed methods include request method",
                "Verify allowed headers include custom headers"
            ],
            "common_fixes": [
                "Add CORS middleware to API",
                "Configure specific allowed origins",
                "Handle OPTIONS method explicitly",
                "Allow credentials if using cookies"
            ],
            "note": "Wildcard (*) not allowed with credentials"
        }
    },
    {
        "instruction": "API authentication token expired or invalid",
        "error_type": "auth_error",
        "response": {
            "status": "handle_gracefully",
            "proper_response": {
                "status_code": 401,
                "body": {"error": "token_expired", "message": "Access token has expired"},
                "header": "WWW-Authenticate: Bearer error='invalid_token'"
            },
            "client_handling": [
                "Attempt token refresh with refresh token",
                "If refresh fails, redirect to login",
                "Clear stored tokens on 401"
            ],
            "server_considerations": [
                "Check token signature",
                "Verify expiration (exp claim)",
                "Validate issuer and audience"
            ]
        }
    },
    {
        "instruction": "API returning incorrect data after update",
        "error_type": "caching_issue",
        "response": {
            "status": "troubleshoot",
            "common_causes": [
                "Stale cache not invalidated",
                "Read replica lag",
                "Client-side caching",
                "CDN caching old response"
            ],
            "solutions": [
                "Invalidate cache on write",
                "Add cache-busting headers for dynamic content",
                "Use Cache-Control: no-cache for sensitive endpoints",
                "Implement cache invalidation events"
            ]
        }
    },
    {
        "instruction": "API request body too large error",
        "error_type": "payload_size",
        "response": {
            "status": "configuration",
            "checks": [
                "Verify server body size limits",
                "Check reverse proxy limits (nginx client_max_body_size)",
                "Review API gateway payload limits"
            ],
            "solutions": [
                "Increase limits if legitimate",
                "Implement chunked upload for large files",
                "Use presigned URLs for file uploads",
                "Validate Content-Length before processing"
            ],
            "proper_response": "413 Payload Too Large with max allowed size"
        }
    },
    {
        "instruction": "API database connection pool exhausted",
        "error_type": "resource_exhaustion",
        "response": {
            "status": "critical",
            "symptoms": [
                "Timeouts acquiring connection",
                "Increasing latency then failures",
                "Application eventually unresponsive"
            ],
            "causes": [
                "Connection leaks (not returning connections)",
                "Long-running queries holding connections",
                "Pool size too small for load",
                "Sudden traffic spike"
            ],
            "solutions": [
                "Fix connection leaks (ensure close/release)",
                "Increase pool size appropriately",
                "Add connection timeout",
                "Implement circuit breaker",
                "Use read replicas for read-heavy workloads"
            ]
        }
    },
    {
        "instruction": "API returning different results for same request",
        "error_type": "inconsistency",
        "response": {
            "status": "investigate",
            "possible_causes": [
                "Multiple server instances with different data",
                "Race conditions in concurrent requests",
                "Caching at different levels returning different versions",
                "Time-sensitive data (timezone issues)"
            ],
            "debugging_steps": [
                "Check which server handled request (add server ID to response)",
                "Verify all instances have same code version",
                "Check for eventual consistency in database",
                "Review cache synchronization"
            ]
        }
    },
    {
        "instruction": "API rate limit hit unexpectedly",
        "error_type": "rate_limiting",
        "response": {
            "status": "analyze",
            "client_side_fixes": [
                "Implement exponential backoff",
                "Respect Retry-After header",
                "Cache API responses client-side",
                "Batch requests where possible"
            ],
            "server_side_considerations": [
                "Review rate limit configuration",
                "Check if limits are per-user or per-IP",
                "Ensure distributed rate limiting works correctly",
                "Consider separate limits for different endpoint tiers"
            ],
            "proper_response": "429 with X-RateLimit headers and Retry-After"
        }
    },
    {
        "instruction": "API breaking change affecting clients",
        "error_type": "compatibility",
        "response": {
            "status": "rollback_and_plan",
            "immediate_actions": [
                "Rollback to previous version",
                "Notify affected clients",
                "Review what changed"
            ],
            "proper_approach": [
                "Version the API when breaking changes needed",
                "Deprecate with sunset period",
                "Maintain old version during transition",
                "Contract testing prevents this"
            ],
            "prevention": "Use semantic versioning, deprecation headers, maintain changelog"
        }
    },
    {
        "instruction": "API webhook delivery failing",
        "error_type": "webhook_failure",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Verify target URL is accessible",
                "Check for firewall/WAF blocking requests",
                "Verify SSL certificate is valid",
                "Check webhook signature validation"
            ],
            "best_practices": [
                "Implement retry with exponential backoff",
                "Log all delivery attempts",
                "Provide webhook logs to users",
                "Dead letter queue for persistent failures",
                "Allow manual retry from dashboard"
            ]
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_command",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_code_response(language: str, code: str, explanation: str) -> str:
    return json.dumps({
        "action": "provide_code",
        "language": language,
        "code": code,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_command_response(task["command"], task["explanation"])
    } for task in API_TASKS]

def generate_code_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": ex["instruction"],
        "response": format_code_response(ex["language"], ex["code"], ex["explanation"])
    } for ex in CODE_EXAMPLES]

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    all_concepts = BASIC_CONCEPTS + ADVANCED_CONCEPTS
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in all_concepts]

def generate_error_examples() -> List[Dict]:
    examples = []
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    return examples

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating API Development Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} tool examples")
    
    code_examples = generate_code_examples()
    all_examples.extend(code_examples)
    print(f"Generated {len(code_examples)} code examples")
    
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"Generated {len(planning_examples)} planning examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "api_development.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
