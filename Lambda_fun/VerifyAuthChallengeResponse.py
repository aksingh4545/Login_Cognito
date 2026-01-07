import boto3
import time

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("otp_login_attempts")

def lambda_handler(event, context):
    email = event["request"]["userAttributes"]["email"]
    user_otp = event["request"]["challengeAnswer"]
    expected_otp = event["request"]["privateChallengeParameters"]["otp"]
    now = int(time.time())

    item = table.get_item(Key={"email": email}).get("Item")

    if not item:
        event["response"]["answerCorrect"] = False
        return event

    # ⛔ Locked user
    if item.get("locked_until", 0) > now:
        event["response"]["answerCorrect"] = False
        return event

    # ✅ Correct OTP
    if user_otp == expected_otp:
        table.update_item(
            Key={"email": email},
            UpdateExpression="SET attempts = :z",
            ExpressionAttributeValues={":z": 0}
        )
        event["response"]["answerCorrect"] = True
        return event

    # ❌ Wrong OTP
    attempts = item.get("attempts", 0) + 1

    update_expr = "SET attempts=:a"
    values = {":a": attempts}

    if attempts >= 6:
        update_expr += ", locked_until=:l"
        values[":l"] = now + 900  # 15 minutes

    table.update_item(
        Key={"email": email},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=values
    )

    event["response"]["answerCorrect"] = False
    return event

