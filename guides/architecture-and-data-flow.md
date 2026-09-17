# Architecture and Data Flow

Fomo Trader Intelligence is a synchronous Python terminal application. Its modules separate user interaction, API transport, numerical normalization, configuration, and persistent state.

## System Overview

```text
Terminal user
     |
     v
FomoTerminal application
     |--------------------------|
     v                          v
FomoClient                  Analysis functions
     |                          |
     v                          v
Fomo REST API              Normalized positions
                                |
                                v
                           SQLite Store
                                |
                                v
                       Watchlist and checkpoints
```

JSON exports form a separate output path from the terminal application to the configured export directory.

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Creates and starts the terminal application |
| `fomo_bot/app.py` | Menus, prompts, tables, workflows, monitoring, and export orchestration |
| `fomo_bot/client.py` | Authentication, request throttling, retries, errors, and endpoint methods |
| `fomo_bot/analysis.py` | Decimal conversion, balance normalization, and position comparisons |
| `fomo_bot/store.py` | SQLite schema, watchlist operations, swap deduplication, and position state |
| `fomo_bot/config.py` | `.env` loading and runtime setting defaults |

The application intentionally keeps execution signing, wallet management, and blockchain RPC logic outside this architecture.

## Startup Sequence

When `python main.py` runs:

1. `config.py` loads `.env` through `python-dotenv`.
2. `FomoTerminal` creates a Rich console.
3. `FomoClient` creates a reusable `requests.Session`.
4. `Store` creates the database parent directory and opens SQLite.
5. SQLite applies idempotent `CREATE TABLE IF NOT EXISTS` statements.
6. The terminal enters its command loop.
7. On exit, the HTTP session and database connection close.

## API Client Design

### Authentication

Protected requests send:

```http
X-API-Key: fomo_live_YOUR_API_KEY
Accept: application/json
User-Agent: FomoTerminal/1.0
```

The health and public frontpage leaderboard methods explicitly disable authentication.

### Endpoint Mapping

| Client method | Endpoint |
|---|---|
| `health()` | `GET /api/health` |
| `public_leaderboard()` | `GET /frontpage/leaderboard` |
| `leaderboard()` | `GET /api/leaderboard/{window}` |
| `resolve_trader()` | `GET /api/users/{handle}` |
| `balances()` | `GET /api/users/{userId}/balances` |
| `spotlight()` | `GET /api/users/{userId}/spotlight` |
| `swaps()` | `GET /api/users/{userId}/swaps` |
| `trader_ranking()` | `GET /api/users/{userId}/leaderboard` |
| `aggregated_snapshot()` | `GET /api/user-tokens/aggregated-snapshot` |
| `following_ids()` | `GET /api/users/current/following-ids` |

Path values are URL-encoded before requests are sent.

### Local Rate Control

The client keeps monotonic timestamps for recent requests in a deque. Before each request, it removes timestamps older than one second. If five timestamps remain, it waits until the oldest leaves the one-second window.

This limits one application process to five requests per second. It cannot coordinate with other processes sharing the same key.

### Retry Strategy

Retries apply to:

- Network exceptions
- HTTP `429`
- HTTP `502`
- HTTP `503`
- HTTP `504`

For API responses, `Retry-After` is preferred when present. Otherwise the delay uses exponential backoff capped at 30 seconds. Random jitter up to half a second reduces synchronized retries.

Non-transient errors fail immediately. HTTP `401` and `403` become `FomoAuthError`; other failures become `FomoApiError` with the API detail where available.

## Response Handling

Most Fomo endpoints wrap endpoint data in:

```json
{
  "success": true,
  "message": "Resource found",
  "responseObject": {},
  "statusCode": 200
}
```

`FomoClient.response_object()` retrieves the inner object. The health endpoint is handled directly because it returns a smaller response.

## Portfolio Normalization

`normalize_positions()` converts nested balance records into a dictionary keyed by network and token:

```text
<networkId>:<tokenAddress>
```

Normalized values include:

