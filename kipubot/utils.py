from typing import Any
import re
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from scipy import stats
from db import get_con
from errors import NoEntriesError, NoRaffleError

CON = get_con()


def int_price_to_str(num: int) -> str:
    return re.sub(r'\.0', '', str(num/100.0))


def remove_emojis(text: str) -> str:
    emojis = re.compile(pattern="["
                        u"\U0001F600-\U0001F64F"  # emoticons
                        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                        u"\U0001F680-\U0001F6FF"  # transport & map symbols
                        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                        "]+", flags=re.UNICODE)
    return emojis.sub(r' ', text)


def calc_pi(x: Any, sterr: Any) -> Any:
    n = len(x)
    t = stats.t.ppf(0.975, n-2)
    pi = t * sterr * np.sqrt(1 + 1/n +
                             (x-x.mean())**2/sum((x-x.mean())**2))
    return pi


def excel_to_graph(excel_path: str,
                   out_img_path: str,
                   chat_id: str,
                   chat_title: str) -> None:
    query_result = (
        CON.execute('SELECT * FROM raffle WHERE chat_id = %s', (chat_id,))
        .fetchone())

    if not query_result:
        raise NoRaffleError(f'No raffle data found in {chat_title}!')

    _, start_date, end_date, _ = query_result

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    #days = (end_date - start_date).days

    df = pd.read_excel(excel_path, usecols='A,D', header=None, names=[
        'date', 'amount'], parse_dates=True)
    df.drop(df[df['amount'] <= 0].index, inplace=True)
    df.drop(df[df['date'] > end_date].index, inplace=True)
    df.drop(df[df['date'] < start_date].index, inplace=True)
    df['amount'] = df['amount'] * 100

    helsinki_tz = pytz.timezone('Europe/Helsinki')
    # take current time in helsinki and convert it to naive time,
    # as mobilepay times are naive (naive = no timezone specified).
    cur_time_hel = pd.Timestamp.utcnow().astimezone(helsinki_tz).replace(tzinfo=None)

    start_and_end_df = pd.DataFrame(
        [[start_date, 0.00], [cur_time_hel, 0.00], [end_date, 0.00]], columns=['date', 'amount'])
    df = pd.concat([df, start_and_end_df], sort=True)
    if not df.size > 0:
        raise NoEntriesError(f'No raffle entries yet in {chat_title}!')
    df['datenum'] = pd.to_numeric(df['date']) // 1_000_000_000
    df = df.sort_values('datenum')
    df.set_index('date', inplace=True)
    df['amount'] = df['amount'].cumsum().astype(int)
    # ignore the end date in curve fitting
    y = np.delete(df['amount'].values, -1)
    x = np.delete(df['datenum'].values, -1)

    slope, intercept, _, _, sterr = stats.linregress(x, y)

    df['y_pred'] = slope * df['datenum'] + intercept  # plot whole

    pi = calc_pi(df['datenum'].values, sterr)

    df['max_pred'] = df['y_pred'] + pi * 1e3
    df['min_pred'] = df['y_pred'] - pi * 1e3

    _, ax = plt.subplots()

    # plot all data
    df['amount'].plot(ax=ax, style='xr')
    df['y_pred'].plot(ax=ax, color='orange')
    df['min_pred'].plot(ax=ax, style='--b')
    df['max_pred'].plot(ax=ax, style='--b')

    # set limits
    pred_max_pool = slope * end_date.timestamp()+intercept
    plt.ylim(0, pred_max_pool)
    plt.xlim((pd.to_datetime(start_date), pd.to_datetime(end_date)))

    # set title and labels
    plt.title(
        f'''{remove_emojis(chat_title).strip()} | {int_price_to_str(df['amount'].max())} €''')
    plt.xlabel(None)
    plt.ylabel('Pool (€)')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m. %H:%M'))
    ax.yaxis.set_major_formatter(lambda x, _: int_price_to_str(x))

    ax.grid(visible=True, which='minor',
            axis='both', linestyle='--', linewidth=1)
    # plt.tick_params(axis='x', which='both', length=0)
    # plt.tick_params(axis='y', which='both', length=0)
    # plt.setxticks(pd.to_datetime(start_date), pd.to_datetime(end_date))
    # plt.setyticks(np.arange(0, total, 100))
    ax.legend(['Data', 'Linear Fit', 'Confidence Intervals'])

    plt.savefig(out_img_path)
