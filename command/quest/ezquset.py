# command/quest/ezquest.py
import discord
import random
from discord import Interaction, User
from util.database import Database

db = Database()

async def handle_slime_quest(interaction: Interaction, participants: list[User]):
    # 각 플레이어의 상태를 DB에서 불러오기
    players = {}
    for p in participants:
        user_id = str(p.id)
        stats = db.get_user(user_id)
        if stats:
            players[user_id] = stats.copy()
            players[user_id]["gear"] = sum(db.get_inventory(user_id).values())
    
    max_attempts = 10
    slime = None

    await interaction.channel.send(f"퀘스트 시작! 참여자 수: {len(participants)}명, 기회: {max_attempts}번")

    for attempt in range(max_attempts):
        event_chance = random.random()
        remaining_attempts = max_attempts - attempt - 1

        if event_chance < 0.5 and slime is None:
            slime = {"hp": random.randint(5, 15), "atk": random.randint(1, 3), "def": random.randint(0, 2)}
            is_elite = slime["hp"] == 15 and random.random() < 0.1
            if is_elite:
                slime["atk"] += 3
                await interaction.channel.send("⚠️ 엘리트 슬라임 등장!")
            else:
                await interaction.channel.send(f"슬라임 등장! (HP: {slime['hp']}, ATK: {slime['atk']})")

        elif event_chance < 0.8 and slime is None:
            gear = random.choice(["낡은 검", "가죽 갑옷", "작은 포션", "엘릭서"])
            lucky_player = random.choice(participants)
            db.add_item(str(lucky_player.id), gear)
            players[str(lucky_player.id)]["gear"] += 1
            await interaction.channel.send(f"<@{lucky_player.id}>가 아이템 발견: {gear}! 기회: {remaining_attempts}")

        elif slime is None:
            await interaction.channel.send(f"아무것도 발견하지 못했습니다... 기회: {remaining_attempts}")

        if slime:
            for pid in players:
                stats = players[pid]
                if stats["hp"] <= 0:
                    continue

                hit_chance = 0.8 + (stats["luk"] / 100)
                if random.random() < hit_chance:
                    crit_chance = stats["luk"] / 200
                    is_crit = random.random() < crit_chance
                    damage = (stats["atk"] * 2) if is_crit else stats["atk"]
                    slime["hp"] -= max(0, damage - slime["def"])
                    hit_msg = f"크리티컬! {damage} 데미지" if is_crit else f"{damage} 데미지"
                    await interaction.channel.send(f"<@{pid}> 공격: {hit_msg} (슬라임 HP: {slime['hp']})")
                else:
                    await interaction.channel.send(f"<@{pid}> 공격이 빗나갔습니다!")

                if slime["hp"] <= 0:
                    stats["quest_clears"] += 1
                    await interaction.channel.send(f"<@{pid}>가 슬라임을 처치했습니다!")
                    slime = None
                    break

            if slime:
                for pid in players:
                    stats = players[pid]
                    if stats["hp"] > 0:
                        # 방어력 적용: 슬라임 공격에서 def만큼 데미지 감소
                        damage_taken = max(0, slime["atk"] - stats["def"])
                        stats["hp"] -= damage_taken
                        await interaction.channel.send(f"슬라임 반격! <@{pid}>에게 {damage_taken} 데미지 (HP: {stats['hp']})")
                        if stats["hp"] <= 0:
                            await interaction.channel.send(f"<@{pid}>가 쓰러졌습니다!")

            if all(stats["hp"] <= 0 for stats in players.values()):
                await interaction.channel.send("퀘스트 실패: 모든 플레이어가 쓰러졌습니다... '슬라임에게 당하다니...'")
                for pid in players:
                    db.update_user_stats(pid, players[pid])
                return

    # 퀘스트 종료 후 DB 업데이트 및 결과 출력
    result_msg = "퀘스트 완료!\n"
    total_clears = sum(stats["quest_clears"] for stats in players.values())
    total_gear = sum(stats["gear"] for stats in players.values())
    if total_clears > 0 or total_gear > 0:
        result_msg += "오늘은 수확이 있다.\n"
        for pid, stats in players.items():
            result_msg += f"<@{pid}> - HP: {stats['hp']}, 퀘스트 클리어: {stats['quest_clears']}, 아이템: {stats['gear']}\n"
            db.update_user_stats(pid, stats)
    else:
        result_msg += "오늘은 아무것도 하지 못했어..."
        for pid in players:
            db.update_user_stats(pid, players[pid])
    await interaction.channel.send(result_msg)

async def handle_judge_quest(interaction: Interaction, participants: list[User] = None):
    await interaction.channel.send("마을 밖 빤짝판사 처치 퀘스트를 시작합니다! (미구현)")
