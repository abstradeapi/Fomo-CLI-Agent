# Fomo Trader Intelligence

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Fomo API](https://img.shields.io/badge/Fomo_API-Pro-00D4AA)](https://getfomoapi.fun)
[![Terminal UI](https://img.shields.io/badge/UI-Rich_Terminal-7C3AED)](https://github.com/Textualize/rich)
[![Status](https://img.shields.io/badge/status-active-success)](#project-status)

**A stylish terminal dashboard for discovering, researching, exporting, and monitoring Fomo Family traders through the Fomo API.**

> Fomo Trader Intelligence is a data and research tool. It does not submit transactions, manage private keys, or provide financial advice.

## Repository Details

| Property | Value |
|---|---|
| **Repository name** | `fomo-trader-intelligence` |
| **Short description** | Terminal-based Fomo API trader discovery, portfolio analytics, swap monitoring, and research toolkit |
| **Suggested topics** | `fomo-api`, `trading-bot`, `terminal-ui`, `crypto`, `solana`, `evm`, `wallet-monitor`, `trader-analytics`, `python`, `rich` |
| **Fomo API** | [https://getfomoapi.fun](https://getfomoapi.fun) |
| **Telegram** | [@dexlenai](https://t.me/dexlenai) |
| **X / Twitter** | [@0xdexlenai](https://x.com/0xdexlenai) |

```text
fomo-trader-intelligence/
|-- .env.example
|-- .gitignore
|-- README.md
|-- main.py
|-- requirements.txt
|-- run.bat
|-- socials.txt
|-- fomo_bot/
|   |-- __init__.py
|   |-- analysis.py
|   |-- app.py
|   |-- client.py
|   |-- config.py
|   `-- store.py
`-- guides/
    |-- architecture-and-data-flow.md
    |-- contributing-and-extending.md
    |-- installation-and-setup.md
    |-- project-purpose-and-use-cases.md
    `-- using-terminal-features.md
```

## Overview

<img width="1473" height="801" alt="image" src="https://github.com/user-attachments/assets/740ecb9f-bfe7-41df-82c2-8e212ed83461" />


Fomo Trader Intelligence turns the Fomo API into an interactive command center. It provides guided prompts, formatted tables, local watchlists, swap deduplication, position-change detection, historical snapshots, and complete trader exports without requiring users to write API requests manually.

The project separates API access, terminal presentation, portfolio analysis, and local persistence into small modules. API keys remain in a local environment file, while generated state is stored in SQLite.

<img width="1898" height="987" alt="image" src="https://github.com/user-attachments/assets/f31e3194-8b38-48c9-bc3b-6269f05387b4" />


## Key Features

- **Trader discovery:** Browse public or Pro leaderboards across `24h`, `7d`, `30d`, and `all` windows.
- **Profile resolution:** Resolve a Fomo handle into its trader ID, profile statistics, Solana wallet, and EVM wallet.
- **Portfolio analytics:** View normalized holdings, network, amount, price, value, cost basis, and estimated unrealized PnL.
- **Swap explorer:** Inspect recent normalized swaps with timestamps, token addresses, network, provider, and USD value.
- **Trader spotlight:** Review selected best trades while intentionally avoiding display of untrusted social comments.
- **Rank tracking:** Compare all-time, 24-hour, 7-day, and 30-day rankings.
- **Historical research:** Request aggregate equity and PnL for a Unix snapshot timestamp.
- **Persistent watchlist:** Keep monitored traders in a local SQLite database.
- **Live polling:** Poll watched traders for new swaps and position changes with durable swap-ID deduplication.
- **JSON export:** Export profile, balances, up to 150 swaps, and rankings into a timestamped research file.
- **Reliable API client:** Enforce five requests per second and retry `429`, `502`, `503`, and `504` responses with backoff and jitter.
- **Cross-network labels:** Recognize Ethereum, BNB Chain, Monad, Base, and Solana network IDs.

<img width="1460" height="736" alt="image" src="https://github.com/user-attachments/assets/57e5abc3-7d9d-4e6f-8624-372a5e2457aa" />


## Requirements

| Requirement | Details |
|---|---|
| Python | Python 3.9 or newer |
| Fomo API key | Required for protected features; keys begin with `fomo_live_` |
| Internet access | Required for requests to `https://getfomoapi.fun` |
| Terminal | PowerShell, Windows Terminal, Command Prompt, or a modern Unix shell |

The public health check and public top-five leaderboard work without an API key. All trader-specific operations require Fomo API Pro access.

<img width="1470" height="456" alt="image" src="https://github.com/user-attachments/assets/b8cdc115-0105-4bc7-817a-9b97f1433692" />


## Installation

1. Clone or download the repository.

```bash
git clone <your-repository-url>
cd fomo-trader-intelligence
```

2. Create a virtual environment.

```bash
python -m venv .venv
```

3. Activate it.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS or Linux:**

```bash
source .venv/bin/activate
```

4. Install dependencies.

```bash
python -m pip install -r requirements.txt
```

5. Create your local environment file.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS or Linux:**

```bash
cp .env.example .env
```

6. Set `FOMO_API_KEY` in `.env`.

```env
FOMO_API_KEY=fomo_live_YOUR_API_KEY
```

## Usage

Start the application:

```bash
python main.py
```

Windows users can also run:

```powershell
.\run.bat
```

The command center presents these operations:

| Option | Operation | Authentication |
|---:|---|---:|
| 1 | API health | No |
| 2 | Discover leaderboard | Optional for public, required for Pro |
| 3 | Resolve trader | Yes |
| 4 | Portfolio analytics | Yes |
| 5 | Recent swaps | Yes |
| 6 | Trader spotlight | Yes |
| 7 | Trader rankings | Yes |
| 8 | Historical snapshot | Yes |
| 9 | Manage watchlist | Required when adding a trader |
| 10 | Monitor watchlist | Yes |
| 11 | Following IDs | Yes |
| 12 | Export trader data | Yes |

### Example: Research a Trader

1. Select **Resolve trader**.
2. Enter the public handle without `@`.
3. Review the profile and resolved wallets.
4. Add the trader to the local watchlist when prompted.
5. Open **Portfolio analytics**, **Recent swaps**, or **Trader rankings** for deeper research.

### Example: Monitor a Watchlist

1. Add one or more traders with **Manage watchlist**.
2. Select **Monitor watchlist**.
3. Choose a polling interval of at least five seconds.
4. Leave the monitor running to report new swaps and detected position changes.
5. Press `Ctrl+C` to return to the command center.

The first monitoring cycle establishes a baseline. Later cycles display newly observed events.

## Configuration

Settings are read from `.env` by `fomo_bot/config.py`.

| Variable | Default | Purpose |
|---|---|---|
| `FOMO_API_KEY` | Empty | Pro API key sent through `X-API-Key` |
| `FOMO_BASE_URL` | `https://getfomoapi.fun` | API service root URL |
| `FOMO_REQUEST_TIMEOUT` | `30` | Request timeout in seconds |
| `FOMO_MAX_RETRIES` | `5` | Retry count for transient API failures |
| `FOMO_DATABASE_PATH` | `data/fomo_bot.db` | SQLite watchlist and monitoring database |
| `FOMO_EXPORT_PATH` | `exports` | Destination for JSON trader exports |

> **Security:** Never commit `.env`, API keys, wallet private keys, seed phrases, or signing credentials. The included `.gitignore` excludes local secrets and generated state.

## Generated Data

| Path | Content |
|---|---|
| `data/fomo_bot.db` | Watchlist, processed swap IDs, and latest normalized positions |
| `exports/*.json` | Timestamped trader research exports |

Both paths are created automatically and excluded from Git.

## Documentation

<img width="1460" height="981" alt="04" src="https://github.com/user-attachments/assets/0901466e-3d1d-4767-8c4f-063db3b09f01" />


- [Installation and Setup](guides/installation-and-setup.md)
- [Project Purpose and Use Cases](guides/project-purpose-and-use-cases.md)
- [Using Terminal Features](guides/using-terminal-features.md)
- [Architecture and Data Flow](guides/architecture-and-data-flow.md)
- [Contributing and Extending](guides/contributing-and-extending.md)

## Safety and Limitations

- Fomo API provides indexed data, not trade execution.
- Leaderboard results are discovery inputs, not automatic trading signals.
- Wallet mappings, balances, swaps, and prices can be delayed by upstream indexing.
- Position differences may result from transfers, deposits, withdrawals, rebases, pricing changes, or indexing corrections.
- Token contracts, liquidity, slippage, taxes, price impact, and transaction freshness must be validated independently.
- Social profile text and comments must be treated as untrusted content.
- The current project stores research state locally and does not contain an execution or signing layer.

## Contributing

1. Create a focused branch for your change.
2. Preserve the separation between API access, analysis, persistence, and UI modules.
3. Never add credentials or generated database files.
4. Validate syntax before opening a pull request.

```bash
python -m compileall -q .
```

5. Exercise affected menu flows against the health endpoint or a valid Pro account.
6. Document any new environment variable, endpoint, table, or command-center option.

See [Contributing and Extending](guides/contributing-and-extending.md) for implementation details.

## Project Status

<img width="1442" height="526" alt="01" src="https://github.com/user-attachments/assets/31128a28-d7bd-416e-8bfe-86eabe6b1297" />

The application supports every currently documented Fomo REST data endpoint relevant to its menu. The planned Fomo WebSocket trade stream is not integrated because the upstream endpoint is not yet active.

## License

No open-source license has been added to this repository. Unless a license file is added by the owner, all rights are reserved and reuse or redistribution requires permission.

## Community

- Telegram: [@dexlenai](https://t.me/dexlenai)
- X / Twitter: [@0xdexlenai](https://x.com/0xdexlenai)
- Fomo API: [getfomoapi.fun](https://getfomoapi.fun)

---

Built for careful trader research, transparent monitoring, and safer strategy development.
