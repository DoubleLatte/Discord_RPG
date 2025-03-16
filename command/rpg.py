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
        if not db.get_character(str(interaction.user.id)):  # get_user -> get_character로 수정
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
            description="10초 동안 참여자를 기다립니다. 아래 버튼을 눌러 참여하세요!",
            colour=0xFF0000
        )
        view = JoinQuestView(quest_name)
        await interaction.response.send_message(embed=embed, view=view)

        await asyncio.sleep(10)
        if not view.participants:
            await interaction.followup.send("참여자가 없어 퀘스트가 취소되었습니다.", ephemeral=False)
            return

        await interaction.followup.send(f"{quest_name} 시작! 참여자: {', '.join([p.mention for p in view.participants])}")
        await quest_func(interaction, view.participants)

class InnView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="휴식하기 (10 HP 회복)", style=ButtonStyle.success)
    async def rest_button(self, interaction: Interaction, button: Button):
        user_id = str(interaction.user.id)
        
        # 유저 데이터 확인
        user_data = db.get_character(user_id)
        if not user_data:
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return
        
        # 골드 차감 (비용 5골드로 설정)
        inn_cost = 5
        if user_data['gold'] < inn_cost:
            await interaction.response.send_message(f"여관 비용 {inn_cost} 골드가 부족합니다! 현재 골드: {user_data['gold']}", ephemeral=True)
            return
        
        # HP 회복 처리
        current_hp = user_data['hp']
        max_hp = 100  # 최대 체력 (필요에 따라 수정)
        
        if current_hp >= max_hp:
            await interaction.response.send_message("이미 체력이 최대입니다!", ephemeral=True)
            return
        
        # HP 회복 및 골드 차감
        new_hp = min(current_hp + 10, max_hp)
        hp_recovered = new_hp - current_hp
        new_gold = user_data['gold'] - inn_cost
        
        # 업데이트할 스탯 딕셔너리
        updated_stats = {
            "hp": new_hp,
            "gold": new_gold
        }
        
        # 데이터베이스 업데이트 (모든 스탯을 한 번에 업데이트)
        db.update_character(user_id, updated_stats)
        
        # 결과 통보
        embed = Embed(
            title="🛏️ 여관에서 휴식",
            description=f"{interaction.user.mention}님이 여관에서 휴식했습니다.",
            colour=0xFFD700
        )
        embed.add_field(name="회복된 HP", value=f"+{hp_recovered} HP")
        embed.add_field(name="현재 HP", value=f"{new_hp}/{max_hp}")
        embed.add_field(name="비용", value=f"{inn_cost} 골드")
        embed.set_footer(text="편안한 휴식을 취했습니다.")
        
        await interaction.response.send_message(embed=embed)

class BioModal(Modal, title="자기소개 설정"):
    bio_input = TextInput(label="자기소개", placeholder="50자 이내로 입력하세요", max_length=50)

    async def on_submit(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if not db.get_character(user_id):  # get_user -> get_character로 수정
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return
        
        if db.set_bio(user_id, self.bio_input.value):
            await interaction.response.send_message(f"자기소개가 설정되었습니다: {self.bio_input.value}", ephemeral=True)
        else:
            await interaction.response.send_message("자기소개는 50자 이내로 설정해야 합니다!", ephemeral=True)

class RPG(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.user_channel_count = {}
        
    
    @app_commands.command(name="유저등록", description="RPG 게임에 유저를 등록합니다")
    async def register_command(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if db.get_character(user_id):  # get_user -> get_character로 수정
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
        user_data = db.get_character(user_id)  # get_user -> get_character로 수정
        user_bio = db.get_bio(user_id) or "자기소개가 없습니다."
        inventory = db.get_inventory(user_id)

        if not user_data:
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return

        # Embed 디자인 개선
        embed = discord.Embed(
            title=f"✨ {interaction.user.display_name}의 모험가 프로필 ✨",
            description=f"📜 **자기소개**: {user_bio}",
            colour=0x1E90FF,  # 더 부드러운 파란색
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        # 기본 정보 섹션
        embed.add_field(
            name="📊 기본 정보",
            value=(
                f"**모험가 등급**: 미개발 등급 \n"
                f"**레벨**: {user_data['lv']}  |  **경험치**: {user_data['xp']}\n"
                f"**완료한 퀘스트**: {user_data['quest_clears']}"
            ),
            inline=False
        )
        
        # 스탯 섹션
        embed.add_field(
            name="⚔️ 스탯",
            value=(
                f"❤️ **HP**: {user_data['hp']}  |  🔵 **MP**: {user_data['mp']}\n"
                f"⚔️ **공격력**: {user_data['atk']}  |  🛡️ **방어력**: {user_data['defen']}\n"
                f"🏃 **민첩**: {user_data['dex']}  |  🧠 **지능**: {user_data['int']}\n"
                f"🙏 **신앙**: {user_data['fai']}  |  💖 **친화력**: {user_data['aff']}\n"
                f"🛡️ **저항**: {user_data['res']}  |  🍀 **행운**: {user_data['luk']}\n"
                f"🎭 **카르마**: {user_data['karma']}  |  🌟 **명성**: {user_data['fame']}"
            ),
            inline=True
        )
        
        # 재화 섹션
        embed.add_field(
            name="💰 재화",
            value=f"**골드**: {user_data['gold']}  |  **캐쉬**: {user_data['cash']}",
            inline=True
        )
        
        # 인벤토리 섹션
        inventory_text = "\n".join([f"**{item_code}**: {qty}개" for item_code, qty in inventory.items()]) if inventory else "소지품이 없습니다."
        embed.add_field(
            name="🎒 인벤토리",
            value=inventory_text,
            inline=False
        )
        
        embed.set_footer(text=f"👤 {interaction.user.name} | RPG 모험가", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="여관", description="여관에서 체력을 회복합니다")
    async def inn_command(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if not db.get_character(user_id):
            await interaction.response.send_message("먼저 `/유저 등록`을 통해 등록해야 합니다!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏨 마을 여관",
            description="피로한 몸을 쉬게 하고 체력을 회복하세요!",
            colour=0xFFD700  # 금색
        )
        embed.add_field(
            name="서비스",
            value="휴식을 취하면 HP를 10 회복합니다.\n비용: 5 골드",
            inline=False
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/inn_icon.png")
        embed.set_footer(text="좋은 휴식으로 새로운 모험을 준비하세요!")
        
        view = InnView()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="게임", description="RPG 게임을 시작")
    #@has_admin_role()
    async def RPG_command(self, interaction: Interaction) -> None:
        if not db.get_character(str(interaction.user.id)):  # get_user -> get_character로 수정
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
    await bot.add_cog(RPG(bot))
    print("RPG cog가 성공적으로 로드되었습니다")