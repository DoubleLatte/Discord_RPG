# command/quest/quest_handlers.py
import discord
from discord import Interaction

async def handle_slime_quest(interaction: Interaction):
    await interaction.response.send_message("마을 앞 슬라임 처치 퀘스트를 시작합니다!", ephemeral=True)

async def handle_judge_quest(interaction: Interaction):
    await interaction.response.send_message("마을 밖 빤짝판사 처치 퀘스트를 시작합니다!", ephemeral=True)
