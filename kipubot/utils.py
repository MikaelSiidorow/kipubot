"""Utility functions for Kipubot."""

import re
from pathlib import Path
from typing import Any

import matplotlib.dates as mdates  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import numpy as np
import pandas as pd
import pytz
import uncertainties as unc  # type: ignore
import uncertainties.unumpy as unp  # type: ignore
from matplotlib.ticker import AutoMinorLocator  # type: ignore
from scipy import stats  # type: ignore
from scipy.optimize import curve_fit  # type: ignore
from telegram import Chat, ChatMember
from telegram.error import BadRequest

from kipubot.db import get_raffle_data, save_raffle_data, update_raffle_data
from kipubot.errors import NoEntriesError, NoRaffleError
from kipubot.types import RaffleData, RaffleStatsData


def is_int(x: str) -> bool:
    """Safely check if a string is an integer."""
    try:
        int(x)
    except ValueError:
        return False
    else:
        return True


def is_float(x: str) -> bool:
    """Safely check if a string is a float."""
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True


def int_price_to_str(num: int) -> str:
    """Format an integer price to a string."""
    float_num = num / 100.0

    str_num: str = (
        format(float_num, ".2f") if float_num >= 0 else "-" + format(-float_num, ".2f")
    )

    euros, cents = str_num.split(".")

    if cents == "00":
        return euros

    if cents[1] == "0":
        return euros + "." + cents[0]

    return str_num


async def get_chat_member_opt(chat: Chat, member_id: int) -> ChatMember | None:
    """Get a chat member, or None if the user is not in the chat."""
    try:
        return await chat.get_member(member_id)
    except BadRequest as e:
        if e.message == "User not found":
            return None
        raise


def preband(x, xd, yd, p, func):  # noqa: ANN201, ANN001
    """Calculate the prediction band for a curve fit."""
    conf = 0.95
    alpha = 1.0 - conf
    quantile = stats.t.ppf(1.0 - alpha / 2.0, xd.size - len(p))
    stdev = np.sqrt(1.0 / (xd.size - len(p)) * np.sum((yd - func(xd, *p)) ** 2))
    # auxiliary definitions
    sx = (x - xd.mean()) ** 2
    sxd = np.sum((xd - xd.mean()) ** 2)
    # predicted values (best-fit model)
    yp = func(x, *p)
    # prediction band
    dy = quantile * stdev * np.sqrt(1.0 + 1.0 / xd.size + sx / sxd)
    # upper & lower
    lpb, upb = yp - dy, yp + dy
    return lpb, upb


def fit_timedata(  # noqa: ANN201
    x_series: "pd.Series[Any]",
    y_series: "pd.Series[Any]",
):
    """Fit a curve to the data."""
    # ignore the end date in curve fitting
    x = x_series.to_numpy()[:-1]
    y = y_series.to_numpy()[:-1]

    def f(x, slope, intercept):  # noqa: ANN001, ANN202
        return slope * x + intercept

    popt, pcov = curve_fit(f, x, y)

    a, b = unc.correlated_values(popt, pcov)

    # calculate regression confidence interval

    # if cur time later than raffle end date, use the end date
    now = get_cur_time_hel().value
    end = x_series[-2] if now >= x_series[-1] else x_series[-1]

    px = np.linspace(x_series[0], end, y_series.size - 1, dtype=np.int64)
    py = a * px + b
    nom = unp.nominal_values(py)
    std = unp.std_devs(py)

    lpb, upb = preband(px, x, y, popt, f)

    # convert back to dates
    px_dates = [pd.to_datetime(x, unit="ns") for x in px]

    return (px_dates, nom, std, lpb, upb)


def remove_emojis(text: str) -> str:
    """Remove emojis from a string."""
    emojis = re.compile(
        pattern="["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags=re.UNICODE,
    )
    return emojis.sub(r" ", text)


def validate_excel(excel_path: str) -> bool:
    """Validate that the submitted excel file is in the correct (MP) format."""
    mp_excel_df = pd.read_excel(
        excel_path,
        usecols="A,B,D",
        header=None,
        names=["date", "name", "amount"],
        parse_dates=True,
    )
    return (
        mp_excel_df.size > 0
        and mp_excel_df["date"].dtype == "datetime64[ns]"
        and mp_excel_df["name"].dtype == "object"
        and mp_excel_df["amount"].dtype in ("int64", "float64")
    )


