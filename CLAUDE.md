# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

API Integration MCP Server based on FastMCP framework that provides:
- Banking services (transfers, balance checks, transaction history, account management)
- Financial product browsing and purchases
- Expense report Excel generation with auto-upload
- Leave request submission (demo with 10-day annual leave balance)

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run MCP server (starts two servers: port 8000 for main MCP, port 8001 for banking)
python mcp_server.py

# Run tests (server must be running first)
python test_fill_expense.py
python test_upload.py
```

## Architecture

**Two concurrent FastMCP servers:**
- `mcp` (port 8000) - API integration tools, expense report filling, and leave request
- `mcp_banking` (port 8001) - Banking and financial product services

**Key modules:**
- `mcp_server.py` - Main entry point, defines all MCP tools
- `db/database.py` - SQLite database wrapper (singleton `db` instance)
- `schemas/` - Pydantic models (ConfigModel, APIConfig, Account, Transaction, FinancialProduct, UserInvestment)
- `clients/api_client.py` - HTTP client for external APIs (singleton `api_client`)
- `utils/config_loader.py` - YAML config loader with env var substitution (singleton `config_loader`)
- `config/api_config.yaml` - API endpoint definitions with `${ENV_VAR}` placeholders
- `template/` - Excel expense report templates

**Database schema (SQLite at `db/db.sqlite3`):**
- `accounts` - Bank accounts with id, name, balance, card_number
- `transactions` - Transfer records
- `financial_products` - Available investment products
- `user_investments` - User investment holdings

## Environment Variables

Required in `.env`:
- `UPLOAD_API_URL` - File upload endpoint
- `CHERRYPICKS_AUTHORIZATION` - Dify API auth token
- `X_N8N_API_KEY` - n8n API key

## Key Implementation Notes

- The `fill_expense_report` tool reads template from `template/报销表格_202501.xlsx`, fills it with expense items, and optionally uploads via `UPLOAD_API_URL`
- The `submit_leave_request` tool (port 8000) accepts: name, leave_type (personal/sick/annual), start_date, end_date. Annual leave deducts from a 10-day balance; personal/sick are demo only. Returns a formatted confirmation message.
- Bank card numbers are masked in output (shows first 4 and last 4 digits only)
- YAML config supports `${ENV_VAR}` syntax for secrets that get substituted at load time
- The API client (`api_client.make_request`) is currently unused by any tool but available for external API integration
