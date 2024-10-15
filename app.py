from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

# Configuration
PAYHERO_API_URL = 'https://backend.payhero.co.ke/api/v2/transaction-status'
AUTH_TOKEN = 'NWlPc1ZpMUpCbTJmRFFKbDVMUEQ6dk54YjF6SGtQVjJ0WXJvNFNnUkRYaFR0V0JFQk9yOFI0NkVRaUJVdmtE'  # Replace with your actual token
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'  # Replace with your actual Telegram bot token
CHAT_ID = 'YOUR_CHAT_ID'  # Replace with your actual chat ID

@app.route('/payhero/callback', methods=['POST'])
def payhero_callback():
    # Receive callback data
    data = request.get_json()
    print(f"Received callback: {data}")  # Log the entire callback data

    transaction_id = data.get('transaction_id')
    reference = data.get('MPESA_Reference')  # Ensure this matches the actual key in the callback data
    status = data.get('woocommerce_payment_status')

    # Check if reference is None
    if reference is None:
        print("Error: MPESA_Reference is None.")
        return jsonify({'status': 'error', 'message': 'Reference is None'}), 400

    # Fetch the transaction status
    transaction_status = fetch_transaction_status(reference)

    if transaction_status and transaction_status.get('success') and transaction_status.get('status') == 'SUCCESS':
        send_telegram_message(f"Transaction {transaction_id} was verified and is successful!")
    else:
        send_telegram_message(f"Transaction {transaction_id} verification failed or is unsuccessful.")

    return jsonify({'status': 'received'}), 200

def fetch_transaction_status(reference):
    headers = {
        'Authorization': f'Basic {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f"{PAYHERO_API_URL}?reference={reference}", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching transaction status: {response.status_code} - {response.json()}")
        return None

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code} - {response.json()}")

if __name__ == '__main__':
    app.run(debug=True)
