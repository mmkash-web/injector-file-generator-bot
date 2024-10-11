from flask import Flask, request, jsonify
import logging
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load file links from JSON
def load_links():
    """Load file links from links.json."""
    with open('links.json', 'r') as file:
        return json.load(file)

links = load_links()

@app.route('/billing/callback1', methods=['POST'])
def handle_payment_callback():
    """Handle payment confirmation callback from PayHero."""
    try:
        # Parse the incoming JSON payload
        data = request.json
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        phone_number = data.get('phone_number')

        # Log the payment details
        logger.info(f"Payment Callback Received: Transaction ID: {transaction_id}, Status: {status}, Phone Number: {phone_number}")

        if status == "successful":
            # Here you can update your database or notify your Telegram bot
            # Example: Notify your Telegram bot
            # send_notification_to_telegram(transaction_id, phone_number)

            return jsonify({"message": "Payment processed successfully."}), 200
        else:
            logger.warning(f"Payment not successful for Transaction ID: {transaction_id}")
            return jsonify({"message": "Payment not successful."}), 400
    except Exception as e:
        logger.error(f"Error handling payment callback: {e}")
        return jsonify({"message": "Error processing payment."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

