import os
import json
import requests
import logging
import traceback
from requests.auth import HTTPBasicAuth
from datetime import datetime
import sys

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
CONFLUENCE_BASE_URL = os.environ["CONFLUENCE_BASE_URL"]
CONFLUENCE_SPACE_KEY = os.environ["CONFLUENCE_SPACE_KEY"]
CONFLUENCE_PARENT_PAGE_ID = os.environ["CONFLUENCE_PARENT_PAGE_ID"]
CONFLUENCE_USERNAME = os.environ["CONFLUENCE_USERNAME"]
CONFLUENCE_API_TOKEN = os.environ["CONFLUENCE_API_TOKEN"]

def lambda_handler(event, context):
    try:
        logger.info("== Lambda Start ==")
        logger.info("Lambda context memory: %s", context.memory_limit_in_mb)
        logger.info("Lambda remaining time: %s", context.get_remaining_time_in_millis())
        print("Raw event:", event)
        sys.stdout.flush()
        logger.info(json.dumps(event))
        raw_params = event.get("parameters", [])

        # Handle incorrectly stringified parameters
        if isinstance(raw_params, str):
            try:
                raw_params = json.loads(raw_params)
            except json.JSONDecodeError:
                return bedrock_response("FAILURE", "Invalid JSON in 'parameters'")

        # Parse parameters into dictionary
        params = {p["name"]: p["value"] for p in raw_params if isinstance(p, dict)}
        title = params.get("title", "Untitled Page")
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        full_title = f"{title} - {timestamp}"
        content = params.get("content", "")
        reference_url = params.get("reference_url", "")
        audience = params.get("audience", "General")

        # Create XHTML body
        body = f"""
        <p><strong>Audience:</strong> {audience}</p>
        <p><strong>Reference:</strong> <a href="{reference_url}">{reference_url}</a></p>
        <p><strong>Summary:</strong></p>
        <p>{content}</p>
        """

        # Create Confluence page
        payload = {
            "type": "page",
            "title": full_title,
            "ancestors": [{"id": CONFLUENCE_PARENT_PAGE_ID}],
            "space": {"key": CONFLUENCE_SPACE_KEY},
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage"
                }
            }
        }

        logger.info("Posting to Confluence...")
        response = requests.post(
            f"{CONFLUENCE_BASE_URL}/rest/api/content",
            auth=HTTPBasicAuth(CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN),
            headers={"Content-Type": "application/json"},
            json=payload
        )

        logger.info("Confluence response code: %s", response.status_code)

        if response.status_code in [200, 201]:
            page_id = response.json().get("id")
            page_url = f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={page_id}"
            final_response = bedrock_response("REPROMPT", f"Confluence page created: {page_url}")
            logger.info("Returning final Bedrock response: %s", json.dumps(final_response))
            return final_response
        else:
            final_response = bedrock_response("FAILURE", f"Confluence error: {response.text}")
            logger.info("Returning final Bedrock response: %s", json.dumps(final_response))
            return final_response

    except Exception as e:
        logger.exception("Unhandled exception")
        return bedrock_response("FAILURE", f"Internal error: {str(e)}")

# Helper to format response for Bedrock
def bedrock_response(state, message):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "upload_confluence_article",
            "function": "createDocumentation",
            "functionResponse": {
                "responseState": state,
                "responseBody": {
                    "TEXT": {
                        "body": message  
                    }
                }
            }
        }
    }

