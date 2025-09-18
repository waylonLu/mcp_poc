from fastmcp import FastMCP
from typing import Dict, Any
from db.database import db
from clients.api_client import api_client
import sqlite3
import asyncio

# Create FastMCP server instances
mcp = FastMCP(name="api-integration-server")
mcp_banking = FastMCP(name="banking-server")

@mcp.tool(name="get_cherrypicks_info", 
          description="cherrypicks(创奇思科技有限公司) is the name of a company. This api returns the company's policies"
          )
async def get_cherrypicks_info(query: str) -> Dict[str, Any]:
    """
    Get cherrypicks info
    """
    try:
        params ={
            "inputs": {},
            "query": query,
            # "response_mode": "streaming",
            "response_mode": "blocking",
            "conversation_id": "",
            "user": "AI_Agent",
            "files": []
        }
                    
        result = await api_client.make_request("get_cherrypicks_info", params)
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Get cherrypicks info failed: {str(e)}"
        }

# 转账功能
@mcp_banking.tool(
    name="transfer_money",
    description="Transfer money from one account to another. Args: from_account_id (source account), to_account_id (destination account), amount (transfer amount), description (optional transfer note). Returns a result message."
)
def transfer_money(from_account_id: str, to_account_id: str, amount: float, description: str = None) -> str:
    """Transfer function
    
    Args:
        from_account_id: Source account ID
        to_account_id: Destination account ID
        amount: Transfer amount
        description: Transfer description (optional)
    """
    # Check if accounts exist
    from_account = db.get_account(from_account_id)
    to_account = db.get_account(to_account_id)
    
    if not from_account:
        return f"Error: Source account {from_account_id} does not exist"
    
    if not to_account:
        return f"Error: Destination account {to_account_id} does not exist"
    
    # Check if amount is valid
    if amount <= 0:
        return f"Error: Transfer amount must be greater than 0"
    
    # Check if balance is sufficient
    if from_account.balance < amount:
        return f"Error: Insufficient balance. Current balance: {from_account.balance}"
    
    # Execute transfer
    db.update_balance(from_account_id, -amount)
    db.update_balance(to_account_id, amount)
    tran = db.add_transaction(from_account_id, to_account_id, amount, description)
    
    return f"Transfer successful, transaction ID: {tran.id}! From account: {format_card_number(from_account.card_number)} to account: {format_card_number(to_account.card_number)} amount: {amount} RMB"

# 查询余额功能
@mcp_banking.tool(
    name="check_balance",
    description="Check the balance of a specific account. Args: account_id (account to check). Returns the current balance or error message."
)
def check_balance(account_id: str) -> str:
    """Check account balance
    
    Args:
        account_id: Account ID
    """
    account = db.get_account(account_id)
    
    if not account:
        return f"Error: Account {account_id} does not exist"
    
    return f"Account name: ({account.name})\nCard number: {format_card_number(account.card_number)} \nCurrent balance: {account.balance} RMB"

# 查询账户信息
@mcp_banking.tool(
    name="get_account_info",
    description="Get information of a specific account. Args: account_name (account to query). Returns account id, name or error message."
)
def get_account_info(account_name: str) -> str:
    """Query account information
    
    Args:
        account_name: Account name
    """
    account = db.get_account_by_name(account_name)
    
    if not account:
        return f"Error: Account {account_name} does not exist"
    
    return f"Account ID: {account.id}\nAccount name: {account.name}\n Card number: {format_card_number(account.card_number)}"

# 查询交易历史功能
@mcp_banking.tool(
    name="get_transaction_history",
    description="Get recent transaction history for an account. Args: account_id (account to query), limit (number of records, default 10). Returns formatted transaction list or error message."
)
def get_transaction_history(account_id: str, limit: int = 10) -> str:
    """Query account transaction history
    
    Args:
        account_id: Account ID
        limit: Number of records to return (default 10)
    """
    account = db.get_account(account_id)
    
    if not account:
        return f"Error: Account {account_id} does not exist"
    
    transactions = db.get_account_transactions(account_id, limit)
    
    if not transactions:
        return f"Account {account_id} has no transaction records"
    
    result = [f"Account {account_id} ({account.name}) transaction history (latest {len(transactions)} records):"]
    for i, t in enumerate(transactions, 1):
        if t.from_account == account_id:
            direction = "Outgoing"
            other_account = t.to_account
        else:
            direction = "Incoming"
            other_account = t.from_account
        
        result.append(
            f"{i}. {t.timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
            f"{direction} {other_account} {t.amount} RMB "
            f"{t.description or ''}"
        )
    
    return "\n".join(result)

# 列出所有账户功能
@mcp_banking.tool(
    name="list_accounts",
    description="List all accounts in the system. Returns a formatted list of account IDs, names, and balances."
)
def list_accounts() -> str:
    """List all accounts"""
    try:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT id, name, balance FROM accounts ORDER BY id")
            accounts = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    
    if not accounts:
        return "No accounts available"
    
    result = ["All accounts:"]
    for account in accounts:
        result.append(f"- {account[0]}: {account[1]} (Balance: {account[2]} RMB)")
    
    return "\n".join(result)

def format_card_number(card_number: str) -> str:
    """
    Format bank card number as 6217...1234, showing only the first 4 and last 4 digits.
    Example: '6222021234567890123' -> '6222...0123'
    """
    if not card_number or len(card_number) < 8:
        return card_number or ""
    return f"{card_number[:4]}...{card_number[-4:]}"

async def run_mcp():
    await mcp.run_async(transport="sse", host="0.0.0.0")

async def run_mcp_banking():
    await mcp_banking.run_async(transport="sse", port=8001, host="0.0.0.0")

async def main():
    # Run both services concurrently
    await asyncio.gather(run_mcp(), run_mcp_banking())

if __name__ == "__main__":
    asyncio.run(main())
