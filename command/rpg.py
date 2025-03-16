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
    def __init__(self, quest_name: str, creator: discord.User, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.quest_name = quest_name
        self.creator = creator
        self.participants = [creator]  # 방장 자동 참여
        self.message = None  # 초기 메시지 저장용

    @discord.ui.button(label="퀘스트 참여", style=ButtonStyle.red)
    async def join_button(self, interaction: Interaction, button: Button):
        user_id = str(interaction.user.id)
        user_data = db.get_character(user_id)

        # 유저 등록 여부 확인
        if not user_data:
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return
        
        # HP 체크 (0이거나 10 미만일 경우)
        if user_data['hp'] <= 0:
            embed = Embed(
                title="⚠️ 체력 부족 경고",
                description="체력이 0입니다! 여관에서 회복 후 참여해주세요.",
                colour=0xFF0000
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/warning_icon.png")
            embed.set_footer(text="HP를 회복하고 다시 시도하세요!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        elif user_data['hp'] < 10:
            embed = Embed(
                title="⚠️ 체력 부족 경고",
                description="체력이 10 미만입니다! 여관에서 회복 후 참여해주세요.",
                colour=0xFFA500
            )
            embed.add_field(name="현재 HP", value=f"{user_data['hp']}/100", inline=True)
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/warning_icon.png")
            embed.set_footer(text="HP를 회복하고 다시 시도하세요!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # 중복 참여 방지
        if interaction.user in self.participants:
            await interaction.response.send_message("이미 참여 중입니다!", ephemeral=True)
            return

        # 참여자 추가 및 임베드 업데이트
        self.participants.append(interaction.user)
        await interaction.response.send_message(f"{interaction.user.mention}님이 {self.quest_name}에 참여했습니다!", ephemeral=True)
        await self.update_embed(interaction)

    async def update_embed(self, interaction: Interaction):
        """참여자 목록으로 임베드를 업데이트"""
        if self.message:
            embed = self.create_embed()
            await self.message.edit(embed=embed)

    def create_embed(self):
        """퀘스트 모집 임베드 생성"""
        embed = Embed(
            title=f"⚔️ {self.quest_name} 모집",
            description="10초 동안 참여자를 모집합니다! 아래 버튼을 눌러 참여하세요!",
            colour=0xFF4500
        )
        embed.add_field(name="👑 방장", value=f"{self.creator.mention}", inline=True)
        embed.add_field(
            name="👥 참여자",
            value="\n".join([p.mention for p in self.participants]),
            inline=True
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/quest_icon.png")
        embed.set_footer(text="⏳ 10초 후 퀘스트 시작", icon_url=self.creator.avatar.url if self.creator.avatar else None)
        return embed

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
        # 퀘스트 모집 시작
        view = JoinQuestView(quest_name, interaction.user)
        embed = view.create_embed()
        message = await interaction.channel.send(embed=embed, view=view)  # 채널에 직접 전송
        view.message = message  # 메시지 객체 저장

        # 초기 응답 defer로 처리
        await interaction.response.defer()

        # 10초 대기 후 퀘스트 진행
        await asyncio.sleep(10)
        start_embed = Embed(
            title=f"🌟 {quest_name} 시작!",
            description=f"참여자: {', '.join([p.mention for p in view.participants])}",
            colour=0x00FF00
        )
        start_embed.set_footer(text=f"방장: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.followup.send(embed=start_embed)
        await quest_func(interaction, view.participants)

class BioModal(Modal, title="자기소개 설정"):
    bio_input = TextInput(label="자기소개", placeholder="50자 이내로 입력하세요", max_length=50)

    async def on_submit(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if not db.get_character(user_id):
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return

        if db.set_bio(user_id, self.bio_input.value):
            await interaction.response.send_message(f"자기소개가 설정되었습니다: {self.bio_input.value}", ephemeral=True)
        else:
            await interaction.response.send_message("자기소개는 50자 이내로 설정해야 합니다!", ephemeral=True)

class RPG(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_channel_count = {}

    @app_commands.command(name="유저등록", description="RPG 게임에 유저를 등록합니다")
    async def register_command(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if db.get_character(user_id):
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
        user_data = db.get_character(user_id)
        user_bio = db.get_bio(user_id) or "자기소개가 없습니다."
        inventory = db.get_inventory(user_id)

        if not user_data:
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return

        embed = Embed(
            title=f"✨ {interaction.user.display_name}의 모험가 프로필 ✨",
            description=f"📜 **자기소개**: {user_bio}",
            colour=0x1E90FF,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.add_field(
            name="📊 기본 정보",
            value=f"**레벨**: {user_data['lv']}  |  **경험치**: {user_data['xp']}\n**완료한 퀘스트**: {user_data['quest_clears']}",
            inline=False
        )
        embed.add_field(
            name="⚔️ 스탯",
            value=(
                f"❤️ **HP**: {user_data['hp']}  |  🔵 **MP**: {user_data['mp']}\n"
                f"⚔️ **공격력**: {user_data['atk']}  |  🛡️ **방어력**: {user_data['defen']}\n"
                f"🏃 **민첩**: {user_data['dex']}  |  🧠 **지능**: {user_data['int']}"
            ),
            inline=True
        )
        embed.add_field(
            name="💰 재화",
            value=f"**골드**: {user_data['gold']}  |  **캐쉬**: {user_data['cash']}",
            inline=True
        )
        inventory_text = "\n".join([f"**{item_code}**: {qty}개" for item_code, qty in inventory.items()]) if inventory else "소지품이 없습니다."
        embed.add_field(name="🎒 인벤토리", value=inventory_text, inline=False)
        embed.set_footer(text=f"👤 {interaction.user.name} | RPG 모험가", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="게임", description="RPG 게임을 시작")
    async def rpg_command(self, interaction: Interaction):
        if not db.get_character(str(interaction.user.id)):
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return
        
        embed = Embed(
            title="✨ 플레이 가능한 여행 퀘스트 ✨",
            description="🔘 버튼으로 퀘스트를 선택하세요",
            colour=0x14BDFF,
            timestamp=datetime.now()
        )
        embed.set_author(name="🎮 RPG 게임 목록", icon_url="https://cdn.discordapp.com/emojis/123456789.png")
        embed.add_field(name="🌳 마을 앞 슬라임 처치", value="```diff\n+ Lv.0 ~ Lv.10\n```", inline=False)
        embed.add_field(name="⚡ 마을 밖 빤짝판사 처치", value="```diff\n+ Lv.0 ~ Lv.0\n```", inline=False)
        embed.set_footer(text="📜 Quest", icon_url="https://cdn.discordapp.com/emojis/987654321.png")
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/quest_icon.png")
        await interaction.response.send_message(embed=embed, view=QuestView())

async def setup(bot: commands.Bot):
    await bot.add_cog(RPG(bot))
    print("RPG cog가 성공적으로 로드되었습니다")