```json
{
  "networkId": 1399811149,
  "tokenAddress": "TOKEN_ADDRESS",
  "symbol": "TOKEN",
  "amount": "100",
  "priceUsd": "0.25",
  "valueUsd": "25.00",
  "costBasisUsd": "20",
  "realizedPnlUsd": "5",
  "includeInEquity": true
}
```

Numeric strings are converted through `Decimal(str(value))`. Normalized numeric fields are stored as strings so SQLite JSON serialization retains decimal text without converting back to binary floats.

### Position Comparison

`compare_positions(previous, current)` evaluates every key present in either snapshot.

| Previous amount | Current amount | Classification |
|---:|---:|---|
| `0` | Greater than `0` | Opened |
| Positive | Greater than previous | Increased |
| Positive | Lower but positive | Reduced |
| Positive | `0` or missing | Closed |

The function reports amount differences but does not claim a transaction cause.

## SQLite Persistence

The default database is `data/fomo_bot.db`.

### `watchlist`

| Column | Role |
|---|---|
| `user_id` | Primary key used by API endpoints |
| `handle` | Unique public handle |
| `display_name` | Last resolved display name |
| `solana` | Resolved Solana wallet |
| `evm` | Resolved EVM wallet |
| `added_at` | UTC insertion timestamp |

Adding an existing user updates profile fields without changing `added_at`.

### `processed_swaps`

| Column | Role |
|---|---|
| `swap_id` | Primary key and deduplication constraint |
| `user_id` | Associated watched trader |
| `created_at` | API event timestamp |
| `payload` | Raw normalized swap JSON |
| `seen_at` | UTC local observation timestamp |

`INSERT OR IGNORE` makes `save_swap()` return false for an already stored event.

### `positions`

| Column | Role |
|---|---|
| `user_id` | Watched trader |
| `position_key` | Network and token compound key |
| `payload` | Normalized position JSON |
| `updated_at` | UTC replacement timestamp |

The compound primary key is `(user_id, position_key)`. A trader's position rows are replaced in one SQLite transaction after each successful balance fetch.

## Monitoring Cycle

```text
For every watched trader:
    Fetch 20 latest swaps
    Insert unseen swap IDs
    Fetch current balances
    Normalize balances
    Load previous positions
    Compare previous and current states
    Replace stored positions
    Display changes after the baseline cycle
Wait for the configured interval
Repeat
```

Errors for one trader are printed and do not end the whole cycle. `Ctrl+C` exits the monitor and returns control to the outer menu.

### Monitoring Tradeoffs

- Processing is sequential, which simplifies rate limiting and SQLite access.
- The configured interval is a pause after a cycle, not a fixed wall-clock schedule.
- Only the latest 20 swaps are checked per cycle, so a very active trader can produce more events than one response contains.
- Swap cursors are supported by the API client but not used by the current monitor.
- SQLite is appropriate for one local process, not distributed workers.

## Export Flow

The export command performs four protected operations:

1. Resolve profile
2. Fetch balances
3. Fetch up to 150 swaps
4. Fetch rankings

Data is placed under a UTC `exportedAt` timestamp and written with UTF-8 encoding and formatted JSON. `ensure_ascii=False` preserves display names as returned by the API.

## Security Boundaries

The project protects its intended boundary by:

- Loading the API key from an ignored environment file
- Sending the key only to the configured API base URL
- Avoiding browser or frontend exposure
- Storing no private wallet credentials
- Performing no signing or execution
- Avoiding display of spotlight comment content

Users must still protect the machine, `.env`, terminal history, exported data, and database backups.

## Scaling Beyond the Current Design

For dozens of traders or production alerting, consider replacing components as follows:

| Current component | Production alternative |
|---|---|
| Menu-driven loop | Scheduler and worker service |
| In-process throttle | Shared Redis rate limiter |
| SQLite | PostgreSQL or CockroachDB |
| Terminal notifications | Alert queue, webhook, email, or chat integration |
| Latest-20 swap polling | Cursor-aware checkpointed pagination |
| Local JSON exports | Object storage with retention controls |

Preserve unique constraints on swap IDs and position keys when moving to another database.
