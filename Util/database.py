# util/database.py
import sqlite3
from sqlite3 import Error

class Database:
    def __init__(self, db_file="rpg_database.db"):
        self.db_file = db_file
        self.create_tables()

    def create_connection(self):
        """DB 연결 생성"""
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except Error as e:
            print(f"DB 연결 오류: {e}")
            return None

    def create_tables(self):
        """테이블 생성"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                # 유저 테이블 (방어력 추가)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        discord_id TEXT PRIMARY KEY,
                        hp INTEGER DEFAULT 50,
                        mp INTEGER DEFAULT 30,
                        atk INTEGER DEFAULT 5,
                        def INTEGER DEFAULT 5,  -- 방어력
                        dex INTEGER DEFAULT 5,  -- 민첩
                        int INTEGER DEFAULT 5,  -- 지능
                        fai INTEGER DEFAULT 5,  -- 신앙
                        aff INTEGER DEFAULT 5,  -- 친화력
                        karma INTEGER DEFAULT 0, -- 카르마
                        fame INTEGER DEFAULT 0, -- 명성
                        res INTEGER DEFAULT 5,  -- 저항
                        luk INTEGER DEFAULT 10, -- 행운
                        quest_clears INTEGER DEFAULT 0
                    )
                ''')
                # 자기소개 테이블
                c.execute('''
                    CREATE TABLE IF NOT EXISTS bio (
                        discord_id TEXT PRIMARY KEY,
                        bio TEXT CHECK(length(bio) <= 50),
                        FOREIGN KEY (discord_id) REFERENCES users (discord_id)
                    )
                ''')
                # 인벤토리 테이블
                c.execute('''
                    CREATE TABLE IF NOT EXISTS inventory (
                        discord_id TEXT,
                        item TEXT,
                        quantity INTEGER DEFAULT 0,
                        PRIMARY KEY (discord_id, item),
                        FOREIGN KEY (discord_id) REFERENCES users (discord_id)
                    )
                ''')
                conn.commit()
            except Error as e:
                print(f"테이블 생성 오류: {e}")
            finally:
                conn.close()

    def register_user(self, discord_id: str):
        """유저 등록"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO users (discord_id) VALUES (?)", (discord_id,))
                conn.commit()
                return True
            except Error as e:
                print(f"유저 등록 오류: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_user(self, discord_id: str):
        """유저 정보 조회"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("SELECT hp, mp, atk, def, dex, int, fai, aff, karma, fame, res, luk, quest_clears FROM users WHERE discord_id = ?", (discord_id,))
                user = c.fetchone()
                if user:
                    return {
                        "hp": user[0], "mp": user[1], "atk": user[2], "def": user[3], "dex": user[4],
                        "int": user[5], "fai": user[6], "aff": user[7], "karma": user[8], "fame": user[9],
                        "res": user[10], "luk": user[11], "quest_clears": user[12]
                    }
                return None
            finally:
                conn.close()
        return None

    def update_user_stats(self, discord_id: str, stats: dict):
        """유저 스탯 업데이트"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("""
                    UPDATE users SET hp = ?, mp = ?, atk = ?, def = ?, dex = ?, int = ?, fai = ?, 
                    aff = ?, karma = ?, fame = ?, res = ?, luk = ?, quest_clears = ? WHERE discord_id = ?
                """, (
                    stats["hp"], stats["mp"], stats["atk"], stats["def"], stats["dex"], stats["int"],
                    stats["fai"], stats["aff"], stats["karma"], stats["fame"], stats["res"], stats["luk"],
                    stats["quest_clears"], discord_id
                ))
                conn.commit()
            except Error as e:
                print(f"스탯 업데이트 오류: {e}")
            finally:
                conn.close()

    def set_bio(self, discord_id: str, bio: str):
        """자기소개 설정 (50자 제한)"""
        if len(bio) > 50:
            return False
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO bio (discord_id, bio) VALUES (?, ?)", (discord_id, bio))
                conn.commit()
                return True
            except Error as e:
                print(f"자기소개 설정 오류: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_bio(self, discord_id: str):
        """자기소개 조회"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("SELECT bio FROM bio WHERE discord_id = ?", (discord_id,))
                result = c.fetchone()
                return result[0] if result else None
            finally:
                conn.close()
        return None

    def add_item(self, discord_id: str, item: str):
        """인벤토리에 아이템 추가 (수량 +1)"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO inventory (discord_id, item, quantity) 
                    VALUES (?, ?, 1) 
                    ON CONFLICT(discord_id, item) DO UPDATE SET quantity = quantity + 1
                """, (discord_id, item))
                conn.commit()
            except Error as e:
                print(f"아이템 추가 오류: {e}")
            finally:
                conn.close()

    def get_inventory(self, discord_id: str):
        """인벤토리 조회"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("SELECT item, quantity FROM inventory WHERE discord_id = ?", (discord_id,))
                return {row[0]: row[1] for row in c.fetchall()}
            finally:
                conn.close()
        return {}
