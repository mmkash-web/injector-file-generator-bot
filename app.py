from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Replace these with your actual PayHero and Telegram bot credentials
PAYHERO_API_KEY = os.getenv('PAYHERO_API_KEY')
API_PASSWORD = os.getenv('API_PASSWORD')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')  # Corrected variable name

@app.route('/payhero/callback', methods=['POST'])
def payhero_callback():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    reference = data.get('reference')
    status = data.get('status')

    print(f"Received callback: {data}")

    transaction_status = fetch_transaction_status(reference)
    
    if transaction_status and transaction_status.get('status') == 'SUCCESS':
        send_telegram_message(f"Transaction {transaction_id} was verified and is successful!")
    else:
        send_telegram_message(f"Transaction {transaction_id} verification failed or is unsuccessful.")
    
    return jsonify({'status': 'received'}), 200

@app.route('/billing/callback', methods=['GET'])
def billing_callback():
    # Handle any GET requests sent to this endpoint
    return jsonify({'status': 'success'}), 200

def fetch_transaction_status(reference):
    url = f"https://backend.payhero.co.ke/api/v2/transaction-status?reference={reference}"
    headers = {
        'Authorization': f'Basic {PAYHERO_API_KEY}',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching transaction status: {response.status_code} - {response.text}")
        return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code} - {response.text}")

if __name__ == '__main__':
    app.run(debug=True)
