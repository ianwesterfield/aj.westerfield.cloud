#!/usr/bin/env python3
"""
Security Training Data Generator
Target: ~200 examples for security best practices, authentication, vulnerability prevention
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for security and secure development.
You help with authentication, authorization, vulnerability prevention, and security best practices."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

SECURITY_TASKS = [
    {
        "instruction": "Scan code for security vulnerabilities",
        "command": "bandit -r src/ -f json -o security-report.json",
        "explanation": "Bandit scans Python code for common security issues"
    },
    {
        "instruction": "Check npm packages for known vulnerabilities",
        "command": "npm audit",
        "explanation": "Audits dependencies against known vulnerability database"
    },
    {
        "instruction": "Fix npm security vulnerabilities",
        "command": "npm audit fix --force",
        "explanation": "Automatically fixes vulnerabilities, may include breaking changes"
    },
    {
        "instruction": "Scan Docker image for vulnerabilities",
        "command": "trivy image myapp:latest --severity HIGH,CRITICAL",
        "explanation": "Scans container image for high and critical CVEs"
    },
    {
        "instruction": "Generate secure random password",
        "command": "openssl rand -base64 32",
        "explanation": "Generates cryptographically secure 32-byte password"
    },
    {
        "instruction": "Generate SSH key pair",
        "command": "ssh-keygen -t ed25519 -C \"your@email.com\" -f ~/.ssh/id_ed25519",
        "explanation": "Creates Ed25519 key pair (preferred over RSA)"
    },
    {
        "instruction": "Check SSL certificate expiry",
        "command": "openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -dates",
        "explanation": "Shows certificate validity dates"
    },
    {
        "instruction": "Scan for secrets in git history",
        "command": "gitleaks detect --source . --verbose",
        "explanation": "Finds leaked secrets in repository history"
    },
    {
        "instruction": "Run OWASP dependency check",
        "command": "dependency-check --scan . --format HTML --out reports/",
        "explanation": "Scans all dependencies for known CVEs"
    },
    {
        "instruction": "Hash password with bcrypt",
        "command": "python -c \"import bcrypt; print(bcrypt.hashpw(b'password', bcrypt.gensalt()).decode())\"",
        "explanation": "Properly hashes password for storage"
    },
    {
        "instruction": "Generate self-signed SSL certificate",
        "command": "openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'",
        "explanation": "Creates self-signed cert for development HTTPS"
    },
    {
        "instruction": "Create certificate signing request",
        "command": "openssl req -new -newkey rsa:4096 -keyout private.key -out request.csr",
        "explanation": "Generates CSR for CA-signed certificate"
    },
    {
        "instruction": "Verify SSL certificate chain",
        "command": "openssl verify -CAfile ca-bundle.crt certificate.crt",
        "explanation": "Validates certificate against CA bundle"
    },
    {
        "instruction": "Scan Python dependencies for vulnerabilities",
        "command": "pip-audit --requirement requirements.txt --format json",
        "explanation": "Checks Python packages against PyPI vulnerability database"
    },
    {
        "instruction": "Run safety check on Python dependencies",
        "command": "safety check --full-report",
        "explanation": "Scans installed packages for known security issues"
    },
    {
        "instruction": "Scan filesystem for SUID/SGID binaries",
        "command": "find / -type f \\( -perm -4000 -o -perm -2000 \\) -exec ls -la {} \\; 2>/dev/null",
        "explanation": "Finds potentially dangerous privilege escalation binaries"
    },
    {
        "instruction": "Check for world-writable files",
        "command": "find / -type f -perm -0002 -not -path '/proc/*' 2>/dev/null",
        "explanation": "Finds files anyone can write to (security risk)"
    },
    {
        "instruction": "List open ports and listening services",
        "command": "netstat -tulpn",
        "explanation": "Shows all listening TCP/UDP ports with process info"
    },
    {
        "instruction": "Scan host for open ports",
        "command": "nmap -sV -sC -p- target.com",
        "explanation": "Full port scan with version detection and scripts"
    },
    {
        "instruction": "Test SSL/TLS configuration",
        "command": "testssl.sh --severity HIGH example.com:443",
        "explanation": "Comprehensive SSL/TLS security testing"
    },
    {
        "instruction": "Generate random AES key",
        "command": "openssl rand -hex 32",
        "explanation": "Generates 256-bit AES key in hex format"
    },
    {
        "instruction": "Encrypt file with AES",
        "command": "openssl enc -aes-256-cbc -salt -pbkdf2 -in plaintext.txt -out encrypted.enc",
        "explanation": "Encrypts file using AES-256 with password"
    },
    {
        "instruction": "Decrypt AES encrypted file",
        "command": "openssl enc -d -aes-256-cbc -pbkdf2 -in encrypted.enc -out decrypted.txt",
        "explanation": "Decrypts AES-256 encrypted file"
    },
    {
        "instruction": "Calculate file hash",
        "command": "sha256sum file.txt",
        "explanation": "Generates SHA-256 checksum for file integrity"
    },
    {
        "instruction": "Sign file with GPG",
        "command": "gpg --sign --armor file.txt",
        "explanation": "Creates ASCII-armored GPG signature"
    },
    {
        "instruction": "Verify GPG signature",
        "command": "gpg --verify file.txt.asc file.txt",
        "explanation": "Verifies file against GPG signature"
    },
    {
        "instruction": "Import GPG public key",
        "command": "gpg --import public_key.asc",
        "explanation": "Imports public key to keyring"
    },
    {
        "instruction": "Check file for malware with ClamAV",
        "command": "clamscan -r /path/to/scan --infected",
        "explanation": "Recursively scans directory for malware"
    },
    {
        "instruction": "Run SQL injection scan with sqlmap",
        "command": "sqlmap -u 'http://target.com/page?id=1' --batch --risk=3 --level=5",
        "explanation": "Tests URL parameter for SQL injection vulnerabilities"
    },
    {
        "instruction": "Scan web application with Nikto",
        "command": "nikto -h https://target.com -o nikto_report.html -Format htm",
        "explanation": "Web vulnerability scanner for common issues"
    },
    {
        "instruction": "Run OWASP ZAP spider scan",
        "command": "zap-cli quick-scan -s all -r https://target.com",
        "explanation": "Automated security scan of web application"
    },
    {
        "instruction": "Check for SSL heartbleed vulnerability",
        "command": "nmap -p 443 --script ssl-heartbleed target.com",
        "explanation": "Tests server for heartbleed CVE"
    },
    {
        "instruction": "Audit Linux user accounts",
        "command": "cat /etc/passwd | awk -F: '$3 == 0 {print $1}'",
        "explanation": "Lists accounts with root privileges (UID 0)"
    },
    {
        "instruction": "Check sudo configuration",
        "command": "sudo visudo -c && cat /etc/sudoers.d/*",
        "explanation": "Validates sudoers syntax and shows rules"
    },
    {
        "instruction": "List all cron jobs",
        "command": "for user in $(cut -f1 -d: /etc/passwd); do crontab -u $user -l 2>/dev/null; done",
        "explanation": "Shows all user cron jobs for security audit"
    },
    {
        "instruction": "Check SSH configuration security",
        "command": "sshd -T | grep -E '(permitrootlogin|passwordauthentication|pubkeyauthentication)'",
        "explanation": "Shows key SSH security settings"
    },
    {
        "instruction": "Generate TOTP secret",
        "command": "python -c \"import pyotp; print(pyotp.random_base32())\"",
        "explanation": "Generates secret for two-factor authentication"
    },
    {
        "instruction": "Check JWT token",
        "command": "echo 'TOKEN' | cut -d. -f2 | base64 -d 2>/dev/null | jq",
        "explanation": "Decodes JWT payload (never verify like this!)"
    },
    {
        "instruction": "Scan Kubernetes for security issues",
        "command": "kubesec scan deployment.yaml",
        "explanation": "Security risk analysis for K8s manifests"
    },
    {
        "instruction": "Run Kubernetes security benchmark",
        "command": "kube-bench run --targets node,master",
        "explanation": "CIS benchmark for Kubernetes security"
    },
    {
        "instruction": "Check Docker security best practices",
        "command": "docker-bench-security",
        "explanation": "Runs CIS Docker Benchmark checks"
    },
    {
        "instruction": "Scan Terraform for security issues",
        "command": "tfsec .",
        "explanation": "Static analysis for Terraform security"
    },
    {
        "instruction": "Scan CloudFormation templates",
        "command": "cfn-nag_scan --input-path template.yaml",
        "explanation": "Checks AWS CloudFormation for security issues"
    },
    {
        "instruction": "Run Snyk container scan",
        "command": "snyk container test myimage:latest --severity-threshold=high",
        "explanation": "Scans container image with Snyk vulnerability database"
    },
    {
        "instruction": "Check for exposed AWS credentials",
        "command": "trufflehog git file://. --only-verified",
        "explanation": "Scans repo for verified exposed credentials"
    },
    {
        "instruction": "Generate secure .env file",
        "command": "echo \"SECRET_KEY=$(openssl rand -base64 32)\" >> .env",
        "explanation": "Creates environment variable with secure random value"
    },
    {
        "instruction": "Check CORS configuration",
        "command": "curl -H 'Origin: http://evil.com' -I https://api.example.com",
        "explanation": "Tests if CORS allows arbitrary origins"
    },
    {
        "instruction": "Test for clickjacking vulnerability",
        "command": "curl -I https://example.com | grep -i 'x-frame-options\\|content-security-policy'",
        "explanation": "Checks for frame protection headers"
    },
    {
        "instruction": "Verify HTTP security headers",
        "command": "curl -I https://example.com | grep -iE '(strict-transport|content-security|x-content-type|x-xss)'",
        "explanation": "Checks essential security headers"
    },
    {
        "instruction": "Run Lynis security audit",
        "command": "lynis audit system --quick",
        "explanation": "Comprehensive Linux security auditing tool"
    },
    {
        "instruction": "Check PAM configuration",
        "command": "cat /etc/pam.d/common-auth",
        "explanation": "Reviews authentication configuration"
    },
    {
        "instruction": "List all setcap binaries",
        "command": "getcap -r / 2>/dev/null",
        "explanation": "Finds binaries with capabilities (privilege escalation vectors)"
    },
    {
        "instruction": "Check AppArmor status",
        "command": "aa-status",
        "explanation": "Shows AppArmor profile enforcement status"
    },
    {
        "instruction": "List SELinux booleans",
        "command": "getsebool -a | grep -E '(httpd|ssh)'",
        "explanation": "Shows SELinux security policy settings"
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "instruction": "Implement secure password hashing in Python",
        "language": "python",
        "code": """import bcrypt
