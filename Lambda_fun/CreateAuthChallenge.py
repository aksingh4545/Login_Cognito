import boto3
import time
import random

ses = boto3.client("ses", region_name="ap-south-1")
dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("otp_login_attempts")

def lambda_handler(event, context):
    email = event["request"]["userAttributes"]["email"]
    now = int(time.time())
    session = event["request"]["session"]

    # Fetch existing record
    item = table.get_item(Key={"email": email}).get("Item")

    # ⛔ Check lock
    if item and item.get("locked_until", 0) > now:
        raise Exception("Account locked. Try again after 15 minutes.")

    # 🔁 RETRY FLOW → reuse OTP, DO NOT send email
    if session and len(session) > 0:
        otp = item["otp"]

    # 🆕 FIRST REQUEST → generate + send OTP
    else:
        otp = str(random.randint(100000, 999999))

        table.put_item(
            Item={
                "email": email,
                "otp": otp,
                "attempts": 0,
                "otp_created_at": now,
                "locked_until": 0
            }
        )

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

        print("OTP email sent")

    event["response"]["privateChallengeParameters"] = {"otp": otp}
    event["response"]["challengeMetadata"] = "OTP_CHALLENGE"
    return event
