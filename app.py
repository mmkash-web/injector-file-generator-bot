from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Replace these with your actual PayHero and Telegram bot credentials
PAYHERO_API_KEY = 'iOsVi1JBm2fDQJl5LPD'
API_PASSWORD='vNxb1zHkPV2tYro4SgRDXhTtWBEBOr8R46EQiBUvkD'
TELEGRAM_BOT_TOKEN = '7480076460:AAGieUKKaivtNGoMDSVKeMBuMOICJ9IKJgQ'

CHAT_ID = '1870796520'  # Your Telegram chat ID

@app.route('/payhero/callback', methods=['POST'])
def payhero_callback():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    status = data.get('status')

    # Log the callback data for debugging
    print(f"Received callback: {data}")

    # Verify transaction with PayHero
    verification_response = verify_transaction(transaction_id)
    
    if verification_response and verification_response.get('status') == 'successful':
        send_telegram_message(f"Transaction {transaction_id} was verified and is successful!")
    else:
        send_telegram_message(f"Transaction {transaction_id} verification failed or is unsuccessful.")
    
    return jsonify({'status': 'received'}), 200

def verify_transaction(transaction_id):
    url = f"https://api.payhero.com/transaction/{transaction_id}/verify"
    headers = {
        'Authorization': f'Bearer {PAYHERO_API_KEY}',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Process the response
    else:
        print(f"Error verifying transaction: {response.status_code} - {response.text}")
        return None  # Handle error

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
