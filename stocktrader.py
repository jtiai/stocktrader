import random
from dearpygui import core, simple

STOCK_TABLE_OFFSETS = [0, 75, 75, 125, 75, 75, 75, 75]


class Offsets:
    def __init__(self, offsets):
        self.offsets = offsets

    def __getitem__(self, item):
        return sum(self.offsets[: item + 1])


stock_table_offsets = Offsets(STOCK_TABLE_OFFSETS)


def left_label_text(
    label: str, name: str, xoffset=100, default_value: str = ""
) -> None:
    core.add_text(label)
    core.add_same_line(xoffset=xoffset)
    core.add_text(name, default_value=default_value)


class Stock:
    def __init__(self, name, price=10):
        self.name = name
        self.price = price
        self.previous_price = 0
        self.dividend = 0
        self.change = 0

    def __str__(self):
        return self.name

    def new_price(self):
        self.dividend = random.random() * 1.5
        x = random.random()
        y = int(random.random() * 4 + 1)
        if x <= 0.4:
            m1 = 1
        elif x <= 0.7:
            m1 = -1
        else:
            m1 = 0
        self.change = m1 * self.price / 8 * y
        self.previous_price = self.price
        self.price += self.change
        if self.price <= 1:
            self.dividend = 0

    def is_bankcrupted(self):
        return self.price <= 1

    def is_share_issued(self):
        return self.price >= 30


class Player:
    def __init__(self, name, cash=100):
        self.name = name
        self.cash = cash

        self.owned_stocks = {}

    def __str__(self):
        return self.name

    def sell_stock(self, stock, amount):
        if self.owned_stocks[stock] < amount:
            raise ValueError("Attempting to sell too many stocks.")

        self.owned_stocks[stock] -= amount
        self.cash += stock.price * amount

    def buy_stock(self, stock, amount):
        if stock.price * amount > self.cash:
            raise ValueError("Not enough cash.")

        self.owned_stocks.setdefault(stock, 0)
        self.owned_stocks[stock] += amount
        self.cash -= stock.price * amount

    def apply_market_changes(self):
        for stock in self.owned_stocks:
            if stock.is_bankcrupted():
                self.owned_stocks[stock] = 0
            if stock.is_share_issued():
                self.owned_stocks[stock] += self.owned_stocks[stock] / 2
            self.cash += stock.dividend

    def get_owned_stocks(self, stock):
        try:
            return self.owned_stocks[stock]
        except KeyError:
            return 0


