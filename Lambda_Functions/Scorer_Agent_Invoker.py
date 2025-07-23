import boto3
import json
import uuid
import logging
import os
import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')  # Use converse API

OUTPUT_BUCKET = "aws-gs-productmanager-bucket"

# Define the structured JSON schema as a tool for Bedrock Converse API
tool_config = {
    "tools": [
        {
            "toolSpec": {
                "name": "classify_article",
                "description": "Classify automotive feedback articles.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "final_classification": { 
                                "type": "string", 
                                "enum": ["alert", "insight"] 
                            },
                            "score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Relevance score of the article, where 1 is least relevant and 10 is most relevant."
                            },
                            "state": { 
                                "type": "string",
                                "enum": ["new", "assessed"] 
                            },
                            "urgency": { "type": "boolean" },
                            "summary": { "type": "string" },
                            "reference_url": { "type": "string" },
                            "tags": {
                                "type": "array",
                                "items": { "type": "string" }
                            }
                        },
                        "required": [
                            "final_classification",
                            "score",
                            "state",
                            "urgency",
                            "summary",
                            "reference_url",
                            "tags"
                        ]
                    }
                }
            }
        }
    ]
}


def lambda_handler(event, context):
    logger.info("Lambda triggered with event: %s", json.dumps(event))

    try:
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        source_key = event['Records'][0]['s3']['object']['key']

        logger.info(f"Fetching file from bucket: {source_bucket}, key: {source_key}")
        response = s3.get_object(Bucket=source_bucket, Key=source_key)
        articles = json.loads(response['Body'].read())

        classified = []

        for article in articles:
            input_text = f"Title: {article['title']}\nContent: {article['content']}\nURL: {article.get('url', '')}"
            logger.info("Invoking Bedrock Converse API with article title: %s", article["title"])

            try:
                response = bedrock.converse(
                    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                    system=[{
                        "text": (
                            """
                            You MUST use the 'classify_article' tool.

                            Classify the article as:
                            - 'alert' → if it describes a problem, urgent issue, or safety concern.
                            - 'insight' → if it provides consumer opinions, suggestions, rankings, or recommendations.

                            Also assign a **relevance score from 1 to 10**, where:
                            - 1 means the article is barely relevant to consumers or product decision-making.
                            - 5 means it is moderately useful or general.
                            - 10 means it is highly relevant and valuable — such as well-tested product reviews, new technology, or detailed consumer advice that could strongly influence purchasing or behavior.

                            Be strict and varied with the scoring. Most articles should NOT be a perfect 10. Think critically about how valuable this article would be for someone deciding what to buy, avoid, or pay attention to.

                            Only respond using the 'classify_article' tool.
                            """)
                    }],
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"text": input_text}
                            ]
                        }
                    ],
                    toolConfig=tool_config
                )
                logger.warning("Full Converse response:\n%s", json.dumps(response, indent=2))

                contents = response.get("output", {}).get("message", {}).get("content", [])
                tool_use = [c["toolUse"] for c in contents if "toolUse" in c]
                if tool_use and "input" in tool_use[0]:
                    result = tool_use[0]["input"]
                else:
                    logger.error("No valid structured response from Bedrock Converse.")
                    continue

                classified.append({
                    "article_id": article['title'].lower().replace(" ", "-"),
                    "title": article['title'],
                    "score": result.get("score"),
                    "final_classification": result.get("final_classification"),
                    "state": result.get("state", "new"),
                    "urgency": result.get("urgency", False),
                    "tags": result.get("tags", []),
                    "summary": result.get("summary"),
                    "reference_url": result.get("reference_url")
                })

            except Exception as e:
                logger.error("Error processing article '%s': %s", article.get("title", "UNKNOWN"), e)
                continue

        base_name = os.path.basename(source_key)
        name_no_ext = os.path.splitext(base_name)[0]

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        output_key = f"classified/{name_no_ext}-scored-{timestamp}.json"
        logger.info("Saving results to %s/%s", OUTPUT_BUCKET, output_key)

        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=json.dumps(classified, indent=2),
            ContentType="application/json"
        )

        logger.info("Processing complete. Articles classified: %d", len(classified))

        return {
            "statusCode": 200,
            "body": f"Successfully processed {len(classified)} articles."
        }

    except Exception as e:
        logger.error("Unhandled error: %s", e)
        return {
            "statusCode": 500,
            "body": str(e)
        }
