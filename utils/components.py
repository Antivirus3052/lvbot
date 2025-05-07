import discord
from discord.ui import Button, View
import asyncio

class ItemView(View):
    """Interactive buttons for shop items with ticket system for purchases"""
    
    def __init__(self, *, timeout=180, item_title=None, seller_id=None):
        super().__init__(timeout=timeout)
        self.item_title = item_title if item_title else "Product"
        self.seller_id = seller_id  # Store the seller's ID
        
        # Purchase button
        purchase_button = Button(
            style=discord.ButtonStyle.success,
            label="Purchase",
            emoji="💳",
            custom_id="purchase_item"
        )
        purchase_button.callback = self.purchase_callback
        self.add_item(purchase_button)
        
        # More info button
        info_button = Button(
            style=discord.ButtonStyle.primary,
            label="More Info",
            emoji="ℹ️",
            custom_id="more_info"
        )
        info_button.callback = self.info_callback
        self.add_item(info_button)
    
    async def purchase_callback(self, interaction: discord.Interaction):
        """Handle purchase button click - create ticket channel"""
        
        # Check permissions
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Error: Bot doesn't have permission to create channels. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        user = interaction.user
        guild = interaction.guild
        
        # Format safe channel name (lowercase, replace spaces with hyphens, max 100 chars)
        safe_item_name = self.item_title.lower().replace(" ", "-")[:50]
        channel_name = f"purchase-{safe_item_name}-{user.name}"
        channel_name = ''.join(c for c in channel_name if c.isalnum() or c in ['-', '_'])
        
        try:
            # Create category if it doesn't exist
            category = discord.utils.get(guild.categories, name="Asset Shop Tickets")
            if not category:
                category = await guild.create_category(
                    name="Asset Shop Tickets",
                    reason="Asset Shop Ticket System"
                )
            
            # Set up permissions for the new channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Try to find seller/admin role
            admin_role = discord.utils.get(guild.roles, name="Seller") or discord.utils.get(guild.roles, name="Admin")
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            # Create the ticket channel
            channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category,
                topic=f"Purchase ticket for {self.item_title} | Customer: {user.name}"
            )
            
            # Send confirmation message to user
            await interaction.response.send_message(
                f"Purchase ticket created! Please check {channel.mention}.",
                ephemeral=True
            )
            
            # Send welcome message in the new channel
            embed = discord.Embed(
                title=f"Purchase: {self.item_title}",
                description=f"Thank you for your interest in purchasing this item!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Next Steps",
                value="A seller will be with you shortly to complete your purchase.",
                inline=False
            )
            embed.add_field(
                name="Customer",
                value=f"{user.mention} ({user.name})",
                inline=True
            )
            embed.set_footer(text="Unreal Engine 5 Asset Shop • Thank you for your purchase!")
            
            await channel.send(f"{user.mention}", embed=embed)
            
            # Ping seller/admin role if exists
            if admin_role:
                await channel.send(f"{admin_role.mention} - New purchase ticket opened!")
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "Error: I don't have permission to create channels. Please contact an administrator.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while creating your ticket: {str(e)}",
                ephemeral=True
            )
    
    async def info_callback(self, interaction: discord.Interaction):
        """Handle more info button click"""
        await interaction.response.send_message(
            "For more information about this item, please contact the seller directly.",
            ephemeral=True
        )