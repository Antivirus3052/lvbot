import discord
from discord.ui import Button, View
from typing import Optional, Dict, Any
import re

# Use a price parsing regex to extract numeric value from price strings
PRICE_REGEX = r'[\$€£]?\s*(\d+(?:\.\d+)?)'

class TicketCloseButton(View):
    """Button for closing tickets"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent button
        
        # Add close ticket button
        close_button = Button(
            style=discord.ButtonStyle.danger,
            label="Close Ticket",
            emoji="🔒",
            custom_id="close_ticket"
        )
        close_button.callback = self.close_ticket_callback
        self.add_item(close_button)
    
    async def close_ticket_callback(self, interaction: discord.Interaction):
        """Handle ticket closing"""
        # Check if user has permission to close the ticket
        channel = interaction.channel
        
        # Check if this is actually a ticket channel
        if not channel.name.startswith(("ticket-", "purchase-")):
            await interaction.response.send_message(
                "This command can only be used in ticket channels!",
                ephemeral=True
            )
            return
        
        # Send closing message
        embed = discord.Embed(
            title="Ticket Closing",
            description="This ticket is being closed...",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
        
        # Archive the channel (move to archived category or delete based on preference)
        try:
            # Find or create archive category
            archive_category = discord.utils.get(interaction.guild.categories, name="Archived Tickets")
            if not archive_category:
                archive_category = await interaction.guild.create_category(
                    name="Archived Tickets",
                    reason="Ticket Archive System"
                )
            
            # Move to archive
            await channel.edit(
                category=archive_category,
                name=f"closed-{channel.name}",
                reason=f"Ticket closed by {interaction.user.name}"
            )
            
            # Lock the channel
            await channel.set_permissions(
                interaction.guild.default_role,
                send_messages=False,
                read_messages=False
            )
            
            # Final message
            embed = discord.Embed(
                title="Ticket Closed",
                description=f"This ticket has been closed by {interaction.user.mention}",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send(
                "Error: I don't have permission to archive this channel.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred: {str(e)}",
                ephemeral=True
            )


class CreateTicketView(View):
    """View with button to create a support ticket"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent button
        
        # Create ticket button
        ticket_button = Button(
            style=discord.ButtonStyle.primary,
            label="Create Ticket",
            emoji="🎫",
            custom_id="create_ticket"
        )
        ticket_button.callback = self.create_ticket_callback
        self.add_item(ticket_button)
    
    async def create_ticket_callback(self, interaction: discord.Interaction):
        """Handle ticket creation button click"""
        
        # Check permissions
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Error: Bot doesn't have permission to create channels. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        user = interaction.user
        guild = interaction.guild
        
        # Format channel name
        channel_name = f"ticket-{user.name}"
        channel_name = ''.join(c for c in channel_name if c.isalnum() or c in ['-', '_'])
        
        try:
            # Create category if it doesn't exist
            category = discord.utils.get(guild.categories, name="Support Tickets")
            if not category:
                category = await guild.create_category(
                    name="Support Tickets",
                    reason="Support Ticket System"
                )
            
            # Set up permissions for the new channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Try to find support/admin role
            support_role = discord.utils.get(guild.roles, name="Support") or discord.utils.get(guild.roles, name="Admin")
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            # Check if ticket already exists
            existing_channel = discord.utils.get(category.channels, name=channel_name)
            if existing_channel:
                await interaction.response.send_message(
                    f"You already have an open ticket at {existing_channel.mention}",
                    ephemeral=True
                )
                return
            
            # Create the ticket channel
            channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category,
                topic=f"Support ticket for {user.name} | Created: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Send confirmation to user
            await interaction.response.send_message(
                f"Your ticket has been created at {channel.mention}",
                ephemeral=True
            )
            
            # Send welcome message in the ticket channel
            embed = discord.Embed(
                title="New Support Ticket",
                description=f"Welcome {user.mention}!\n\nPlease describe your issue or question in detail, and a staff member will assist you shortly.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Ticket Creator",
                value=f"{user.mention} ({user.name})",
                inline=True
            )
            embed.add_field(
                name="Created At",
                value=discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                inline=True
            )
            embed.set_footer(text="UE5 Asset Shop Support • Thank you for your patience")
            
            # Add close ticket button to welcome message
            close_view = TicketCloseButton()
            await channel.send(f"{user.mention}", embed=embed, view=close_view)
            
            # Ping support role if exists
            if support_role:
                await channel.send(f"{support_role.mention} - New support ticket opened!")
            
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


