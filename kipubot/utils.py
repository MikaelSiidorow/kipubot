import os
import re
from typing import NamedTuple, Optional
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator
import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
import uncertainties as unc
import uncertainties.unumpy as unp
from kipubot.errors import NoRaffleError
from kipubot import db


class RaffleData(NamedTuple):
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    entry_fee: int
    df: Optional[pd.DataFrame]


def int_price_to_str(num: int) -> str:
    return re.sub(r'\.0', '', str(num/100.0))


def preband(x, xd, yd, p, func):
    conf = 0.95
    alpha = 1.0 - conf
    quantile = stats.t.ppf(1.0 - alpha / 2.0, xd.size - len(p))
    stdev = np.sqrt(1. / (xd.size - len(p)) * np.sum((yd - func(xd, *p))**2))
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


def fit_timedata(x_series: pd.Series, y_series: pd.Series):
    # ignore the end date in curve fitting
    x = x_series.values[:-1]
    y = y_series.values[:-1]

    def f(x, slope, intercept):
        return slope * x + intercept

    # pylint: disable=unbalanced-tuple-unpacking
    popt, pcov = curve_fit(f, x, y)

    a, b = unc.correlated_values(popt, pcov)

    # calculate regression confidence interval
    px = np.linspace(x_series[:1], x_series[-1:], y_series.size)
    py = a*px+b
    nom = unp.nominal_values(py)
    std = unp.std_devs(py)

    lpb, upb = preband(px, x, y, popt, f)

    # convert back to dates
    px = [pd.to_datetime(x, unit='ns') for x in px]

    return (px, nom, std, lpb, upb)


def remove_emojis(text: str) -> str:
    emojis = re.compile(pattern="["
                        u"\U0001F600-\U0001F64F"  # emoticons
                        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                        u"\U0001F680-\U0001F6FF"  # transport & map symbols
                        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                        "]+", flags=re.UNICODE)
    return emojis.sub(r' ', text)


def validate_excel(excel_path: str) -> bool:
    df = pd.read_excel(excel_path, usecols='A,B,D', header=None, names=[
        'date', 'name', 'amount'], parse_dates=True)
    return (df.size > 0 and
            df['date'].dtype == 'datetime64[ns]' and
            df['name'].dtype == 'object' and
            df['amount'].dtype in ('int64', 'float64'))


def read_excel_to_df(excel_path: str,
                     start_date: pd.Timestamp,
                     end_date: pd.Timestamp) -> pd.DataFrame:
    df = pd.read_excel(excel_path, usecols='A,B,D', header=None, names=[
        'date', 'name', 'amount'], parse_dates=True)
    df.drop(df[df['amount'] <= 0].index, inplace=True)
    df.drop(df[df['date'] > end_date].index, inplace=True)
    df.drop(df[df['date'] < start_date].index, inplace=True)
    df['amount'] = df['amount'] * 100
    return df


def get_raffle(chat_id: int, include_df: bool = False) -> RaffleData:
    query_result = db.get_raffle_data(chat_id)

    if query_result is None:
        raise NoRaffleError(f'No raffle found for chat {chat_id}')

    _, start_date, end_date, entry_fee, dates, entries, amounts = query_result

    if include_df:
        df = pd.DataFrame(
            data={'date': dates, 'name': entries, 'amount': amounts})
        df.set_index('date', inplace=True)
        return RaffleData(start_date, end_date, entry_fee, df)

    return RaffleData(start_date, end_date, entry_fee, None)


def get_cur_time_hel() -> pd.Timestamp:
    # take current time in helsinki and convert it to naive time,
    # as mobilepay times are naive (naive = no timezone specified).
    helsinki_tz = pytz.timezone('Europe/Helsinki')
    cur_time_hel = pd.Timestamp.utcnow().astimezone(helsinki_tz).replace(tzinfo=None)

    return cur_time_hel


def save_raffle(chat_id: int,
                start_date: pd.Timestamp,
                end_date: pd.Timestamp,
                entry_fee: int,
                df: pd.DataFrame) -> None:
    db.save_raffle_data(chat_id, start_date, end_date, entry_fee, df)


