# command/quest/quest_handlers.py
import discord
import random
from discord import Interaction

async def handle_slime_quest(interaction: Interaction):
    # 초기 캐릭터 상태 (초보자용 낮은 난이도 + LUK 추가) 임시 데이터
    player_hp = 50
    player_atk = 5
    player_luk = 10  # 기본 행운 수치 (0~100 범위로 가정, 높을수록 유리)
    slime_kills = 0
    gear_found = 0
    max_attempts = 10

    # 퀘스트 시작 메시지
    await interaction.response.send_message(f"마을 앞 슬라임 처치 퀘스트를 시작합니다! 기회: {max_attempts}번, 행운: {player_luk}", ephemeral=True)

    # 10번의 이벤트 진행
    for attempt in range(max_attempts):
        event_chance = random.random()  # 0.0 ~ 1.0 사이 랜덤 값
        remaining_attempts = max_attempts - attempt - 1

        # 이벤트 1: 슬라임 등장 (50% 확률)
        if event_chance < 0.5:
            slime_hp = random.randint(5, 15)  # 낮은 난이도 HP
            slime_atk = random.randint(1, 3)
            slime_def = random.randint(0, 2)

            # 엘리트 슬라임 (10% 확률로 HP가 15일 때)
            is_elite = slime_hp == 15 and random.random() < 0.1
            if is_elite:
                slime_atk += 3  # 엘리트는 공격력 +3
                await interaction.followup.send("⚠️ 엘리트 슬라임 등장!", ephemeral=True)
            else:
                await interaction.followup.send(f"슬라임 등장! (HP: {slime_hp}, ATK: {slime_atk})", ephemeral=True)

            # 전투 로직 (LUK 반영)
            while slime_hp > 0 and player_hp > 0:
                # 명중률: LUK에 따라 공격이 빗나갈 확률 조정 (기본 80% + LUK/100)
                hit_chance = 0.8 + (player_luk / 100)
                if random.random() < hit_chance:
                    # 크리티컬 확률: LUK/200 (LUK 10일 때 5% 확률)
                    crit_chance = player_luk / 200
                    is_crit = random.random() < crit_chance
                    damage = (player_atk * 2) if is_crit else player_atk
                    slime_hp -= max(0, damage - slime_def)
                    hit_msg = f"크리티컬 공격! {damage} 데미지" if is_crit else f"{damage} 데미지"
                    await interaction.followup.send(f"공격 성공: {hit_msg}", ephemeral=True)
                else:
                    await interaction.followup.send("공격이 빗나갔습니다!", ephemeral=True)

                # 슬라임 반격 (플레이어 HP 감소)
                if slime_hp > 0:
                    player_hp -= slime_atk
                    await interaction.followup.send(f"슬라임의 반격! {slime_atk} 데미지 (남은 HP: {player_hp})", ephemeral=True)

            if player_hp <= 0:
                await interaction.followup.send("퀘스트 실패: 체력이 모두 소진되었습니다... '슬라임에게 당하다니...' ", ephemeral=True)
                return  # 퀘스트 종료

            slime_kills += 1
            await interaction.followup.send(f"슬라임을 처치했습니다! 남은 HP: {player_hp}, 기회: {remaining_attempts}", ephemeral=True)

        # 이벤트 2: 장비 획득 (30% 확률)
        elif event_chance < 0.8:  # 0.5 ~ 0.8
            gear = random.choice(["낡은 검", "가죽 갑옷", "작은 포션"])
            gear_found += 1
            await interaction.followup.send(f"장비 발견: {gear}! 기회: {remaining_attempts}", ephemeral=True)

        # 이벤트 3: 아무것도 안 나옴 (20% 확률)
        else:  # 0.8 ~ 1.0
            await interaction.followup.send(f"아무것도 발견하지 못했습니다... 기회: {remaining_attempts}", ephemeral=True)

    # 퀘스트 종료 후 결과
    if slime_kills > 0 or gear_found > 0:
        result_msg = f"퀘스트 완료! 오늘은 수확이 있다.\n- 슬라임 처치: {slime_kills}\n- 장비 획득: {gear_found}"
    else:
        result_msg = "퀘스트 완료: 오늘은 아무것도 하지 못했어..."
    
    await interaction.followup.send(result_msg, ephemeral=True)

async def handle_judge_quest(interaction: Interaction):
    await interaction.response.send_message("마을 밖 빤짝판사 처치 퀘스트를 시작합니다!", ephemeral=True)
