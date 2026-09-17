# Project Purpose and Use Cases

Fomo Trader Intelligence is an interactive research and monitoring client for the [Fomo API](https://getfomoapi.fun). It helps users examine normalized Fomo Family social trading data from a terminal without manually building HTTP requests or parsing large JSON responses.

## The Problem It Solves

Trader data is spread across profiles, leaderboards, balances, swaps, rankings, and historical snapshots. A leaderboard alone does not explain whether a trader has broad experience, concentrated exposure, recent activity, or consistent results.

This project brings those data sources into one workflow:

```text
Discover traders
      |
Resolve identity and wallets
      |
Inspect positions and activity
      |
Add selected traders to a watchlist
      |
Monitor changes and export research
```

It is designed to support investigation and strategy development, not automatic execution.

## Intended Users

| User | How the project helps |
|---|---|
| Individual researcher | Explore trader behavior from a guided terminal interface |
| Strategy developer | Collect examples and exports for signal research |
| Wallet monitor builder | Use watchlists, deduplication, and position comparisons as a reference |
| Risk analyst | Compare exposure, cost basis, PnL, network, and activity |
| Fomo API integrator | Study a working Python client with retry and rate-limit handling |

## Core Use Cases

### 1. Discover Candidate Traders

The leaderboard view can query four windows:

| Window | Typical research question |
|---|---|
| `24h` | Who has performed strongly during the latest daily period? |
| `7d` | Is recent performance broader than a single day? |
| `30d` | Has the trader sustained results over a longer period? |
| `all` | How does the trader compare over the complete indexed history? |

Useful fields include 24-hour PnL, total volume, trade count, followers, and a resolved wallet. Candidate discovery should compare multiple windows rather than selecting the highest daily PnL.

**Example workflow:**

1. Load ten traders from the `24h` leaderboard.
2. Repeat with `7d` and `30d`.
3. Note handles that appear consistently.
4. Resolve each profile.
5. Review account age, trade count, total volume, wallets, and holdings.
6. Add only relevant profiles to the local watchlist.

### 2. Research a Trader's Portfolio

The portfolio view normalizes each balance into a common display:

- Token symbol and address
- Network name or numeric network ID
- Human-readable amount
- Current quoted price
- Estimated market value
- Current cost basis
- Estimated unrealized PnL

The estimated value uses:

```text
human-readable balance x quoted USD price
```

Estimated unrealized PnL uses:

```text
estimated market value - current cost basis
```

The application performs financial arithmetic with Python `Decimal` values to avoid unnecessary binary floating-point errors.

> **Note:** A displayed value depends on the API's indexed balance and quoted price. It is not a guaranteed liquidation value or executable quote.

### 3. Inspect Recent Swap Activity

The swap view displays normalized swap events with:

- Timestamp
- Primary network
- Received and sent amounts
- Input and output token addresses
- Estimated USD amount
- Execution provider

This can answer questions such as:

- Has the trader been active recently?
- Which network is being used?
- Is activity made of small repeated swaps or larger allocations?
- Does the swap history align with the current portfolio?

Swap token fields must be interpreted using `networkId`, `inNetworkId`, and `outNetworkId`. An address beginning with `0x` is generally an EVM contract, while a non-EVM string may be a Solana mint or another network-specific address.

### 4. Maintain a Local Watchlist

Resolved profiles can be stored in `data/fomo_bot.db`. A watched record includes:

| Field | Purpose |
|---|---|
| User ID | Stable key for protected trader endpoints |
| Handle | Human-readable profile identifier |
| Display name | Terminal presentation |
| Solana wallet | Independent Solana research |
| EVM wallet | Independent EVM research |
| Added timestamp | Local watchlist history |

The local watchlist belongs to the application. It is different from `/api/users/current/following-ids`, which reflects the upstream Fomo identity used by the service.

### 5. Detect Newly Observed Activity

Monitoring polls each watched trader for swaps and balances. It stores swap IDs under a unique SQLite key, which prevents the same indexed event from being reported repeatedly.

Balances are normalized by:

```text
user ID + network ID + token address
```

The latest normalized state is compared with the previous state to classify positions as:

- **Opened:** Previous amount was zero and current amount is positive.
- **Increased:** Current amount is greater than the previous amount.
- **Reduced:** Current amount is less than the previous amount but remains present.
- **Closed:** Previous amount was positive and current amount is zero or absent.

The first monitor cycle stores a baseline. Reports begin on later cycles so existing swaps are not presented as newly occurring signals.

> **Warning:** A balance change does not prove that a swap occurred. Transfers, deposits, withdrawals, token rebases, and index corrections can also change a balance.

### 6. Export a Research Snapshot

The export operation collects:

- Resolved profile
- Current balances and related portfolio data
- Up to 150 recent swaps
- Current rankings
- UTC export timestamp

The resulting JSON file can be archived, compared outside the application, or used as input to an independent analysis pipeline.

## What the Project Does Not Do

Fomo Trader Intelligence does not:

- Sign or submit blockchain transactions
- Store wallet private keys or seed phrases
- Connect to an exchange account
- Calculate a safe execution quote
- Verify token contracts or mint authority
- Validate liquidity, holder concentration, taxes, or transfer restrictions
- Guarantee API freshness or final blockchain state
- Convert comments or profile text into executable instructions
- Provide financial advice

## Responsible Research Workflow

Before using observed activity in a strategy, independently validate:

1. Network ID and token address
2. Token decimals and metadata
3. Current onchain price and available liquidity
4. Pool route, slippage, and price impact
5. Contract restrictions and token taxes where applicable
6. Holder concentration and token age
7. Transaction timestamp and finality
8. Position sizing and portfolio-level risk
9. Duplicate-event and idempotency controls
10. Manual approval requirements

## Example Research Scenario

Suppose a trader appears near the top of the 24-hour leaderboard.

1. Check the trader's 7-day and 30-day ranking.
2. Resolve the handle and confirm both wallet mappings.
3. Inspect total trades, volume, followers, and average holding time.
4. Open the portfolio and identify concentration in the largest holdings.
5. Review recent swaps for position entries or exits.
6. Add the trader to the watchlist.
7. Run monitoring to observe future indexed changes.
8. Export a snapshot for offline comparison.
9. Verify relevant wallet and token activity independently onchain.

This process produces a richer research record than reacting to one leaderboard number.

## Best Practices

- Compare multiple performance windows.
- Prefer repeated evidence over isolated activity.
- Treat large PnL figures as data that needs context.
- Keep API and signing systems completely separate.
- Use independent RPC or indexer data for time-sensitive decisions.
- Retain exports when reproducibility matters.
- Back up the SQLite database if the watchlist is valuable.
- Stop monitoring cleanly with `Ctrl+C` before moving database files.
