import json
import boto3

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    bucket_name = 'aws-gs-ui-bucket'  # Replace with your alerts S3 bucket name
    file_name = 'filtered_alerts/example_alert.json'  # Path to your alerts JSON file

    # Fetch the JSON file from the alerts S3 bucket
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        alerts_data = json.loads(response['Body'].read().decode('utf-8'))

        # Extract the necessary fields for each alert
        simplified_alerts = []
        for alert in alerts_data:
            simplified_alert = {
                'title': alert['alert_box']['title'],
                'subtitle': alert['alert_box']['subtitle'],
                'image_url': alert['alert_box']['image_url'],
                'time': alert['alert_box']['time'],
                'alert_type': alert['alert_box']['alert_type']
            }
            simplified_alerts.append(simplified_alert)
        
        # Return the simplified data as JSON
        return {
            'statusCode': 200,
            'body': json.dumps(simplified_alerts),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Allow cross-origin requests
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }
