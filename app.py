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
    # This is a placeholder for demonstration. Replace with actual API call.
    
    # Simulating the response for the payment initiation
    reference_id = "some_reference_id"  # Replace with actual reference ID from payment API response
    return jsonify({"reference_id": reference_id})

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

if __name__ == '__main__':
    app.run(debug=True)  # Set debug to True for development
