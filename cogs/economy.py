import discord
from discord import app_commands
from discord.ext import commands
from utils.currency_manager import CurrencyManager

class Economy(commands.Cog):
    """Economy system with user balances and transactions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.currency = CurrencyManager()
        self.currency_name = "Credits"  # Can be customized
        
    @commands.command(name="balance", aliases=["bal"])
    async def check_balance_prefix(self, ctx, member: discord.Member = None):
        """Check your balance or another user's balance"""
        target = member or ctx.author
        balance = self.currency.get_balance(target.id)
        
        embed = discord.Embed(
            title=f"{target.display_name}'s Balance",
            description=f"**{balance:,.2f}** {self.currency_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="balance", description="Check your balance or another user's balance")
    @app_commands.describe(member="The user whose balance to check (defaults to yourself)")
    async def check_balance_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        """Check balance via slash command"""
        target = member or interaction.user
        balance = self.currency.get_balance(target.id)
        
        embed = discord.Embed(
            title=f"{target.display_name}'s Balance",
            description=f"**{balance:,.2f}** {self.currency_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name="addbalance", aliases=["addbal"])
    @commands.has_permissions(administrator=True)
    async def add_balance_prefix(self, ctx, member: discord.Member, amount: float):
        """Add balance to a user (Admin only)"""
        try:
            if amount <= 0:
                await ctx.send("Amount must be positive!")
                return
                
            new_balance = self.currency.add_balance(member.id, amount)
            
            embed = discord.Embed(
                title="Balance Updated",
                description=f"Added **{amount:,.2f}** {self.currency_name} to {member.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="New Balance", value=f"**{new_balance:,.2f}** {self.currency_name}")
            
            await ctx.send(embed=embed)
            
        except ValueError as e:
            await ctx.send(f"Error: {str(e)}")
    
    @app_commands.command(name="addbalance", description="Add balance to a user (Admin only)")
    @app_commands.describe(
        member="The user to add balance to",
        amount="Amount to add (must be positive)"
    )
    @app_commands.default_permissions(administrator=True)
    async def add_balance_slash(self, interaction: discord.Interaction, member: discord.Member, amount: float):
        """Add balance via slash command"""
        try:
            if amount <= 0:
                await interaction.response.send_message("Amount must be positive!", ephemeral=True)
                return
                
            new_balance = self.currency.add_balance(member.id, amount)
            
            embed = discord.Embed(
                title="Balance Updated",
                description=f"Added **{amount:,.2f}** {self.currency_name} to {member.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="New Balance", value=f"**{new_balance:,.2f}** {self.currency_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
    
    @commands.command(name="removebalance", aliases=["rmbal"])
    @commands.has_permissions(administrator=True)
    async def remove_balance_prefix(self, ctx, member: discord.Member, amount: float):
        """Remove balance from a user (Admin only)"""
        try:
            if amount <= 0:
                await ctx.send("Amount must be positive!")
                return
                
            new_balance = self.currency.remove_balance(member.id, amount)
            
            embed = discord.Embed(
                title="Balance Updated",
                description=f"Removed **{amount:,.2f}** {self.currency_name} from {member.mention}",
                color=discord.Color.red()
            )
            embed.add_field(name="New Balance", value=f"**{new_balance:,.2f}** {self.currency_name}")
            
            await ctx.send(embed=embed)
            
        except ValueError as e:
            await ctx.send(f"Error: {str(e)}")
    
    @app_commands.command(name="removebalance", description="Remove balance from a user (Admin only)")
    @app_commands.describe(
        member="The user to remove balance from",
        amount="Amount to remove (must be positive)"
    )
    @app_commands.default_permissions(administrator=True)
    async def remove_balance_slash(self, interaction: discord.Interaction, member: discord.Member, amount: float):
        """Remove balance via slash command"""
        try:
            if amount <= 0:
                await interaction.response.send_message("Amount must be positive!", ephemeral=True)
                return
                
            new_balance = self.currency.remove_balance(member.id, amount)
            
            embed = discord.Embed(
                title="Balance Updated",
                description=f"Removed **{amount:,.2f}** {self.currency_name} from {member.mention}",
                color=discord.Color.red()
            )
            embed.add_field(name="New Balance", value=f"**{new_balance:,.2f}** {self.currency_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Economy(bot))