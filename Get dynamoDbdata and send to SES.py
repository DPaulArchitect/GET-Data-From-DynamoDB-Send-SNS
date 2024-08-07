import json
import boto3
import os
import logging

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients for DynamoDB and SES
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses', region_name='YOUR-AWS-REGION')

# Get environment variables
jokes_table_name = os.environ['JOKES_TABLE']
subscribers_table_name = os.environ['SUBSCRIBERS_TABLE']
sender_email = os.environ['SENDER_EMAIL']

# Get references to the DynamoDB tables
jokes_table = dynamodb.Table(jokes_table_name)
subscribers_table = dynamodb.Table(subscribers_table_name)

def lambda_handler(event, context):
    try:
        # Get the latest joke from the JokesTable
        response = jokes_table.scan()
        jokes = response['Items']
        
        # Log the retrieved jokes for debugging
        logger.info("Retrieved jokes: %s", jokes)
        
        if not jokes:
            raise ValueError("No jokes found in the JokesTable.")
        
        # Use 'Timestamp' attribute to find the latest joke
        latest_joke = max(jokes, key=lambda x: x.get('Timestamp', ''))
        joke_text = f"{latest_joke['Setup']} - {latest_joke['Punchline']}"
        
        # Get all subscribers from the DailyJoke table
        response = subscribers_table.scan()
        subscribers = response['Items']
        
        # Log the retrieved subscribers for debugging
        logger.info("Retrieved subscribers: %s", subscribers)
        
        if not subscribers:
            raise ValueError("No subscribers found in the DailyJoke table.")
        
        # Send the joke to each subscriber using SES
        for subscriber in subscribers:
            email = subscriber['Email']
            name = subscriber['Name']
            
            ses.send_email(
                Source=sender_email,
                Destination={
                    'ToAddresses': [email],
                },
                Message={
                    'Subject': {
                        'Data': 'Daily Joke',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': joke_text,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Joke sent successfully to all subscribers.'})
        }
    
    except Exception as e:
        logger.error("Error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
