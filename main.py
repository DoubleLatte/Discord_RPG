import sys
import os
import yaml
import discord
from discord.ext import commands
from discord import Game, Status

def resource_path(relative_path):
    """리소스 파일의 절대 경로를 반환 (개발 및 PyInstaller 환경 모두 지원)"""
    try:
        # PyInstaller는 임시 폴더를 생성하고 경로를 _MEIPASS에 저장
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_config():
    """config.yml 파일에서 설정 불러오기"""
    config_path = 'config.yml'
    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        print(f"오류: {config_path} 파일을 찾을 수 없습니다. 실행 파일과 같은 디렉토리에 있는지 확인하세요.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"{config_path} 파일 읽기 오류: {e}")
        sys.exit(1)

class MyBot(commands.Bot):
    def __init__(self, config):
        # 인텐트 설정
        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            sync_commands=True,
            application_id=config['application_id']
        )
        
        self.config = config
        self.initial_extensions = [
            "command.dev",  # 개발 명령어 추가
            # 추가 확장기능은 여기에 "폴더.파일명" 형식으로 추가
        ]

    async def setup_hook(self):
        """확장 기능 로드 및 명령어 동기화를 통한 봇 설정"""
        # 모든 확장 기능 로드
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                print(f"확장 기능 로드 성공: {ext}")
            except commands.ExtensionNotFound:
                print(f"오류: 확장 기능 {ext}을(를) 찾을 수 없습니다.")
            except commands.ExtensionFailed as e:
                print(f"오류: 확장 기능 {ext} 로드 실패. {e}")
        
        # 애플리케이션 명령어 동기화
        try:
            synced = await self.tree.sync()
            print(f"{len(synced)}개 명령어 동기화 완료")
        except discord.HTTPException as e:
            print(f"명령어 트리 동기화 오류: {e}")

    async def on_ready(self):
        """봇이 준비되었을 때 실행되는 이벤트"""
        print("===============")
        print("봇이 온라인 상태입니다")
        print(f"봇 이름: {self.user.name}")
        print(f"봇 ID: {self.user.id}")
        print("===============")
        
        # 봇 활동 상태 설정
        game = Game("~~~ 하는중")
        await self.change_presence(status=Status.online, activity=game)

def main():
    """봇의 주 실행 함수"""
    config = load_config()
    bot = MyBot(config)
    
    try:
        print("봇 시작 중...")
        bot.run(config['token'])
    except KeyError:
        print("오류: config.yml에서 'token'을 찾을 수 없습니다.")
        sys.exit(1)
    except discord.LoginFailure:
        print("오류: 로그인 실패. 토큰이 올바른지 확인하세요.")
        sys.exit(1)
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
