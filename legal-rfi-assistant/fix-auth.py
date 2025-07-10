import boto3
import os

COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-west-2")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")
cognito_idp = boto3.client('cognito-idp', region_name=COGNITO_REGION)

def authenticate_user(username, password):
    try:
        response = cognito_idp.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthParameters={'USERNAME': username, 'PASSWORD': password}
        )
        
        if 'ChallengeName' in response and response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            return {
                'success': False, 
                'challenge': 'NEW_PASSWORD_REQUIRED',
                'session': response['Session'],
                'message': 'You need to set a permanent password.'
            }
        
        if 'AuthenticationResult' in response:
            return {
                'success': True,
                'id_token': response['AuthenticationResult']['IdToken'],
                'access_token': response['AuthenticationResult']['AccessToken'],
                'refresh_token': response['AuthenticationResult']['RefreshToken']
            }
        
        return {'success': False, 'message': 'Authentication failed'}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}

def set_permanent_password(username, new_password, session):
    try:
        response = cognito_idp.respond_to_auth_challenge(
            ClientId=COGNITO_APP_CLIENT_ID,
            ChallengeName='NEW_PASSWORD_REQUIRED',
            Session=session,
            ChallengeResponses={'USERNAME': username, 'NEW_PASSWORD': new_password}
        )
        
        if 'AuthenticationResult' in response:
            return {
                'success': True,
                'id_token': response['AuthenticationResult']['IdToken'],
                'access_token': response['AuthenticationResult']['AccessToken'],
                'refresh_token': response['AuthenticationResult']['RefreshToken']
            }
        
        return {'success': False, 'message': 'Failed to set permanent password'}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}