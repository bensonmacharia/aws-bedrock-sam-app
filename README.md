# aws-bedrock-sam-app

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. We build and deploy a Large Language Model (LLM) application on AWS Lambda, leveraging the power of AWS BedRock. We also explore the capabilities of AWS Secrets Manager in storing, retrieving, and managing secrets within AWS to allow generation of secure JWT tokens to protect the LLM API from misuse.

The application uses several AWS resources, including:-

- Lambda functions
- API Gateway
- Amazon Dynamo DB
- AWS Bedrock
- Secrets Manager.

These resources are defined in the `template.yaml` file in this project.

## Deploy application

To build and deploy the application for the first time, run the following commands:

```bash
$ git clone https://github.com/bensonmacharia/aws-bedrock-sam-app.git
$ cd aws-bedrock-sam-app
$ sam validate
$ sam build
$ sam deploy --guided
```

We need to first validate and build the source of your application. We then package and deploy the application to AWS, with a series of prompts.

## Cleanup

To delete the application that you created, use the AWS CLI. Run the following:

```bash
sam delete --stack-name aws-bedrock-sam-app
```

## Writeup
