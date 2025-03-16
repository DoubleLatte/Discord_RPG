import discord
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ext import commands
from discord.ui import View, Button
from util.database import Database

db = Database()

class ShopView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="휴식하기 (10 HP 회복)", style=ButtonStyle.success)
    async def rest_button(self, interaction: Interaction, button: Button):
        user_id = str(interaction.user.id)
        user_data = db.get_character(user_id)

        if not user_data:
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return

        inn_cost = 5
        if user_data['gold'] < inn_cost:
            await interaction.response.send_message(f"여관 비용 {inn_cost} 골드가 부족합니다! 현재 골드: {user_data['gold']}", ephemeral=True)
            return

        current_hp = user_data['hp']
        max_hp = 100
        if current_hp >= max_hp:
            await interaction.response.send_message("이미 체력이 최대입니다!", ephemeral=True)
            return

        new_hp = min(current_hp + 10, max_hp)
        hp_recovered = new_hp - current_hp
        new_gold = user_data['gold'] - inn_cost
        db.update_character(user_id, {"hp": new_hp, "gold": new_gold})

        embed = Embed(
            title="🛏️ 여관에서 휴식",
            description=f"{interaction.user.mention}님이 편안한 휴식을 취했습니다.",
            colour=0xFFD700
        )
        embed.add_field(name="HP", value=f"회복된 HP: +{hp_recovered} HP | 현재 HP {new_hp}/{max_hp}", inline=True)
        embed.add_field(name="골드", value=f"사용된 골드 : {inn_cost} | 남은 골드 : {new_gold}", inline=True)
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/inn_icon.png")
        embed.set_footer(text="새로운 모험을 위해 준비 완료!")
        await interaction.response.send_message(embed=embed)

class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="여관", description="여관에서 체력을 회복합니다")
    async def inn_command(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        user_data = db.get_character(user_id)
        if not db.get_character(str(interaction.user.id)):
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return
        
        embed = Embed(
            title="🏨 마을 여관",
            description="피로한 몸을 쉬게 하고 체력을 회복하세요!",
            colour=0xFFD700
        )
        embed.add_field(name="서비스", value=f"소지금 : {user_data['gold']} \n휴식: 10 HP 회복 (비용: 5 골드)", inline=False)
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/inn_icon.png")
        embed.set_footer(text="좋은 휴식으로 새로운 모험을 준비하세요!")
        await interaction.response.send_message(embed=embed, view=ShopView())

async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
    print("Shop cog가 성공적으로 로드되었습니다")