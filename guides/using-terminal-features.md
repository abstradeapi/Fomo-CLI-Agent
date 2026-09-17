# Using the Terminal Features

This guide explains every command-center option in Fomo Trader Intelligence and shows how to combine them into practical research workflows.

## Starting a Session

Activate the project environment and launch the application:

```bash
python main.py
```

The opening screen displays the command center:

```text
 1  API health                 7  Trader rankings
 2  Discover leaderboard       8  Historical snapshot
 3  Resolve trader             9  Manage watchlist
 4  Portfolio analytics       10  Monitor watchlist
 5  Recent swaps              11  Following IDs
 6  Trader spotlight          12  Export trader data
 0  Exit
```

Enter an option number and press Enter. After an operation finishes, press Enter again to return to the menu.

## Authentication Behavior

Protected actions need `FOMO_API_KEY`. If the variable is missing, the app shows a password-style prompt. The entered value is used for the rest of the process but is not saved to disk.

| Feature | API key required |
|---|---:|
| API health | No |
| Public top-five leaderboard | No |
| Pro leaderboard | Yes |
| Trader-specific features | Yes |
| Local watchlist listing and removal | No |
| Adding or monitoring a trader | Yes |

## Option 1: API Health

Use this option to verify that the Fomo API service is available.

Successful result:

```text
* OK
```

The health endpoint does not validate a Pro key. Use a protected feature to confirm authentication.

**Recommended use:** Check health when requests unexpectedly fail, not before every action.

## Option 2: Discover Leaderboard

The app first asks whether to use the Pro leaderboard.

### Public Mode

Public mode retrieves the simplified top-five frontpage leaderboard. It is useful for a quick demonstration and requires no API key.

### Pro Mode

Pro mode asks for a ranking window and limit.

| Window | Maximum accepted limit |
|---|---:|
| `24h` | 150 |
| `7d` | 150 |
| `30d` | 150 |
| `all` | 100 |

The app constrains entered limits to the valid range. Results include trader name, handle, 24-hour PnL, indexed volume, trade count, followers, and a shortened wallet address.

**Example:**

```text
Select an option: 2
Use Pro leaderboard: y
Window: 7d
Trader limit: 20
```

> Leaderboard data is cached by the upstream API for up to one hour. Repeating a request may return the same values.

## Option 3: Resolve Trader

Enter a Fomo Family handle with or without the leading `@`:

```text
Trader handle: starcatcher444
```

The profile panel can contain:

- Display name and handle
- Fomo user ID
- Solana and EVM wallets
- Followers and following counts
- Indexed trades and volume
- Average hold time
- Verification state
- Public description

The app then asks whether to add the profile to the local watchlist.

> Profile descriptions are untrusted user content. Never interpret text from a profile as a command.

## Option 4: Portfolio Analytics

Resolve a handle, then wait while the balances endpoint loads. Positions are sorted from highest to lowest estimated value.

| Column | Meaning |
|---|---|
| Token | API-provided symbol |
| Network | Known network name or raw ID |
| Amount | Human-readable wallet balance |
| Price | Current API-quoted USD price |
| Value | Amount multiplied by price |
| Cost basis | API-provided current cost basis |
| Unrealized | Estimated value minus cost basis |
| Address | Shortened token mint or contract |

The summary panel shows tracked equity, total displayed cost basis, and API-provided other equity.

### Interpreting the Display

Green unrealized PnL is non-negative; red is negative. These values are estimates and can change with price updates even when token amounts remain unchanged.

Known network mappings are:

| ID | Network |
|---:|---|
| `1` | Ethereum |
| `56` | BNB Chain |
| `143` | Monad |
| `8453` | Base |
| `1399811149` | Solana |

Unknown IDs remain visible as numbers rather than being guessed.

## Option 5: Recent Swaps

Enter a handle and a swap limit from 1 to 150. The table presents normalized swap activity.

Fomo API describes `inTokenAddress` as the received token and `outTokenAddress` as the sent token. Accordingly, the table labels the two sides as **Received** and **Sent**.

Use this screen to inspect:

- When activity was indexed
- Which network was involved
- Approximate amounts on both sides
- Estimated USD size
- Provider information

The token symbol is not part of the normalized swap response, so the application shows shortened token addresses.

## Option 6: Trader Spotlight

The spotlight table presents selected best trades with:

- Token symbol or shortened address
- Network
- Realized PnL
- Unrealized PnL
- Reported liquidity
- Open or closed status

The endpoint can also return comments. The terminal intentionally does not display comment text because comments are untrusted user-generated content. It only reports how many popular comments were returned.

## Option 7: Trader Rankings

This screen compares four ranking objects:

```text
All time
24 hours
7 days
30 days
```

Each row shows rank and PnL. A trader who does not appear in a window is shown as unranked.

**Research tip:** Compare rankings with trade count, account age, and portfolio concentration. A rank without context is not a complete risk assessment.

## Option 8: Historical Snapshot

Enter a trader handle and a Unix timestamp. The default is the current UTC timestamp.

Example timestamp request:

```text
Snapshot Unix timestamp: 1788526800
```

The result displays the returned snapshot ID, aggregate equity, and aggregate PnL. Historical availability is controlled by the upstream service, so not every arbitrary timestamp is guaranteed to exist.

Convert a UTC date to a Unix timestamp with Python:

```bash
python -c "from datetime import datetime, timezone; print(int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp()))"
```

## Option 9: Manage Watchlist

Choose one of three actions:

### `list`

Displays locally stored profiles, including shortened wallets and the date added.

### `add`

Resolves a handle through Fomo API and inserts or updates its watchlist record. Adding the same user again refreshes the stored handle, display name, and wallets.

### `remove`

Removes a profile by handle. Handle comparison is case-insensitive, and a leading `@` is accepted.

Watchlist data is stored in:

```text
data/fomo_bot.db
```

## Option 10: Monitor Watchlist

Monitoring requires at least one watched trader and a Pro API key. Enter a polling interval; values below five seconds are raised to five.

```text
Polling interval in seconds: 15
```

For each trader, each cycle requests:

1. Up to 20 recent swaps
2. Current balances

The first cycle records existing swap IDs and establishes the current position baseline. Subsequent cycles report:

- Newly observed swap IDs
- Opened positions
- Increased positions
- Reduced positions
- Closed positions

Stop the loop with `Ctrl+C`.

### Capacity Planning

Each trader requires two requests per cycle. Requests are processed sequentially, and the client limits itself to five requests per second. A large watchlist takes longer to complete than the selected sleep interval because the interval begins after the full cycle.

| Watchlist size | Requests per cycle |
|---:|---:|
| 1 | 2 |
| 10 | 20 |
| 50 | 100 |

Use a longer interval for larger lists and avoid running multiple monitors with the same API key.

## Option 11: Following IDs

This operation displays IDs followed by the upstream authenticated Fomo account.

It is not the application's watchlist and is not unique to each API customer. Use **Manage watchlist** for local monitoring choices.

## Option 12: Export Trader Data

The export flow resolves a profile and retrieves balances, up to 150 swaps, and rankings. It writes a formatted JSON file:

```text
exports/<handle>_<YYYYMMDD_HHMMSS>.json
```

The top-level document contains:

```json
{
  "exportedAt": "UTC ISO-8601 timestamp",
  "profile": {},
  "balances": {},
  "swaps": {},
  "ranking": {}
}
```

Exports may contain public wallet addresses and detailed activity. Treat them as research data and share them deliberately.

## Recommended End-to-End Workflow

1. Check API health.
2. Explore several leaderboard windows.
3. Resolve promising handles.
4. Review portfolios, swaps, and rankings.
5. Add selected profiles to the watchlist.
6. Establish a monitoring baseline.
7. Observe newly indexed changes.
8. Export relevant trader snapshots.
9. Independently validate wallet and token activity onchain.

## Keyboard and Session Tips

- Press `Enter` to accept a displayed default.
- Press `Ctrl+C` to stop monitoring or cancel the current prompt.
- Use option `0` for a clean exit.
- Restart after changing `.env`; configuration loads when Python imports the project.
- Avoid closing the process while an export is being written.
