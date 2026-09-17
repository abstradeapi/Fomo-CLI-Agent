# Installation and Setup Guide

This guide installs Fomo Trader Intelligence in an isolated Python environment, configures Fomo API access, and verifies that the terminal application can reach the service.

## Prerequisites

| Item | Requirement |
|---|---|
| Python | Version 3.9 or newer |
| Package installer | `pip`, included with standard Python installations |
| Fomo API key | A Pro key beginning with `fomo_live_` for protected endpoints |
| Network | HTTPS access to `https://getfomoapi.fun` |
| Terminal | A modern terminal with color support is recommended |

Check the Python installation:

```bash
python --version
python -m pip --version
```

On systems where `python` points to Python 2 or is unavailable, try `python3` in each command.

## 1. Obtain the Project

Clone the repository and enter its directory:

```bash
git clone <your-repository-url>
cd fomo-trader-intelligence
```

If you downloaded an archive, extract it and open a terminal in the extracted project directory. Confirm that `main.py`, `requirements.txt`, and the `fomo_bot` directory are present.

## 2. Create a Virtual Environment

A virtual environment keeps project dependencies separate from other Python applications.

```bash
python -m venv .venv
```

Activate the environment for the current terminal session.

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks local activation scripts, use Command Prompt or review the execution policy for your own machine. Do not lower organization-wide security controls just to activate an environment.

### Windows Command Prompt

```bat
.venv\Scripts\activate.bat
```

### macOS or Linux

```bash
source .venv/bin/activate
```

The prompt usually shows `(.venv)` after activation.

## 3. Install Dependencies

Upgrade the installer and install the pinned dependency ranges:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The project directly uses:

| Package | Purpose |
|---|---|
| `requests` | HTTPS communication with Fomo API |
| `python-dotenv` | Loading local environment settings from `.env` |
| `rich` | Tables, prompts, panels, colors, and progress indicators |

SQLite support is part of Python's standard library and requires no separate package.

## 4. Configure the Environment

Create `.env` from the supplied template.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS or Linux

```bash
cp .env.example .env
```

Open `.env` and replace the example key:

```env
FOMO_API_KEY=fomo_live_YOUR_API_KEY
FOMO_BASE_URL=https://getfomoapi.fun
FOMO_REQUEST_TIMEOUT=30
FOMO_MAX_RETRIES=5
FOMO_DATABASE_PATH=data/fomo_bot.db
FOMO_EXPORT_PATH=exports
```

### Configuration Reference

| Variable | Required | Accepted value | Guidance |
|---|---:|---|---|
| `FOMO_API_KEY` | For protected operations | Fomo Pro API key | Keep private and rotate it if exposed |
| `FOMO_BASE_URL` | No | HTTPS URL | Keep the default for the production service |
| `FOMO_REQUEST_TIMEOUT` | No | Positive seconds | Increase only for consistently slow networks |
| `FOMO_MAX_RETRIES` | No | Non-negative integer | Controls retries for transient failures |
| `FOMO_DATABASE_PATH` | No | Local file path | Parent directories are created automatically |
| `FOMO_EXPORT_PATH` | No | Local directory path | JSON exports are written here |

> **Warning:** Never put wallet private keys, seed phrases, exchange secrets, or signing credentials in this project. It is a data client and has no transaction execution layer.

The `.gitignore` file excludes `.env`, `.venv`, `data`, and `exports`. Verify this behavior before pushing to a public repository.

## 5. Verify the Installation

Compile all Python modules:

```bash
python -m compileall -q .
```

Test the unauthenticated health endpoint:

```bash
python -c "from fomo_bot.client import FomoClient; c=FomoClient(); print(c.health()); c.close()"
```

Expected output:

```text
{'status': 'ok'}
```

This confirms Python imports, HTTPS connectivity, and Fomo API availability. It does not verify Pro key access.

## 6. Start the Application

```bash
python main.py
```

Windows users can alternatively run:

```powershell
.\run.bat
```

Select **API health** for an unauthenticated check. Then select **Resolve trader** or **Discover leaderboard**, choose the Pro version, and confirm that authenticated requests succeed.

If `FOMO_API_KEY` is absent, the terminal asks for one when a protected operation begins. A key entered this way is held only for the running process and is not written to `.env`.

## Generated Directories

The following paths do not need to exist before startup:

```text
data/
`-- fomo_bot.db

exports/
`-- <handle>_<timestamp>.json
```

The database is created when the application initializes. The export directory is created after the first export.

## Updating

After pulling a newer project version, reactivate the environment and synchronize dependencies:

```bash
git pull
python -m pip install -r requirements.txt
python -m compileall -q .
```

Back up `data/fomo_bot.db` before running a release that documents database schema changes.

## Troubleshooting

### `ModuleNotFoundError`

Confirm the virtual environment is active and install dependencies with the same Python executable used to launch the app:

```bash
python -m pip install -r requirements.txt
python main.py
```

### `A Fomo API key is required`

Set `FOMO_API_KEY` in `.env`, restart the app, or enter the key at the protected-operation prompt.

### HTTP `401` or `403`

- Check for spaces or quotes around the key.
- Confirm the key begins with `fomo_live_`.
- Confirm the associated Pro plan is active.
- Rotate the key if it may have been exposed.

### HTTP `429`

The client automatically enforces a five-request-per-second limit and honors `Retry-After`. Repeated rate limiting can still occur when the same key is used by multiple applications.

### Empty Leaderboard or Portfolio

An empty table can be a valid result. Confirm the selected window, handle, and account activity. Data freshness depends on upstream indexing.

### Terminal Colors Look Incorrect

Use Windows Terminal, PowerShell, or another terminal with ANSI color support. The application remains usable when colors are limited.

## Setup Checklist

- [ ] Python 3.9 or newer is installed.
- [ ] The virtual environment is active.
- [ ] Dependencies install without errors.
- [ ] `.env` exists and is excluded from Git.
- [ ] The health test returns `ok`.
- [ ] Protected menu actions accept the Pro API key.
- [ ] No wallet or signing secrets are stored in the project.
