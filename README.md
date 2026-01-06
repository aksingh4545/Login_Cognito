## Identity, Authentication, and Access Control Architecture

This project uses **Amazon Cognito as the identity backbone**, integrated with **AWS Lambda for custom authentication behavior**, **OIDC tokens for secure session management**, **Streamlit as a client**, and **CircleCI for controlled delivery**.  
This section explains **why these services are used**, **what role each plays**, and **how they work together at a protocol and system level**.

---

## Why Amazon Cognito Is Used

Authentication systems are difficult to build correctly because they require:

- Secure credential handling
- Token lifecycle management
- Protection against brute-force and replay attacks
- Standards-compliant identity tokens
- Integration with external identity providers
- Auditable authentication events

Amazon Cognito solves these problems as a **fully managed identity service**, allowing the application to delegate authentication complexity to AWS while retaining control over business-specific rules through Lambda.

Cognito is not just a login service. It acts as:

- An **identity provider (IdP)**
- A **token issuer**
- A **session authority**
- A **security enforcement layer**

---

## Role of Amazon Cognito in This System

At a high level, Cognito is responsible for:

| Responsibility | Description |
|---|---|
| User identity storage | Maintains user profiles and identifiers |
| Authentication orchestration | Controls authentication flow stages |
| Token issuance | Generates OIDC-compliant JWT tokens |
| Session lifecycle | Manages authentication sessions |
| Security enforcement | Integrates with adaptive risk controls |
| Extensibility | Allows Lambda-based customization |

The application **never authenticates users directly**.  
It asks Cognito to authenticate users and trusts Cognito-issued tokens.

---

## Amazon Cognito User Pools

### What a User Pool Is

An **Amazon Cognito User Pool** is a managed user directory that acts as an **OpenID Connect (OIDC) Identity Provider**.

It handles:

- User sign-up and sign-in
- User attributes (email, name, etc.)
- Authentication workflows
- Token generation

Once authentication succeeds, Cognito issues **JWT tokens** that downstream systems can trust without re-verifying credentials.

---

### Why User Pools Are Critical

User Pools allow you to:

- Avoid storing passwords or credentials in your application
- Rely on AWS-managed security controls
- Enforce consistent authentication rules across clients
- Integrate social and enterprise identity providers

In this project, the User Pool is configured for:

- **Custom Authentication**
- **Email as the username**
- **Passwordless OTP-based login**
- **No hosted UI dependency**

---

### User Pool Extensibility with Lambda

Cognito User Pools support **Lambda triggers**, which allow you to override or extend default behavior.

This enables:

- Custom OTP generation
- Dynamic validation logic
- Retry limits and lockouts
- Integration with external systems (DynamoDB, SES)

This project uses Lambda triggers to enforce **all authentication rules server-side**.

---

## OpenID Connect (OIDC)

### What OIDC Solves

OpenID Connect (OIDC) is an identity layer built on OAuth 2.0 that standardizes:

- How applications verify a user’s identity
- How identity information is exchanged securely
- How single sign-on (SSO) works across systems

OIDC ensures that authentication is **interoperable, secure, and auditable**.

---

### Tokens Issued by Cognito

After successful authentication, Cognito issues:

| Token | Purpose |
|---|---|
| ID Token | Proves the user’s identity |
| Access Token | Grants access to protected resources |
| Refresh Token | Allows session renewal without re-authentication |

These tokens are **JSON Web Tokens (JWTs)** signed by Cognito and verifiable by any trusted service.

---

### Token Contents and Claims

- **ID Token**
  - User identity information (email, username)
  - Authentication metadata
- **Access Token**
  - Authorization scopes
  - Group membership (`cognito:groups`)
  - API access permissions

Applications and APIs rely on token claims rather than user credentials.

---

## How Tokens Are Used in Practice

1. User authenticates via Cognito
2. Cognito validates authentication
3. Cognito issues tokens
4. Application stores tokens securely
5. Tokens are presented to downstream services
6. Services validate token signature and claims

No service needs direct access to Cognito’s user database.

---

## Lambda Functions and Custom Authentication

### Why Lambda Is Required

Default authentication flows do not cover:

- Custom OTP rules
- Account lockout policies
- External state tracking
- Non-password-based logic

Lambda allows Cognito to **delegate decisions** without giving up control of the session.

---

### How Cognito and Lambda Interact

