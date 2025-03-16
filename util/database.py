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
                # 캐릭터 테이블
                c.execute('''
                    CREATE TABLE IF NOT EXISTS characters (
                        discord_id TEXT PRIMARY KEY,
                        lv INTEGER DEFAULT 0,
                        xp INTEGER DEFAULT 0,
                        hp INTEGER DEFAULT 50,
                        mp INTEGER DEFAULT 30,
                        atk INTEGER DEFAULT 5,
                        defen INTEGER DEFAULT 5,
                        dex INTEGER DEFAULT 5,
                        int INTEGER DEFAULT 5,
                        fai INTEGER DEFAULT 5,
                        aff INTEGER DEFAULT 5,
                        karma INTEGER DEFAULT 0,
                        fame INTEGER DEFAULT 0,
                        res INTEGER DEFAULT 5,
                        luk INTEGER DEFAULT 10,
                        quest_clears INTEGER DEFAULT 0,
                        gold INTEGER DEFAULT 0,
                        cash INTEGER DEFAULT 0
                    )
                ''')
                # 자기소개 테이블
                c.execute('''
                    CREATE TABLE IF NOT EXISTS bio (
                        discord_id TEXT PRIMARY KEY,
                        bio TEXT CHECK(length(bio) <= 50),
                        FOREIGN KEY (discord_id) REFERENCES characters (discord_id)
                    )
                ''')
                # 인벤토리 테이블
                c.execute('''
                    CREATE TABLE IF NOT EXISTS inventory (
                        discord_id TEXT,
                        item_code TEXT,
                        quantity INTEGER DEFAULT 0,
                        PRIMARY KEY (discord_id, item_code),
                        FOREIGN KEY (discord_id) REFERENCES characters (discord_id)
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
                c.execute("""
                    INSERT OR IGNORE INTO characters (
                        discord_id, lv, xp, hp, mp, atk, defen, dex, int, fai, aff, 
                        karma, fame, res, luk, quest_clears, gold, cash
                    ) VALUES (?, 0, 0, 20, 10, 5, 5, 5, 5, 5, 5, 0, 0, 5, 5, 0, 20, 0)
                """, (discord_id,))
                conn.commit()
                return True
            except Error as e:
                print(f"유저 등록 오류: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_character(self, discord_id: str):
        """캐릭터 정보 조회"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("""
                    SELECT lv, xp, hp, mp, atk, defen, dex, int, fai, aff, karma, fame, 
                           res, luk, quest_clears, gold, cash 
                    FROM characters WHERE discord_id = ?
                """, (discord_id,))
                result = c.fetchone()
                if result:
                    return {
                        "lv": result[0], "xp": result[1], "hp": result[2], "mp": result[3],
                        "atk": result[4], "defen": result[5], "dex": result[6], "int": result[7],
                        "fai": result[8], "aff": result[9], "karma": result[10], "fame": result[11],
                        "res": result[12], "luk": result[13], "quest_clears": result[14],
                        "gold": result[15], "cash": result[16]
                    }
                return None
            except Error as e:
                print(f"캐릭터 조회 오류: {e}")
                return None
            finally:
                conn.close()
        return None

    def update_character(self, discord_id: str, stats: dict):
        """캐릭터 정보 업데이트"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                # 현재 캐릭터 정보를 가져와 기본값으로 사용
                current = self.get_character(discord_id) or {}
                c.execute("""
                    UPDATE characters SET 
                        lv = ?, xp = ?, hp = ?, mp = ?, atk = ?, defen = ?, dex = ?, int = ?, 
                        fai = ?, aff = ?, karma = ?, fame = ?, res = ?, luk = ?, 
                        quest_clears = ?, gold = ?, cash = ?
                    WHERE discord_id = ?
                """, (
                    stats.get("lv", current.get("lv", 0)),
                    stats.get("xp", current.get("xp", 0)),
                    stats.get("hp", current.get("hp", 20)),
                    stats.get("mp", current.get("mp", 10)),
                    stats.get("atk", current.get("atk", 5)),
                    stats.get("def", current.get("def", 5)),
                    stats.get("dex", current.get("dex", 5)),
                    stats.get("int", current.get("int", 5)),
                    stats.get("fai", current.get("fai", 5)),
                    stats.get("aff", current.get("aff", 5)),
                    stats.get("karma", current.get("karma", 0)),
                    stats.get("fame", current.get("fame", 0)),
                    stats.get("res", current.get("res", 5)),
                    stats.get("luk", current.get("luk", 5)),
                    stats.get("quest_clears", current.get("quest_clears", 0)),
                    stats.get("gold", current.get("gold", 0)),
                    stats.get("cash", current.get("cash", 0)),
                    discord_id
                ))
                conn.commit()
            except Error as e:
                print(f"캐릭터 업데이트 오류: {e}")
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
            except Error as e:
                print(f"자기소개 조회 오류: {e}")
                return None
            finally:
                conn.close()
        return None

    def add_item(self, discord_id: str, item_code: str, quantity: int = 1):
        """인벤토리에 아이템 추가 (수량 지정 가능, 기본값 1)"""
        conn = self.create_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO inventory (discord_id, item_code, quantity) 
                    VALUES (?, ?, ?) 
                    ON CONFLICT(discord_id, item_code) DO UPDATE SET quantity = quantity + ?
                """, (discord_id, item_code, quantity, quantity))
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
                c.execute("SELECT item_code, quantity FROM inventory WHERE discord_id = ?", (discord_id,))
                return dict(c.fetchall())  # {'1': 3, '2': 1, ...} 형태로 반환
            except Error as e:
                print(f"인벤토리 조회 오류: {e}")
                return {}
            finally:
                conn.close()
        return