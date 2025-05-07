import discord
from discord import app_commands
from discord.ext import commands
from utils.ticket_system import CreateTicketView

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setticket")
    @commands.has_permissions(administrator=True)
    async def set_ticket_prefix(self, ctx):
        """Convert the current channel to a ticket channel with a panel"""
        await self._create_ticket_panel(ctx.channel, ctx.author)
        await ctx.send("Ticket panel created in this channel!")
        
    @app_commands.command(name="setticket", description="Create a ticket panel in the current channel")
    @app_commands.describe(
        title="The title for the ticket panel",
        description="The description for the ticket panel"
    )
    @app_commands.default_permissions(administrator=True)
    async def set_ticket_slash(
        self,
        interaction: discord.Interaction,
        title: str = "Support Tickets",
        description: str = "Need help? Click the button below to create a ticket!"
    ):
        """Create a ticket panel in the current channel"""
        embed = await self._create_ticket_panel(
            interaction.channel,
            interaction.user,
            title=title,
            description=description
        )
        await interaction.response.send_message("Ticket panel created in this channel!", ephemeral=True)
        
    async def _create_ticket_panel(
        self,
        channel,
        user,
        title="Support Tickets",
        description="Need help? Click the button below to create a ticket!"
    ):
        """Create a ticket panel in the specified channel"""
        # Create embed for ticket panel
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        
        # Add info about how tickets work
        embed.add_field(
            name="How It Works",
            value="When you create a ticket, a private channel will be created where you can discuss your issue with our staff.",
            inline=False
        )
        
        embed.add_field(
            name="Response Time",
            value="Our team typically responds within 24 hours.",
            inline=False
        )
        
        # Add UE5 logo or server icon
        if hasattr(channel, 'guild') and channel.guild.icon:
            embed.set_thumbnail(url=channel.guild.icon.url)
        else:
            embed.set_thumbnail(url="https://cdn2.unrealengine.com/ue-logo-stacked-unreal-engine-w-677x545-fac11de0943f.png")
            
        embed.set_footer(text=f"Ticket System • Created by {user.name}")
        
        # Create button view
        view = CreateTicketView()
        
        # Send the panel
        await channel.send(embed=embed, view=view)
        return embed

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))