from flask import Flask, request, jsonify
import os
import base64
import requests
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
PAYHERO_API_URL = "https://backend.payhero.co.ke/api/v2/payments"
API_USERNAME = "5iOsVi1JBm2fDQJl5LPD"
API_PASSWORD = "vNxb1zHkPV2tYro4SgRDXhTtWBEr8R46EQiBUvkD"

@app.route('/billing/callback', methods=['POST'])
def handle_mpesa_callback():
    """Handle the M-Pesa callback from PayHero API."""
    data = request.json
    logger.info(f"Received callback at /billing: {data}")

    # Check if the callback contains 'response' and 'ResultCode'
    if data and 'response' in data and 'ResultCode' in data['response']:
        result_code = data['response']['ResultCode']
        phone_number = data['response'].get('Phone', '')

        if result_code == 0:  # Assuming '0' indicates success
            logger.info(f"Payment successful. Phone Number: {phone_number}")
            # Implement further actions here, like notifying the user
            return jsonify({"status": "success"}), 200
        else:
            logger.warning(f"Payment not successful. Result Code: {result_code}")
            return jsonify({"status": "pending"}), 200
    else:
        logger.error("Invalid callback data at /billing")
        return jsonify({"status": "error", "message": "Invalid data"}), 400

@app.route('/payhero/callback', methods=['POST'])
def handle_payhero_callback():
    """Handle the PayHero callback."""
    data = request.json
    logger.info(f"Received PayHero callback: {data}")

    # Check if the callback contains 'response' and 'Transaction_Reference'
    if data and 'response' in data and 'Transaction_Reference' in data['response']:
        transaction_reference = data['response']['Transaction_Reference']
        phone_number = data['response'].get('Source', '')

        # Here you can implement your payment verification logic
        logger.info(f"Payment successful for Transaction Reference: {transaction_reference}. Phone Number: {phone_number}")
        return jsonify({"status": "success"}), 200
    else:
        logger.error("Invalid PayHero callback data")
        return jsonify({"status": "error", "message": "Invalid data"}), 400

def check_payment_status(transaction_id: str):
    """Check the payment status via PayHero API."""
    url = f"{PAYHERO_API_URL}/status/{transaction_id}"
    auth_token = base64.b64encode(f"{API_USERNAME}:{API_PASSWORD}".encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("status"), data.get("phone_number")
    return None, None

if __name__ == '__main__':
    app.run(port=5000)