Cognito pauses authentication and invokes Lambda at predefined stages.


---

## Problem Statement

Traditional password-based authentication introduces several operational and security challenges:

| Issue | Impact |
|---|---|
| Password reuse | Increased account takeover risk |
| Credential storage | Compliance and breach exposure |
| Brute-force attacks | Requires complex mitigation |
| Poor UX | Password resets and lockouts |

The goal of this project is to design a **secure, passwordless authentication flow** that:

- Eliminates stored passwords
- Enforces server-side verification
- Protects against brute-force OTP attempts
- Scales without stateful backend servers
- Cleanly separates UI from identity logic

---

## Architecture Overview

### High-Level Flow

```

User (Streamlit UI)
↓
Amazon Cognito (User Pool)
↓
AWS Lambda (Custom Auth Triggers)
↓
Amazon DynamoDB (OTP State)
↓
Amazon SES (OTP Email)
↓
Amazon Cognito (Token Issuance)

```

### Design Principles

- Authentication logic is **never handled in the frontend**
- All decisions are **stateless and server-enforced**
- OTPs are **ephemeral and single-use**
- Raw session state is persisted only where required

---

## Core Components and Responsibilities

### Amazon Cognito – User Pool

Cognito acts as the **authentication orchestrator**, not the decision-maker.

**Key characteristics in this project:**

- Authentication mode: `CUSTOM_AUTH`
- Username: Email
- Passwords: Not used
- Hosted UI: Not used
- OAuth tokens: Issued only after OTP verification
- Identity standard: OpenID Connect (OIDC)

**Why Cognito**

- Managed identity service with built-in token issuance
- Native support for Lambda-based custom authentication
- Secure session handling without managing credentials manually
- Seamless integration with OIDC-compliant systems

---

### Cognito Custom Authentication Flow

Cognito pauses the authentication process and delegates decisions to Lambda at defined checkpoints.

```

Cognito → Lambda → Cognito

```

This allows full control over:

- OTP generation logic
- Validation rules
- Retry limits
- Account lockout policies

---

## Lambda Triggers

### 1. CreateAuthChallenge

**Purpose**

- Generate and send OTP
- Initialize authentication state

**Responsibilities**

- Check account lock status
- Generate a secure OTP
- Reset attempt counters
- Store OTP metadata in DynamoDB
- Send OTP email via SES

**File**

```

lambda/createAuthChallenge.py

```

---

### 2. VerifyAuthChallengeResponse

**Purpose**

- Validate user-submitted OTP

**Responsibilities**

- Compare OTP securely
- Increment failed attempts
- Lock account after threshold
- Clear OTP state on success

**File**

```

lambda/verifyAuthChallengeResponse.py

```

---

### 3. DefineAuthChallenge

**Purpose**

- Control authentication progression

**Responsibilities**

- Decide whether to:
  - Retry OTP
  - Issue tokens
  - Fail authentication

**Rules Enforced**

- Tokens issued only after successful OTP validation
- Authentication fails after 6 incorrect attempts

**File**

```

lambda/defineAuthChallenge.py

```

---

## DynamoDB Design

### Table: `otp_login_attempts`

| Attribute | Type | Description |
|---|---|---|
| email | String (PK) | User identifier |
| otp | String | Generated OTP |
| attempts | Number | Failed attempts count |
| last_attempt_time | Number | Epoch timestamp |
| locked_until | Number | Lock expiry timestamp |

**Why DynamoDB**

- Low-latency key-based access
- Fully serverless
- Naturally fits ephemeral authentication state
- No connection pooling or scaling concerns

**Tradeoff**

- Strong consistency must be handled carefully
- Explicit cleanup logic is required

---

## Amazon SES – Email Delivery

SES is used exclusively by Lambda for OTP delivery.

**Design Constraints**

- Sender identity must be verified
- Correct region alignment with Lambda
- IAM permission: `ses:SendEmail`

**Why SES**

- Native AWS integration
- Reliable delivery at scale
- No frontend exposure to email APIs

---

## Streamlit UI

Streamlit serves as a **thin client only**.

**Responsibilities**

- Collect email input
- Submit OTP
- Display authentication state

**Non-Responsibilities**

- OTP generation
- Validation
- Retry logic
- Session enforcement

**Why Streamlit**

- Rapid UI development
- Clear separation from backend logic
- Ideal for internal tools and prototypes that still require secure auth

