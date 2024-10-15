from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Endpoint for handling PayHero callback
@app.route('/payhero/callback', methods=['POST'])
def payhero_callback():
    try:
        data = request.json
        if not data or 'MPESA_Reference' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
        
        # Extracting necessary details
        mpesa_reference = data['MPESA_Reference']
        user_reference = data.get('User_Reference', 'N/A')
        
        # Process the transaction status here (if needed)
        print(f"Received callback with reference: {mpesa_reference} and user reference: {user_reference}")
        
        # Send a message to Telegram (if needed)
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        telegram_message = f"Transaction completed: {mpesa_reference} by {user_reference}"
        
        requests.post(f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': telegram_message})
        
        return jsonify({'status': 'success', 'message': 'Callback received'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
