import os
import logging
import json
import time
import base64
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = "7480076460:AAGieUKKaivtNGoMDSVKeMBuMOICJ9IKJgQ"  # Your bot token
PAYHERO_API_URL = "https://backend.payhero.co.ke/api/v2/payments"
API_USERNAME = "5iOsVi1JBm2fDQJl5LPD"
API_PASSWORD = "vNxb1zHkPV2tYro4SgRDXhTtWBEr8R46EQiBUvkD"

# Load file links from JSON
def load_links():
    """Load file links from links.json."""
    with open('links.json', 'r') as file:
        return json.load(file)

# Load the links into variables
links = load_links()
FILE_LINKS_10_DAYS = links["HTTP_10_DAYS"]
FILE_LINKS_14_DAYS = links["HTTP_14_DAYS"]

# Store the current index of the link sent for each file type
current_link_index = {
    "HTTP_10_DAYS": 0,
    "HTTP_14_DAYS": 0,
}

# Store sent config links and confirmation status for each user
user_sent_links = {}

# Track used M-Pesa confirmation messages globally
used_confirmation_messages = set()

# Define states for conversation
CHOOSING_TYPE, ENTERING_PHONE, ENTERING_MPESA_CONFIRMATION = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the bot and sends the welcome message"""
    keyboard = [
        [InlineKeyboardButton("HTTP Injector 10 Days - 80KES", callback_data="HTTP_10_DAYS")],
        [InlineKeyboardButton("HTTP Injector 14 Days - 100KES", callback_data="HTTP_14_DAYS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to EMMKASH-TECH files generator bot:🤖", reply_markup=reply_markup)
    return CHOOSING_TYPE

async def file_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the file type choice and asks for the phone number"""
    query = update.callback_query
    await query.answer()

    selected_package = query.data
    context.user_data["selected_package"] = selected_package
    await query.message.reply_text(f"You selected {selected_package.replace('_', ' ').title()}. Please enter your phone number:")
    return ENTERING_PHONE

