import boto3
import time
import random

ses = boto3.client("ses", region_name="ap-south-1")
dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("otp_login_attempts")

def lambda_handler(event, context):
    email = event["request"]["userAttributes"]["email"]
    now = int(time.time())

    # Get existing record
    response = table.get_item(Key={"email": email})
    item = response.get("Item")

    # Block if still locked
    if item and item.get("locked_until", 0) > now:
        raise Exception("Account locked. Try again after 15 minutes.")

    # ALWAYS generate a fresh OTP on Send OTP
    otp = str(random.randint(100000, 999999))

    table.put_item(
        Item={
            "email": email,
            "otp": otp,
            "attempts": 0,
            "last_attempt_time": now,
            "locked_until": 0
        }
    )

    # Send email every time OTP is generated
    ses.send_email(
        Source="aksingh4539047@gmail.com",
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Your OTP"},
            "Body": {
                "Text": {"Data": f"Your OTP is {otp}. Valid for 15 minutes."}
            }
        }
    )

    print("OTP SENT TO:", email)

    event["response"]["privateChallengeParameters"] = {"otp": otp}
    event["response"]["challengeMetadata"] = "OTP_CHALLENGE"
    return event
