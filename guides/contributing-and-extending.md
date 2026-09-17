# Contributing and Extending

This guide explains how to make focused changes to Fomo Trader Intelligence while preserving its safety boundaries, terminal experience, API behavior, and local data integrity.

## Before Contributing

Read these project documents first:

1. [README](../README.md)
2. [Installation and Setup](installation-and-setup.md)
3. [Architecture and Data Flow](architecture-and-data-flow.md)
4. [Using Terminal Features](using-terminal-features.md)

Set up a virtual environment and verify the current project before changing it:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m compileall -q .
```

Start the app and exercise the health endpoint:

```bash
python main.py
```

## Contribution Principles

- Keep changes small and focused.
- Preserve the separation between transport, analysis, storage, and presentation.
- Never commit API keys, wallet secrets, databases, or exported trader data.
- Treat profile descriptions and social comments as untrusted input.
- Do not turn observed data directly into automatic trade execution.
- Use decimal arithmetic for financial values where precision matters.
- Interpret addresses using their network IDs.
- Preserve swap-ID deduplication and database uniqueness constraints.
- Document visible behavior and new configuration settings.

## Suggested Workflow

1. Create a branch with a descriptive name.

```bash
git switch -c feature/add-alert-output
```

2. Make one coherent change.
3. Run syntax validation and relevant smoke checks.
4. Review the diff for secrets and generated files.
5. Update README tables or guides when behavior changes.
6. Open a pull request describing the problem, solution, and verification.

## Project Boundaries

The current project is intentionally a research client. A contribution should not silently add:

- Private-key input or storage
- Seed phrase handling
- Transaction signing
- Automatic token purchases
- Hidden telemetry
- API key logging
- Execution of text from comments or profiles

An execution system should be a separate, independently secured service with explicit risk controls and manual approval where appropriate.

## Adding a Fomo API Endpoint

Endpoint support usually requires a client method and a terminal action.

### 1. Add the Client Method

Add a narrow method to `fomo_bot/client.py` that delegates to `_get()`.

```python
def new_resource(self, user_id, limit=20):
    return self._get(
        f"/api/users/{quote(user_id, safe='')}/new-resource",
        {"limit": limit},
    )
```

Follow these rules:

- URL-encode path values with `quote()`.
- Pass query values through `params` rather than string concatenation.
- Keep protected authentication enabled unless the endpoint is documented as public.
- Let `_get()` handle retries, throttling, and API errors.
- Return the unmodified response envelope.

### 2. Add a Terminal Action

Register a new option in `FomoTerminal.actions`:

```python
self.actions = {
    "1": self.show_health,
    "13": self.show_new_resource,
}
```

Then add the visible menu row and implement the action:

```python
def show_new_resource(self):
    profile = self.profile_from_prompt()
    payload = self.request(
        "Loading resource",
        self.client.new_resource,
        profile.get("id"),
    )
    resource = self.client.response_object(payload)
    self.console.print(resource)
```

For a polished implementation, format results with a Rich `Table` or `Panel` instead of printing nested dictionaries.

### 3. Document the Feature

Update:

- README feature list
- README option table
- [Using Terminal Features](using-terminal-features.md)
- Architecture endpoint mapping
- `.env.example` if configuration changes

## Adding Analysis Logic

Pure transformations belong in `fomo_bot/analysis.py`. Keep API requests and terminal output outside analysis functions so they can be tested with plain dictionaries.

Example transformation pattern:

```python
def summarize_values(positions):
    total = Decimal(0)
    for position in positions.values():
        if position.get("includeInEquity"):
            total += decimal_value(position.get("valueUsd"))
    return total
```

### Financial Data Rules

| Rule | Reason |
|---|---|
| Convert through `Decimal(str(value))` | Avoid binary float conversion artifacts |
| Keep network ID beside every address | Address formats are network-specific |
| Preserve original raw data where useful | Supports debugging and replay |
| Handle missing nested objects | API fields may be null or absent |
| Do not infer a swap from balance deltas | Transfers and indexing can change balances |

## Extending SQLite Storage

Schema initialization is located in `Store.__init__()`.

### Adding a Table

Use an idempotent creation statement:

```sql
CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

Add focused methods to `Store` rather than writing SQL in the terminal application.