async def enter_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles phone number input and proceeds with the payment"""
    phone_number = update.message.text
    context.user_data["phone_number"] = phone_number

    selected_package = context.user_data["selected_package"]

    # Initiate STK Push
    transaction_id = await initiate_stk_push(phone_number, 80 if selected_package == "HTTP_10_DAYS" else 100, update)

    # Store transaction ID in user data
    context.user_data["transaction_id"] = transaction_id

    await update.message.reply_text("Payment initiated! Please enter the full M-Pesa confirmation message you received:✅")
    return ENTERING_MPESA_CONFIRMATION

async def enter_mpesa_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles M-Pesa confirmation message input and sends the config link."""
    mpesa_confirmation_message = update.message.text
    selected_package = context.user_data["selected_package"]
    user_id = update.effective_user.id
    transaction_id = context.user_data["transaction_id"]
    user_phone_number = context.user_data["phone_number"]

    # Validate the confirmation message format
    if not is_valid_mpesa_confirmation(mpesa_confirmation_message):
        await update.message.reply_text("Invalid M-Pesa confirmation message format. Please try again.")
        return ENTERING_MPESA_CONFIRMATION

    # Check if the user has already confirmed for this package
    if user_id not in user_sent_links:
        user_sent_links[user_id] = {"HTTP_10_DAYS": False, "HTTP_14_DAYS": False}

    # Check if confirmation message has been used before
    if mpesa_confirmation_message in used_confirmation_messages:
        await update.message.reply_text("This M-Pesa confirmation message has already been used. Please verify your payment or contact support.")
        return ENTERING_MPESA_CONFIRMATION

    # Check payment status from PayHero
    payment_status, payment_phone_number = await check_payment_status(transaction_id)
    if payment_status == "successful":
        if payment_phone_number == user_phone_number:
            if "DUKE EMMANUEL KIRERA-7." in mpesa_confirmation_message and not user_sent_links[user_id][selected_package]:
                # Mark the message as used and store the confirmation for the user
                used_confirmation_messages.add(mpesa_confirmation_message)
                user_sent_links[user_id][selected_package] = True

                # Get the current link index for the selected package
                if selected_package == "HTTP_10_DAYS":
                    link = FILE_LINKS_10_DAYS[current_link_index[selected_package]]
                    current_link_index[selected_package] = (current_link_index[selected_package] + 1) % len(FILE_LINKS_10_DAYS)
                else:
                    link = FILE_LINKS_14_DAYS[current_link_index[selected_package]]
                    current_link_index[selected_package] = (current_link_index[selected_package] + 1) % len(FILE_LINKS_14_DAYS)

                # Send the configuration link
                await update.message.reply_text(f"Payment confirmed. Here is your config link: {link}")

                # Send guidelines
                await update.message.reply_text(
                    "GUIDELINES TO FOLLOW:\n\n"
                    "1. SEARCH FOR A WORKING IP (10.60s or 10.200s)\n"
                    "   Example IPs: 10.244; 10.217; 10.216; 10.247; 10.60; 10.246; 10.245; 10.244; 10.209; 10.62; 10.213; 10.210; 10.212; 10.61\n\n"
                    "2. CONNECT THE TWO HTTP CUSTOM FILES EVERYDAY ONCE IN A DAY:\n"
                    "   - File 1: 45MB\n"
                    "   - File 2: 22MB\n"
                    "   - If you have Roodito data, connect File 1 first, then HTTP Injector.\n\n"
                    "   Get the 2 HTTP Custom files here: https://t.me/emmkashtech2/2884?single\n\n"
                    "3. SEARCH FOR ANOTHER IP (must be from the list in Step 1).\n\n"
                    "4. CONNECT HTTP Injector for unlimited access.\n\n"
                    "For help, click here: @emmkash\n\n"
                )

                # Offer the user to choose another file
                await update.message.reply_text("Choose another file if needed:", reply_markup=InlineKeyboardMarkup([ 
                    [InlineKeyboardButton("HTTP Injector 10 Days", callback_data="HTTP_10_DAYS")],
                    [InlineKeyboardButton("HTTP Injector 14 Days", callback_data="HTTP_14_DAYS")],
                ]))
                return CHOOSING_TYPE
            elif user_sent_links[user_id][selected_package]:
                await update.message.reply_text("You have already confirmed the payment and received the link for this package.")
                return CHOOSING_TYPE
            else:
                await update.message.reply_text("The message you provided does not appear to be a valid M-Pesa confirmation. Please try again.")
                return ENTERING_MPESA_CONFIRMATION
        else:
            await update.message.reply_text("The phone number associated with this payment does not match the one you provided. Please verify your payment or contact support.")
            return ENTERING_MPESA_CONFIRMATION
    else:
        await update.message.reply_text("Payment is still pending. Please wait for confirmation.")
        return ENTERING_MPESA_CONFIRMATION

async def initiate_stk_push(phone_number: str, amount: int, update: Update):
    """Initiate STK Push payment via PayHero API."""
    payload = {
        "amount": amount,
        "phone_number": phone_number,
        "channel_id": 852,
        "provider": "m-pesa",
        "external_reference": "INV-009",
        "callback_url": "https://callback1-21e1c9a49f0d.herokuapp.com/billing/callback1"
    }

    auth_token = base64.b64encode(f"{API_USERNAME}:{API_PASSWORD}".encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_token}"
    }

    response = requests.post(PAYHERO_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        transaction_id = response.json().get("transaction_id")
        await update.message.reply_text(f"STK Push initiated successfully. Transaction ID: {transaction_id}")
        return transaction_id
    else:
        await update.message.reply_text("Failed to initiate payment. Please try again.")
        return None

async def check_payment_status(transaction_id: str):
    """Check the payment status via PayHero API."""
    url = f"{PAYHERO_API_URL}/{transaction_id}"
    auth_token = base64.b64encode(f"{API_USERNAME}:{API_PASSWORD}".encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("status"), data.get("phone_number")  # Assuming "phone_number" is returned with the status
    else:
        logger.error(f"Error checking payment status: {response.text}")
        return None, None

def is_valid_mpesa_confirmation(message: str) -> bool:
    """Validate the M-Pesa confirmation message format."""
    keywords = ["Payment", "Received", "of", "Ksh"]
    return all(keyword in message for keyword in keywords)

def main():
    """Run the bot."""
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
