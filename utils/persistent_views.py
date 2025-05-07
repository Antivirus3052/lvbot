import discord
from discord.ext import commands
import json
import os
from utils.ticket_system import CreateTicketView, TicketCloseButton
from cogs.feedback import FeedbackView

class PersistentViewHandler:
    """Handler for persistent views across bot restarts"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def register_views(self):
        """Register persistent views when bot starts"""
        # Add persistent ticket creation view
        self.bot.add_view(CreateTicketView())
        
        # Add persistent ticket close button
        self.bot.add_view(TicketCloseButton())
        
        # Register feedback views
        feedback_config_file = 'feedback_config.json'
        if os.path.exists(feedback_config_file):
            try:
                with open(feedback_config_file, 'r') as f:
                    feedback_config = json.load(f)
                    
                # Register each feedback view with its channel ID
                for guild_id, guild_config in feedback_config.items():
                    if "feedback_channel_id" in guild_config:
                        self.bot.add_view(FeedbackView(guild_config["feedback_channel_id"]))
            except Exception as e:
                print(f"Error loading feedback views: {e}")
        
        print("Registered persistent views")