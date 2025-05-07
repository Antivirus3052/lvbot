import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import json
import os

# Config file to store feedback channel IDs
FEEDBACK_CONFIG_FILE = 'feedback_config.json'

class FeedbackModal(Modal):
    """Modal for collecting user feedback"""
    
    def __init__(self, feedback_channel_id: int):
        super().__init__(title="Provide Feedback")
        self.feedback_channel_id = feedback_channel_id
        
        # Title field
        self.title_input = TextInput(
            label="Title",
            placeholder="Brief summary of your feedback",
            style=discord.TextStyle.short,
            max_length=100,
            required=True
        )
        self.add_item(self.title_input)
        
        # Detailed feedback field
        self.feedback_input = TextInput(
            label="Your Feedback",
            placeholder="Please share your detailed feedback, suggestions, or experience...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        self.add_item(self.feedback_input)
        
        # Rating field
        self.rating_input = TextInput(
            label="Rating (1-5 stars)",
            placeholder="Enter a rating from 1-5",
            style=discord.TextStyle.short,
            max_length=1,
            required=True
        )
        self.add_item(self.rating_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process the submitted feedback"""
        # Validate rating
        try:
            rating = int(self.rating_input.value)
            if rating < 1 or rating > 5:
                await interaction.response.send_message("Please provide a rating between 1 and 5.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Please provide a numeric rating between 1 and 5.", ephemeral=True)
            return
        
        # Get the feedback channel
        feedback_channel = interaction.client.get_channel(self.feedback_channel_id)
        if not feedback_channel:
            await interaction.response.send_message(
                "Feedback channel not found. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        # Create stars representation
        stars = "⭐" * rating
        
        # Create feedback embed
        embed = discord.Embed(
            title=f"📝 {self.title_input.value}",
            description=self.feedback_input.value,
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_author(
            name=f"Feedback from {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        embed.add_field(name="Rating", value=f"{stars} ({rating}/5)", inline=False)
        
        # Send feedback to the designated channel
        try:
            await feedback_channel.send(embed=embed)
            await interaction.response.send_message(
                "Thank you for your feedback! It has been submitted successfully.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Error submitting feedback: {str(e)}",
                ephemeral=True
            )

class FeedbackView(View):
    """View with feedback button"""
    
    def __init__(self, feedback_channel_id: int):
        super().__init__(timeout=None)  # Persistent view
        self.feedback_channel_id = feedback_channel_id
        
        # Add feedback button
        feedback_button = Button(
            style=discord.ButtonStyle.primary,
            label="Give Feedback",
            emoji="📝",
            custom_id=f"feedback_button_{feedback_channel_id}"
        )
        feedback_button.callback = self.feedback_callback
        self.add_item(feedback_button)
    
    async def feedback_callback(self, interaction: discord.Interaction):
        """Open feedback modal when button is clicked"""
        modal = FeedbackModal(self.feedback_channel_id)
        await interaction.response.send_modal(modal)

class FeedbackSystem(commands.Cog):
    """System for collecting user feedback"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = self._load_config()
    
    def _load_config(self):
        """Load feedback configuration from file"""
        if os.path.exists(FEEDBACK_CONFIG_FILE):
            try:
                with open(FEEDBACK_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading feedback config: {e}")
                return {}
        return {}
    
    def _save_config(self):
        """Save feedback configuration to file"""
        try:
            with open(FEEDBACK_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving feedback config: {e}")
    
    @commands.command(name="setfeedback")
    @commands.has_permissions(administrator=True)
    async def set_feedback_prefix(self, ctx, feedback_channel: discord.TextChannel = None):
        """Set up a feedback panel in the current channel"""
        if not feedback_channel:
            await ctx.send("Please specify a channel to receive feedback.")
            return
        
        # Store configuration
        guild_id = str(ctx.guild.id)
        self.config[guild_id] = {
            "panel_channel_id": ctx.channel.id,
            "feedback_channel_id": feedback_channel.id
        }
        self._save_config()
        
        # Create the panel
        await self._create_feedback_panel(ctx.channel, feedback_channel, ctx.author)
        await ctx.send(f"Feedback panel created! Feedback will be sent to {feedback_channel.mention}")
    
    @app_commands.command(name="setfeedback", description="Set up a feedback panel")
    @app_commands.describe(
        feedback_channel="Channel where feedback will be posted",
        title="Title for the feedback panel",
        description="Description for the feedback panel"
    )
    @app_commands.default_permissions(administrator=True)
    async def set_feedback_slash(
        self,
        interaction: discord.Interaction,
        feedback_channel: discord.TextChannel,
        title: str = "We Value Your Feedback",
        description: str = "Please click the button below to share your thoughts and suggestions with us."
    ):
        """Set up a feedback panel using slash command"""
        # Store configuration
        guild_id = str(interaction.guild_id)
        self.config[guild_id] = {
            "panel_channel_id": interaction.channel_id,
            "feedback_channel_id": feedback_channel.id
        }
        self._save_config()
        
        # Create the panel
        await self._create_feedback_panel(
            interaction.channel, 
            feedback_channel, 
            interaction.user,
            title=title,
            description=description
        )
        await interaction.response.send_message(
            f"Feedback panel created! Feedback will be sent to {feedback_channel.mention}",
            ephemeral=True
        )
    
    async def _create_feedback_panel(
        self,
        panel_channel,
        feedback_channel,
        creator,
        title="We Value Your Feedback",
        description="Please click the button below to share your thoughts and suggestions with us."
    ):
        """Create a feedback panel in the specified channel"""
        # Create embed for feedback panel
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="How It Works",
            value="Click the button below to open a feedback form. Your feedback will be anonymous to other users and only visible to our team.",
            inline=False
        )
        
        # Add server icon if available
        if hasattr(panel_channel, 'guild') and panel_channel.guild.icon:
            embed.set_thumbnail(url=panel_channel.guild.icon.url)
        
        embed.set_footer(text=f"Feedback System • Created by {creator.name}")
        
        # Create button view
        view = FeedbackView(feedback_channel.id)
        
        # Send the panel
        await panel_channel.send(embed=embed, view=view)
        return embed
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Register persistent feedback views when bot starts"""
        for guild_id, guild_config in self.config.items():
            if "feedback_channel_id" in guild_config:
                self.bot.add_view(FeedbackView(guild_config["feedback_channel_id"]))

async def setup(bot):
    await bot.add_cog(FeedbackSystem(bot))