import json
import time
from datetime import datetime, timezone
from decimal import Decimal

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from fomo_bot.analysis import compare_positions, decimal_value, normalize_positions
from fomo_bot.client import FomoApiError, FomoAuthError, FomoClient
from fomo_bot.config import API_KEY, DATABASE_PATH, EXPORT_PATH
from fomo_bot.store import Store


NETWORKS = {
    1: "Ethereum",
    56: "BNB Chain",
    143: "Monad",
    8453: "Base",
    1399811149: "Solana",
}


class FomoTerminal:
    def __init__(self):
        self.console = Console()
        self.client = FomoClient(API_KEY)
        self.store = Store(DATABASE_PATH)
        self.actions = {
            "1": self.show_health,
            "2": self.show_leaderboard,
            "3": self.show_profile,
            "4": self.show_portfolio,
            "5": self.show_swaps,
            "6": self.show_spotlight,
            "7": self.show_ranking,
            "8": self.show_snapshot,
            "9": self.manage_watchlist,
            "10": self.monitor_watchlist,
            "11": self.show_following,
            "12": self.export_trader,
        }

    def run(self):
        try:
            while True:
                self.console.clear()
                self.console.print(self.header())
                self.console.print(self.menu())
                choice = Prompt.ask("[bold cyan]Select an option[/]", choices=[*self.actions, "0"], default="2")
                if choice == "0":
                    break
                self.console.clear()
                self.console.print(self.header(compact=True))
                try:
                    self.actions[choice]()
                except FomoAuthError as error:
                    self.console.print(Panel(str(error), title="[bold red]Authentication[/]", border_style="red"))
                except FomoApiError as error:
                    self.console.print(Panel(str(error), title="[bold red]API Error[/]", border_style="red"))
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Operation cancelled[/]")
                except Exception as error:
                    self.console.print(Panel(str(error), title="[bold red]Error[/]", border_style="red"))
                self.console.print()
                Prompt.ask("[dim]Press Enter to return[/]", default="")
        finally:
            self.client.close()
            self.store.close()
            self.console.print("[bold cyan]Session closed.[/]")

    def header(self, compact=False):
        title = Text("FOMO", style="bold bright_cyan")
        title.append(" // ", style="dim white")
        title.append("TRADER INTELLIGENCE", style="bold white")
        if compact:
            return Panel(Align.center(title), border_style="cyan", padding=(0, 1))
        subtitle = Text("Discovery  |  Portfolio  |  Signals  |  Monitoring", style="dim")
        warning = Text("Research and monitoring only. No trade execution.", style="yellow")
        return Panel(Align.center(Group(title, subtitle, warning)), border_style="bright_cyan", padding=(1, 2))

    def menu(self):
        table = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 2))
        table.add_column(style="bold cyan", width=4, justify="right")
        table.add_column(style="white")
        table.add_column(style="bold cyan", width=4, justify="right")
        table.add_column(style="white")
        rows = [
            ("1", "API health", "7", "Trader rankings"),
            ("2", "Discover leaderboard", "8", "Historical snapshot"),
            ("3", "Resolve trader", "9", "Manage watchlist"),
            ("4", "Portfolio analytics", "10", "Monitor watchlist"),
            ("5", "Recent swaps", "11", "Following IDs"),
            ("6", "Trader spotlight", "12", "Export trader data"),
            ("0", "Exit", "", ""),
        ]
        for row in rows:
            table.add_row(*row)
        return Panel(table, title="[bold]COMMAND CENTER[/]", border_style="blue")

    def require_key(self):
        if self.client.api_key:
            return
        key = Prompt.ask("[bold yellow]Fomo API key[/]", password=True).strip()
        if not key:
            raise FomoAuthError("A Fomo API key is required")
        self.client.set_api_key(key)

    def request(self, label, method, *args, **kwargs):
        with self.console.status(f"[cyan]{label}[/]", spinner="dots12"):
            return method(*args, **kwargs)

    def profile_from_prompt(self):
        self.require_key()
        handle = Prompt.ask("[bold]Trader handle[/]").strip().lstrip("@")
        if not handle:
            raise FomoApiError("Trader handle cannot be empty")
        payload = self.request("Resolving trader", self.client.resolve_trader, handle)
        return self.client.response_object(payload)

    def money(self, value):
        amount = decimal_value(value)
        sign = "-" if amount < 0 else ""
        return f"{sign}${abs(amount):,.2f}"

    def short(self, value, size=12):
        value = str(value or "-")
        if len(value) <= size:
            return value
        side = max((size - 3) // 2, 2)
        return f"{value[:side]}...{value[-side:]}"

    def show_health(self):
        payload = self.request("Checking API", self.client.health)
        status = payload.get("status", "unknown")
        color = "green" if status == "ok" else "red"
        self.console.print(Panel(Align.center(f"[{color}]* {status.upper()}[/]"), title="API STATUS", border_style=color))

    def show_leaderboard(self):
        protected = Confirm.ask("Use Pro leaderboard", default=bool(self.client.api_key))
        if protected:
            self.require_key()
            window = Prompt.ask("Window", choices=["24h", "7d", "30d", "all"], default="24h")
            maximum = 100 if window == "all" else 150
            limit = IntPrompt.ask("Trader limit", default=10)
            limit = max(1, min(limit, maximum))
            payload = self.request("Loading leaderboard", self.client.leaderboard, window, limit)
        else:
            payload = self.request("Loading public leaderboard", self.client.public_leaderboard)
        traders = self.client.response_object(payload).get("leaderboard", [])
        table = Table(title="Trader Leaderboard", box=box.ROUNDED, border_style="cyan", header_style="bold cyan", expand=True)
        table.add_column("#", justify="right", width=4)
        table.add_column("Trader")
        table.add_column("Handle")
        table.add_column("PnL 24h", justify="right")
        table.add_column("Volume", justify="right")
        table.add_column("Trades", justify="right")
        table.add_column("Followers", justify="right")
        table.add_column("Wallet")
        for index, trader in enumerate(traders, 1):
            pnl = decimal_value(trader.get("pnl24h"))
            style = "green" if pnl >= 0 else "red"
            table.add_row(
                str(trader.get("rank", index)),
                str(trader.get("displayName") or "-"),
                f"@{trader.get('userHandle', '-')}",
                f"[{style}]{self.money(pnl)}[/]",
                self.money(trader.get("totalVolume")),
                str(trader.get("numTrades", "-")),
                str(trader.get("followers", "-")),
                self.short(trader.get("solana") or trader.get("evm")),
            )
        self.console.print(table)

    def show_profile(self):
        profile = self.profile_from_prompt()
        details = Table.grid(padding=(0, 2))
        details.add_column(style="bold cyan")
        details.add_column()
        fields = [
            ("Name", profile.get("displayName")),
            ("Handle", f"@{profile.get('userHandle', '-') }"),
            ("User ID", profile.get("id")),
            ("Solana", profile.get("solana")),
            ("EVM", profile.get("evm")),
            ("Followers", profile.get("followers")),
            ("Following", profile.get("following")),
            ("Trades", profile.get("numTrades")),
            ("Volume", self.money(profile.get("totalVolume"))),
            ("Average hold", self.duration(profile.get("averageHoldTimeSeconds"))),
            ("Verified", "Yes" if profile.get("verified") else "No"),
            ("Description", profile.get("description")),
        ]
        for label, value in fields:
            details.add_row(label, str(value if value not in {None, ""} else "-"))
        self.console.print(Panel(details, title="TRADER PROFILE", border_style="cyan"))
        if Confirm.ask("Add to local watchlist", default=False):
            self.store.add_trader(profile)
            self.console.print("[green]Trader added to watchlist[/]")

    def duration(self, seconds):
        if seconds is None:
            return "-"
        seconds = int(seconds)
        days, remainder = divmod(seconds, 86400)
        hours, _ = divmod(remainder, 3600)
        return f"{days}d {hours}h" if days else f"{hours}h"

    def show_portfolio(self):
        profile = self.profile_from_prompt()
        payload = self.request("Loading portfolio", self.client.balances, profile.get("id"))
        balances = self.client.response_object(payload)
        positions = normalize_positions(balances)
        table = Table(title=f"@{profile.get('userHandle')} Portfolio", box=box.ROUNDED, border_style="cyan", header_style="bold cyan", expand=True)
        table.add_column("Token")
        table.add_column("Network")
        table.add_column("Amount", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Value", justify="right")
        table.add_column("Cost basis", justify="right")
        table.add_column("Unrealized", justify="right")
        table.add_column("Address")
        equity = Decimal(0)
        cost = Decimal(0)
        for position in sorted(positions.values(), key=lambda item: decimal_value(item["valueUsd"]), reverse=True):
            value = decimal_value(position["valueUsd"])
            basis = decimal_value(position["costBasisUsd"])
            unrealized = value - basis
            if position["includeInEquity"]:
                equity += value
            cost += basis
            color = "green" if unrealized >= 0 else "red"
            table.add_row(
                position["symbol"],
                NETWORKS.get(position["networkId"], str(position["networkId"])),
                f"{decimal_value(position['amount']):,.6f}",
                self.money(position["priceUsd"]),
                self.money(value),
                self.money(basis),
                f"[{color}]{self.money(unrealized)}[/]",
                self.short(position["tokenAddress"]),
            )
        self.console.print(table)
        summary = Table.grid(expand=True)
        summary.add_column(justify="center")
        summary.add_column(justify="center")
        summary.add_column(justify="center")
        summary.add_row(f"[bold]Tracked Equity[/]\n[cyan]{self.money(equity)}[/]", f"[bold]Cost Basis[/]\n{self.money(cost)}", f"[bold]Other Equity[/]\n{self.money(balances.get('otherEquity'))}")
        self.console.print(Panel(summary, border_style="blue"))

    def show_swaps(self):
        profile = self.profile_from_prompt()
        limit = max(1, min(IntPrompt.ask("Swap limit", default=20), 150))
        payload = self.request("Loading swaps", self.client.swaps, profile.get("id"), limit)
        swaps = self.client.response_object(payload).get("swaps", [])
        self.render_swaps(swaps, f"@{profile.get('userHandle')} Recent Swaps")

    def render_swaps(self, swaps, title):
        table = Table(title=title, box=box.ROUNDED, border_style="cyan", header_style="bold cyan", expand=True)
        table.add_column("Time")
        table.add_column("Network")
        table.add_column("Received", justify="right")
        table.add_column("In token")
        table.add_column("Sent", justify="right")
        table.add_column("Out token")
        table.add_column("USD", justify="right")
        table.add_column("Provider")
        for swap in swaps:
            timestamp = str(swap.get("createdAt", "-")).replace("T", " ").replace("Z", "")[:19]
            table.add_row(
                timestamp,
                NETWORKS.get(swap.get("networkId"), str(swap.get("networkId", "-"))),
                f"{decimal_value(swap.get('inHumanAmount')):,.6f}",
                self.short(swap.get("inTokenAddress")),
                f"{decimal_value(swap.get('outHumanAmount')):,.6f}",
                self.short(swap.get("outTokenAddress")),
                self.money(swap.get("humanUsdAmountIn") or swap.get("humanUsdAmountOut")),
                str(swap.get("provider") or "-"),
            )
        self.console.print(table)

    def show_spotlight(self):
        profile = self.profile_from_prompt()
        payload = self.request("Loading spotlight", self.client.spotlight, profile.get("id"))
        spotlight = self.client.response_object(payload)
        trades = spotlight.get("bestTrades", [])
        table = Table(title=f"@{profile.get('userHandle')} Best Trades", box=box.ROUNDED, border_style="cyan", header_style="bold cyan", expand=True)
        table.add_column("Token")
        table.add_column("Network")
        table.add_column("Realized PnL", justify="right")
        table.add_column("Unrealized PnL", justify="right")
        table.add_column("Liquidity", justify="right")
        table.add_column("Status")
        for item in trades:
            trade = item.get("trade") or {}
            metadata = trade.get("tokenMetadata") or {}
            realized = decimal_value(trade.get("realizedPnlUsd"))
            unrealized = decimal_value(trade.get("unrealizedPnlUsd"))
            table.add_row(
                str(metadata.get("symbol") or self.short(trade.get("tokenAddress"))),
                NETWORKS.get(trade.get("networkId"), str(trade.get("networkId", "-"))),
                f"[{'green' if realized >= 0 else 'red'}]{self.money(realized)}[/]",
                f"[{'green' if unrealized >= 0 else 'red'}]{self.money(unrealized)}[/]",
                self.money(metadata.get("liquidity")),
                "Open" if trade.get("closedAt") is None else "Closed",
            )
        self.console.print(table)
        self.console.print(f"[dim]Popular comments returned: {len(spotlight.get('bestComments', []))}. Comment content is not displayed or trusted.[/]")

    def show_ranking(self):
        profile = self.profile_from_prompt()
        payload = self.request("Loading rankings", self.client.trader_ranking, profile.get("id"))
        ranking = self.client.response_object(payload)
        table = Table(title=f"@{profile.get('userHandle')} Rankings", box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
        table.add_column("Window")
        table.add_column("Rank", justify="right")
        table.add_column("PnL", justify="right")
        for label, key in [("All time", "rank"), ("24 hours", "rank24h"), ("7 days", "rank7d"), ("30 days", "rank30d")]:
            item = ranking.get(key) or {}
            pnl = decimal_value(item.get("pnl"))
            table.add_row(label, str(item.get("rank", "Unranked")), f"[{'green' if pnl >= 0 else 'red'}]{self.money(pnl)}[/]")
        self.console.print(table)

    def show_snapshot(self):
        profile = self.profile_from_prompt()
        default = int(datetime.now(timezone.utc).timestamp())
        snapshot_id = IntPrompt.ask("Snapshot Unix timestamp", default=default)
        payload = self.request("Loading historical snapshot", self.client.aggregated_snapshot, profile.get("id"), snapshot_id)
        snapshot = self.client.response_object(payload)
        pnl = decimal_value(snapshot.get("pnl"))
        grid = Table.grid(padding=(0, 3))
        grid.add_row("[bold cyan]Snapshot[/]", str(snapshot.get("snapshotId", snapshot_id)))
        grid.add_row("[bold cyan]Equity[/]", self.money(snapshot.get("equity")))
        grid.add_row("[bold cyan]PnL[/]", f"[{'green' if pnl >= 0 else 'red'}]{self.money(pnl)}[/]")
        self.console.print(Panel(grid, title="HISTORICAL PERFORMANCE", border_style="cyan"))

    def manage_watchlist(self):
        action = Prompt.ask("Action", choices=["list", "add", "remove"], default="list")
        if action == "add":
            profile = self.profile_from_prompt()
            self.store.add_trader(profile)
            self.console.print(f"[green]@{profile.get('userHandle')} added[/]")
        elif action == "remove":
            handle = Prompt.ask("Handle to remove")
            removed = self.store.remove_trader(handle)
            self.console.print("[green]Trader removed[/]" if removed else "[yellow]Trader was not in the watchlist[/]")
        self.render_watchlist()

    def render_watchlist(self):
        table = Table(title="Local Watchlist", box=box.ROUNDED, border_style="cyan", header_style="bold cyan", expand=True)
        table.add_column("Trader")
        table.add_column("Handle")
        table.add_column("User ID")
        table.add_column("Solana")
        table.add_column("EVM")
        table.add_column("Added")
        for trader in self.store.traders():
            table.add_row(str(trader["display_name"] or "-"), f"@{trader['handle']}", self.short(trader["user_id"], 18), self.short(trader["solana"], 16), self.short(trader["evm"], 16), trader["added_at"][:10])
        self.console.print(table)

    def monitor_watchlist(self):
        self.require_key()
        traders = self.store.traders()
        if not traders:
            self.console.print("[yellow]The watchlist is empty. Add a trader first.[/]")
            return
        interval = max(5, IntPrompt.ask("Polling interval in seconds", default=15))
        self.console.print(Panel(f"Monitoring {len(traders)} trader(s) every {interval}s. Press Ctrl+C to stop.", border_style="cyan"))
        cycles = 0
        while True:
            cycles += 1
            for trader in traders:
                try:
                    swap_payload = self.client.swaps(trader["user_id"], 20)
                    swaps = self.client.response_object(swap_payload).get("swaps", [])
                    new_swaps = [swap for swap in swaps if swap.get("id") and self.store.save_swap(trader["user_id"], swap)]
                    balance_payload = self.client.balances(trader["user_id"])
                    current = normalize_positions(self.client.response_object(balance_payload))
                    previous = self.store.positions(trader["user_id"])
                    changes = compare_positions(previous, current) if previous else {"opened": [], "increased": [], "reduced": [], "closed": []}
                    self.store.replace_positions(trader["user_id"], current)
                    now = datetime.now().strftime("%H:%M:%S")
                    self.console.print(f"[dim]{now}[/] [bold cyan]@{trader['handle']}[/]  swaps [bold]{len(new_swaps)}[/]  positions [bold]{sum(len(items) for items in changes.values())}[/]")
                    if cycles > 1:
                        for swap in sorted(new_swaps, key=lambda item: item.get("createdAt", "")):
                            self.console.print(f"  [green]NEW SWAP[/] {self.money(swap.get('humanUsdAmountIn') or swap.get('humanUsdAmountOut'))}  {self.short(swap.get('outTokenAddress'))} -> {self.short(swap.get('inTokenAddress'))}")
                        for kind, items in changes.items():
                            for item in items:
                                position = item["position"]
                                self.console.print(f"  [yellow]{kind.upper()}[/] {position.get('symbol')}  change {decimal_value(item.get('change')):,.6f}  {NETWORKS.get(position.get('networkId'), position.get('networkId'))}")
                except FomoApiError as error:
                    self.console.print(f"[red]@{trader['handle']}: {error}[/]")
            time.sleep(interval)

    def show_following(self):
        self.require_key()
        payload = self.request("Loading following IDs", self.client.following_ids)
        ids = self.client.response_object(payload).get("followingIds", [])
        table = Table(title="Upstream Following IDs", box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
        table.add_column("#", justify="right")
        table.add_column("User ID")
        for index, user_id in enumerate(ids, 1):
            table.add_row(str(index), str(user_id))
        self.console.print(table)

    def export_trader(self):
        profile = self.profile_from_prompt()
        user_id = profile.get("id")
        balances = self.request("Loading balances", self.client.balances, user_id)
        swaps = self.request("Loading swaps", self.client.swaps, user_id, 150)
        ranking = self.request("Loading rankings", self.client.trader_ranking, user_id)
        data = {
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "profile": profile,
            "balances": self.client.response_object(balances),
            "swaps": self.client.response_object(swaps),
            "ranking": self.client.response_object(ranking),
        }
        EXPORT_PATH.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = EXPORT_PATH / f"{profile.get('userHandle', 'trader')}_{timestamp}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self.console.print(Panel(str(path), title="[green]EXPORT CREATED[/]", border_style="green"))
