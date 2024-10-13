import os
import logging
import json
import time
import base64
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from pymongo import MongoClient

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection with credentials
MONGO_URI = "mongodb+srv://admin:y1Y6kNKXol48UMp7Cmij@mongodb-542f00de-o22372ca4.database.cloud.ovh.net/admin?replicaSet=replicaset&tls=true"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["payment_bot_db"]  # Database name
payments_collection = db["payments"]  # Collection name to store payments

# Load environment variables
BOT_TOKEN = "7480076460:AAGieUKKaivtNGoMDSVKeMBuMOICJ9IKJgQ"  # Replace with your actual bot token
PAYHERO_API_URL = "https://backend.payhero.co.ke/api/v2/payments"
API_USERNAME = "5iOsVi1JBm2fDQJl5LPD"
API_PASSWORD = "vNxb1zHkPV2tYro4SgRDXhTtWBEBOr8R46EQiBUvkD"
FLASK_APP_URL = "https://callback1-21e1c9a49f0d.herokuapp.com/"  # Flask app URL for verifying transactions

# Load file links from JSON
def load_links():
    """Load file links from links.json."""
    with open('links.json', 'r') as file:
        return json.load(file)

links = load_links()
FILE_LINKS_10_DAYS = links["HTTP_10_DAYS"]
FILE_LINKS_14_DAYS = links["HTTP_14_DAYS"]

current_link_index = {"HTTP_10_DAYS": 0, "HTTP_14_DAYS": 0}
user_sent_links = {}  # To track user payments
used_transaction_references = set()

# Define conversation states
CHOOSING_TYPE, ENTERING_PHONE, ENTERING_MPESA_CONFIRMATION = range(3)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("HTTP Injector 10 Days - 80KES", callback_data="HTTP_10_DAYS")],
        [InlineKeyboardButton("HTTP Injector 14 Days - 100KES", callback_data="HTTP_14_DAYS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to EMMKASH-TECH files generator bot:🤖", reply_markup=reply_markup)
    return CHOOSING_TYPE

# File selection
async def file_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_package = query.data
    context.user_data["selected_package"] = selected_package
    await query.message.reply_text(f"You selected {selected_package.replace('_', ' ').title()}. Please enter your phone number:")
    return ENTERING_PHONE

# Handle phone number entry and initiate STK push
async def enter_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    context.user_data["phone_number"] = phone_number
    selected_package = context.user_data["selected_package"]
    
    # Initiate STK Push
    transaction_reference = await initiate_stk_push(phone_number, 80 if selected_package == "HTTP_10_DAYS" else 100, update)
    context.user_data["transaction_reference"] = transaction_reference
    
    await update.message.reply_text("Payment initiated! Please enter the full M-Pesa confirmation message you received:✅")
    return ENTERING_MPESA_CONFIRMATION

# Store payment confirmation in MongoDB
async def enter_mpesa_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mpesa_confirmation_message = update.message.text
    selected_package = context.user_data["selected_package"]
    user_id = update.effective_user.id
    user_phone_number = context.user_data["phone_number"]

    # Validate the confirmation message format
    if not is_valid_mpesa_confirmation(mpesa_confirmation_message):
        await update.message.reply_text("Invalid M-Pesa confirmation message format. Please try again.")
        return ENTERING_MPESA_CONFIRMATION

    # Extract the transaction reference
    transaction_reference = context.user_data["transaction_reference"]

    # Verify transaction and store it in MongoDB
    if await verify_transaction_with_flask(transaction_reference, mpesa_confirmation_message):
        # Store the payment in MongoDB
        payment_data = {
            "user_id": user_id,
            "phone_number": user_phone_number,
            "transaction_reference": transaction_reference,
            "confirmation_message": mpesa_confirmation_message,
            "package": selected_package,
            "timestamp": time.time(),
        }
        payments_collection.insert_one(payment_data)  # Insert payment data into MongoDB
        await confirm_and_send_link(update, user_id, selected_package, mpesa_confirmation_message)
        return CHOOSING_TYPE
    else:
        await update.message.reply_text("The transaction could not be verified. Please check your details or try again.")
        return ENTERING_MPESA_CONFIRMATION

# Confirm and send the config link
async def confirm_and_send_link(update: Update, user_id: int, selected_package: str, mpesa_confirmation_message: str):
    used_transaction_references.add(context.user_data["transaction_reference"])
    user_sent_links[user_id][selected_package] = True

    link = FILE_LINKS_10_DAYS[current_link_index[selected_package]] if selected_package == "HTTP_10_DAYS" else FILE_LINKS_14_DAYS[current_link_index[selected_package]]
    current_link_index[selected_package] = (current_link_index[selected_package] + 1) % len(FILE_LINKS_10_DAYS if selected_package == "HTTP_10_DAYS" else FILE_LINKS_14_DAYS)

    await update.message.reply_text(f"Payment confirmed. Here is your config link: {link}")
    await update.message.reply_text("Thank you for your payment!")

# Helper functions: STK Push, validation, etc.
async def initiate_stk_push(phone_number: str, amount: int, update: Update):
    payload = {
        "amount": amount,
        "phone_number": phone_number,
        "channel_id": 852,
        "provider": "m-pesa",
        "external_reference": "INV-009",
        "callback_url": FLASK_APP_URL + "/callback",
    }
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{API_USERNAME}:{API_PASSWORD}'.encode()).decode()}",
        "Content-Type": "application/json",
    }

    response = requests.post(PAYHERO_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        transaction_reference = response.json()["data"]["transaction_reference"]
        await update.message.reply_text("Payment initiated successfully! Check M-Pesa for a confirmation message.")
        return transaction_reference
    else:
        await update.message.reply_text("Failed to initiate payment. Please try again later.")
        return None

async def verify_transaction_with_flask(transaction_reference: str, mpesa_confirmation_message: str):
    url = f"{FLASK_APP_URL}/verify"
    payload = {"transaction_reference": transaction_reference, "mpesa_message": mpesa_confirmation_message}
    response = requests.get(url, params=payload)
    return response.status_code == 200 and response.json().get("status") == "Completed"

def is_valid_mpesa_confirmation(mpesa_message: str) -> bool:
    return "Confirmed" in mpesa_message and "Ksh" in mpesa_message

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(file_choice_callback)],
            ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone_number)],
            ENTERING_MPESA_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_mpesa_confirmation)],
        },
        fallbacks=[CommandHandler('start', start)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
