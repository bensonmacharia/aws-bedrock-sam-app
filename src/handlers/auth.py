import datetime
import json
import uuid
import hashlib
import boto3
import os
import time
import base64
import hmac
from src.utils import generate_jwt

region = "us-east-1"

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + dk.hex()

def verify_password(stored_password: str, provided_password: str) -> bool:
    salt = bytes.fromhex(stored_password[:32])
    stored_hash = stored_password[32:]
    dk = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
    return dk.hex() == stored_hash

def user_register_handler(event, context):
    """Body expected:
    {
        "email": "User Name",
        "password": "User Password"
    }
    """
    print('Register Event: ', json.dumps(event))

    if not event["body"] or event["body"] == "":
        return {"statusCode": 400, "headers": {}, "body": "Bad request"}

    action: dict[str, str] = json.loads(event["body"])

    params = {
        "id": str(uuid.uuid4()),
        "email": action["email"],
        "password": hash_password(action["password"]),
        "created_at": str(datetime.datetime.now())
    }

    try:
        table_name = "users-table"
        # Initialize DynamoDB resource
        dynamodb = boto3.resource("dynamodb", region_name=region)
        # Get the table
        table = dynamodb.Table(table_name)
        # Put the item
        response = table.put_item(Item=params)
        
        api_response = {
            "id": params['id'],
            "email": params['email'],
            "message": "Account created. Proceed to login to access the Chat"
        }
        return {"statusCode": 201, "headers": {}, "body": json.dumps(api_response)}
    except Exception as e:
        print('Error:', e)
        return {"statusCode": 500, "headers": {}, "body": "Internal Server Error"}
    

def user_login_handler(event, context):
    """Body expected:
    {
        "email": "User Name",
        "password": "User Password"
    }
    """
    print('Login Event: ', json.dumps(event))

    if not event["body"] or event["body"] == "":
        return {"statusCode": 400, "headers": {}, "body": "Bad request"}

    action: dict[str, str] = json.loads(event["body"])

    provided_password = action["password"]

    try:
        table_name = "users-table"
        region = "us-east-1"
        # Initialize DynamoDB resource
        dynamodb = boto3.resource("dynamodb", region_name=region)
        # Get the table
        table = dynamodb.Table(table_name)
        # Email is the primary key
        response = table.get_item(Key={"email": action["email"]})
        if "Item" in response:
            user_item = response["Item"]
            stored_password = user_item.get("password")
            is_valid = verify_password(stored_password, provided_password)
            
            if is_valid:
                jwt_token = generate_jwt(user_item.get("id"), action["email"])
                api_response = {
                    "statusCode": 200,
                    "email": action['email'],
                    "message": "Successfully authenticated. Proceed to access the Chat",
                    "token": jwt_token
                }
            else:
                api_response = {
                    "statusCode": 403,
                    "message": "Wrong credentials. Try again"
                }
        else:
            api_response = {
                    "statusCode": 403,
                    "message": "Wrong credentials. Try again"
                }
        return {"statusCode": api_response['statusCode'], "headers": {}, "body": json.dumps(api_response)}
    except Exception as e:
        print('Error: ', e)
        return {"statusCode": 500, "headers": {}, "body": "Internal Server Error"}