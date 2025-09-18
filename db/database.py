
import sqlite3
from typing import List, Optional
import uuid
from datetime import datetime
from schemas.bank_models import Account, Transaction

class Database:
    def __init__(self, db_path="db/db.sqlite3"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        print("初始化数据库...")
        with self.get_connection() as conn:
            # 创建账户表（含 card_number 字段）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    balance REAL NOT NULL DEFAULT 0.0,
                    card_number TEXT
                )
            """)
            # 创建交易记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    from_account TEXT NOT NULL,
                    to_account TEXT NOT NULL,
                    amount REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (from_account) REFERENCES accounts (id),
                    FOREIGN KEY (to_account) REFERENCES accounts (id)
                )
            """)
            # 插入示例数据（如果表为空）
            if conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0:
                self._insert_sample_data(conn)
            conn.commit()
    
    def _insert_sample_data(self, conn):
        # 插入示例账户
        print("插入示例数据...")
        sample_accounts = [
            ("1001", "John Smith", 1000.0, "6222021001000001"),
            ("1002", "Emma Johnson", 2000.0, "6222021001000002"),
            ("1003", "Michael Brown", 3000.0, "6222021001000003"),
            ("1004", "Sarah Davis", 7000.0, "6222021001000004"),
            ("1005", "David Wilson", 8000.0, "6222021001000005")
        ]
        conn.executemany(
            "INSERT INTO accounts (id, name, balance, card_number) VALUES (?, ?, ?, ?)",
            sample_accounts
        )
        
        # 插入示例交易记录
        sample_transactions = [
            (str(uuid.uuid4()), "1001", "1002", 100.0, datetime.now().isoformat(), "cost of lunch"),
            (str(uuid.uuid4()), "1002", "1003", 200.0, datetime.now().isoformat(), "cost of shopping")
        ]
        conn.executemany(
            "INSERT INTO transactions (id, from_account, to_account, amount, timestamp, description) VALUES (?, ?, ?, ?, ?, ?)",
            sample_transactions
        )
    
    def get_account(self, account_id: str) -> Optional[Account]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, balance, card_number FROM accounts WHERE id = ?",
                (account_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return Account(id=row[0], name=row[1], balance=row[2], card_number=row[3])
            return None
        
    def get_account_by_name(self, name: str) -> Optional[Account]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, balance, card_number FROM accounts WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            
            if row:
                return Account(id=row[0], name=row[1], balance=row[2], card_number=row[3])
            return None
    
    def update_balance(self, account_id: str, amount: float) -> bool:
        with self.get_connection() as conn:
            # 检查账户是否存在
            account = self.get_account(account_id)
            if not account:
                return False
            
            # 更新余额
            conn.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (amount, account_id)
            )
            conn.commit()
            return True
    
    def add_transaction(self, from_account: str, to_account: str, amount: float, description: str = None) -> Optional[Transaction]:
        with self.get_connection() as conn:
            transaction_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            conn.execute(
                "INSERT INTO transactions (id, from_account, to_account, amount, timestamp, description) VALUES (?, ?, ?, ?, ?, ?)",
                (transaction_id, from_account, to_account, amount, timestamp, description)
            )
            conn.commit()
            
            return Transaction(
                id=transaction_id,
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                timestamp=datetime.fromisoformat(timestamp),
                description=description
            )
    
    def get_account_transactions(self, account_id: str, limit: int = 10) -> List[Transaction]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, from_account, to_account, amount, timestamp, description 
                FROM transactions 
                WHERE from_account = ? OR to_account = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (account_id, account_id, limit)
            )
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append(Transaction(
                    id=row[0],
                    from_account=row[1],
                    to_account=row[2],
                    amount=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    description=row[5]
                ))
            
            return transactions

# 初始化数据库
db = Database()