def read_excel_to_df(
    excel_path: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    """Read the excel file to a dataframe."""
    mobilepay_df = pd.read_excel(
        excel_path,
        usecols="A,B,D",
        header=None,
        names=["date", "name", "amount"],
        parse_dates=True,
    )
    mobilepay_df = mobilepay_df.drop(mobilepay_df[mobilepay_df["amount"] <= 0].index)
    mobilepay_df = mobilepay_df.drop(
        mobilepay_df[mobilepay_df["date"] > end_date].index,
    )
    mobilepay_df = mobilepay_df.drop(
        mobilepay_df[mobilepay_df["date"] < start_date].index,
    )
    mobilepay_df["amount"] = mobilepay_df["amount"] * 100
    return mobilepay_df


def get_raffle_stats(chat_id: int) -> tuple[str, RaffleStatsData]:
    """Get the stats of a raffle, not including dataframe."""
    query_result = get_raffle_data(chat_id)

    if query_result is None:
        error_text = f"No raffle found for chat {chat_id}"
        raise NoRaffleError(error_text)

    raffle_id, start_date, end_date, _, entry_fee, _, _, _, _, _ = query_result

    return (raffle_id, RaffleStatsData(start_date, end_date, entry_fee))


def get_raffle(chat_id: int) -> RaffleData:
    """Get the data of a raffle, including dataframe."""
    query_result = get_raffle_data(chat_id)

    if query_result is None:
        error_text = f"No raffle found for chat {chat_id}"
        raise NoRaffleError(error_text)

    _, start_date, end_date, _, entry_fee, dates, entries, amounts, _, _ = query_result

    if len(dates) == 0 or len(entries) == 0 or len(amounts) == 0:
        error_text = f"No entries found for chat {chat_id}"
        raise NoEntriesError(error_text)

    mp_dataframe = pd.DataFrame(
        data={"date": dates, "name": entries, "amount": amounts},
    )
    mp_dataframe = mp_dataframe.set_index("date")

    return RaffleData(start_date, end_date, entry_fee, mp_dataframe)


def get_cur_time_hel() -> pd.Timestamp:
    """Get the current time in Helsinki as a Timestamp.

    Take current time in helsinki and convert it to naive time,
    as mobilepay times are naive (naive = no timezone specified).
    """
    helsinki_tz = pytz.timezone("Europe/Helsinki")

    return pd.Timestamp.utcnow().astimezone(helsinki_tz).replace(tzinfo=None)


def save_raffle(
    chat_id: int,
    user_id: int,
    raffle_data: RaffleData,
) -> None:
    """Save a raffle to the database."""
    save_raffle_data(chat_id, user_id, raffle_data)


def update_raffle(
    raffle_id: str,
    raffle_data: RaffleData,
) -> None:
    """Update a raffle in the database."""
    update_raffle_data(raffle_id, raffle_data)


def parse_df_essentials(raffle_data: RaffleData) -> RaffleData:
    """Parse the essentials of a raffle dataframe."""
    start_date, end_date, fee, mp_dataframe = raffle_data

    mp_dataframe.loc[start_date, "amount"] = 0

    mp_dataframe["datenum"] = pd.to_numeric(mp_dataframe.index.values)
    mp_dataframe = mp_dataframe.sort_values("datenum")
    mp_dataframe["amount"] = mp_dataframe["amount"].cumsum().astype(int)
    mp_dataframe["unique"] = (~mp_dataframe["name"].duplicated()).cumsum() - 1

    return RaffleData(start_date, end_date, fee, mp_dataframe)


def parse_expected(raffle_data: RaffleData) -> RaffleData:
    """Parse the expected values of a raffle dataframe."""
    start_date, end_date, entry_fee, mp_dataframe = parse_df_essentials(raffle_data)

    mp_dataframe["win_odds"] = 1.0 / mp_dataframe["unique"]
    mp_dataframe["next_expected"] = (
        (
            -entry_fee * (1 - mp_dataframe["win_odds"])
            + (mp_dataframe["amount"] - entry_fee) * mp_dataframe["win_odds"]
        )
        .fillna(0)
        .round()
        .astype(int)
    )

    return RaffleData(start_date, end_date, entry_fee, mp_dataframe)


def parse_graph(raffle_data: RaffleData) -> RaffleData:
    """Parse the graph values of a raffle dataframe."""
    mp_dataframe = raffle_data.df

    mp_dataframe.loc[get_cur_time_hel(), "amount"] = 0
    mp_dataframe.loc[raffle_data.end_date, "amount"] = 0

    return parse_df_essentials(
        raffle_data._replace(df=mp_dataframe),
    )


def configure_and_save_plot(out_img_path: str) -> None:
    """Configure and save the plot to an image file."""
    ax = plt.gca()

    # toggle legend
    ax.legend()

    # format axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m. %H:%M"))
    ax.yaxis.set_major_formatter(lambda x, _: int_price_to_str(x))

    # set grid
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    plt.grid(visible=True, which="major", axis="both", linestyle="--", linewidth=0.5)

    Path(out_img_path).parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(out_img_path)
    plt.clf()


def generate_graph(out_img_path: str, chat_id: int, chat_title: str) -> None:
    """Generate a graph of raffle progress."""
    # -- get raffle data --
    raffle_data = get_raffle(chat_id)

    # -- parse and fit data --
    start_date, end_date, _, mp_dataframe = parse_graph(raffle_data)
    px, nom, std, lpb, upb = fit_timedata(
        mp_dataframe["datenum"],
        mp_dataframe["amount"],
    )

    # -- plot --
    # clear previous plot in case of leftovers
    plt.clf()
    ax = plt.gca()
    # plot data
    mp_dataframe["amount"][:-1].plot(ax=ax, marker="o", style="r", label="Pool")
    # plot regression
    ax.plot(px, nom, "-", color="black", label="y=ax+b")
    # uncertainty lines (95% conf)
    ax.plot(px, nom - 1.96 * std, c="orange", label="95% confidence region")
    ax.plot(px, nom + 1.96 * std, c="orange")
    # prediction band (95% conf)
    ax.plot(px, lpb, "k--", label="95% prediction band")
    ax.plot(px, upb, "k--")

    # -- style graph --
    pred_max_pool = (nom + 1.96 * std)[-1]
    pool_total = mp_dataframe["amount"].max()
    plt.ylim(0, max(pred_max_pool, pool_total))
    plt.xlim((pd.to_datetime(start_date), pd.to_datetime(end_date)))

    plt.title(
        str(remove_emojis(chat_title).strip())
        + "\n"
        + f"Entries {mp_dataframe['unique'].max()}"
        + f" | Pool {int_price_to_str(pool_total)} €",
    )
    plt.xlabel(None)
    plt.ylabel("Pool (€)")

    configure_and_save_plot(out_img_path)


def generate_expected(out_img_path: str, chat_id: int, chat_title: str) -> None:
    """Generate a graph of expected values."""
    # -- get raffle data --
    raffle_data = get_raffle(chat_id)

    # -- parse and fit data --
    start_date, _, entry_fee, mp_dataframe = parse_expected(raffle_data)

    # -- plot --
    # clear previous plot in case of leftovers
    plt.clf()
    ax = plt.gca()

    mp_dataframe["next_expected"].plot(
        ax=ax,
        marker="o",
        style="r",
        label="Expected Value",
    )

    # -- style graph --
    plt.ylim(
        float(int_price_to_str((mp_dataframe["next_expected"].min() - 100) * 110)),
        float(int_price_to_str((mp_dataframe["next_expected"].max() + 100) * 110)),
    )
    plt.xlim((pd.to_datetime(start_date), pd.to_datetime(get_cur_time_hel())))

    plt.title(
        (
            f"{remove_emojis(chat_title).strip()}"
            " | "
            f"Fee {int_price_to_str(entry_fee)} €\n"
            "Expected Value "
            f"{int_price_to_str(mp_dataframe['next_expected'].iloc[-1])} €"
        ),
    )
    plt.xlabel(None)
    plt.ylabel("Expected Value (€)")

    configure_and_save_plot(out_img_path)
