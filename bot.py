import os
from dotenv import load_dotenv
import requests
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()
BOT_TOKEN = os.environ['BOT_TOKEN']
defaultRegion = ""

twoHourForecast = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"

MENU, AWAITING_REGION, AWAITING_DEF_REGION, OPTION3 = range(4)

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
            return AWAITING_REGION
        else:
            message = update.message or update.callback_query.message
            await message.reply_text("Apologies. Weather forecast not working right now.")
            return MENU
    except Exception as e:
        message = update.message or update.callback_query.message
        await message.reply_text(str(e))
        return MENU
        
async def region_handler(update: Update, context: CallbackContext):
    areaChosen = update.message.text.strip("/").lower().replace(" ", "")
    availableRegions = context.user_data.get('availableRegions', [])
    
    for area in availableRegions:
        if areaChosen in area["area"].lower().replace(" ", ""):
            await update.message.reply_text(f'Weather at {area["area"]} is {area["forecast"]}')
            return AWAITING_REGION
    else:
        if areaChosen == "cancel":
            return MENU
        await update.message.reply_text("Region selected is not a valid one")
        return AWAITING_REGION

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


    
async def set_default_region_1(update: Update, context: CallbackContext):
    message = update.message or update.callback_query.message
    await message.reply_text("Please input your chosen default region.")
    return AWAITING_DEF_REGION

async def set_default_region_2(update: Update, context: CallbackContext):
    print(update.message.text)
    message = update.message or update.callback_query.message
    defaultRegion = message.text.strip("/")
    context.user_data['defaultRegion'] = defaultRegion
    await message.reply_text("Default area set to " + defaultRegion)
    return MENU
    
    
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Welcome. There are the current command: /weather, /setDef, /weatherD"
    )
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
    
    weather_handler = ConversationHandler(
        entry_points = [CommandHandler("weather", return_weather)],
        states = {
            AWAITING_REGION: [MessageHandler(filters.TEXT | filters.COMMAND, region_handler)], 
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    def_weather_handler = ConversationHandler(
        entry_points = [CommandHandler("setDef", set_default_region_1)],
        states = {
            AWAITING_DEF_REGION: [MessageHandler(filters.TEXT | filters.COMMAND, set_default_region_2)], 
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(weather_handler)
    application.add_handler(def_weather_handler)
    application.add_handler(CommandHandler("weatherD", weather_default))


    application.run_polling()
    
main()
