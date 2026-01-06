import streamlit as st
import boto3
import hmac
import hashlib
import base64

REGION = "ap-south-1"
USER_POOL_ID = "ap-south-1_Vu2fj6EP8"
CLIENT_ID = "7vgo6qhl7ibe25k5ihln621b48"
CLIENT_SECRET = "1amkp4dtgr0l1rppuvhivlf1aqc9k03c03onbtp1mi78gtqlnhkt"

client = boto3.client("cognito-idp", region_name=REGION)

def get_secret_hash(username):
    msg = username + CLIENT_ID
    dig = hmac.new(
        CLIENT_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode("utf-8")

def ensure_user_exists(email):
    try:
        client.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=email
        )
    except client.exceptions.UserNotFoundException:
        client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"}
            ],
            MessageAction="SUPPRESS"
        )

st.title("Email OTP Login")

email = st.text_input("Email").strip().lower()

# ---------- SEND OTP ----------
if st.button("Send OTP"):
    if "@" not in email:
        st.error("Please enter a valid email address")
    else:
        try:
            # 🔑 IMPORTANT: clear any old session
            st.session_state.pop("session", None)

            ensure_user_exists(email)

            response = client.initiate_auth(
                AuthFlow="CUSTOM_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "SECRET_HASH": get_secret_hash(email)
                },
                ClientId=CLIENT_ID
            )

            # store fresh session only
            st.session_state["session"] = response["Session"]
            st.session_state["email"] = email

            st.success("OTP sent to your email")

        except Exception as e:
            st.error(str(e))

otp = st.text_input("Enter OTP")

# ---------- VERIFY OTP ----------
if st.button("Verify OTP"):
    if "session" not in st.session_state:
        st.error("Session expired. Please request OTP again.")
    else:
        try:
            response = client.respond_to_auth_challenge(
                ClientId=CLIENT_ID,
                ChallengeName="CUSTOM_CHALLENGE",
                Session=st.session_state["session"],
                ChallengeResponses={
                    "USERNAME": st.session_state["email"],
                    "ANSWER": otp.strip(),
                    "SECRET_HASH": get_secret_hash(st.session_state["email"])
                }
            )

            # ✅ ONLY success if tokens exist
            if "AuthenticationResult" in response:
                st.session_state.pop("session", None)
                st.success("Login successful")
            else:
                # ❌ Wrong OTP
                st.session_state["session"] = response.get("Session")
                st.error("Invalid OTP. Please try again.")

        except Exception as e:
            st.error(str(e))
