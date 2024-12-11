from django.core.management.base import BaseCommand
import asyncio
from bot.bot import main  # Import the main function from bot.py

class Command(BaseCommand):
    help = "Run the Telegram bot"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting the Telegram bot...\n")
        # Run the bot's main function asynchronously
        asyncio.run(main())  # Starts the bot asynchronously