import secrets

def hash_password(password: str) -> str:
    \"\"\"Hash password using bcrypt with automatic salt.\"\"\"
    salt = bcrypt.gensalt(rounds=12)  # Increase rounds for more security
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    \"\"\"Verify password against stored hash.\"\"\"
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )

def generate_secure_token(length: int = 32) -> str:
    \"\"\"Generate cryptographically secure token.\"\"\"
    return secrets.token_urlsafe(length)

# Usage
hashed = hash_password("user_password")
is_valid = verify_password("user_password", hashed)
reset_token = generate_secure_token()""",
        "explanation": "bcrypt automatically handles salting, use secrets for tokens"
    },
    {
        "instruction": "Implement JWT authentication in FastAPI",
        "language": "python",
        "code": """from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = "your-secret-key"  # Load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    username: Optional[str] = None
    exp: Optional[datetime] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # Check expiration
        exp = payload.get("exp")
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception""",
        "explanation": "JWT with expiration, proper error handling, OAuth2 pattern"
    },
    {
        "instruction": "Prevent SQL injection with parameterized queries",
        "language": "python",
        "code": """import sqlite3
from typing import Optional, List

# WRONG - SQL Injection vulnerable
def get_user_vulnerable(username: str):
    conn = sqlite3.connect('db.sqlite')
    # NEVER do this - user input directly in query
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return conn.execute(query).fetchone()

