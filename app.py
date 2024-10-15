from flask import Flask, request, jsonify
import httpx
import os

app = Flask(__name__)

# Payhero API credentials
AUTH_TOKEN = os.environ.get('PAYHERO_AUTH_TOKEN')  # Store your auth token in environment variable

# Endpoint to initiate payment (dummy example)
@app.route('/pay', methods=['POST'])
def initiate_payment():
    # This would include the details you need to send to Payhero to initiate a payment
    payment_data = {
        "amount": request.json.get("amount"),
        "phone": request.json.get("phone"),
        "user_reference": request.json.get("user_reference"),
        # Add more fields as required by Payhero
    }
    
    # Dummy response simulating a successful payment initiation
    reference_id = "UNIQUE_REF_12345"  # In a real scenario, you'd get this from the Payhero response

    # Store the reference_id somewhere (database or in-memory)
    # For demonstration, we return it as response
    return jsonify({"status": "success", "reference_id": reference_id}), 200

# Endpoint to fetch transaction status
@app.route('/transaction-status', methods=['GET'])
def fetch_transaction_status():
    reference_id = request.args.get('reference')
    if not reference_id:
        return jsonify({"error": "Reference ID is required"}), 400

    url = f'https://backend.payhero.co.ke/api/v2/transaction-status?reference={reference_id}'
    headers = {
        'Authorization': f'Basic {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = httpx.get(url, headers=headers)
    if response.status_code == 200:
        return response.json(), 200
    else:
        return jsonify({"error": "Failed to fetch transaction status", "details": response.json()}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)

