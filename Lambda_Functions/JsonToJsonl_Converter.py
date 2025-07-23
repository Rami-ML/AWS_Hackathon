import boto3
import json
import logging
import os

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

OUTPUT_BUCKET = 'aws-gs-productmanager-bucket'
OUTPUT_PREFIX = 'kb-ready/'  # Bucket prefix for Bedrock KB ingestion

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        logger.info(f"Processing file: {key}")
        
        response = s3.get_object(Bucket=bucket, Key=key)
        content = json.loads(response['Body'].read())

        jsonl_lines = []
        for item in content:
            line = {
                "text": item.get("summary", ""),
                "metadata": {
                    "classification": item.get("final_classification", "").lower(),
                    "score": item.get("score", 0),
                    "state": item.get("state", "new"),
                    "urgency": item.get("urgency", False),
                    "reference_url": item.get("reference_url", ""),
                    "tags": item.get("tags", [])
                }
            }
            jsonl_lines.append(json.dumps(line))

        jsonl_body = "\n".join(jsonl_lines)

        # ✅ FIX: clean output path and use filename safely
        filename = os.path.basename(key)
        output_key = f"{OUTPUT_PREFIX}{filename.replace('.json', '.jsonl')}"

        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=jsonl_body.encode('utf-8'),
            ContentType='application/json'
        )

        logger.info(f"Converted and saved JSONL to: {output_key}")