# CORRECT - Parameterized query
def get_user_safe(username: str) -> Optional[dict]:
    conn = sqlite3.connect('db.sqlite')
    # Parameters are properly escaped
    query = "SELECT * FROM users WHERE username = ?"
    result = conn.execute(query, (username,)).fetchone()
    return dict(result) if result else None

# CORRECT - Using ORM (SQLAlchemy)
from sqlalchemy.orm import Session
from models import User

def get_user_orm(db: Session, username: str) -> Optional[User]:
    # ORM handles parameterization automatically
    return db.query(User).filter(User.username == username).first()

# For complex queries, use named parameters
def search_users(db: Session, filters: dict) -> List[User]:
    query = db.query(User)
    if filters.get('name'):
        query = query.filter(User.name.ilike(f"%{filters['name']}%"))
    if filters.get('role'):
        query = query.filter(User.role == filters['role'])
    return query.all()""",
        "explanation": "Always use parameterized queries or ORM, never string concatenation"
    },
    {
        "instruction": "Implement CSRF protection in web application",
        "language": "python",
        "code": """import secrets
from fastapi import Request, HTTPException, Depends
from fastapi.responses import HTMLResponse

def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)

async def get_csrf_token(request: Request) -> str:
    \"\"\"Get or create CSRF token in session.\"\"\"
    if 'csrf_token' not in request.session:
        request.session['csrf_token'] = generate_csrf_token()
    return request.session['csrf_token']

async def verify_csrf_token(request: Request):
    \"\"\"Verify CSRF token on state-changing requests.\"\"\"
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return
    
    session_token = request.session.get('csrf_token')
    
    # Check header first (for AJAX), then form data
    request_token = request.headers.get('X-CSRF-Token')
    if not request_token:
        form = await request.form()
        request_token = form.get('csrf_token')
    
    if not session_token or not secrets.compare_digest(session_token, request_token or ''):
        raise HTTPException(status_code=403, detail="CSRF token validation failed")

# In your form template:
# <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

