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
        """유저와 인벤토리 테이블 생성"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                # 유저 테이블 (discord_id, 스탯)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        discord_id TEXT PRIMARY KEY,
                        hp INTEGER DEFAULT 50,
                        atk INTEGER DEFAULT 5,
                        luk INTEGER DEFAULT 10,
                        kills INTEGER DEFAULT 0
                    )
                ''')
                # 인벤토리 테이블 (discord_id, 아이템)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        discord_id TEXT,
                        item TEXT,
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
                c.execute("SELECT hp, atk, luk, kills FROM users WHERE discord_id = ?", (discord_id,))
                user = c.fetchone()
                if user:
                    return {"hp": user[0], "atk": user[1], "luk": user[2], "kills": user[3]}
                return None
            finally:
                conn.close()
        return None

    def update_user_stats(self, discord_id: str, hp: int, kills: int):
        """유저 스탯 업데이트"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("UPDATE users SET hp = ?, kills = ? WHERE discord_id = ?", (hp, kills, discord_id))
                conn.commit()
            except Error as e:
                print(f"스탯 업데이트 오류: {e}")
            finally:
                conn.close()

    def add_item(self, discord_id: str, item: str):
        """인벤토리에 아이템 추가"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("INSERT INTO inventory (discord_id, item) VALUES (?, ?)", (discord_id, item))
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
                c.execute("SELECT item FROM inventory WHERE discord_id = ?", (discord_id,))
                items = [row[0] for row in c.fetchall()]
                return items
            finally:
                conn.close()
        return []