def parse_df_essentials(raffle_data: RaffleData) -> RaffleData:
    start_date, end_date, fee, df = raffle_data

    df.at[start_date, 'amount'] = 0

    df['datenum'] = pd.to_numeric(df.index.values)
    df = df.sort_values('datenum')
    df['amount'] = df['amount'].cumsum().astype(int)
    df['unique'] = (~df['name'].duplicated()).cumsum() - 1

    return RaffleData(start_date, end_date, fee, df)


def parse_expected(raffle_data: RaffleData) -> RaffleData:
    start_date, end_date, entry_fee, df = parse_df_essentials(raffle_data)

    df['win_odds'] = 1.0 / df['unique']
    df['next_expected'] = ((- entry_fee * (1 - df['win_odds'])
                           + (df['amount'] - entry_fee) * df['win_odds'])
                           ).fillna(0).round().astype(int)

    return RaffleData(start_date, end_date, entry_fee, df)


def parse_graph(raffle_data: RaffleData) -> RaffleData:
    df = raffle_data.df

    df.at[get_cur_time_hel(), 'amount'] = 0
    df.at[raffle_data.end_date, 'amount'] = 0

    parsed_raffle_data = parse_df_essentials(
        raffle_data._replace(df=df))

    return parsed_raffle_data


def configure_and_save_plot(out_img_path: str) -> None:
    ax = plt.gca()

    # toggle legend
    ax.legend()

    # format axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m. %H:%M'))
    ax.yaxis.set_major_formatter(lambda x, _: int_price_to_str(x))

    # set grid
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    plt.grid(visible=True, which='major',
             axis='both', linestyle='--', linewidth=0.5)

    if not os.path.exists(os.path.dirname(out_img_path)):
        os.makedirs(os.path.dirname(out_img_path))

    plt.savefig(out_img_path)
    plt.clf()


def generate_graph(out_img_path: str,
                   chat_id: int,
                   chat_title: str) -> None:

    # -- get raffle data --
    raffle_data = get_raffle(chat_id, include_df=True)

    # -- parse and fit data --
    start_date, end_date, _, df = parse_graph(raffle_data)
    px, nom, std, lpb, upb = fit_timedata(df['datenum'], df['amount'])

    # -- plot --
    ax = plt.gca()
    # plot data
    df['amount'][:-1].plot(ax=ax, marker='o', style='r', label='Pool')
    # plot regression
    ax.plot(px, nom, '-', color='black', label='y=ax+b')
    # uncertainty lines (95% conf)
    ax.plot(px, nom-1.96*std, c='orange', label='95% confidence region')
    ax.plot(px, nom+1.96*std, c='orange')
    # prediction band (95% conf)
    ax.plot(px, lpb, 'k--', label='95% prediction band')
    ax.plot(px, upb, 'k--')

    # -- style graph --
    pred_max_pool = (nom+1.96*std)[-1]
    plt.ylim(0, pred_max_pool)
    plt.xlim((pd.to_datetime(start_date), pd.to_datetime(end_date)))

    plt.title(str(remove_emojis(chat_title).strip()) + "\n" +
              f"Entries {df['unique'].max()} | Pool {int_price_to_str(df['amount'].max())} €")
    plt.xlabel(None)
    plt.ylabel('Pool (€)')

    configure_and_save_plot(out_img_path)


def generate_expected(out_img_path: str,
                      chat_id: int,
                      chat_title: str) -> None:

    # -- get raffle data --
    raffle_data = get_raffle(chat_id, include_df=True)

    # -- parse and fit data --
    start_date, _, entry_fee, df = parse_expected(raffle_data)

    # -- plot --
    ax = plt.gca()

    df['next_expected'].plot(
        ax=ax, marker='o', style='r', label='Expected Value')

    # -- style graph --
    plt.ylim(int(int_price_to_str((df['next_expected'].min() - 100) * 110)),
             int(int_price_to_str((df['next_expected'].max() + 100) * 110)))
    plt.xlim((pd.to_datetime(start_date), pd.to_datetime(get_cur_time_hel())))

    plt.title(str(remove_emojis(chat_title).strip()) +
              f' | Fee {int_price_to_str(entry_fee)} €\n' +
              f"Expected Value { int_price_to_str(df['next_expected'].iloc[-1])} €")
    plt.xlabel(None)
    plt.ylabel('Expected Value (€)')

    configure_and_save_plot(out_img_path)
