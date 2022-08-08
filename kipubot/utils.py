import re
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
import uncertainties as unc
import uncertainties.unumpy as unp
from db import get_con
from errors import NoEntriesError, NoRaffleError

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
    # days = (end_date - start_date).days

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

    # parse dataframe a bit to make it easier to plot
    df['datenum'] = pd.to_numeric(df['date'])
    df = df.sort_values('datenum')
    df.set_index('date', inplace=True)
    df['amount'] = df['amount'].cumsum().astype(int)

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
    px = np.linspace(x[:1], x[-1:], df['amount'].size)
    py = a*px+b
    nom = unp.nominal_values(py)
    std = unp.std_devs(py)

    lpb, upb = preband(px, x, y, popt, f)

    # -- plot --
    _, ax = plt.subplots()

    # convert back to dates
    x = [pd.to_datetime(x, unit='ns') for x in x]
    px = [pd.to_datetime(x, unit='ns') for x in px]

    # plot data
    df['amount'].plot(ax=ax, style='xr', label='Data')
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
    plt.title(
        f'''{remove_emojis(chat_title).strip()} | {int_price_to_str(df['amount'].max())} €''')
    plt.xlabel(None)
    plt.ylabel('Pool (€)')
    ax.legend()

    # format axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m. %H:%M'))
    ax.yaxis.set_major_formatter(lambda x, _: int_price_to_str(x))

    # set grid (broken currently)
    # plt.grid(visible=True, which='minor',
    #         axis='both', linestyle='--', linewidth=1)
    # plt.tick_params(axis='x', which='both', length=0)
    # plt.tick_params(axis='y', which='both', length=0)
    # plt.setxticks(pd.to_datetime(start_date), pd.to_datetime(end_date))
    # plt.setyticks(np.arange(0, total, 100))

    plt.savefig(out_img_path)