# Updated ItemView to include real purchases and asset delivery
class ItemView(View):
    """Interactive buttons for shop items with ticket system and real purchases"""
    
    def __init__(self, *, timeout=180, item_title=None, seller_id=None, price=None):
        super().__init__(timeout=timeout)
        self.item_title = item_title if item_title else "Product"
        self.seller_id = seller_id  # Store the seller's ID
        self.price = self._extract_price(price) if price else 0.0
        
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
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numeric price value from a price string (e.g. '$19.99' -> 19.99)"""
        if not price_str:
            return 0.0
            
        match = re.search(PRICE_REGEX, price_str)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                pass
        return 0.0
    
    async def purchase_callback(self, interaction: discord.Interaction):
        """Handle purchase button click - verify funds and create ticket channel"""
        
        # Check permissions
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Error: Bot doesn't have permission to create channels. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        user = interaction.user
        guild = interaction.guild
        
        # Get CurrencyManager from bot's cogs
        economy_cog = interaction.client.get_cog('Economy')
        if not economy_cog:
            await interaction.response.send_message(
                "Economy system is not available. Please contact an administrator.",
                ephemeral=True
            )
            return
            
        # Format safe channel name
        safe_item_name = self.item_title.lower().replace(" ", "-")[:50]
        channel_name = f"purchase-{safe_item_name}-{user.name}"
        channel_name = ''.join(c for c in channel_name if c.isalnum() or c in ['-', '_'])
        
        # Check if user has enough funds
        transaction_result = None
        has_funds = False
        user_balance = economy_cog.currency.get_balance(user.id)
        
        if self.price > 0 and self.seller_id:
            has_funds = economy_cog.currency.has_sufficient_balance(user.id, self.price)
        
        # Process the transaction if user has enough funds
        if has_funds:
            transaction_result = economy_cog.currency.process_purchase(
                user_id=user.id,
                seller_id=self.seller_id,
                amount=self.price
            )
        
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
            
            # Add seller permissions if available
            if self.seller_id:
                try:
                    seller = await guild.fetch_member(self.seller_id)
                    if seller:
                        overwrites[seller] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                except:
                    # Seller might no longer be in the server
                    pass
            
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
            
            # Create the purchase status embed based on transaction result
            if transaction_result and transaction_result.get("success"):
                embed = discord.Embed(
                    title=f"✅ Purchase Successful: {self.item_title}",
                    description=f"Thank you for your purchase! The asset has been automatically unlocked.",
                    color=discord.Color.green()
                )
                
                # Transaction details
                embed.add_field(
                    name="Transaction Details",
                    value=f"**Price:** {self.price:,.2f} Credits\n"
                          f"**Remaining Balance:** {transaction_result.get('user_balance'):,.2f} Credits",
                    inline=False
                )
                
                # Find the private assets channel to share from
                asset_channel = discord.utils.get(guild.channels, name="private-assets")
                
                # Add instructions on how to access the asset
                if asset_channel:
                    # Search for messages that mention this item in the assets channel
                    asset_found = False
                    try:
                        # Look for the first message containing the item name in the assets channel
                        async for message in asset_channel.history(limit=100):
                            if self.item_title.lower() in message.content.lower():
                                # Found the asset post - share it
                                embed.add_field(
                                    name="Asset Download",
                                    value=f"The asset will be shared below. Please follow the installation instructions.",
                                    inline=False
                                )
                                
                                # Share the asset content
                                await channel.send(f"**ASSET DOWNLOAD INFORMATION**\n\n{message.content}")
                                
                                # Share any attachments from the asset post
                                for attachment in message.attachments:
                                    await channel.send(file=await attachment.to_file())
                                
                                asset_found = True
                                break
                        
                        # If asset wasn't found, notify that it will be delivered manually
                        if not asset_found:
                            embed.add_field(
                                name="Asset Delivery",
                                value="Your purchased asset will be delivered manually by the seller shortly.",
                                inline=False
                            )
                    except Exception as e:
                        embed.add_field(
                            name="Asset Delivery",
                            value="There was an issue with automatic asset delivery. The seller will deliver it manually.",
                            inline=False
                        )
                else:
                    embed.add_field(
                        name="Asset Delivery",
                        value="Your purchased asset will be delivered manually by the seller shortly.",
                        inline=False
                    )
            else:
                # Insufficient funds or transaction failed
                embed = discord.Embed(
                    title=f"🛒 Purchase Discussion: {self.item_title}",
                    description=(
                        f"Thank you for your interest in this item!" +
                        (f"\n\n⚠️ **Insufficient Funds:** You need {self.price:,.2f} Credits, but have {user_balance:,.2f} Credits." 
                         if self.price > 0 and not has_funds else "")
                    ),
                    color=discord.Color.orange()
                )
                
                embed.add_field(
                    name="Next Steps",
                    value=(
                        "A seller will assist you shortly with your purchase process. "
                        "You can discuss payment options, request more information, or arrange a manual transaction."
                    ),
                    inline=False
                )
            
            # Add customer information
            embed.add_field(
                name="Customer",
                value=f"{user.mention} ({user.name})",
                inline=True
            )
            
            # Add seller information if available
            if self.seller_id:
                try:
                    seller = await guild.fetch_member(self.seller_id)
                    if seller:
                        embed.add_field(
                            name="Seller",
                            value=f"{seller.mention} ({seller.name})",
                            inline=True
                        )
                except:
                    pass
            
            embed.set_footer(text="Unreal Engine 5 Asset Shop • Thank you for your interest!")
            
            # Add close ticket button to the message
            close_button = TicketCloseButton()
            await channel.send(f"{user.mention}", embed=embed, view=close_button)
            
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