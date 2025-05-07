import discord
import datetime
from typing import List, Optional

def create_shop_embed(
    title: str, 
    description: str, 
    detailed_info: str, 
    price: str, 
    category: str = "Asset",
    main_image_url: Optional[str] = None,
    screenshots: Optional[List[str]] = None
):
    """Create a visually appealing embed for UE5 shop items with large main image and screenshots support"""
    
    # Category-based color coding
    colors = {
        "Actor Component": 0x3498db,  # Blue
        "Weapon System": 0xe74c3c,    # Red
        "Character System": 0x2ecc71, # Green
        "Game Mode": 0xf1c40f,        # Yellow
        "Blueprint": 0x9b59b6,        # Purple
        "Material": 0xe67e22,         # Orange
        "Asset": 0x1abc9c,            # Teal (default)
    }
    
    color = colors.get(category, colors["Asset"])
    
    # Create the main embed
    embed = discord.Embed(
        title=f"🛒 {title}",
        description=f"**{description}**\n\n",
        color=color,
        timestamp=datetime.datetime.now()
    )
    
    # Set the main image as a large banner image above information
    # This creates a prominent display area for the main product image
    if main_image_url:
        embed.set_image(url=main_image_url)
    
    # Category badge
    embed.add_field(name="🏷️ Category", value=f"`{category}`", inline=True)
    
    # Add price with formatting based on price level
    price_num = price.replace("$", "").replace("€", "").strip()
    try:
        price_float = float(price_num)
        if price_float < 15:
            price_emoji = "💰"
        elif price_float < 30:
            price_emoji = "💰💰"
        else:
            price_emoji = "💰💰💰"
    except ValueError:
        price_emoji = "💰"
    
    embed.add_field(name="💲 Price", value=f"**{price_emoji} {price}**", inline=True)
    
    # Add detailed info with better formatting
    if detailed_info:
        formatted_info = detailed_info.replace("•", "• ")
        embed.add_field(name="📋 Detailed Information", value=formatted_info, inline=False)
    
    # Add UE5 logo as a small thumbnail (optional)
    # If you want to keep a small logo alongside the main image
    embed.set_thumbnail(url="https://cdn2.unrealengine.com/ue-logo-stacked-unreal-engine-w-677x545-fac11de0943f.png")
    
    # Add screenshots section if provided
    if screenshots and len(screenshots) > 0:
        screenshot_links = []
        for i, url in enumerate(screenshots, 1):
            screenshot_links.append(f"[Screenshot {i}]({url})")
        
        embed.add_field(
            name="📸 Screenshots", 
            value=" | ".join(screenshot_links),
            inline=False
        )
    
    # Add footer with branding
    embed.set_footer(text="Unreal Engine 5 Asset Shop • Professional Game Development Tools")
    
    return embed