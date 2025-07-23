import boto3
import json
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('bedrock-agent-runtime')

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # If the event has a 'body' key, parse that as JSON, else use event directly
    if 'body' in event:
        try:
            body = json.loads(event['body'])
        except Exception as e:
            logger.error(f"Error parsing body JSON: {e}")
            body = {}
    else:
        body = event

    user_input = body.get('input', 'Hello!')

    logger.info(f"User input: {user_input}")

    try:
        response = client.invoke_agent(
            agentId='2FMWI0S1KW',  # Replace with your agent ID
            agentAliasId='BNA3RADBBD',  # Replace with your agent alias ID
            sessionId=str(uuid.uuid4()),
            inputText=user_input
        )

        output = ""
        for event_stream in response['completion']:
            if "chunk" in event_stream:
                part = event_stream["chunk"]["bytes"].decode("utf-8")
                output += part

        logger.info(f"Agent response text: {output}")

        return {
            'statusCode': 200,
            'body': json.dumps({"response": output}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
