import os
from dotenv import load_dotenv
import requests
# import telebot
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()
BOT_TOKEN = os.environ['BOT_TOKEN']
# bot = telebot.TeleBot(BOT_TOKEN)
defaultRegion = ""

twoHourForecast = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"

MENU, OPTION1, OPTION2, OPTION3 = range(4)

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def return_weather(update: Update, context: CallbackContext):
    text = "What region are you interested in?\nChoose one: \n"
    
    try:
        response = requests.get(twoHourForecast)
        if response.status_code == 200:
            posts = response.json()
            availableRegions = posts["data"]["items"][0]["forecasts"]
            context.user_data['availableRegions'] = availableRegions
            text += "\n".join(["/" + item["area"].replace(" ", "") for item in availableRegions])
            
            # Determine whether the update is a message or a callback query
            message = update.message or update.callback_query.message
            await message.reply_text(text)
            return OPTION1
        else:
            message = update.message or update.callback_query.message
            await message.reply_text("Apologies. Weather forecast not working right now.")
            return MENU
    except Exception as e:
        message = update.message or update.callback_query.message
        await message.reply_text(str(e))
        return MENU
        
async def region_handler(update: Update, context: CallbackContext):
    areaChosen = update.message.text.strip("/").lower()
    availableRegions = context.user_data.get('availableRegions', [])
    
    for area in availableRegions:
        if areaChosen.lower().replace("/", "") in area["area"].lower().replace(" ", ""):
            await update.message.reply_text(f'Weather at {area["area"]} is {area["forecast"]}')
            return MENU
    else:
        if areaChosen == "cancel":
            return MENU
        await update.message.reply_text("Region selected is not a valid one")
        return OPTION1

async def weather_default(update: Update, context: CallbackContext):
    defaultRegion = context.user_data.get('defaultRegion')
    if not defaultRegion:
        message = (
            update.message or update.callback_query.message
        )  # Handle both message and callback_query contexts
        await message.reply_text("Please set a default region first.")
        return MENU

    try:
        response = requests.get(twoHourForecast)
        if response.status_code == 200:
            posts = response.json()
            availableRegions = posts["data"]["items"][0]["forecasts"]

            for area in availableRegions:
                if defaultRegion.lower().replace("/", "").replace(" ", "") in area["area"].lower().replace(" ", ""):
                    message = (
                        update.message or update.callback_query.message
                    )
                    await message.reply_text("Weather at " + area["area"] + " is " + area["forecast"])
                    return MENU
            else:
                message = (
                    update.message or update.callback_query.message
                )
                await message.reply_text("Default region " + defaultRegion + " is not a valid one")
                return MENU
        else:
            message = (
                update.message or update.callback_query.message
            )
            await message.reply_text("Apologies. Weather forecast not working right now.")
            return MENU
    except Exception as e:
        message = (
            update.message or update.callback_query.message
        )
        await message.reply_text(str(e))
        return MENU


    
async def set_default_region(update: Update, context: CallbackContext):
    defaultRegion = update.message.text
    context.user_data['defaultRegion'] = defaultRegion
    await update.message.reply_text("Default area set to " + defaultRegion)
    return MENU
    
    
async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Get Weather", callback_data="weather")],
        [InlineKeyboardButton("Set Default Region", callback_data="setDefaultR")],
        [InlineKeyboardButton("Get Weather of Default Region", callback_data="weatherD")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome. There are the current options:", reply_markup=reply_markup
    )
    return MENU

async def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "weather":
        await return_weather(update, context)
        return OPTION1
    elif query.data == "setDefaultR":
        await query.edit_message_text(text="Please type in your default region.")
        return OPTION2
    elif query.data == "weatherD":
        await weather_default(update, context)
        return OPTION3
    else:
        await query.edit_message_text(text=query.data)
        return MENU

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


def main():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(10)
        .write_timeout(10)
        .concurrent_updates(True)
        .build()
    )
    
    conv_handler = ConversationHandler(
        entry_points = [CommandHandler("start", start)],
        states = {
            MENU: [CallbackQueryHandler(button)],
            OPTION1: [
                CommandHandler("weather", return_weather),
                # MessageHandler(filters.COMMAND, region_handler),
                ],
            OPTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_default_region)], 
            OPTION3: [CommandHandler("weatherD", weather_default)], 
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("setDefault", set_default_region))
    application.add_handler(CommandHandler("weather", return_weather))
    application.add_handler(CommandHandler("weatherD", weather_default))
    application.add_handler(MessageHandler(filters.COMMAND, region_handler))

    application.run_polling()
    
main()
