from typing import Any
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from scipy import stats
from db import get_con
from errors import NoEntriesError, NoRaffleError

CON = get_con()


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

    helsinki_tz = pytz.timezone('Europe/Helsinki')
    # take current time in helsinki and convert it to naive time,
    # as mobilepay times are naive (naive = no timezone specified).
    cur_time_hel = pd.Timestamp.utcnow().astimezone(helsinki_tz).replace(tzinfo=None)
    print(cur_time_hel)
    end = end_date if cur_time_hel > end_date else cur_time_hel
    start_and_end_df = pd.DataFrame(
        [[start_date, 0.00], [end, 0.00]], columns=['date', 'amount'])
    df = pd.concat([df, start_and_end_df], sort=True)
    if not df.size > 0:
        raise NoEntriesError(f'No raffle entries yet in {chat_title}!')
    df['datenum'] = pd.to_numeric(df['date']) // 1_000_000_000
    df = df.sort_values('datenum')
    df.set_index('date', inplace=True)
    df['amount'] = df['amount'].cumsum()
    y = df['amount'].values
    x = df['datenum'].values

    slope, intercept, _, _, sterr = stats.linregress(x, y)

    df['y_pred'] = slope * x + intercept

    pi = calc_pi(x, sterr)

    df['max_pred'] = df['y_pred'] + pi * 1e3
    df['min_pred'] = df['y_pred'] - pi * 1e3

    _, ax = plt.subplots()

    df['amount'].plot(ax=ax, style='xr')
    df['y_pred'].plot(ax=ax, color='orange')
    df['min_pred'].plot(ax=ax, style='--b')
    df['max_pred'].plot(ax=ax, style='--b')

    plt.xlim((pd.to_datetime(start_date), pd.to_datetime(end_date)))
    plt.title(f'''{chat_title} -- Pool {df['amount'].max()}€''')
    plt.xlabel('Time')
    plt.ylabel('Pool (€)')
    # plt.xticks(np.linspace(start_date.toordinal(),
    #           end_date.toordinal(), days*6+1))
    # plt.ticklabel_format({},axis='x')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m. %H:%M'))

    ax.grid(visible=True, which='minor',
            axis='both', linestyle='--', linewidth=1)
    # plt.tick_params(axis='x', which='both', length=0)
    # plt.tick_params(axis='y', which='both', length=0)
    # plt.setxticks(pd.to_datetime(start_date), pd.to_datetime(end_date))
    # plt.setyticks(np.arange(0, total, 100))
    ax.legend(['Data', 'Linear Fit', 'Confidence Intervals'])

    plt.savefig(out_img_path)