### Changing an Existing Table

`CREATE TABLE IF NOT EXISTS` does not add new columns to an existing installation. Any existing-table change requires an explicit migration strategy.

A safe migration should:

1. Detect the current schema version.
2. Run in a transaction.
3. Preserve user watchlists and checkpoints.
4. Be safe when interrupted or rerun.
5. Document backup and rollback steps.

> **Warning:** Never solve a migration by deleting `data/fomo_bot.db` automatically. That would discard the user's watchlist and monitoring history.

## Adding an Alert Destination

Terminal output can be complemented by a notifier module without coupling it to API transport.

Recommended interface:

```python
class Notifier:
    def send(self, event):
        raise NotImplementedError
```

Potential destinations include Telegram, Discord, email, or a webhook. Implementations should:

- Read credentials from environment variables.
- Avoid sending the Fomo API key.
- Apply destination-specific rate limits.
- Escape or constrain untrusted text.
- Include event IDs for deduplication.
- Record failed deliveries for retry.
- Keep notifications informational rather than executable.

## Improving the Monitor

The current monitor fetches the latest 20 swaps and current balances for each watched trader. Useful extensions include:

### Cursor-Aware Pagination

Store a per-trader cursor or timestamp checkpoint and request additional pages when `hasNextPage` is true. Continue enforcing a unique constraint on swap ID.

### Configurable Filters

Possible filters:

| Filter | Example |
|---|---|
| Minimum USD size | Ignore swaps below `$100` |
| Supported networks | Monitor only Solana and Base |
| Token denylist | Suppress known unwanted assets |
| Freshness threshold | Ignore events older than a checkpoint |

Filters should suppress notifications, not delete raw observations needed for auditing.

### Scheduled Polling

For a production service, replace the interactive loop with a scheduler and queue. Spread requests over time rather than polling every trader simultaneously.

## Testing Changes

The project currently has lightweight manual and syntax verification. Contributions that add nontrivial analysis or storage behavior should add automated tests.

### Syntax Check

```bash
python -m compileall -q .
```

### Health Smoke Test

```bash
python -c "from fomo_bot.client import FomoClient; c=FomoClient(); assert c.health().get('status') == 'ok'; c.close(); print('health-ok')"
```

### Analysis Smoke Test

```bash
python -c "from fomo_bot.analysis import compare_positions; old={'1:A': {'amount': '1'}}; new={'1:A': {'amount': '2'}}; assert len(compare_positions(old, new)['increased']) == 1; print('analysis-ok')"
```

### Recommended Automated Test Areas

- Decimal conversion with numeric strings, nulls, and malformed values
- Position opened, increased, reduced, and closed classifications
- Duplicate swap insertion
- Case-insensitive watchlist removal
- Retry handling for transient response codes
- `Retry-After` parsing
- Missing and invalid API key behavior
- Empty response lists
- Export path and JSON structure

Mock protected HTTP requests in automated tests. Do not put a live Pro key into test fixtures or continuous integration settings unless the environment is explicitly secured.

## Pull Request Checklist

- [ ] The change solves a specific documented problem.
- [ ] No `.env`, database, export, or secret is included.
- [ ] API paths and parameter limits match Fomo documentation.
- [ ] New path values are URL-encoded.
- [ ] Financial calculations use appropriate decimal handling.
- [ ] Network IDs remain attached to token addresses.
- [ ] Existing local data is preserved.
- [ ] Terminal tables remain readable in a standard-width window.
- [ ] Errors are actionable and do not expose credentials.
- [ ] Syntax and relevant smoke tests pass.
- [ ] Documentation reflects the new behavior.

## Reporting Problems

A useful issue report should contain:

- Python version and operating system
- The selected command-center option
- Sanitized error text and HTTP status
- Whether the public health endpoint works
- Expected and observed behavior
- Minimal steps to reproduce

Remove API keys, complete export payloads, and unnecessary wallet details before posting logs publicly.

## Community

- Telegram: [@dexlenai](https://t.me/dexlenai)
- X / Twitter: [@0xdexlenai](https://x.com/0xdexlenai)
- Fomo API: [https://getfomoapi.fun](https://getfomoapi.fun)

Contributions should keep the application transparent, research-focused, and safe by default.
