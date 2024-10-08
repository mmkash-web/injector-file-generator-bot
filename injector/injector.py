import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import requests
import base64

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = "6817650329:AAHIFSuDQ3BbS4FQjO6FOCUy20lpniH2YEc"  # Your bot token
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

# Define states for conversation
CHOOSING_TYPE, ENTERING_PHONE, ENTERING_MPESA_CONFIRMATION = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the bot and sends the welcome message"""
    keyboard = [
        [InlineKeyboardButton("HTTP Injector 10 Days-80KES", callback_data="HTTP_10_DAYS")],
        [InlineKeyboardButton("HTTP Injector 14 Days-100KES", callback_data="HTTP_14_DAYS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("WELCOME! TO EMMKASH-TECH FILES GENERATOR BOT PLEASE CHOOSE A FILE TYPE YOU WANT TO BUY:", reply_markup=reply_markup)
    return CHOOSING_TYPE

async def file_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the file type choice and asks for the phone number"""
    query = update.callback_query
    await query.answer()

    # Store the selected package in user_data
    if query.data == "HTTP_10_DAYS":
        selected_package = "HTTP_10_DAYS"
    elif query.data == "HTTP_14_DAYS":
        selected_package = "HTTP_14_DAYS"

    context.user_data["selected_package"] = selected_package
    await query.message.reply_text(f"You selected {selected_package.replace('_', ' ').title()}. Please enter your phone number:")

    return ENTERING_PHONE

async def enter_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles phone number input and proceeds with the payment"""
    phone_number = update.message.text
    context.user_data["phone_number"] = phone_number

    selected_package = context.user_data["selected_package"]

    # Initiate STK Push
    if selected_package == "HTTP_10_DAYS":
        await initiate_stk_push(phone_number, 80, update)
    else:
        await initiate_stk_push(phone_number, 100, update)

    # Ask user to enter M-Pesa confirmation message
    await update.message.reply_text("Payment initiated! Please enter the full M-Pesa confirmation message you received:")
    return ENTERING_MPESA_CONFIRMATION

async def enter_mpesa_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles M-Pesa confirmation message input and sends the config link."""
    mpesa_confirmation_message = update.message.text
    context.user_data["mpesa_confirmation_message"] = mpesa_confirmation_message

    selected_package = context.user_data["selected_package"]
    user_id = update.effective_user.id

    # Check if the user has already confirmed for this package
    if user_id not in user_sent_links:
        user_sent_links[user_id] = {"HTTP_10_DAYS": False, "HTTP_14_DAYS": False}

    # Validate the M-Pesa confirmation message and check if the user has already sent it
    if "Confirmed" in mpesa_confirmation_message and not user_sent_links[user_id][selected_package]:
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

        # Send the guidelines after sending the config link
        await update.message.reply_text(
            "GUIDELINES TO FOLLOW:\n\n"
            "1. SEARCH FOR A WORKING IP (10.60s or 10.200s)\n"
            "e.g. 10.244;10.217;10.216;10.247;10.60;10.246;10.245;10.244;10.209;10.62;\n"
            "10.213;10.210;10.212;10.61;10.246;10.216;10.247;10.60;10.246;10.245;\n"
            "10.244;10.209;10.62;10.213;10.210;10.212;10.61;10.246;10.237;10.238;10.239\n\n"
            "2. CONNECT THE TWO HTTP CUSTOM FILES EVERY DAY ONCE IN A DAY (EXHAUST THE DATA FOR THE TWO FILES).\n"
            "   FILE 1: 45MB, FILE 2: 22MB\n"
            "   IF YOU HAVE ROODITO DATA, CONNECT FILE 1 ONLY THEN HTTP INJECTOR.\n\n"
            "   GET THE 2 HTTP CUSTOM FILES HERE: https://t.me/emmkashtech2/2884?single\n\n"
            "3. SEARCH FOR ANOTHER IP (MUST BE FROM THE LIST IN STEP 1).\n\n"
            "4. CONNECT HTTP INJECTOR FOR UNLIMITED🔥🥳.\n\n"
            "FOR HELP, CLICK HERE @emmkash"
        )

        # Allow user to choose another type after payment
        await update.message.reply_text("Choose another file if needed:", reply_markup=InlineKeyboardMarkup([ 
            [InlineKeyboardButton("HTTP Injector 10 Days", callback_data="HTTP_10_DAYS")],
            [InlineKeyboardButton("HTTP Injector 14 Days", callback_data="HTTP_14_DAYS")],
        ]))
        return CHOOSING_TYPE
    elif user_sent_links[user_id][selected_package]:
        await update.message.reply_text("You have already confirmed the payment and received the link for this package. For assistance, click here @emmkash.")
        return CHOOSING_TYPE
    else:
        await update.message.reply_text("The message you provided does not appear to be a valid M-Pesa confirmation. Please try again:")
        return ENTERING_MPESA_CONFIRMATION

async def initiate_stk_push(phone_number: str, amount: int, update: Update):
    """Initiate STK Push payment via PayHero API."""
    payload = {
        "amount": amount,
        "phone_number": phone_number,
        "channel_id": 852,
        "provider": "m-pesa",
        "external_reference": "INV-009",
        "callback_url": "https://softcash.co.ke/billing/callbackurl.php"
    }

    # Create the Basic Auth header
    auth_token = base64.b64encode(f"{API_USERNAME}:{API_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_token}"}

    try:
        response = requests.post(PAYHERO_API_URL, json=payload, headers=headers)
        
        logger.info(f"Payment response: {response.json()}")

        if response.status_code == 200 and response.json().get('success'):
            await update.message.reply_text("STK push sent. Please enter the M-Pesa confirmation message you received.")
        else:
            await update.message.reply_text("Check the M-Pesa pop-up to enter your PIN🥳✅.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        await update.message.reply_text("An error occurred while processing your payment.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the current operation"""
    await update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

def main():
    """Run the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation handler for the bot
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

if __name__ == '__main__':
    main()
