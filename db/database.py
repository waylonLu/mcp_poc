import sqlite3
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from schemas.bank_models import Account, Transaction
from schemas.financial_models import FinancialProduct, UserInvestment

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
            # 创建理财产品表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS financial_products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    min_investment REAL NOT NULL,
                    expected_return_rate REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'available'
                )
            """)
            # 创建用户投资记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_investments (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    investment_amount REAL NOT NULL,
                    investment_date TEXT NOT NULL,
                    expected_maturity_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (product_id) REFERENCES financial_products (id)
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
            ("1005", "David Wilson", 50000.0, "6222021001000005")
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
        
        # 插入示例理财产品
        sample_products = [
            ("FP001", "Stable Wealth 30 Days", "Low-risk 30-day fixed wealth management", 1000.0, 0.035, "Low Risk", 30, "available"),
            ("FP002", "Enhanced Yield 90 Days", "Medium-risk 90-day wealth management", 5000.0, 0.045, "Medium Risk", 90, "available"),
            ("FP003", "High Yield 180 Days", "High-risk high-yield wealth management", 10000.0, 0.065, "High Risk", 180, "available")
        ]
        conn.executemany(
            "INSERT INTO financial_products (id, name, description, min_investment, expected_return_rate, risk_level, duration_days, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            sample_products
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
    
    def get_financial_products(self) -> List[FinancialProduct]:
        """获取所有理财产品"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, description, min_investment, expected_return_rate, risk_level, duration_days, status FROM financial_products WHERE status = 'available'"
            )
            
            products = []
            for row in cursor.fetchall():
                products.append(FinancialProduct(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    min_investment=row[3],
                    expected_return_rate=row[4],
                    risk_level=row[5],
                    duration_days=row[6],
                    status=row[7]
                ))
            
            return products
    
    def get_financial_product(self, product_id: str) -> Optional[FinancialProduct]:
        """获取特定理财产品"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, description, min_investment, expected_return_rate, risk_level, duration_days, status FROM financial_products WHERE id = ?",
                (product_id,)
            )
            
            row = cursor.fetchone()
            if row:
                return FinancialProduct(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    min_investment=row[3],
                    expected_return_rate=row[4],
                    risk_level=row[5],
                    duration_days=row[6],
                    status=row[7]
                )
            return None
    
    def purchase_financial_product(self, account_id: str, product_id: str, amount: float) -> Optional[UserInvestment]:
        """购买理财产品"""
        with self.get_connection() as conn:
            # 检查账户是否存在且有足够余额
            account = self.get_account(account_id)
            if not account:
                return None
            
            # 检查理财产品是否存在
            product = self.get_financial_product(product_id)
            if not product:
                return None
            
            # 检查投资金额是否满足最低要求
            if amount < product.min_investment:
                return None
            
            # 检查账户余额是否足够
            if account.balance < amount:
                return None
            
            # 扣除账户余额
            conn.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (amount, account_id)
            )
            
            # 创建投资记录
            investment_id = str(uuid.uuid4())
            investment_date = datetime.now().isoformat()
            expected_maturity_date = (datetime.now() + timedelta(days=product.duration_days)).isoformat()
            
            conn.execute(
                "INSERT INTO user_investments (id, account_id, product_id, investment_amount, investment_date, expected_maturity_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (investment_id, account_id, product_id, amount, investment_date, expected_maturity_date, "active")
            )
            
            conn.commit()
            
            return UserInvestment(
                id=investment_id,
                account_id=account_id,
                product_id=product_id,
                investment_amount=amount,
                investment_date=datetime.fromisoformat(investment_date),
                expected_maturity_date=datetime.fromisoformat(expected_maturity_date),
                status="active"
            )
    
    def get_user_investments(self, account_id: str) -> List[UserInvestment]:
        """获取用户的所有投资记录"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, account_id, product_id, investment_amount, investment_date, expected_maturity_date, status 
                FROM user_investments 
                WHERE account_id = ? 
                ORDER BY investment_date DESC
                """,
                (account_id,)
            )
            
            investments = []
            for row in cursor.fetchall():
                investments.append(UserInvestment(
                    id=row[0],
                    account_id=row[1],
                    product_id=row[2],
                    investment_amount=row[3],
                    investment_date=datetime.fromisoformat(row[4]),
                    expected_maturity_date=datetime.fromisoformat(row[5]),
                    status=row[6]
                ))
            
            return investments

# 初始化数据库
db = Database()
