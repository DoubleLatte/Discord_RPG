import discord
import random
from discord import Interaction, User, Embed, ButtonStyle
from discord.ui import Button, View
from util.database import Database
import asyncio

# 확률 설정
chance = 0.4  # 슬라임 등장 확률
chance2 = 0.5  # 아이템 발견 확률
db = Database()  # 데이터베이스 객체 생성

class CombatView(View):
    def __init__(self, user_id: str, slime: dict, players: dict, message: discord.Message):
        super().__init__(timeout=20.0)  # 20초 타임아웃 설정
        self.user_id = user_id  # 현재 플레이어 ID
        self.slime = slime  # 슬라임 상태
        self.players = players  # 모든 플레이어 상태
        self.message = message  # 전투 메시지 객체
        self.result = None  # 행동 결과 저장

    @discord.ui.button(label="전투", style=ButtonStyle.red)
    async def fight_button(self, interaction: Interaction, button: Button):
        # 현재 플레이어가 아닌 경우 차단
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("지금은 당신의 차례가 아닙니다!", ephemeral=True)
            return

        stats = self.players[self.user_id]
        hit_chance = 0.8 + (stats["luk"] / 100)  # 명중 확률 계산
        if random.random() < hit_chance:
            crit_chance = stats["luk"] / 200  # 크리티컬 확률 계산
            is_crit = random.random() < crit_chance
            damage = (stats["atk"] * 2) if is_crit else stats["atk"]  # 크리티컬 여부에 따른 데미지
            self.slime["hp"] -= max(0, damage - self.slime["defen"])  # 슬라임 HP 감소
            hit_msg = f"크리티컬! {damage} 데미지" if is_crit else f"{damage} 데미지"
            self.result = f"<@{self.user_id}> 공격: {hit_msg}"
        else:
            self.result = f"<@{self.user_id}> 공격이 빗나갔습니다!"

        await self.update_combat()  # 전투 상태 업데이트
        await interaction.response.defer()  # 응답 지연

    @discord.ui.button(label="도망", style=ButtonStyle.grey)
    async def flee_button(self, interaction: Interaction, button: Button):
        # 현재 플레이어가 아닌 경우 차단
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("지금은 당신의 차례가 아닙니다!", ephemeral=True)
            return

        stats = self.players[self.user_id]
        flee_chance = 0.5 + (stats["dex"] / 100)  # 도망 성공 확률 계산

        if random.random() < flee_chance:
            self.result = f"<@{self.user_id}>가 성공적으로 도망쳤습니다!"
            self.players[self.user_id]["escaped"] = True  # 도망 상태 설정
            escape_embed = Embed(
                title="🏃‍♂️ 도망 성공",
                description=self.result,
                colour=0x00FF00
            )
            await self.message.edit(embed=escape_embed, view=None)  # 즉시 도망 성공 표시
            self.stop()  # 턴 종료
        else:
            self.result = f"<@{self.user_id}> 도망 실패!"
            await self.update_combat()  # 실패 시 전투 상태 업데이트

        await interaction.response.defer()

    @discord.ui.button(label="가방", style=ButtonStyle.blurple)
    async def bag_button(self, interaction: Interaction, button: Button):
        # 현재 플레이어가 아닌 경우 차단
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("지금은 당신의 차례가 아닙니다!", ephemeral=True)
            return

        self.result = f"<@{self.user_id}>가 가방을 열었습니다! (PASS - 차후 구현)"
        await self.update_combat()
        await interaction.response.defer()

    async def update_combat(self):
        # 플레이어 행동 결과 표시
        embed = Embed(
            title="⚔️ 플레이어 행동",
            description=self.result or f"<@{self.user_id}>의 차례입니다!",
            colour=0xFF4500
        )
        await self.message.edit(embed=embed)
        await asyncio.sleep(1.5)  # 1.5초 대기

        # 전투 상태 업데이트
        embed = Embed(
            title="⚔️ 슬라임 전투 진행",
            description=f"**슬라임 상태**\n❤️ HP: {self.slime['hp']}  |  ⚔️ ATK: {self.slime['atk']}  |  🛡️ DEF: {self.slime['defen']}",
            colour=0xFF4500
        )
        for p_id, p_stats in self.players.items():
            if p_stats["hp"] > 0:
                status = "🏃‍♂️ 도망" if p_stats.get("escaped", False) else "⚔️ 전투 중"
                embed.add_field(
                    name=f"👤 <@{p_id}>",
                    value=f"❤️ HP: {p_stats['hp']}  |  ⚔️ ATK: {p_stats['atk']}  |  🛡️ DEF: {p_stats['defen']}  |  {status}",
                    inline=True
                )
        embed.add_field(name="📝 최근 행동", value=self.result, inline=False)
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/slime_icon.png")
        await asyncio.sleep(0.5)  # 추가 지연
        # 전투가 끝났는지 확인 후 뷰 유지/제거
        await self.message.edit(embed=embed, view=self if self.slime["hp"] > 0 and any(stats["hp"] > 0 and not stats.get("escaped", False) for stats in self.players.values()) else None)
        self.stop()

