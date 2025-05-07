import discord
from discord import app_commands
from discord.ext import commands
from utils.embed_builder import create_shop_embed
from utils.ticket_system import ItemView  # Updated import path
from typing import List, Optional

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Category choices for slash command
    CATEGORIES = [
        "Actor Component",
        "Weapon System",
        "Character System",
        "Game Mode",
        "Blueprint",
        "Material",
        "Asset"
    ]

    # Prefix command with attachment support
    @commands.command(name="additem")
    @commands.has_permissions(administrator=True)
    async def add_item_prefix(self, ctx, title: str, price: str, category: str = "Asset", *, details: str = None):
        """Add an item to the shop with image attachments
        
        Usage: #additem "Title" "$19.99" "Category" "Description\\nDetailed info"
        Then attach your images to the same message
        """
        # Parse the details parameter
        description = ""
        detailed_info = ""
        
        if details:
            # Split by custom delimiter
            parts = details.split('\\n', 1)
            description = parts[0] if parts else ""
            
            # Get detailed info if available
            if len(parts) > 1:
                detailed_info = parts[1]
        
        # Get attached images
        attachments = []
        for attachment in ctx.message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                attachments.append(attachment)
        
        main_image = attachments[0].url if attachments else None
        screenshots = [attachment.url for attachment in attachments[1:]] if len(attachments) > 1 else []
        
        # Create and send the embed
        embed = create_shop_embed(
            title=title,
            description=description,
            detailed_info=detailed_info,
            price=price,
            category=category,
            main_image_url=main_image,
            screenshots=screenshots
        )
        
        # Add interactive view with item title and seller ID
        view = ItemView(item_title=title, seller_id=ctx.author.id, price=price)
        await ctx.send(embed=embed, view=view)

    # Updated slash command with direct image upload support
    @app_commands.command(name="additem", description="Add an item to the UE5 asset shop")
    @app_commands.describe(
        title="Title of the asset",
        description="Short description of the asset",
        detailed_info="Detailed information about features and usage",
        price="Price of the asset (e.g. $19.99)",
        category="Category of the asset",
        main_image="Main image of the asset (required)",
        screenshot1="Additional screenshot 1 (optional)",
        screenshot2="Additional screenshot 2 (optional)",
        screenshot3="Additional screenshot 3 (optional)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name=cat, value=cat) for cat in CATEGORIES
    ])
    @app_commands.default_permissions(administrator=True)
    async def add_item_slash(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        price: str, 
        description: str, 
        detailed_info: str, 
        main_image: discord.Attachment,
        category: str = "Asset",
        screenshot1: Optional[discord.Attachment] = None,
        screenshot2: Optional[discord.Attachment] = None,
        screenshot3: Optional[discord.Attachment] = None
    ):
        """Add an item to the shop using slash command with direct image uploads"""
        
        # Process main image
        main_image_url = main_image.url if main_image else None
        
        # Collect screenshots
        screenshots = []
        for screenshot in [screenshot1, screenshot2, screenshot3]:
            if screenshot:
                screenshots.append(screenshot.url)
        
        # Create the embed with all the information
        embed = create_shop_embed(
            title=title,
            description=description,
            detailed_info=detailed_info,
            price=price,
            category=category,
            main_image_url=main_image_url,
            screenshots=screenshots
        )
        
        # Add interactive view with item title and seller ID
        view = ItemView(item_title=title, seller_id=interaction.user.id, price=price)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Shop(bot))