# For AJAX requests, include header:
# fetch('/api/data', {
#     method: 'POST',
#     headers: { 'X-CSRF-Token': csrfToken },
#     body: JSON.stringify(data)
# })""",
        "explanation": "CSRF tokens prevent cross-site request forgery attacks"
    },
    {
        "instruction": "Sanitize user input to prevent XSS",
        "language": "typescript",
        "code": """import DOMPurify from 'dompurify';

// WRONG - XSS vulnerable
function renderUserContent_VULNERABLE(content: string): void {
    // Never do this - allows script injection
    document.getElementById('output')!.innerHTML = content;
}

// CORRECT - Sanitize HTML
function renderUserContent(content: string): void {
    const clean = DOMPurify.sanitize(content, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
        ALLOWED_ATTR: ['href', 'title'],
        ALLOW_DATA_ATTR: false
    });
    document.getElementById('output')!.innerHTML = clean;
}

// CORRECT - Use textContent for plain text
function renderPlainText(content: string): void {
    // textContent is automatically escaped
    document.getElementById('output')!.textContent = content;
}

// CORRECT - Template literal escaping for dynamic HTML
function escapeHtml(str: string): string {
    const escapeMap: Record<string, string> = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return str.replace(/[&<>"']/g, char => escapeMap[char]);
}

// React handles this automatically with JSX
// Vue uses v-text or {{ }} which escapes by default
// Use v-html or dangerouslySetInnerHTML only with sanitized content""",
        "explanation": "Always sanitize user content, use textContent for plain text"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Implement OAuth 2.0 authentication flow",
        "steps": [
            "Register application with OAuth provider (Google, GitHub, etc.)",
            "Configure redirect URI (callback URL)",
            "Create login endpoint that redirects to provider",
            "Include scope, state (CSRF), and redirect_uri in auth URL",
            "Implement callback endpoint to receive authorization code",
            "Verify state parameter matches session",
            "Exchange authorization code for access token",
            "Store tokens securely (encrypted in database or secure session)",
            "Use access token to fetch user profile",
            "Create or update local user account",
            "Generate session or JWT for your application",
            "Implement token refresh flow",
            "Add logout endpoint (revoke tokens)",
            "Handle error cases (denied access, expired tokens)"
        ]
    },
    {
        "instruction": "Perform security audit of web application",
        "steps": [
            "Review authentication flow (password policies, MFA, session management)",
            "Check authorization (role-based access, resource ownership)",
            "Scan for OWASP Top 10 vulnerabilities",
            "Test for SQL injection on all inputs",
            "Test for XSS (stored, reflected, DOM-based)",
            "Check CSRF protection on state-changing operations",
            "Review API authentication (tokens, rate limiting)",
            "Check for sensitive data exposure (logs, errors, responses)",
            "Verify TLS configuration (cipher suites, certificate)",
            "Review dependencies for known vulnerabilities",
            "Check security headers (CSP, HSTS, X-Frame-Options)",
            "Test file upload handling (type validation, storage)",
            "Review error handling (no stack traces in production)",
            "Check secrets management (no hardcoded secrets)",
            "Document findings and remediation plan"
        ]
    },
    {
        "instruction": "Implement secure file upload functionality",
        "steps": [
            "Define allowed file types (whitelist, not blacklist)",
            "Validate file extension AND content type (magic bytes)",
            "Set maximum file size limit",
            "Generate new random filename (don't use user input)",
            "Store files outside web root",
            "Scan uploaded files for malware",
            "Use separate domain/CDN for serving user content",
            "Set proper Content-Type and Content-Disposition headers",
            "Implement rate limiting on uploads",
            "Log all upload attempts with user and file metadata",
            "Implement cleanup for incomplete/orphaned uploads",
            "Consider virus scanning integration",
            "Test with malicious files (polyglots, oversized)"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is the OWASP Top 10?",
        "answer": "OWASP Top 10 is a list of most critical web application security risks. Current list: Broken Access Control (#1), Cryptographic Failures, Injection (SQL, XSS), Insecure Design, Security Misconfiguration, Vulnerable Components, Authentication Failures, Software Integrity Failures, Logging Failures, SSRF. Updated periodically based on real-world data. Provides testing guides and remediation. Not exhaustive but essential baseline. Use OWASP resources: ASVS, Testing Guide, Cheat Sheets."
    },
    {
        "question": "What is the difference between authentication and authorization?",
        "answer": "Authentication (AuthN): verifies WHO you are - username/password, MFA, biometrics. Establishes identity. Authorization (AuthZ): determines WHAT you can do - permissions, roles, policies. Controls access. Example: login proves you're 'alice' (authn), checking if alice can delete posts (authz). JWT can contain both: identity claims (authn) and role claims (authz). Always do both: authenticate first, then authorize every action."
    },
    {
        "question": "What is HTTPS and why is it important?",
        "answer": "HTTPS = HTTP + TLS encryption. Provides: confidentiality (data encrypted in transit), integrity (data not modified), authentication (server verified via certificate). Without it: passwords visible to network sniffers, data can be modified by ISPs/attackers, no server verification. Always use HTTPS in production. Get free certificates from Let's Encrypt. Configure HSTS to enforce HTTPS. Modern browsers mark HTTP as 'not secure'."
    },
    {
        "question": "What is hashing vs encryption?",
        "answer": "Hashing: one-way function, cannot reverse to get original. Used for passwords, integrity checks. Same input = same hash. Use bcrypt/argon2 for passwords (slow by design). MD5/SHA1 broken for security. Encryption: two-way, can decrypt with key. Symmetric (AES): same key encrypts/decrypts. Asymmetric (RSA): public key encrypts, private decrypts. Use encryption for data you need to read later. Never encrypt passwords, always hash them."
    },
    {
        "question": "What is SQL injection?",
        "answer": "SQL injection: attacker inserts SQL code into inputs that get executed. Example: login bypass with ' OR '1'='1 in password field. Impact: data theft, modification, deletion, full database compromise. Prevention: parameterized queries/prepared statements (never string concatenation), input validation, least privilege database users, WAF. ORM helps but doesn't guarantee safety. Test with tools like sqlmap. One of oldest but still common vulnerabilities."
    },
    {
        "question": "What is XSS (Cross-Site Scripting)?",
        "answer": "XSS: attacker injects JavaScript that executes in victim's browser. Types: Reflected (in URL), Stored (in database), DOM-based (client-side). Impact: session hijacking, defacement, malware, phishing. Prevention: output encoding (escape HTML), Content-Security-Policy header, HTTPOnly cookies, input validation. React/Angular auto-escape by default. Avoid innerHTML, eval, document.write. XSS enables full account takeover."
    },
    {
        "question": "What is CSRF (Cross-Site Request Forgery)?",
        "answer": "CSRF: attacker tricks user into performing unwanted action on site where they're logged in. Example: hidden form on malicious site submits money transfer. Prevention: CSRF tokens (unique per session/request), SameSite cookie attribute, verify Origin/Referer headers, require re-authentication for sensitive actions. Modern frameworks include CSRF protection. Not applicable to APIs with token auth (no cookies)."
    },
    {
        "question": "What is Multi-Factor Authentication (MFA)?",
        "answer": "MFA requires multiple authentication factors. Categories: something you know (password), something you have (phone, key), something you are (biometrics). Examples: password + OTP, password + hardware key (FIDO2/WebAuthn). Greatly reduces account compromise risk. SMS codes less secure than authenticator apps or hardware keys. Implement for: admin accounts, sensitive operations, high-value accounts. Consider passwordless with strong second factor."
    },
    {
        "question": "What is the principle of least privilege?",
        "answer": "Grant minimum permissions required for a task. Apply to: user accounts, service accounts, API keys, database users, file permissions. Benefits: limits blast radius of compromise, prevents accidents, enables auditing. Implementation: role-based access control (RBAC), attribute-based access control (ABAC), just-in-time access. Review permissions regularly. Default deny, explicit allow. Don't use root/admin for routine tasks."
    },
    {
        "question": "What is input validation?",
        "answer": "Input validation: verify user input meets expected format before processing. Types: whitelist (allow known good), blacklist (block known bad - less secure). Validate: type, length, range, format, encoding. Server-side validation mandatory (client-side bypassed easily). Use schema validation (JSON Schema, Zod). Don't trust any input - headers, cookies, files, API data. Validation != sanitization (transformation for safe use)."
    },
    {
        "question": "What are security headers?",
        "answer": "HTTP headers that enable browser security features. Essential: Content-Security-Policy (XSS prevention), X-Content-Type-Options: nosniff, X-Frame-Options/frame-ancestors (clickjacking), Strict-Transport-Security (HTTPS enforcement). Others: Referrer-Policy, Permissions-Policy, X-XSS-Protection (legacy). Configure in web server or application. Test with securityheaders.com. Headers are defense in depth - not sole protection."
    },
    {
        "question": "What is secure password storage?",
        "answer": "Passwords must be hashed, never stored plain or encrypted. Use: bcrypt, Argon2 (preferred), scrypt - purpose-built, intentionally slow. Include unique salt (automatic with bcrypt). Factors: memory cost, iterations, parallelism. Verify: hash input and compare hashes, never decrypt. Pepper (secret key) adds layer. Libraries handle complexity - don't implement yourself. Allow long passwords, don't limit character types."
    },
    {
        "question": "What is session management?",
        "answer": "Session tracks authenticated users. Secure sessions: generate cryptographically random session IDs, regenerate ID on login (prevents fixation), expire after inactivity, absolute timeout. Cookie security: HttpOnly (no JavaScript access), Secure (HTTPS only), SameSite (CSRF protection), appropriate domain/path. Server-side sessions vs JWTs: tradeoffs in scalability vs revocation. Implement logout properly - invalidate server-side."
    },
    {
        "question": "What is defense in depth?",
        "answer": "Multiple security layers so single failure doesn't compromise system. Layers: network (firewall, segmentation), host (OS hardening, antivirus), application (input validation, authentication), data (encryption, access control). Example: WAF + CSP + input validation + parameterized queries. No single control is perfect. Assumes breach will occur - limit impact. Balance security with usability and performance."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "What is a Content Security Policy (CSP)?",
        "answer": "CSP is HTTP header that controls what resources page can load. Prevents XSS by blocking inline scripts, restricting script sources. Example: Content-Security-Policy: default-src 'self'; script-src 'self' cdn.example.com; img-src *. Directives: default-src, script-src, style-src, img-src, connect-src, frame-src. Values: 'self', 'none', domain, 'unsafe-inline' (avoid), 'nonce-xxx'. Start with report-only mode to test. Use report-uri to collect violations. Essential defense-in-depth for XSS."
    },
    {
        "question": "How do you securely store API keys and secrets?",
        "answer": "Never in code or git. Local dev: .env file (in .gitignore), direnv. CI/CD: platform secrets (GitHub Actions secrets, GitLab CI vars). Production: secret managers (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault). Kubernetes: external-secrets operator, sealed-secrets. Runtime injection via environment variables or mounted files. Rotate regularly, different secrets per environment. Audit access, monitor for leaks. Pre-commit hooks to scan for secrets."
    },
    {
        "question": "What is Zero Trust security?",
        "answer": "Zero Trust assumes no implicit trust - verify everything. Principles: never trust, always verify; least privilege access; assume breach. Implementation: strong identity verification (MFA), device health checks, micro-segmentation, encrypt everything, continuous monitoring. Network location doesn't grant trust. Every request authenticated and authorized. Tools: identity providers, conditional access, SASE, microsegmentation. Contrast with perimeter security (castle-and-moat). Journey not destination - implement gradually."
    },
    {
        "question": "How do you prevent timing attacks?",
        "answer": "Timing attacks exploit execution time differences to leak information. Example: comparing strings char by char - wrong char fails faster than wrong position. Prevention: constant-time comparison (secrets.compare_digest in Python, crypto.timingSafeEqual in Node). Applies to: password/token comparison, cryptographic operations. Also: avoid early returns based on secret data, use constant-time crypto libraries. Difficult to exploit remotely but critical for high-security applications. Test with timing analysis tools."
    },
    {
        "question": "What is SSRF (Server-Side Request Forgery)?",
        "answer": "SSRF: attacker makes server send requests to unintended destinations. Impact: access internal services, cloud metadata endpoints, port scanning. Example: fetch(userProvidedUrl) with URL http://169.254.169.254 (AWS metadata). Prevention: whitelist allowed domains/IPs, don't allow internal IP ranges, disable redirects, use separate network for fetching. Cloud: use IMDSv2, restrict metadata access. Common in webhook handlers, URL preview features."
    },
    {
        "question": "What is JWT security?",
        "answer": "JWT (JSON Web Token) for stateless authentication. Signed (JWS) not encrypted by default. Security: use strong secret/RSA keys, validate signature, check exp/iat/nbf claims, verify issuer and audience. Vulnerabilities: algorithm confusion (alg:none attack), key confusion (RS256→HS256), exposed in URLs. Best practices: short expiry, refresh tokens, don't store sensitive data in payload, use HttpOnly cookies or memory (not localStorage). Consider sessions for sensitive apps."
    },
    {
        "question": "What is CORS and why does it matter?",
        "answer": "CORS (Cross-Origin Resource Sharing) controls which domains can access API. Browser enforces Same-Origin Policy; CORS relaxes it. Headers: Access-Control-Allow-Origin, Allow-Methods, Allow-Headers, Allow-Credentials. Preflight OPTIONS request for complex requests. Misconfiguration: Allow-Origin: * with credentials is blocked; reflecting Origin header without validation is dangerous. Configure: specific allowed origins, not wildcards for authenticated APIs. Not security for server-to-server."
    },
    {
        "question": "How do you implement rate limiting?",
        "answer": "Rate limiting prevents abuse: brute force, DoS, scraping. Strategies: fixed window, sliding window, token bucket, leaky bucket. Identify by: IP, user, API key. Apply at: reverse proxy (nginx), application, API gateway. Headers: X-RateLimit-Limit, Remaining, Reset. Response: 429 Too Many Requests with Retry-After. Consider: distributed rate limiting (Redis), different limits per endpoint, authenticated vs anonymous. Captcha as additional protection."
    },
    {
        "question": "What is security logging and monitoring?",
        "answer": "Log security-relevant events: authentication (success/failure), authorization failures, input validation failures, errors. Include: timestamp, user, IP, action, resource, outcome. Don't log: passwords, tokens, PII (or mask it). Centralize logs (ELK, Splunk, cloud logging). Set up alerts: failed logins, privilege escalation, suspicious patterns. Retain logs per compliance requirements. Log integrity: append-only, signed. Part of incident response capability."
    },
    {
        "question": "What is secure deserialization?",
        "answer": "Deserialization: converting serialized data back to objects. Insecure deserialization allows code execution. Vulnerable: Java serialization, Python pickle, PHP unserialize. Prevention: never deserialize untrusted data, use safe formats (JSON, Protocol Buffers), validate before deserializing, integrity checks (HMAC). If unavoidable: sandbox, allowlist classes, monitor. Led to major breaches. Avoid serializing complex objects from user input."
    },
    {
        "question": "How do you secure file uploads?",
        "answer": "File uploads are high-risk. Validate: file type by content (magic bytes), not just extension; file size limits; filename sanitization. Store: outside webroot, random names, no execute permissions. Serve: via handler that sets Content-Disposition: attachment; Content-Type: application/octet-stream. Scan for malware. Consider: separate domain for user content, presigned URLs to storage. Never trust client-provided content type."
    },
    {
        "question": "What is security in CI/CD pipelines?",
        "answer": "CI/CD security: SAST (static analysis in build), DAST (dynamic testing), dependency scanning, secret scanning, container image scanning, IaC security (Terraform, k8s). Tools: Snyk, Trivy, SonarQube, Checkov. Fail builds on critical issues. Protect secrets: never echo, use platform secrets. Signed commits, protected branches, required reviews. Supply chain: verify dependencies, lock versions, use private registries. Audit pipeline access."
    },
    {
        "question": "What is cryptographic key management?",
        "answer": "Key management: generation, storage, distribution, rotation, revocation. Generate: cryptographically secure random generators. Store: HSM, cloud KMS, never in code. Distribute: secure channels, per-environment. Rotate: regular schedule, immediately on compromise. Revoke: CRL, OCSP for certificates. Separation: different keys for different purposes. Backup securely for recovery. Key escrow considerations. Document procedures. Most crypto failures are key management, not algorithms."
    },
    {
        "question": "What is penetration testing?",
        "answer": "Pen testing: authorized simulated attacks to find vulnerabilities. Types: black box (no info), white box (full access), gray box (partial). Scope: network, web app, social engineering, physical. Process: reconnaissance, scanning, exploitation, post-exploitation, reporting. Frequency: annually or after major changes. Complement with: bug bounty, automated scanning, code review. Choose reputable testers, define scope clearly. Fix findings by risk level."
    },
    # === EXPANDED SECURITY CONCEPTS ===
    {
        "question": "What is OAuth 2.0 and OpenID Connect?",
        "answer": "OAuth 2.0: authorization framework for delegated access. Grants access tokens without sharing passwords. Flows: Authorization Code (web apps), PKCE (mobile/SPA), Client Credentials (server-to-server), Device Code (IoT). OpenID Connect (OIDC): authentication layer on OAuth 2.0, adds ID token with user identity. Use OAuth for authorization (what can you do), OIDC for authentication (who are you). Validate: issuer, audience, expiry, signature. Secure: use PKCE always, short-lived tokens, secure token storage."
    },
    {
        "question": "What is certificate pinning and when should I use it?",
        "answer": "Certificate pinning: app validates server cert against known value, not just CA chain. Prevents MITM even with compromised CA or rogue cert. Types: pin certificate, pin public key (more flexible), pin CA (less secure). Use for: mobile apps, high-security APIs, financial apps. Challenges: cert rotation requires app update, pinning mistakes cause outages. Backup pins: include backup cert/key. HPKP deprecated for web. Mobile: implement in app code or networking library. Test pinning bypass during security audit."
    },
    {
        "question": "How do you implement secure session management?",
        "answer": "Session security: generate cryptographically random session IDs (128+ bits), regenerate on login (prevent fixation), set secure attributes: HttpOnly, Secure, SameSite=Strict. Storage: server-side (Redis, DB) preferred over client-side (JWT). Expire: short idle timeout, absolute timeout, invalidate on logout. Don't: expose in URL, trust client session data. Multi-device: track sessions, allow forced logout. Consider: sliding expiration, remember-me with separate long-lived token. Monitor: concurrent sessions, impossible travel."
    },
    {
        "question": "What is defense in depth for web applications?",
        "answer": "Defense in depth: multiple security layers, no single point of failure. Layers: network (firewall, WAF), infrastructure (patched OS, hardened config), application (input validation, output encoding, auth), data (encryption, access control, backups). Web app: validate input AND encode output AND use CSP AND use parameterized queries. Each layer assumes others might fail. Monitoring at each layer. Security controls: preventive (block), detective (alert), corrective (respond). Don't rely on single control."
    },
    {
        "question": "What is security headers and which should I use?",
        "answer": "Essential headers: Content-Security-Policy (XSS protection), Strict-Transport-Security (force HTTPS), X-Content-Type-Options: nosniff (MIME sniffing), X-Frame-Options: DENY or CSP frame-ancestors (clickjacking), Referrer-Policy (control referrer leakage), Permissions-Policy (disable features). Remove: Server, X-Powered-By headers (information leakage). Test with: securityheaders.com. Apply at: reverse proxy, application middleware. Start strict, relax if needed. Document exceptions."
    },
    {
        "question": "How do you secure WebSocket connections?",
        "answer": "WebSocket security: use WSS (TLS), validate Origin header, authenticate on connect (token in query/header), authorize each message. Vulnerabilities: CSWSH (Cross-Site WebSocket Hijacking) - check Origin strictly. Rate limit messages. Validate/sanitize all incoming data. Set message size limits. Reconnection: re-authenticate. Don't assume persistent connection means trusted. Close on auth failure. Log: connections, auth failures, suspicious activity. Same security mindset as HTTP endpoints."
    },
    {
        "question": "What is secure error handling?",
        "answer": "Error handling security: don't leak internal details (stack traces, SQL errors, file paths), use generic user messages with error IDs. Log: full error details server-side with correlation ID. Different modes: development (detailed), production (generic). Custom error pages: don't reveal framework. Catch-all handlers for unexpected errors. Don't: echo user input in errors (XSS), expose versions. Maintain usability: clear enough for user to understand problem without revealing internals."
    },
    {
        "question": "What is API security best practices?",
        "answer": "API security: authentication (API keys, OAuth, JWT), authorization (check permissions every endpoint), input validation (schema validation, type checking), rate limiting, versioning. Use HTTPS only. Validate Content-Type. Don't expose sensitive data (filter responses). Pagination to prevent data dumps. Audit logging. API gateway for cross-cutting concerns. Document: authentication methods, rate limits, error codes. Test: automated security scanning, manual review. Consider: API-specific WAF rules."
    },
    {
        "question": "How do you prevent business logic vulnerabilities?",
        "answer": "Business logic vulnerabilities: flaws in application flow, not traditional injection/XSS. Examples: bypassing payment, accessing other users' data, race conditions in inventory. Prevention: threat modeling, define business rules explicitly, server-side validation of all flows, don't trust client flow. Test: manually trace critical flows, look for skip/replay/reorder attacks. Logging: track business events, alert on anomalies. Code review: verify business rules enforced. Often missed by automated scanners. Think like attacker: what if user skips step?"
    },
    {
        "question": "What is secure coding for mobile apps?",
        "answer": "Mobile security: OWASP Mobile Top 10. Storage: avoid storing sensitive data, use secure storage (Keychain iOS, Keystore Android), encrypt databases. Network: HTTPS only, certificate pinning, don't trust WiFi. Auth: biometric with secure enclave backup, don't store passwords. Code: obfuscation, tamper detection, root/jailbreak detection. Binary: strip debug symbols, protect API keys. Testing: static analysis, dynamic analysis, penetration testing. Updates: enforce minimum versions, remote disable compromised versions."
    },
    {
        "question": "What is security compliance (SOC2, HIPAA, PCI-DSS)?",
        "answer": "SOC 2: service organization controls, trust principles (security, availability, confidentiality, processing integrity, privacy). Type I: point in time, Type II: over period. HIPAA: healthcare data (PHI) protection, technical safeguards (access control, encryption, audit). PCI-DSS: payment card data, 12 requirements (network security, encryption, access control). Compliance process: gap analysis, remediation, audit. Controls: technical + administrative + physical. Evidence: policies, logs, configurations. Ongoing: continuous monitoring, regular audits."
    },
    {
        "question": "How do you secure microservices communication?",
        "answer": "Microservices security: service-to-service authentication (mTLS, JWT), authorization (each service verifies permissions), network policies (restrict traffic paths). Service mesh: Istio, Linkerd handle mTLS automatically. API gateway: external traffic entry point. Internal: don't assume trust, validate all requests. Secrets: no hardcoding, inject at runtime. Observability: trace requests across services, correlate security events. Challenges: more attack surface, distributed security policies. Pattern: zero trust even internally."
    },
    {
        "question": "What is threat modeling?",
        "answer": "Threat modeling: systematic identification of threats and mitigations. When: design phase (shift left), major changes, security reviews. Frameworks: STRIDE (Spoofing, Tampering, Repudiation, Information disclosure, DoS, Elevation of privilege), DREAD (rating), PASTA (process for attack simulation). Process: diagram system, identify assets, enumerate threats, rate risk, plan mitigations. Who: developers, security team, architects together. Output: prioritized threat list with mitigations. Review: periodically, as system evolves. Tools: Microsoft Threat Modeling Tool, OWASP Threat Dragon."
    },
    {
        "question": "How do you handle security incidents?",
        "answer": "Incident response phases: preparation, identification, containment, eradication, recovery, lessons learned. Preparation: playbooks, communication plan, tools ready, team trained. Identification: monitoring, alerts, user reports. Containment: isolate affected systems, preserve evidence. Eradication: remove threat, patch vulnerability. Recovery: restore services, verify clean, monitor closely. Post-incident: root cause analysis, improve defenses, update playbooks. Communication: internal escalation, customer notification (GDPR 72h), legal/compliance. Practice: tabletop exercises, chaos engineering."
    },
    {
        "question": "What is supply chain security?",
        "answer": "Supply chain security: protecting against compromised dependencies. Risks: typosquatting, hijacked packages, malicious maintainers, compromised build systems. Prevention: lock dependency versions (lock files), verify integrity (checksums, signatures), use private registry/mirror, dependency scanning, SBOM (Software Bill of Materials). Monitor: new CVEs in dependencies, suspicious updates. Vendoring: copy dependencies into repo. Build: reproducible builds, signed artifacts. Review: audit critical dependencies. Recent attacks: SolarWinds, ua-parser-js. Trust but verify."
    },
]

