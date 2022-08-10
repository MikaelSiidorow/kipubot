import os
import re
from typing import Tuple, Union
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
from db import get_con
from errors import NoRaffleError

CON = get_con()


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


def remove_emojis(text: str) -> str:
    emojis = re.compile(pattern="["
                        u"\U0001F600-\U0001F64F"  # emoticons
                        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                        u"\U0001F680-\U0001F6FF"  # transport & map symbols
                        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                        "]+", flags=re.UNICODE)
    return emojis.sub(r' ', text)


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


def get_raffle(chat_id: int, include_df: bool = False) -> Tuple[
        pd.Timestamp, pd.Timestamp, int, Union[pd.DataFrame, None]]:

    query_result = CON.execute(
        'SELECT * FROM raffle WHERE chat_id = %s', [chat_id]).fetchone()

    if query_result is None:
        return None

    _, start_date, end_date, entry_fee, dates, entries, amounts = query_result

    if include_df:
        df = pd.DataFrame(
            data={'date': dates, 'name': entries, 'amount': amounts})
        df.set_index('date', inplace=True)
        return (start_date, end_date, entry_fee, df)

    return (start_date, end_date, entry_fee, None)


def save_raffle(chat_id: int,
                start_date: pd.Timestamp,
                end_date: pd.Timestamp,
                entry_fee: int,
                df: pd.DataFrame) -> None:

    dates = df['date'].tolist()
    entries = df['name'].tolist()
    amounts = df['amount'].tolist()

    CON.execute('''INSERT INTO raffle
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chat_id)
                    DO UPDATE SET 
                        start_date = EXCLUDED.start_date,
                        end_date = EXCLUDED.end_date,
                        entry_fee = EXCLUDED.entry_fee,
                        dates = EXCLUDED.dates,
                        entries = EXCLUDED.entries,
                        amounts = EXCLUDED.amounts''',
                (chat_id, start_date, end_date, entry_fee, dates, entries, amounts))

    CON.commit()


def generate_graph(out_img_path: str,
                   chat_id: str,
                   chat_title: str) -> None:
    query_result = get_raffle(chat_id, include_df=True)

    if not os.path.exists(os.path.dirname(out_img_path)):
        os.makedirs(os.path.dirname(out_img_path))

    if not query_result:
        raise NoRaffleError(f'No raffle data found in {chat_title}!')

    start_date, end_date, _, df = query_result

    # take current time in helsinki and convert it to naive time,
    # as mobilepay times are naive (naive = no timezone specified).
    helsinki_tz = pytz.timezone('Europe/Helsinki')
    cur_time_hel = pd.Timestamp.utcnow().astimezone(helsinki_tz).replace(tzinfo=None)

    df.at[start_date, 'amount'] = 0
    df.at[cur_time_hel, 'amount'] = 0
    df.at[end_date, 'amount'] = 0

    # parse dataframe a bit to make it easier to plot
    df['datenum'] = pd.to_numeric(df.index.values)
    df = df.sort_values('datenum')
    df['amount'] = df['amount'].cumsum().astype(int)
    df['unique'] = (~df['name'].duplicated()).cumsum() - 1

    # -- curve calculations --
    # ignore the end date in curve fitting
    x = np.delete(df['datenum'].values, -1)
    y = np.delete(df['amount'].values, -1)

    def f(x, slope, intercept):
        return slope * x + intercept

    # pylint: disable=unbalanced-tuple-unpacking
    popt, pcov = curve_fit(f, x, y)

    a, b = unc.correlated_values(popt, pcov)

    # calculate regression confidence interval
    px = np.linspace(df['datenum'][:1], df['datenum'][-1:], df['amount'].size)
    py = a*px+b
    nom = unp.nominal_values(py)
    std = unp.std_devs(py)

    lpb, upb = preband(px, x, y, popt, f)

    # -- plot --
    ax = plt.axes()

    # convert back to dates
    x = [pd.to_datetime(x, unit='ns') for x in x]
    px = [pd.to_datetime(x, unit='ns') for x in px]

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

    # set limits
    pred_max_pool = (nom+1.96*std)[-1]
    plt.ylim(0, pred_max_pool)
    plt.xlim((pd.to_datetime(start_date), pd.to_datetime(end_date)))

    # set title, labels and legend
    plt.title(str(remove_emojis(chat_title).strip()) + "\n" +
              f"Entries {df['unique'].max()} | Pool {int_price_to_str(df['amount'].max())} €")
    plt.xlabel(None)
    plt.ylabel('Pool (€)')
    ax.legend()

    # format axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m. %H:%M'))
    ax.yaxis.set_major_formatter(lambda x, _: int_price_to_str(x))

    # set grid
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    plt.grid(visible=True, which='major',
             axis='both', linestyle='--', linewidth=0.5)
    plt.savefig(out_img_path)
    plt.clf()


def generate_expected(out_img_path: str,
                      chat_id: str,
                      chat_title: str) -> None:
    query_result = get_raffle(chat_id, include_df=True)

    if not os.path.exists(os.path.dirname(out_img_path)):
        os.makedirs(os.path.dirname(out_img_path))

    if not query_result:
        raise NoRaffleError(f'No raffle data found in {chat_title}!')

    start_date, _, entry_fee, df = query_result

    helsinki_tz = pytz.timezone('Europe/Helsinki')
    cur_time_hel = pd.Timestamp.utcnow().astimezone(helsinki_tz).replace(tzinfo=None)

    df.at[start_date, 'amount'] = 0
    # parse dataframe a bit to make it easier to plot
    df['datenum'] = pd.to_numeric(df.index.values)
    df = df.sort_values('datenum')
    df['amount'] = df['amount'].cumsum().astype(int)
    df['unique'] = (~df['name'].duplicated()).cumsum() - 1
    df['win_odds'] = 1.0 / df['unique']
    df['next_expected'] = - entry_fee * \
        (1 - df['win_odds']) + (df['amount']) * df['win_odds']

    # -- plot --
    ax = plt.axes()

    # plot data
    df['next_expected'].plot(
        ax=ax, marker='o', style='r', label='Expected Value')

    # set limits
    plt.ylim(0, )
    plt.xlim((pd.to_datetime(start_date), pd.to_datetime(cur_time_hel)))

    # set title, labels and legend
    plt.title(str(remove_emojis(chat_title).strip()) +
              f' | Fee {int_price_to_str(entry_fee)} €\n' +
              f"Expected Value { (df['next_expected'].iloc[-1]/100):.2f} €")
    plt.xlabel(None)
    plt.ylabel('Expected Value (€)')
    ax.legend()

    # format axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m. %H:%M'))
    ax.yaxis.set_major_formatter(lambda x, _: int_price_to_str(x))

    # set grid
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    plt.grid(visible=True, which='major',
             axis='both', linestyle='--', linewidth=0.5)
    plt.savefig(out_img_path)
    plt.clf()
