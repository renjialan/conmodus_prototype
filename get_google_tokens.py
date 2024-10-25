from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

def get_google_tokens():
    # Define the scopes your application needs
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]

    try:
        # Load client secrets from a file
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',  # Download this from Google Cloud Console
            scopes=SCOPES
        )

        # Run the OAuth flow locally
        credentials = flow.run_local_server(port=0)

        # Create tokens dictionary
        tokens = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
        }

        # Create .streamlit directory if it doesn't exist
        os.makedirs('.streamlit', exist_ok=True)

        # Write to secrets.toml
        with open('.streamlit/secrets.toml', 'w') as f:
            for key, value in tokens.items():
                f.write(f'{key} = "{value}"\n')

        print("Tokens have been successfully saved to .streamlit/secrets.toml")
        return tokens

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    get_google_tokens()