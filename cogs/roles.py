import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Dict, Optional
import json
import os
import asyncio

# File to store reaction role data
REACTION_ROLES_FILE = 'reaction_roles.json'

class RoleReactionPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = {}
        self._load_reaction_roles()
        
    def _load_reaction_roles(self):
        """Load reaction roles from file"""
        if os.path.exists(REACTION_ROLES_FILE):
            try:
                with open(REACTION_ROLES_FILE, 'r') as f:
                    # Convert string keys back to integers for message_id and role_id
                    data = json.load(f)
                    for message_id, reactions in data.items():
                        self.reaction_roles[int(message_id)] = {
                            emoji: int(role_id) for emoji, role_id in reactions.items()
                        }
            except Exception as e:
                print(f"Error loading reaction roles: {e}")
        
    def _save_reaction_roles(self):
        """Save reaction roles to file"""
        try:
            with open(REACTION_ROLES_FILE, 'w') as f:
                # Convert int keys to strings for JSON serialization
                serializable_data = {
                    str(message_id): {
                        emoji: str(role_id) for emoji, role_id in reactions.items()
                    } for message_id, reactions in self.reaction_roles.items()
                }
                json.dump(serializable_data, f, indent=4)
        except Exception as e:
            print(f"Error saving reaction roles: {e}")
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Event handler for when a reaction is added to a message"""
        if payload.user_id == self.bot.user.id:
            return  # Ignore bot's own reactions
        
        # Check if this is a role reaction message
        message_id = payload.message_id
        if message_id in self.reaction_roles:
            emoji = str(payload.emoji)
            
            # Check if this emoji is registered for a role
            if emoji in self.reaction_roles[message_id]:
                role_id = self.reaction_roles[message_id][emoji]
                guild = self.bot.get_guild(payload.guild_id)
                
                if not guild:
                    return
                
                # Get the role and member objects
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    try:
                        await member.add_roles(role, reason="Reaction role assignment")
                    except discord.Forbidden:
                        print(f"Missing permissions to assign role {role.name}")
                    except Exception as e:
                        print(f"Error assigning role: {e}")
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Event handler for when a reaction is removed from a message"""
        # Skip bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a role reaction message
        message_id = payload.message_id
        if message_id in self.reaction_roles:
            emoji = str(payload.emoji)
            
            # Check if this emoji is registered for a role
            if emoji in self.reaction_roles[message_id]:
                role_id = self.reaction_roles[message_id][emoji]
                guild = self.bot.get_guild(payload.guild_id)
                
                if not guild:
                    return
                
                # Get the role and member objects
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    try:
                        await member.remove_roles(role, reason="Reaction role removal")
                    except discord.Forbidden:
                        print(f"Missing permissions to remove role {role.name}")
                    except Exception as e:
                        print(f"Error removing role: {e}")
    
    @commands.command(name="rolespanel")
    @commands.has_permissions(administrator=True)
    async def roles_panel_prefix(self, ctx):
        """Create a role reaction panel (prefix command)
        
        Usage: !rolespanel
        Then follow the interactive setup instructions
        """
        await self._interactive_panel_setup(ctx)
    
    @app_commands.command(name="rolespanel", description="Create a role reaction panel")
    @app_commands.default_permissions(administrator=True)
    async def roles_panel_slash(self, interaction: discord.Interaction):
        """Create a role reaction panel (slash command)"""
        await interaction.response.send_message("Starting role panel setup. Please answer the following questions:", ephemeral=True)
        await self._interactive_panel_setup(interaction)
    
    async def _interactive_panel_setup(self, ctx_or_interaction):
        """Interactive setup for role reaction panel"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        channel = ctx_or_interaction.channel
        user = ctx_or_interaction.user
        
        # Helper function to get response from user
        async def get_response():
            try:
                def check(m):
                    return m.author == user and m.channel == channel
                
                response = await self.bot.wait_for('message', check=check, timeout=120)
                return response.content
            except asyncio.TimeoutError:
                if is_interaction:
                    await ctx_or_interaction.followup.send("Setup timed out. Please try again.", ephemeral=True)
                else:
                    await channel.send("Setup timed out. Please try again.")
                return None
        
        # 1. Get the panel title
        if is_interaction:
            await ctx_or_interaction.followup.send("What should be the **title** of the role panel?", ephemeral=True)
        else:
            await channel.send("What should be the **title** of the role panel?")
        
        title = await get_response()
        if not title:
            return
        
        # 2. Get the panel description
        if is_interaction:
            await ctx_or_interaction.followup.send("What should be the **description** of the role panel?", ephemeral=True)
        else:
            await channel.send("What should be the **description** of the role panel?")
        
        description = await get_response()
        if not description:
            return
        
        # 3. Collect roles and emojis
        if is_interaction:
            await ctx_or_interaction.followup.send(
                "Now, let's add roles and emojis. Enter them in this format:\n"
                "`ROLE_ID EMOJI ROLE_NAME`\n"
                "Example: `123456789012345678 👍 Supporter`\n"
                "Enter one role per line. Type `done` when finished.", 
                ephemeral=True
            )
        else:
            await channel.send(
                "Now, let's add roles and emojis. Enter them in this format:\n"
                "`ROLE_ID EMOJI ROLE_NAME`\n"
                "Example: `123456789012345678 👍 Supporter`\n"
                "Enter one role per line. Type `done` when finished."
            )
        
        roles_data = []
        while True:
            entry = await get_response()
            if not entry:
                return
            
            if entry.lower() == 'done':
                break
                
            # Parse the entry: ROLE_ID EMOJI ROLE_NAME
            parts = entry.split(' ', 2)
            if len(parts) < 2:
                if is_interaction:
                    await ctx_or_interaction.followup.send("Invalid format. Please try again.", ephemeral=True)
                else:
                    await channel.send("Invalid format. Please try again.")
                continue
                
            role_id_str, emoji = parts[0], parts[1]
            role_name = parts[2] if len(parts) > 2 else "Role"
                
            # Validate role ID
            try:
                role_id = int(role_id_str)
                # Verify role exists
                guild = ctx_or_interaction.guild
                role = guild.get_role(role_id)
                if not role:
                    if is_interaction:
                        await ctx_or_interaction.followup.send(f"Role with ID {role_id} not found. Please try again.", ephemeral=True)
                    else:
                        await channel.send(f"Role with ID {role_id} not found. Please try again.")
                    continue
                    
                # Add to roles data
                roles_data.append({
                    'id': role_id,
                    'emoji': emoji,
                    'name': role_name or role.name
                })
                
                if is_interaction:
                    await ctx_or_interaction.followup.send(f"Added role: {role.name} with emoji {emoji}", ephemeral=True)
                else:
                    await channel.send(f"Added role: {role.name} with emoji {emoji}")
                    
            except ValueError:
                if is_interaction:
                    await ctx_or_interaction.followup.send("Invalid role ID. Please enter a valid ID.", ephemeral=True)
                else:
                    await channel.send("Invalid role ID. Please enter a valid ID.")
        
        # Check if we have any roles
        if not roles_data:
            if is_interaction:
                await ctx_or_interaction.followup.send("No roles were added. Setup cancelled.", ephemeral=True)
            else:
                await channel.send("No roles were added. Setup cancelled.")
            return
            
        # 4. Create the panel embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        
        # Add each role to the embed
        for role_info in roles_data:
            embed.add_field(
                name=f"{role_info['emoji']} {role_info['name']}", 
                value=f"React with {role_info['emoji']} to get this role", 
                inline=False
            )
            
        embed.set_footer(text="React to get or remove a role")
        
        # 5. Ask for target channel
        if is_interaction:
            await ctx_or_interaction.followup.send(
                "In which channel should I post the role panel? Please enter the channel ID or #mention the channel.", 
                ephemeral=True
            )
        else:
            await channel.send(
                "In which channel should I post the role panel? Please enter the channel ID or #mention the channel."
            )
        
        channel_input = await get_response()
        if not channel_input:
            return
            
        # Parse channel mention or ID
        target_channel = None
        if channel_input.startswith("<#") and channel_input.endswith(">"):
            # Channel mention
            try:
                channel_id = int(channel_input[2:-1])
                target_channel = ctx_or_interaction.guild.get_channel(channel_id)
            except:
                pass
        else:
            # Channel ID
            try:
                channel_id = int(channel_input)
                target_channel = ctx_or_interaction.guild.get_channel(channel_id)
            except:
                pass
                
        if not target_channel:
            if is_interaction:
                await ctx_or_interaction.followup.send("Invalid channel. Setup cancelled.", ephemeral=True)
            else:
                await channel.send("Invalid channel. Setup cancelled.")
            return
        
        # 6. Send the panel message
        panel_message = await target_channel.send(embed=embed)
        
        # 7. Add reactions
        role_emoji_mapping = {}
        for role_info in roles_data:
            await panel_message.add_reaction(role_info['emoji'])
            role_emoji_mapping[role_info['emoji']] = role_info['id']
        
        # 8. Save reaction roles configuration
        self.reaction_roles[panel_message.id] = role_emoji_mapping
        self._save_reaction_roles()
        
        # 9. Confirm completion
        if is_interaction:
            await ctx_or_interaction.followup.send(
                f"Role panel created successfully in {target_channel.mention}!", 
                ephemeral=True
            )
        else:
            await channel.send(f"Role panel created successfully in {target_channel.mention}!")

async def setup(bot):
    await bot.add_cog(RoleReactionPanel(bot))