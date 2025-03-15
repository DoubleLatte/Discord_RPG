import discord
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime
import asyncio
from command.quest.ezquest import handle_slime_quest, handle_judge_quest
from util.permission import has_admin_role
from util.database import Database

db = Database()

class JoinQuestView(View):
    def __init__(self, quest_name: str, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.quest_name = quest_name
        self.participants = []

    @discord.ui.button(label="퀘스트 참여", style=ButtonStyle.red)
    async def join_button(self, interaction: Interaction, button: Button):
        if not db.get_user(str(interaction.user.id)):
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return
        if interaction.user not in self.participants:
            self.participants.append(interaction.user)
            await interaction.response.send_message(f"{interaction.user.mention}님이 {self.quest_name}에 참여했습니다!", ephemeral=True)
        else:
            await interaction.response.send_message("이미 참여 중입니다!", ephemeral=True)

class QuestView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="마을 앞 슬라임 처치", style=ButtonStyle.green)
    async def slime_button(self, interaction: Interaction, button: Button):
        await self.start_quest(interaction, "마을 앞 슬라임 처치", handle_slime_quest)

    @discord.ui.button(label="마을 밖 빤짝판사 처치", style=ButtonStyle.blurple)
    async def judge_button(self, interaction: Interaction, button: Button):
        await self.start_quest(interaction, "마을 밖 빤짝판사 처치", handle_judge_quest)

    async def start_quest(self, interaction: Interaction, quest_name: str, quest_func):
        embed = Embed(
            title=f"{quest_name} 모집",
            description="30초 동안 참여자를 기다립니다. 아래 버튼을 눌러 참여하세요!",
            colour=0xFF0000
        )
        view = JoinQuestView(quest_name)
        await interaction.response.send_message(embed=embed, view=view)

        await asyncio.sleep(30)
        if not view.participants:
            await interaction.followup.send("참여자가 없어 퀘스트가 취소되었습니다.", ephemeral=False)
            return

        await interaction.followup.send(f"{quest_name} 시작! 참여자: {', '.join([p.mention for p in view.participants])}")
        await quest_func(interaction, view.participants)

class BioModal(Modal, title="자기소개 설정"):
    bio_input = TextInput(label="자기소개", placeholder="50자 이내로 입력하세요", max_length=50)

    async def on_submit(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if not db.get_user(user_id):
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return
        
        if db.set_bio(user_id, self.bio_input.value):
            await interaction.response.send_message(f"자기소개가 설정되었습니다: {self.bio_input.value}", ephemeral=True)
        else:
            await interaction.response.send_message("자기소개는 50자 이내로 설정해야 합니다!", ephemeral=True)

class Paper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.user_channel_count = {}
    
    @app_commands.command(name="유저 등록", description="RPG 게임에 유저를 등록합니다")
    async def register_command(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if db.get_user(user_id):
            await interaction.response.send_message("이미 등록된 유저입니다!", ephemeral=True)
        elif db.register_user(user_id):
            await interaction.response.send_message(f"{interaction.user.mention}님이 성공적으로 등록되었습니다!", ephemeral=True)
        else:
            await interaction.response.send_message("등록 중 오류가 발생했습니다.", ephemeral=True)

    @app_commands.command(name="자기소개", description="자기소개를 설정하거나 확인합니다 (50자 이내)")
    async def bio_command(self, interaction: Interaction):
        await interaction.response.send_modal(BioModal())
    
    @app_commands.command(name="유저정보", description="유저의 RPG 정보를 확인합니다")
    async def user_info_command(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        user_data = db.get_user(user_id)
        user_bio = db.get_bio(user_id) or "자기소개가 없습니다."

        if not user_data:
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{interaction.user.display_name}님의 정보",
            description=f"📝 {user_bio}",
            colour=0x3498db,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.add_field(name="❤️ HP", value=f"{user_data['hp']}", inline=True)
        embed.add_field(name="🔵 MP", value=f"{user_data['mp']}", inline=True)
        embed.add_field(name="⚔️ 공격력", value=f"{user_data['atk']}", inline=True)
        embed.add_field(name="🛡 방어력", value=f"{user_data['def']}", inline=True)
        embed.add_field(name="🏃 민첩", value=f"{user_data['dex']}", inline=True)
        embed.add_field(name="🧠 지능", value=f"{user_data['int']}", inline=True)
        embed.add_field(name="🙏 신앙", value=f"{user_data['fai']}", inline=True)
        embed.add_field(name="💖 친화력", value=f"{user_data['aff']}", inline=True)
        embed.add_field(name="🎭 카르마", value=f"{user_data['karma']}", inline=True)
        embed.add_field(name="🌟 명성", value=f"{user_data['fame']}", inline=True)
        embed.add_field(name="🛡 저항", value=f"{user_data['res']}", inline=True)
        embed.add_field(name="🍀 행운", value=f"{user_data['luk']}", inline=True)
        embed.add_field(name="🏆 완료한 퀘스트", value=f"{user_data['quest_clears']}", inline=True)
        embed.set_footer(text=f"{interaction.user.name}님의 RPG 정보")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="게임", description="Rpg 게임을 시작")
        @has_admin_role()
        async def paper_command(self, interaction: Interaction) -> None:
            if not db.get_user(str(interaction.user.id)):
                await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="✨ 플레이 가능한 여행 퀘스트 ✨",
                description="🔘 버튼으로 선택하세요",
                colour=0x14bdff,
                timestamp=datetime.now()
            )
            embed.set_author(name="🎮 RPG 게임 목록", icon_url="https://cdn.discordapp.com/emojis/123456789.png")
            embed.add_field(name="🌳 마을 앞 슬라임 처치", value="```diff\n+ Lv.0 ~ Lv.10\n```", inline=False)
            embed.add_field(name="⚡ 마을 밖 빤짝판사 처치", value="```diff\n+ Lv.0 ~ Lv.0\n```", inline=False)
            embed.set_footer(text="📜 Quest", icon_url="https://cdn.discordapp.com/emojis/987654321.png")
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/quest_icon.png")
            
            view = QuestView()
            await interaction.response.send_message(embed=embed, view=view)
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Paper(bot))
    print("Paper cog가 성공적으로 로드되었습니다")