---

## Security Controls

| Control | Implementation |
|---|---|
| Passwordless auth | No passwords stored or transmitted |
| Brute-force protection | Max 6 OTP attempts |
| Temporary lockout | 15-minute account lock |
| Session safety | Old sessions invalidated |
| Server-side enforcement | Lambda + DynamoDB only |

All security rules are enforced **outside the UI**.

---

## CI/CD and Deployment Considerations

When paired with **CircleCI**, this architecture supports:

- Automated testing of Lambda functions
- Static analysis for IAM policies
- Controlled deployment of Streamlit applications
- Environment-based configuration separation

**Why CI/CD matters here**

- Authentication systems demand correctness
- Manual deployments increase risk
- Infrastructure and code must evolve together

---

## AWS Cognito Beyond OTP

While this project focuses on **email OTP**, Cognito also supports:

- Username/password authentication
- Passwordless passkeys
- MFA
- Social identity providers (Google, Apple, Facebook)
- Enterprise IdPs via SAML 2.0 or OIDC (Okta, Entra ID)

This architecture can be extended without redesigning the core system.

---

## OpenID Connect (OIDC)

Cognito operates as an **OIDC Identity Provider**.

- Issues JWT access and ID tokens
- Enables secure SSO
- Decouples authentication from application logic

OIDC allows downstream services to trust tokens without sharing credentials.

---

## Repository Structure

```

.
├── lambda/
│   ├── createAuthChallenge.py
│   ├── defineAuthChallenge.py
│   └── verifyAuthChallengeResponse.py
│
├── streamlit/
│   └── app.py
│
├── images/
│   ├── add_Trigger.png
│   ├── app_Client.png
│   ├── extension.png
│   ├── cognito_IAM.png
│   ├── dynamoDB.png
│   ├── ses.png
│   ├── streamlit_ui.png
│   ├── correctOtp.png
│   ├── invalidOtp.png
│   └── moreLogin.png
│
└── README.md

```

---

## Screenshots (Reference)

- **Cognito Lambda Triggers Configuration**  
  _add_Trigger.png_

- **Cognito App Client Settings**  
  _app_Client.png_

- **DynamoDB OTP State Table**  
  _dynamoDB.png_

- **SES Verified Identity**  
  _ses.png_

- **Streamlit Login UI**  
  _streamlit_ui.png_

- **Successful OTP Verification**  
  _correctOtp.png_

- **Invalid OTP Attempt**  
  _invalidOtp.png_

- **Account Lockout Message**  
  _moreLogin.png_

---

## Non-Goals

- Hosted UI customization
- Password-based login
- Client-side OTP validation
- Real-time streaming authentication

---

## Final Outcome

This repository demonstrates:

- A real-world passwordless authentication design
- Secure serverless enforcement of identity rules
- Clear separation of UI and authentication
- Extensible identity architecture using AWS-native services

---

## 🚀 Deployment (End-to-End)

This section describes how to deploy the **Passwordless Email OTP Authentication System** across AWS services and run the Streamlit client.  
The steps are written for clarity and completeness, not as a lab exercise. Each step reflects required production wiring between services.

---

## Prerequisites

Before deploying, ensure the following are available and correctly configured:

- An active AWS account
- AWS CLI configured locally (`aws configure`)
- Python 3.9 or higher
- Basic familiarity with the AWS Console
- One email address that can be verified in Amazon SES
- Internet access to run the Streamlit application

---

## Step 1: Configure Amazon SES (Email Delivery)

### 1.1 Verify Sender Email Identity

Amazon SES must be able to send OTP emails on behalf of your system.

Actions:

- Open **Amazon SES Console**
- Select region: `ap-south-1`
- Navigate to **Verified identities**
- Choose **Create identity**
- Select **Email address**
- Enter a sender email address (example: `your_email@example.com`)
- Confirm verification using the link received in the inbox

SES will block all outbound emails until the identity is verified.

---

### 1.2 SES Sandbox Considerations

By default, SES operates in **sandbox mode**.

Implications:

- Emails can only be sent to verified email addresses
- This is sufficient for testing, demos, and development
- Production usage requires requesting sandbox removal

---

## Step 2: Create DynamoDB Table

### 2.1 Table Creation

DynamoDB stores OTP state and security metadata.

Actions:

- Open **Amazon DynamoDB**
- Choose **Create table**

