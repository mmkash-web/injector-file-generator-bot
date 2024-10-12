import os
import logging
import json
import time
import base64
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot and API credentials
BOT_TOKEN = "7480076460:AAGieUKKaivtNGoMDSVKeMBuMOICJ9IKJgQ"
PAYHERO_API_URL = "https://backend.payhero.co.ke/api/v2/payments"
API_USERNAME = "YOUR_API_USERNAME"
API_PASSWORD = "YOUR_API_PASSWORD"
FLASK_APP_URL = "https://callback1-21e1c9a49f0d.herokuapp.com/"

# Conversation states
CHOOSING_TYPE, ENTERING_PHONE, ENTERING_MPESA_CONFIRMATION = range(3)

# Load file links from JSON
def load_links():
    with open('links.json', 'r') as file:
        return json.load(file)

links = load_links()
FILE_LINKS = {
    "HTTP_10_DAYS": links["HTTP_10_DAYS"],
    "HTTP_14_DAYS": links["HTTP_14_DAYS"]
}
current_link_index = {"HTTP_10_DAYS": 0, "HTTP_14_DAYS": 0}
used_transaction_references = set()
user_sent_links = {}

# Bot commands and handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("HTTP Injector 10 Days - 80KES", callback_data="HTTP_10_DAYS")],
        [InlineKeyboardButton("HTTP Injector 14 Days - 100KES", callback_data="HTTP_14_DAYS")],
        [InlineKeyboardButton("Cancel", callback_data="CANCEL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to EMMKASH-TECH files generator bot 🤖", reply_markup=reply_markup)
    return CHOOSING_TYPE

async def file_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_package = query.data
    context.user_data["selected_package"] = selected_package
    
    if selected_package == "CANCEL":
        return await cancel(update, context)

    await query.message.reply_text(f"You selected {selected_package.replace('_', ' ').title()}. Please enter your phone number:")
    return ENTERING_PHONE

async def enter_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    context.user_data["phone_number"] = phone_number
    selected_package = context.user_data["selected_package"]
    amount = 80 if selected_package == "HTTP_10_DAYS" else 100

    transaction_reference = await initiate_stk_push(phone_number, amount, update)
    context.user_data["transaction_reference"] = transaction_reference
    await update.message.reply_text("Payment initiated! Please enter the M-Pesa confirmation message you received.")
    return ENTERING_MPESA_CONFIRMATION

async def enter_mpesa_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation_message = update.message.text
    selected_package = context.user_data["selected_package"]
    user_id = update.effective_user.id

    if not is_valid_mpesa_confirmation(confirmation_message):
        await update.message.reply_text("Invalid M-Pesa confirmation message. Please try again.")
        return ENTERING_MPESA_CONFIRMATION

    transaction_reference = extract_transaction_reference(confirmation_message)

    if transaction_reference in used_transaction_references:
        await update.message.reply_text("This transaction has already been used. Please verify your payment.")
        return ENTERING_MPESA_CONFIRMATION

    if await verify_transaction_with_flask(transaction_reference, confirmation_message):
        await confirm_and_send_link(update, user_id, selected_package, transaction_reference)
        return CHOOSING_TYPE
    else:
        await update.message.reply_text("Transaction verification failed. Please try again.")
        return ENTERING_MPESA_CONFIRMATION

# Helper functions
async def confirm_and_send_link(update, user_id, selected_package, transaction_reference):
    used_transaction_references.add(transaction_reference)
    user_sent_links[user_id] = True

    link_list = FILE_LINKS[selected_package]
    link = link_list[current_link_index[selected_package]]
    current_link_index[selected_package] = (current_link_index[selected_package] + 1) % len(link_list)

    await update.message.reply_text(f"Payment confirmed. Here is your config link: {link}")

async def initiate_stk_push(phone_number, amount, update):
    payload = {
        "amount": amount,
        "phone_number": phone_number,
        "channel_id": 852,
        "provider": "m-pesa",
        "external_reference": "INV-009",
        "callback_url": FLASK_APP_URL,
    }
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{API_USERNAME}:{API_PASSWORD}'.encode()).decode()}",
        "Content-Type": "application/json",
    }
    response = requests.post(PAYHERO_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        transaction_reference = response.json()["data"]["transaction_reference"]
        await update.message.reply_text("Payment initiated successfully.")
        return transaction_reference
    else:
        await update.message.reply_text("Failed to initiate payment.")
        return None

def is_valid_mpesa_confirmation(message):
    return bool(re.search(r"Transaction ID: (\w+)", message))

def extract_transaction_reference(message):
    match = re.search(r"Transaction ID: (\w+)", message)
    return match.group(1) if match else ""

async def verify_transaction_with_flask(transaction_reference, confirmation_message):
    try:
        response = requests.post(FLASK_APP_URL, json={
            "transaction_reference": transaction_reference,
            "confirmation_message": confirmation_message
        })
        return response.status_code == 200 and response.json().get("status") == "success"
    except Exception as e:
        logger.error(f"Error verifying transaction: {e}")
        return False

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Operation canceled.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(file_choice_callback)],
            ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone_number)],
            ENTERING_MPESA_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_mpesa_confirmation)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
