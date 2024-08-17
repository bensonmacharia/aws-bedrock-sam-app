import boto3
import json
import hashlib
import base64
import hmac
from src.utils import validate_jwt, save_prompt, count_prompts

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

modelId = 'cohere.command-text-v14'

def lambda_handler(event, context):
    """Header expected:
        "Authorization: Bearere generated token" 
    """
    """Body expected:
    {
        "prompt":"Where is Lake Naivasha?"
    }
    """
    print('Event: ', json.dumps(event))

    # Check if headers are present
    if 'headers' in event:
        headers = event['headers']
        
        # Retrieve the Authorization header
        if 'Authorization' in headers:
            authorization_header = headers['Authorization']
            # Extract the token from the header
            if authorization_header.startswith('Bearer '):
                token = authorization_header.split(' ')[1]
                result = validate_jwt(token)
                
                if isinstance(result, dict) and result['user']:
                    countp = count_prompts(result['user'])
                    
                    if countp > 2:
                        api_response = {
                            "statusCode": 401,
                            "body": json.dumps({
                                "message": "You have exhausted the number of queries allowed per day, try again tomorrow."
                            })
                        }
                    else:
                        response_body = json.loads(event['body'])
                        prompt = response_body['prompt']
                        body = {
                            'prompt': prompt,
                            'max_tokens': 400,
                            'temperature': 0.75,
                            'p': 0.01,
                            'k':0,
                            'stop_sequences': [],
                            'return_likelihoods':'NONE'
                        }

                        bedrock_response = bedrock.invoke_model(
                            modelId=modelId,
                            body=json.dumps(body),
                            accept='*/*',
                            contentType='application/json')
                        
                        response = json.loads(bedrock_response['body'].read())['generations'][0]['text']
                        sprompt = save_prompt(prompt, result['sub'], result['user'])
                        
                        queries = countp+1
                        balance = 50-queries
                        if response and sprompt:
                            api_response = {
                                "statusCode": 200,
                                "body": json.dumps({
                                    'prompt': prompt,
                                    'response': response,
                                    'queries': queries,
                                    'balance': balance,
                                })
                            }
                        else:
                            api_response = {
                                "statusCode": 500,
                            "body": json.dumps({
                                    "message": "Error occured. Try again"
                                })
                            }
                else:
                    api_response = {
                            "statusCode": 500,
                           "body": json.dumps({
                                "message": "Error occured. Try again"
                            })
                        }
            else:
                api_response = {
                    "statusCode": 400,
                    "body": json.dumps({
                        "message": "Invalid Authorization header format"
                    })
                }
        else:
            api_response = {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "Authorization header missing"
                })
            }
    else:
        api_response = {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Headers missing"
            })
        }

    return api_response