# =============================================================================
# GUARDRAIL SCENARIOS
# =============================================================================

GUARDRAIL_SCENARIOS = [
    {
        "instruction": "Store password in plain text for quick testing",
        "response": {
            "status": "blocked",
            "reason": "Storing plain text passwords is never acceptable, even for testing",
            "risks": [
                "Passwords exposed if database compromised",
                "Users often reuse passwords across services",
                "Violates security best practices and regulations",
                "Test habits become production habits"
            ],
            "correct_approach": "Use bcrypt.hashpw() even in development - it's equally easy"
        }
    },
    {
        "instruction": "Disable SSL certificate verification for API call",
        "response": {
            "status": "warning",
            "reason": "Disabling SSL verification enables man-in-the-middle attacks",
            "when_acceptable": "Local development with self-signed certs only",
            "if_needed": "Use verify=False only in dev, add environment check",
            "better_solution": "Add self-signed cert to trust store, or use mkcert for local HTTPS",
            "code_example": "requests.get(url, verify=os.getenv('ENV') != 'development')"
        }
    },
    {
        "instruction": "Log all request bodies for debugging",
        "response": {
            "status": "warning",
            "reason": "Request bodies often contain sensitive data",
            "risks": [
                "Passwords logged in plain text",
                "PII/PHI exposed in logs",
                "Tokens and secrets visible",
                "Compliance violations (GDPR, HIPAA)"
            ],
            "safe_approach": [
                "Redact sensitive fields before logging",
                "Use structured logging with field filtering",
                "Log headers/metadata, not full body",
                "Short retention for debug logs"
            ]
        }
    },
    {
        "instruction": "Use MD5 to hash user passwords",
        "response": {
            "status": "blocked",
            "reason": "MD5 is cryptographically broken and unsuitable for passwords",
            "problems": [
                "Too fast - allows billions of guesses per second",
                "Rainbow table attacks readily available",
                "No salt by default",
                "Known collision vulnerabilities"
            ],
            "correct_approach": "Use bcrypt, Argon2, or scrypt - designed for password hashing",
            "code_example": "import bcrypt; hashed = bcrypt.hashpw(password, bcrypt.gensalt())"
        }
    },
    {
        "instruction": "Create admin account with password 'admin123'",
        "response": {
            "status": "blocked",
            "reason": "Weak default passwords are a critical security vulnerability",
            "risks": [
                "First thing attackers try",
                "In every password dictionary",
                "Often forgotten and left unchanged"
            ],
            "correct_approach": [
                "Generate random secure password: openssl rand -base64 24",
                "Require password change on first login",
                "Enforce password complexity requirements",
                "Consider passwordless admin setup"
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

def format_guardrail_response(data: dict) -> str:
    return json.dumps(data, indent=2)

def generate_tool_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_command_response(task["command"], task["explanation"])
    } for task in SECURITY_TASKS]

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

def generate_guardrail_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": scenario["instruction"],
        "response": format_guardrail_response(scenario["response"])
    } for scenario in GUARDRAIL_SCENARIOS]

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Security Training Data")
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
    
    guardrail_examples = generate_guardrail_examples()
    all_examples.extend(guardrail_examples)
    print(f"Generated {len(guardrail_examples)} guardrail examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "security.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
