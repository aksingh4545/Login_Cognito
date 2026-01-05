**AWS Cognito enables you to authenticate users securely, whether through traditional username and password or social identity providers like Google. When you pair this with Streamlit’s simplicity in building interactive, data-driven web applications and CircleCI’s powerful Continuous Integration and Continuous Deployment (CI/CD) capabilities, you create a robust, secure, and scalable deployment pipeline.**

<h3>Understand AWS Cognito’s role</h3>
<p>AWS Cognito is a fully managed service that handles user sign-up, sign-in, and access control. In your Streamlit app, you will use Cognito’s User Pools and Hosted UI to authenticate users through either username/password or social login (e.g., Google). Cognito will issue OAuth2 tokens, which your application will use to validate and manage user sessions.</p>

Easy setup
with SDKs and managed login pages
Amazon Cognito has efficient tools for applications. Step through setup guidance for technologies like JavaScript, IOS, and Android. Apply custom branding to your managed login pages.

Protect your users with
a range of security features
The security features of Amazon Cognito are ever growing and improving. The options that help protect your users include mitigation of compromised credentials and adaptive responses to malicious activity. Amazon Cognito also produces exportable logs of user authentication risks, outcomes, and characteristics.

Powerful customer identity with
password, passwordless, and passkey authentication
Use Amazon Cognito as an identity provider. Support flexible authentication, MFA, one-time passwords, biometric devices, and security keys.

Get user identities from anywhere
Use Amazon Cognito as a gateway to many identity providers. Give your internal users authentication with SAML 2.0 or OIDC like Okta and Entra ID. Give your external users authentication with social providers like Amazon, Apple, Google, and Facebook.

<h2>User Pool</h2>
An Amazon Cognito User Pool is a managed user directory service for web and mobile apps, handling user sign-up, sign-in, and access control, acting as an OpenID Connect (OIDC) Identity Provider (IdP) that secures your app with features like user profiles, social sign-in (Facebook, Google), MFA, and customizable login flows, issuing secure JWT tokens after authentication. It simplifies identity management by offloading user authentication to AWS, letting developers focus on app features

You can, for example, verify that your users’ sessions are from trusted sources. You can combine the Amazon Cognito directory with an external identity provider. With your preferred AWS SDK, you can choose the API authorization model that works best for your app. And you can add AWS Lambda functions that modify or overhaul the default behavior of Amazon Cognito.

<img>userPool_arc.png<img>

<h2>OIDC</h2>
OpenID Connect (OIDC) is an identity layer built on OAuth 2.0, an authorization framework, that standardizes how applications verify a user's identity (authentication) and get basic profile info, enabling secure single sign-on (SSO) across different services. It uses JSON Web Tokens (JWTs) (ID Tokens) to securely exchange user identity information, allowing users to log in with one provider (like Google or Microsoft) to access multiple apps without sharing passwords
<img>openID.png<img>



<h2>with Lambda Function</h2>
Amazon Cognito works with AWS Lambda functions to modify the authentication behavior of your user pool. You can configure your user pool to automatically invoke Lambda functions before their first sign-up, after they complete authentication, and at several stages in between. Your functions can modify the default behavior of your authentication flow, make API requests to modify your user pool or other AWS resources, and communicate with external systems. The code in your Lambda functions is your own. Amazon Cognito sends event data to your function, waits for the function to process the data, and in most cases anticipates a response event that reflects any changes you want to make to the session.
Add a user pool Lambda trigger

To add a user pool Lambda trigger with the console
Use the Lambda console to create a Lambda function. For more information on Lambda functions, see the AWS Lambda Developer Guide.

Go to the Amazon Cognito console, and then choose User Pools.

Choose an existing user pool from the list, or create a user pool.

Choose the Extensions menu and locate Lambda triggers.

Choose Add a Lambda trigger.

Select a Lambda trigger Category based on the stage of authentication that you want to customize.

Select Assign Lambda function and select a function in the same AWS Region as your user pool.


Tokens are artifacts of authentication that your applications can use as proof of OIDC authentication and to request access to resources. The claims in tokens are information about your user. The ID token contains claims about their identity, like their username, family name, and email address. The access token contains claims like scope that the authenticated user can use to access third-party APIs, Amazon Cognito user self-service API operations, and the userInfo endpoint. The access and ID tokens both include a cognito:groups claim that contains your user's group membership in your user pool. For more information about user pool groups, see Adding groups to a user pool.
Authenticating with tokens
When a user signs into your app, Amazon Cognito verifies the login information. If the login is successful, Amazon Cognito creates a session and returns an ID token, an access token, and a refresh token for the authenticated user. You can use the tokens to grant your users access to downstream resources and APIs like Amazon API Gateway. Or you can exchange them for temporary AWS credentials to access other AWS services.



<img>cognito_DBs<img>
See the diagram above for a common Amazon Cognito scenario. Here the idea is to authenticate your user, and then grant your user access to another AWS service.

In the first step, application user signs in through a user pool and receives user pool tokens after a successful authentication.
Next, application exchanges the user pool tokens for AWS credentials through an identity pool.
Finally, application user can then use those AWS credentials to access other AWS services such as Amazon S3 or DynamoDB.



<h4>Cognito pauses → Lambda runs → Cognito continues.</h4>
<img>jwt_Congito<img>


Big picture (simple flow)

User enters email + password in Streamlit

Streamlit calls Cognito User Pool

Cognito triggers a Lambda function

Lambda checks:

failed attempts

lock time (15 minutes)

Cognito allows or blocks login

Components used

Amazon Cognito → authentication

AWS Lambda → login attempt logic

Streamlit → UI