Configuration:

| Setting | Value |
|---|---|
| Table name | `otp_login_attempts` |
| Partition key | `email` (String) |
| Other settings | Default |

Create the table.

---

### 2.2 Runtime Attributes

The following attributes are created dynamically by Lambda functions and do not need pre-definition:

- `otp`
- `attempts`
- `last_attempt_time`
- `locked_until`

This design keeps the schema minimal and flexible.

---

## Step 3: Create Amazon Cognito User Pool

### 3.1 User Pool Configuration

Actions:

- Open **Amazon Cognito**
- Choose **Create user pool**

Key settings:

| Setting | Value |
|---|---|
| Authentication method | Email |
| Self sign-up | Enabled |
| Required attributes | `email` |
| Password policy | Not applicable (passwordless) |

Complete the user pool creation.

---

### 3.2 Create App Client

Actions:

- Go to **App integration → App clients**
- Choose **Create app client**

Configuration:

| Setting | Value |
|---|---|
| App type | Public client |
| Enabled auth flows | `CUSTOM_AUTH` |
| Disabled flows | `USER_PASSWORD_AUTH`, SRP |
| Client secret | Enabled |

Save and securely record:

- User Pool ID
- Client ID
- Client Secret

These values are required by the Streamlit application.

---

## Step 4: Create IAM Role for Lambda

### 4.1 IAM Role Setup

Lambda functions require controlled access to DynamoDB, SES, and Cognito.

Actions:

- Open **IAM**
- Create role → **AWS service** → **Lambda**

Attach policies:

- `AmazonDynamoDBFullAccess`
- `AmazonSESFullAccess`
- `AmazonCognitoPowerUser`

Role name:

cognito-otp-lambda-role

yaml
Copy code

This role centralizes permissions required for authentication logic.

---

## Step 5: Create Lambda Functions

All Lambda functions must be created in the **same region as the Cognito User Pool** (`ap-south-1`).

---

### 5.1 CreateAuthChallenge

Purpose:

- Generate OTP
- Check lock status
- Reset attempts
- Send OTP via SES

Configuration:

| Setting | Value |
|---|---|
| Runtime | Python 3.10 |
| Execution role | `cognito-otp-lambda-role` |
| File | `createAuthChallenge.py` |

---

### 5.2 VerifyAuthChallengeResponse

Purpose:

- Validate OTP
- Increment failure count
- Enforce lockout after repeated failures

Configuration:

| Setting | Value |
|---|---|
| Runtime | Python 3.10 |
| Execution role | `cognito-otp-lambda-role` |
| File | `verifyAuthChallengeResponse.py` |

---

### 5.3 DefineAuthChallenge

Purpose:

- Control authentication state transitions
- Decide whether to retry, issue tokens, or fail authentication

Configuration:

| Setting | Value |
|---|---|
| Runtime | Python 3.10 |
| Execution role | `cognito-otp-lambda-role` |
| File | `defineAuthChallenge.py` |

---

## Step 6: Attach Lambda Triggers to Cognito

Cognito must invoke Lambda during authentication.

Actions:

- Open **Cognito User Pool**
- Navigate to **Extensions → Lambda triggers**

Configure:

| Trigger | Lambda Function |
|---|---|
| Create auth challenge | `createAuthChallenge` |
| Verify auth challenge | `verifyAuthChallengeResponse` |
| Define auth challenge | `defineAuthChallenge` |

Save changes.

At this point, Cognito delegates authentication decisions to Lambda.

---

## Step 7: Configure Streamlit Application

### 7.1 Install Dependencies

```bash
pip install streamlit boto3
7.2 Application Configuration
Update the following values in streamlit/app.py:

python
Copy code
REGION = "ap-south-1"
USER_POOL_ID = "your_user_pool_id"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
These values must match the Cognito configuration exactly.

7.3 Run the Application
bash
Copy code
streamlit run app.py
Access the UI at:

arduino
Copy code
http://localhost:8501
Step 8: System Validation
Test Scenarios
Validate the following behaviors end-to-end:

Enter email → OTP is sent via SES

Enter incorrect OTP → error message displayed

Enter incorrect OTP 6 times → account locked

Attempt login during lock window → access blocked

Retry after 15 minutes → new OTP allowed

Enter correct OTP → Cognito issues tokens and login succeeds

All enforcement is handled server-side.





## License

Specify license here.
```
