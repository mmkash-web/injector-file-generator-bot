from flask import Flask, request, jsonify
import requests
import os
import base64

app = Flask(__name__)

# Replace these with your actual PayHero and Telegram bot credentials
PAYHERO_API_KEY = os.getenv('PAYHERO_API_KEY')
API_PASSWORD = os.getenv('API_PASSWORD')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')  # Use CHAT_ID variable

@app.route('/payhero/callback', methods=['POST'])
def payhero_callback():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    reference = data.get('MPESA_Reference')  # Adjusted to match your callback structure
    status = data.get('woocommerce_payment_status')

    # Log the callback data for debugging
    print(f"Received callback: {data}")

    # Fetch the transaction status
    transaction_status = fetch_transaction_status(reference)
    
    if transaction_status and transaction_status.get('success') and transaction_status.get('status') == 'SUCCESS':
        send_telegram_message(f"Transaction {transaction_id} was verified and is successful!")
    else:
        send_telegram_message(f"Transaction {transaction_id} verification failed or is unsuccessful.")
    
    return jsonify({'status': 'received'}), 200

def fetch_transaction_status(reference):
    url = f"https://backend.payhero.co.ke/api/v2/transaction-status?reference={reference}"
    
    # Ensure the credentials are correctly encoded
    credentials = f"{PAYHERO_API_KEY}:{API_PASSWORD}".encode('utf-8')
    encoded_credentials = base64.b64encode(credentials).decode('utf-8')

    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.get(url, headers=headers)
        # Log the request and response
        print(f"Request URL: {url}")
        print(f"Request Headers: {headers}")

        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result}")  # Log the response
            return result
        else:
            print(f"Error fetching transaction status: {response.status_code} - {response.text}")
            return {'status': 'ERROR', 'message': response.text}
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return {'status': 'ERROR', 'message': str(e)}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',  # Optional: format the message
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code} - {response.text}")

if __name__ == '__main__':
    app.run(debug=True)
