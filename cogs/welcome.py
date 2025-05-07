import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# File to store welcome message settings
WELCOME_CONFIG_FILE = 'welcome_config.json'

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_config = self._load_config()
    
    def _load_config(self):
        """Load welcome configuration from file"""
        if os.path.exists(WELCOME_CONFIG_FILE):
            try:
                with open(WELCOME_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading welcome config: {e}")
                return {}
        return {}
    
    def _save_config(self):
        """Save welcome configuration to file"""
        try:
            with open(WELCOME_CONFIG_FILE, 'w') as f:
                json.dump(self.welcome_config, f, indent=4)
        except Exception as e:
            print(f"Error saving welcome config: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when a new member joins"""
        guild_id = str(member.guild.id)
        
        # Check if welcome messages are enabled for this guild
        if guild_id not in self.welcome_config:
            return
        
        guild_config = self.welcome_config[guild_id]
        
        # Check if we have a channel to send to
        if "channel_id" not in guild_config:
            return
            
        channel_id = int(guild_config["channel_id"])
        channel = member.guild.get_channel(channel_id)
        
        if not channel:
            return
            
        # Create welcome embed
        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=guild_config.get("message", f"Welcome {member.mention} to our server! We're glad to have you here."),
            color=discord.Color.green()
        )
        
        # Add server icon if available
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)
        
        # Add member avatar
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        
        # Add footer with join position
        member_count = len([m for m in member.guild.members if not m.bot])
        embed.set_footer(text=f"Member #{member_count} • Joined {member.joined_at.strftime('%Y-%m-%d')}")
        
        # Add info fields if configured
        if "info_fields" in guild_config:
            for field in guild_config["info_fields"]:
                embed.add_field(
                    name=field.get("name", "Information"),
                    value=field.get("value", "No information provided."),
                    inline=field.get("inline", False)
                )
        
        # Add rules field
        rules_channel = discord.utils.get(member.guild.channels, name="rules")
        if rules_channel:
            embed.add_field(
                name="📜 Server Rules",
                value=f"Please check {rules_channel.mention} to see our server rules.",
                inline=False
            )
            
        # Send welcome message
        await channel.send(content=member.mention, embed=embed)
    
    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def set_welcome_prefix(self, ctx, channel: discord.TextChannel = None):
        """Set the welcome channel for this server"""
        if not channel:
            channel = ctx.channel
            
        guild_id = str(ctx.guild.id)
        
        # Create or update welcome config
        if guild_id not in self.welcome_config:
            self.welcome_config[guild_id] = {}
            
        self.welcome_config[guild_id]["channel_id"] = channel.id
        self._save_config()
        
        await ctx.send(f"Welcome channel set to {channel.mention}!")
    
    @app_commands.command(name="setwelcome", description="Set the welcome channel and message")
    @app_commands.describe(
        channel="The channel to send welcome messages to",
        message="Custom welcome message (use {user} to mention the new member)"
    )
    @app_commands.default_permissions(administrator=True)
    async def set_welcome_slash(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel = None,
        message: str = None
    ):
        """Set welcome channel and message via slash command"""
        if not channel:
            channel = interaction.channel
            
        guild_id = str(interaction.guild_id)
        
        # Create or update welcome config
        if guild_id not in self.welcome_config:
            self.welcome_config[guild_id] = {}
            
        self.welcome_config[guild_id]["channel_id"] = channel.id
        
        if message:
            # Replace {user} with mention placeholder
            message = message.replace("{user}", "{}")
            self.welcome_config[guild_id]["message"] = message
            
        self._save_config()
        
        await interaction.response.send_message(
            f"Welcome channel set to {channel.mention}!" + 
            (f"\nCustom message set." if message else ""),
            ephemeral=True
        )
        
    @app_commands.command(name="testwelcome", description="Test the welcome message")
    @app_commands.default_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        """Test the welcome message"""
        # Simulate the member join event for the command user
        await self.on_member_join(interaction.user)
        await interaction.response.send_message("Test welcome message sent!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))