class StockTrader:
    def __init__(self):
        self.players = [
            Player("Player 1"),
        ]
        self.max_turns = 10
        self.round = 1
        self.player = self.players[0]  # Currently hardcoded

        # Pre-create 10 stocks
        self.stocks = [Stock(f"{i+1}") for i in range(10)]

    def buy_or_sell(self, sender, data):
        (stock,) = data
        currently_owned = self.player.get_owned_stocks(stock)
        change = core.get_value(sender) - currently_owned
        if change > 0:
            self.player.buy_stock(stock, change)
        elif change < 0:
            self.player.sell_stock(stock, -change)
        else:
            return  # Empty handed
        core.set_value("cash", self.player.cash)
        self.update_buy_caps()

    def update_buy_caps(self):
        """
        Update buy cap to reflect player cash
        """
        for stock in self.stocks:
            core.configure_item(
                f"stock.{stock.name}.owned",
                max_value=self.player.get_owned_stocks(stock)
                + int(self.player.cash / stock.price),
            )

    def news_close(self, sender):
        if sender:
            core.delete_item(sender)
        core.configure_item("next_round", enabled=True)
        for stock in self.stocks:
            core.configure_item(f"stock.{stock.name}.owned", enabled=True)

    def next_round(self):
        core.configure_item("next_round", enabled=False)

        self.round += 1
        core.set_value("round", str(self.round))

        for stock in self.stocks:
            core.configure_item(f"stock.{stock.name}.owned", enabled=False)
            stock.new_price()

        self.player.apply_market_changes()
        core.set_value("cash", self.player.cash)

        bankrupted = []
        share_issued = []
        for stock in self.stocks:
            if stock.is_bankcrupted():
                bankrupted.append(stock)
                stock.price = 10
                stock.dividend = 0
                stock.change = 0
                stock.previous_price = 0
            if stock.is_share_issued():
                share_issued.append(stock)
            core.set_value(f"stock.{stock.name}.price", f"{stock.price:0.2f}")
            core.set_value(
                f"stock.{stock.name}.previous_price", f"{stock.previous_price:0.2f}"
            )
            core.set_value(f"stock.{stock.name}.change", f"{stock.change:0.2f}")
            core.set_value(f"stock.{stock.name}.dividend", f"{stock.dividend:0.2f}")

        if bankrupted or share_issued:
            with simple.window(
                "Stock news!",
                autosize=True,
                no_collapse=True,
                no_move=True,
                on_close=self.news_close,
            ):
                if bankrupted:
                    core.add_text("The following stocks are gone bankruptcy:")
                    for stock in bankrupted:
                        core.add_text(f"{stock.name}")
                    core.add_spacing(count=5)
                if share_issued:
                    core.add_text("The following stocks are giving share issue:")
                    for stock in share_issued:
                        core.add_text(f"{stock.name}")
                core.add_spacing(count=5)
                core.add_button(
                    "Close", callback=lambda: self.news_close("Stock news!")
                )
        else:
            self.news_close("")

    def build(self):
        with simple.window("game_win", autosize=True):
            with simple.group("player"):
                left_label_text("Round: ", "round", default_value=str(self.round))
                left_label_text("Player: ", "player", default_value=self.player.name)
                left_label_text("Cash: ", "cash", default_value=str(self.player.cash))
                core.add_spacing(count=5)
                core.add_button(
                    "next_round", label="Next round", callback=self.next_round
                )

            core.add_spacing(count=5)
            core.add_separator()
            core.add_spacing(count=5)

            with simple.group("stocks"):
                # Titles
                core.add_text("Company")
                core.add_same_line(xoffset=stock_table_offsets[1])
                core.add_text("Price")
                core.add_same_line(xoffset=stock_table_offsets[2])
                core.add_text("Owned")
                core.add_same_line(xoffset=stock_table_offsets[3])
                core.add_text("Change")
                core.add_same_line(xoffset=stock_table_offsets[4])
                core.add_text("Old price")
                core.add_same_line(xoffset=stock_table_offsets[5])
                core.add_text("New price")
                core.add_same_line(xoffset=stock_table_offsets[6])
                core.add_text("Dividend")

                for stock in self.stocks:
                    core.add_text(stock.name)
                    core.add_same_line(xoffset=stock_table_offsets[1])
                    core.add_text(
                        f"stock.{stock.name}.price", default_value=str(stock.price)
                    )
                    core.add_same_line(xoffset=stock_table_offsets[2])

                    # Buy / Sell functionality
                    core.add_input_int(
                        f"stock.{stock.name}.owned",
                        label="",
                        default_value=self.player.get_owned_stocks(stock),
                        max_value=int(self.player.cash / stock.price),
                        min_clamped=True,
                        max_clamped=True,
                        callback=self.buy_or_sell,
                        callback_data=[
                            stock,
                        ],
                        width=100,
                    )

                    core.add_same_line(xoffset=stock_table_offsets[3])
                    core.add_text(
                        f"stock.{stock.name}.change", default_value=str(stock.change)
                    )
                    core.add_same_line(xoffset=stock_table_offsets[4])
                    core.add_text(
                        f"stock.{stock.name}.previous_price",
                        default_value=str(stock.previous_price),
                    )
                    core.add_same_line(xoffset=stock_table_offsets[5])
                    core.add_text(
                        f"stock.{stock.name}.price2", default_value=str(stock.price)
                    )
                    core.add_same_line(xoffset=stock_table_offsets[6])
                    core.add_text(
                        f"stock.{stock.name}.dividend",
                        default_value=str(stock.dividend),
                    )

        core.set_main_window_title("Stock Trader")
        core.set_main_window_size(650, 450)
        core.set_main_window_resizable(False)

    def run(self):
        self.build()

        core.start_dearpygui(primary_window="game_win")
        # core.add_debug_window("debug")
        # core.start_dearpygui()


if __name__ == "__main__":
    StockTrader().run()
