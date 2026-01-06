def lambda_handler(event, context):
    session = event["request"]["session"]

    # First attempt
    if len(session) == 0:
        event["response"]["challengeName"] = "CUSTOM_CHALLENGE"
        event["response"]["issueTokens"] = False
        event["response"]["failAuthentication"] = False
        return event

    last_attempt = session[-1]

    # ✅ Only success path
    if last_attempt["challengeResult"] is True:
        event["response"]["issueTokens"] = True
        event["response"]["failAuthentication"] = False
        return event

    # ❌ Too many attempts
    if len(session) >= 6:
        event["response"]["issueTokens"] = False
        event["response"]["failAuthentication"] = True
        return event

    # 🔁 Retry OTP
    event["response"]["challengeName"] = "CUSTOM_CHALLENGE"
    event["response"]["issueTokens"] = False
    event["response"]["failAuthentication"] = False
    return event
