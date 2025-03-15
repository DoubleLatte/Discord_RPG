# command/paper.py
import discord
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
from command.quest.quest_handlers import handle_slime_quest, handle_judge_quest
from util.util import has_admin_role  # 절대 경로로 util에서 가져오기

class QuestView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="마을 앞 슬라임 처치", style=ButtonStyle.green)
    async def slime_button(self, interaction: Interaction, button: Button):
        await handle_slime_quest(interaction)

    @discord.ui.button(label="마을 밖 빤짝판사 처치", style=ButtonStyle.blurple)
    async def judge_button(self, interaction: Interaction, button: Button):
        await handle_judge_quest(interaction)

class Paper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.user_channel_count = {}
    
    @app_commands.command(
        name="게임 Rpg", 
        description="Rpg 게임을 시작한다"
    )
    @has_admin_role()
    async def paper_command(self, interaction: Interaction) -> None:
        embed = discord.Embed(
            title="✨ 플레이 가능한 여행 퀘스트 ✨",
            description="🔘 버튼으로 선택하세요",
            colour=0x14bdff,
            timestamp=datetime.now()
        )
    
        embed.set_author(
            name="🎮 RPG 게임 목록",
            icon_url="https://cdn.discordapp.com/emojis/123456789.png"
        )
    
        embed.add_field(
            name="🌳 마을 앞 슬라임 처치",
            value="```diff\n+ Lv.0 ~ Lv.10\n```",
            inline=False
        )
        embed.add_field(
            name="⚡ 마을 밖 빤짝판사 처치",
            value="```diff\n+ Lv.0 ~ Lv.0\n```",
            inline=False
        )
    
        embed.set_footer(
            text="📜 Quest",
            icon_url="https://cdn.discordapp.com/emojis/987654321.png"
        )
    
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/quest_icon.png")
        
        view = QuestView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @paper_command.error
    async def paper_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "이 명령어를 사용할 권한이 없습니다.", 
                ephemeral=True
            )
        else:
            print(f"페이퍼 명령어에서 오류 발생: {error}")
            await interaction.response.send_message(
                "명령어 실행 중 오류가 발생했습니다.", 
                ephemeral=True
            )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Paper(bot))
    print("Paper cog가 성공적으로 로드되었습니다")