async def handle_slime_quest(interaction: Interaction, participants: list[User]):
    # 플레이어 상태 초기화
    players = {}
    for p in participants:
        user_id = str(p.id)
        stats = db.get_character(user_id)
        if stats:
            players[user_id] = stats.copy()
            players[user_id]["gear"] = sum(db.get_inventory(user_id).values())

    max_attempts = 10  # 최대 탐색 횟수
    slime = None  # 슬라임 객체
    combat_message = None  # 전투 메시지 객체

    # 퀘스트 시작 알림
    start_embed = Embed(
        title="🌳 마을 앞 슬라임 처치 퀘스트",
        description=f"👥 **참여자**: {len(participants)}명\n⏳ **남은 기회**: {max_attempts}번",
        colour=0x32CD32,
        timestamp=discord.utils.utcnow()
    )
    start_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/123456789.png")
    start_embed.set_footer(text="퀘스트 시작!", icon_url="https://cdn.discordapp.com/emojis/987654321.png")
    await interaction.channel.send(embed=start_embed)

    for attempt in range(max_attempts):
        event_chance = random.random()
        remaining_attempts = max_attempts - attempt - 1

        # 슬라임 등장
        if event_chance < chance and slime is None:
            slime = {"hp": random.randint(5, 15), "atk": random.randint(5, 10), "defen": random.randint(0, 2)}
            is_elite = slime["hp"] == 15 and random.random() < 0.1
            if is_elite:
                slime["atk"] += 3
                slime_desc = "⚠️ **엘리트 슬라임 등장!**"
                colour = 0xFF0000
            else:
                slime_desc = f"🐍 슬라임 등장! (HP: {slime['hp']}, ATK: {slime['atk']}, DEF: {slime['defen']})"
                colour = 0xFF4500

            embed = Embed(
                title="⚔️ 슬라임 전투 시작",
                description=slime_desc,
                colour=colour
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/slime_icon.png")
            combat_message = await interaction.channel.send(embed=embed)

        # 아이템 발견
        elif event_chance < chance2 and slime is None:
            gear = random.choice(["낡은 검", "가죽 갑옷", "작은 포션", "엘릭서"])
            lucky_player = random.choice(participants)
            db.add_item(str(lucky_player.id), gear)
            players[str(lucky_player.id)]["gear"] += 1
            embed = Embed(
                title="🎁 아이템 발견!",
                description=f"🎉 <@{lucky_player.id}>가 **{gear}**을(를) 획득했습니다!\n⏳ 남은 기회: {remaining_attempts}",
                colour=0xFFD700
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/treasure_icon.png")
            await interaction.channel.send(embed=embed)

        # 아무것도 발견하지 못함
        elif slime is None:
            embed = Embed(
                title="🔍 탐색 중...",
                description=f"❌ 아무것도 발견하지 못했습니다...\n⏳ 남은 기회: {remaining_attempts}",
                colour=0x808080
            )
            embed.set_footer(text="조금 더 찾아보자!")
            await interaction.channel.send(embed=embed)

        # 슬라임 전투 처리
        if slime:
            for pid in players:
                stats = players[pid]
                # HP가 0이거나 도망친 플레이어는 건너뜀
                if stats["hp"] <= 0 or stats.get("escaped", False):
                    continue

                # 전투 UI 표시
                view = CombatView(pid, slime, players, combat_message)
                embed = Embed(
                    title="⚔️ 슬라임 전투 진행",
                    description=f"**슬라임 상태**\n❤️ HP: {slime['hp']}  |  ⚔️ ATK: {slime['atk']}  |  🛡️ DEF: {slime['defen']}",
                    colour=0xFF4500
                )
                for p_id, p_stats in players.items():
                    if p_stats["hp"] > 0:
                        status = "🏃‍♂️ 도망" if p_stats.get("escaped", False) else "⚔️ 전투 중"
                        embed.add_field(
                            name=f"👤 <@{p_id}>",
                            value=f"❤️ HP: {p_stats['hp']}  |  ⚔️ ATK: {p_stats['atk']}  |  🛡️ DEF: {p_stats['defen']}  |  {status}",
                            inline=True
                        )
                embed.add_field(name="📝 최근 행동", value=f"<@{pid}>의 차례입니다! (20초 내 선택)", inline=False)
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/slime_icon.png")
                embed.set_footer(text="버튼을 눌러 행동을 선택하세요!", icon_url="https://cdn.discordapp.com/emojis/clock_icon.png")
                await combat_message.edit(embed=embed, view=view)

                # 플레이어 응답 대기
                await view.wait()

                # 타임아웃 처리
                if view.result is None:
                    view.result = f"<@{pid}>가 20초 동안 응답하지 않았습니다!"
                    timeout_embed = Embed(
                        title="⏰ 타임아웃 경고",
                        description=f"⚠️ <@{pid}>가 행동을 선택하지 않아 턴이 종료되었습니다!",
                        colour=0xFFA500
                    )
                    timeout_embed.set_footer(text="다음 플레이어로 넘어갑니다...")
                    await interaction.channel.send(embed=timeout_embed)
                    await combat_message.edit(embed=embed, view=None)

                # 슬라임 처치 확인
                if slime["hp"] <= 0:
                    stats["quest_clears"] += 1
                    embed = Embed(
                        title="🏆 슬라임 처치 성공!",
                        description=f"🎉 <@{pid}>가 슬라임을 처치했습니다!",
                        colour=0x00FF00
                    )
                    embed.set_image(url="https://cdn.discordapp.com/emojis/victory_icon.png")
                    embed.set_footer(text="전투 종료!")
                    await combat_message.edit(embed=embed)
                    slime = None
                    break

                # 슬라임 반격 (도망친 플레이어 제외)
                if slime and players[pid]["hp"] > 0 and not players[pid].get("escaped", False):
                    damage_taken = max(0, slime["atk"] - players[pid]["defen"])
                    players[pid]["hp"] -= damage_taken
                    combat_embed = Embed(
                        title="⚔️ 슬라임 전투 진행",
                        description=f"**슬라임 상태**\n❤️ HP: {slime['hp']}  |  ⚔️ ATK: {slime['atk']}  |  🛡️ DEF: {slime['defen']}",
                        colour=0xFF4500
                    )
                    for p_id, p_stats in players.items():
                        if p_stats["hp"] > 0:
                            status = "🏃‍♂️ 도망" if p_stats.get("escaped", False) else "⚔️ 전투 중"
                            combat_embed.add_field(
                                name=f"👤 <@{p_id}>",
                                value=f"❤️ HP: {p_stats['hp']}  |  ⚔️ ATK: {p_stats['atk']}  |  🛡️ DEF: {p_stats['defen']}  |  {status}",
                                inline=True
                            )
                    combat_embed.add_field(
                        name="📝 최근 행동",
                        value=f"💥 슬라임 반격! <@{pid}>에게 {damage_taken} 데미지 (남은 HP: {players[pid]['hp']})",
                        inline=False
                    )
                    combat_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/slime_icon.png")
                    await combat_message.edit(embed=combat_embed)

                    # 플레이어 사망 확인
                    if players[pid]["hp"] <= 0:
                        defeat_embed = Embed(
                            title="💀 플레이어 쓰러짐",
                            description=f"😵 <@{pid}>가 슬라임의 공격으로 쓰러졌습니다!",
                            colour=0x8B0000
                        )
                        await interaction.channel.send(embed=defeat_embed)

            # 전투 종료 조건 (모두 사망하거나 도망)
            if slime and all(stats["hp"] <= 0 or stats.get("escaped", False) for stats in players.values()):
                embed = Embed(
                    title="💀 퀘스트 실패 또는 종료",
                    description="😢 모든 플레이어가 쓰러졌거나 도망쳤습니다...",
                    colour=0x000000
                )
                embed.set_image(url="https://cdn.discordapp.com/emojis/defeat_icon.png")
                embed.set_footer(text="다음엔 더 잘해보자...")
                await combat_message.edit(embed=embed)
                for pid in players:
                    db.update_character(pid, players[pid])
                return

    # 퀘스트 결과 표시
    result_embed = Embed(
        title="🏁 퀘스트 종료",
        colour=0xFFD700,
        timestamp=discord.utils.utcnow()
    )
    total_clears = sum(stats["quest_clears"] for stats in players.values())
    total_gear = sum(stats["gear"] for stats in players.values())
    if total_clears > 0 or total_gear > 0:
        result_embed.description = "🎉 오늘은 수확이 있다!"
        for pid, stats in players.items():
            status = "🏃‍♂️ 도망" if stats.get("escaped", False) else f"❤️ HP: {stats['hp']}"
            result_embed.add_field(
                name=f"👤 <@{pid}>",
                value=f"{status}  |  🏆 퀘스트 클리어: {stats['quest_clears']}  |  🎒 아이템: {stats['gear']}",
                inline=False
            )
    else:
        result_embed.description = "😔 오늘은 아무것도 하지 못했어..."
    result_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/quest_complete_icon.png")
    result_embed.set_footer(text="모험의 끝!", icon_url="https://cdn.discordapp.com/emojis/flag_icon.png")

    # 데이터베이스 업데이트
    for pid in players:
        db.update_character(pid, players[pid])
    await interaction.channel.send(embed=result_embed)

async def handle_judge_quest(interaction: Interaction, participants: list[User] = None):
    # 미구현 퀘스트 예시
    embed = Embed(
        title="⚡ 마을 밖 빤짝판사 처치",
        description="🛠 퀘스트를 시작합니다! (미구현)",
        colour=0x00CED1,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="준비 중...")
    await interaction.channel.send(embed=embed)