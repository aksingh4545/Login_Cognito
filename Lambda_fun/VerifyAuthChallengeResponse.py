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

    # No record → fail
    if not item:
        event["response"]["answerCorrect"] = False
        return event

    # ✅ Correct OTP
    if user_otp == expected_otp:
        # cleanup on success
        table.delete_item(Key={"email": email})
        event["response"]["answerCorrect"] = True
        return event

    # ❌ Wrong OTP
    attempts = item.get("attempts", 0) + 1

    update_expr = "SET attempts=:a, last_attempt_time=:t"
    values = {
        ":a": attempts,
        ":t": now
    }

    if attempts >= 6:
        update_expr += ", locked_until=:l"
        values[":l"] = now + 900

    table.update_item(
        Key={"email": email},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=values
    )

    # ❌ THIS MUST BE FALSE
    event["response"]["answerCorrect"] = False
    return event
