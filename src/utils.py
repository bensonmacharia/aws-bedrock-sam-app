import json
import hashlib
import boto3
import time
import uuid
import base64
import hmac
import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

region = "us-east-1"

def base64url_encode(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b'=')

def base64url_decode(data: bytes) -> bytes:
    return base64.urlsafe_b64decode(data + b'=' * (4 - len(data) % 4))

def retrieve_secret():
    secret_name = "JWTUserTokenSecret"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )
    try:
        # Retrieve the secret value
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        print('Secret: ', get_secret_value_response)
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        return None

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    secret_data = json.loads(secret)

    # Extract the jwt_secret from the secret data
    jwt_secret = secret_data.get("jwt_secret")
    return jwt_secret

def generate_jwt(id: str, email: str):
    secret = retrieve_secret()
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }

    # Set the expiration time (e.g., 1 hour from now)
    expiration_time = int(time.time()) + 3600  # 3600 seconds = 1 hour

    payload = {
        "sub": id,
        "user": email,
        "iat": int(time.time()),
        "exp": expiration_time
    }
    # Encode the header and payload
    header_encoded = base64url_encode(json.dumps(header).encode())
    payload_encoded = base64url_encode(json.dumps(payload).encode())

    # Create the signature
    signature = hmac.new(
        secret.encode(), 
        header_encoded + b'.' + payload_encoded, 
        hashlib.sha256
    ).digest()
    
    signature_encoded = base64url_encode(signature)

    # Combine all parts
    jwt_token = header_encoded + b'.' + payload_encoded + b'.' + signature_encoded
    return jwt_token.decode()

def validate_jwt(token: str):
    secret = retrieve_secret()
    try:
        header_encoded, payload_encoded, signature_encoded = token.split('.')

        signature_check = hmac.new(
            secret.encode(), 
            f"{header_encoded}.{payload_encoded}".encode(), 
            hashlib.sha256
        ).digest()

        if base64url_encode(signature_check) != signature_encoded.encode():
            return "Invalid token"

        payload = json.loads(base64url_decode(payload_encoded.encode()))
        if payload['exp'] < time.time():
            return "Token has expired"

        return payload
    except Exception as e:
        return f"Invalid token: {e}"
    
def save_prompt(prompt: str, id:str, email: str):
    params = {
        "id": str(uuid.uuid4()),
        "uid": id,
        "email": email,
        "prompt": prompt,
        "created_at": str(datetime.datetime.now())
    }
    try:
        table_name = "prompts-table"
        # Initialize DynamoDB resource
        dynamodb = boto3.resource("dynamodb", region_name=region)
        # Get the table
        table = dynamodb.Table(table_name)
        # Put the item
        response = table.put_item(Item=params)
        if response:
            return True
    except Exception as e:
        print('Error:', e)
        return False
    
def count_prompts(email: str):
    try:
        table_name = "prompts-table"
        region = "us-east-1"
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)
        # Get today's date in the correct format
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        # Query the table using the secondary index
        response = table.query(
            IndexName='email-created_at-index',
            KeyConditionExpression=Key('email').eq(email) & Key('created_at').begins_with(today)
        )
        # Count the number of items returned
        count = response['Count']
        return count
    except Exception as e:
        print('Error: ', e)
        return 0