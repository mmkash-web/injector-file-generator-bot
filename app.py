from flask import Flask, request, jsonify
import httpx
import os
import base64

app = Flask(__name__)

# Fetching credentials from environment variables
API_USERNAME = os.getenv('PAYHERO_API_USERNAME')  # Your API username
API_PASSWORD = os.getenv('PAYHERO_API_PASSWORD')  # Your API password

def get_auth_header():
    # Create Basic Auth header
    credentials = f"{API_USERNAME}:{API_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

@app.route('/pay', methods=['POST'])
def pay():
    # Implement your payment initiation logic here
    reference_id = "some_reference_id"  # Replace with actual reference ID from payment API response
    return jsonify({"reference_id": reference_id})

@app.route('/payhero/callback', methods=['POST'])
def payhero_callback():
    # Handle the Payhero callback logic
    data = request.json
    # Process the callback data here
    return jsonify({"message": "Payhero callback received", "data": data}), 200

@app.route('/billing/callback', methods=['POST'])
def billing_callback():
    # Handle the billing callback logic
    data = request.json
    # Process the callback data here
    return jsonify({"message": "Billing callback received", "data": data}), 200

@app.route('/transaction-status', methods=['GET'])
def fetch_transaction_status():
    reference = request.args.get('reference')
    
    if not reference:
        return jsonify({"error": "Reference ID is required"}), 400
    
    url = f'https://backend.payhero.co.ke/api/v2/transaction-status?reference={reference}'
    headers = get_auth_header()
    
    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Return the JSON response directly
    except httpx.HTTPStatusError as e:
        return jsonify({"error": f"HTTP error occurred: {e.response.status_code} - {e.response.text}"}), e.response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/verify-mpesa-message', methods=['POST'])
def verify_mpesa_message():
    """Endpoint to verify M-Pesa messages uploaded by users."""
    user_data = request.json
    reference_id = user_data.get('reference_id')  # Expecting the reference ID in the uploaded message

    if not reference_id:
        return jsonify({"error": "Reference ID is required"}), 400

    # Call the transaction status function
    transaction_status = fetch_transaction_status(reference=reference_id)
    
    if isinstance(transaction_status, tuple):  # If it's an error response
        return transaction_status  # Return the error response directly

    # Process the transaction status and create a response for the user
    if transaction_status['success'] and transaction_status['status'] == 'SUCCESS':
        response_message = "Transaction successful!"
    else:
        response_message = "Transaction not successful or still pending."

    return jsonify({"message": response_message, "transaction_status": transaction_status}), 200

if __name__ == '__main__':
    app.run(debug=True)  # Set debug to True for development
