import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from scipy import stats
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters
import psycopg.errors as PSErrors
from db import get_con

CON = get_con()


async def graph(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title

    base_path = f'data/{chat_id}/'

    excel_path = base_path + 'data.xlsx'
    graph_path = base_path + 'graph.png'

    try:
        query_result = (
            CON.execute('SELECT * FROM raffle WHERE chat_id = %s', (chat_id,))
            .fetchone())

        if not query_result:
            await update.message.reply_text(f'No raffle data found in {chat_title}!')
            return

        _, start_str, end_str, _entry_fee = query_result

        start_date = pd.to_datetime(start_str)
        end_date = pd.to_datetime(end_str)
        _days = (end_date - start_date).days

        df = pd.read_excel(excel_path, usecols='A,D', header=None, names=[
            'date', 'amount'], parse_dates=True)

        df.drop(df[df['amount'] <= 0].index, inplace=True)
        df.drop(df[df['date'] > end_date].index, inplace=True)
        df.drop(df[df['date'] < start_date].index, inplace=True)

        df['datenum'] = pd.to_numeric(df['date']) // 1_000_000_000

        df.set_index('date', inplace=True)

        df = df.iloc[::-1]

        df['amount'] = df['amount'].cumsum()

        y = df['amount'].values
        x = df['datenum'].values

        if not df.size > 0:
            await update.message.reply_text(f'No raffle entries yet in {chat_title}!')
            return

        slope, intercept, _r, _p, sterr = stats.linregress(x, y)

        df['y_pred'] = slope * x + intercept

        n = len(x)
        t = stats.t.ppf(0.975, n-2)
        pi = t * sterr * np.sqrt(1 + 1/n +
                                 (x-x.mean())**2/sum((x-x.mean())**2))

        df['max_pred'] = df['y_pred'] + pi * 1e3
        df['min_pred'] = df['y_pred'] - pi * 1e3

        _fig, ax = plt.subplots()

        df['amount'].plot(ax=ax, style='xr')
        df['y_pred'].plot(ax=ax, color='orange')
        df['min_pred'].plot(ax=ax, style='--b')
        df['max_pred'].plot(ax=ax, style='--b')

        plt.xlim((pd.to_datetime(start_date), pd.to_datetime(end_date)))
        total = df['amount'].max()
        plt.title(f'{chat_title} -- Pool {total}€')
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

        plt.savefig(graph_path)

        with open(graph_path, 'rb') as f:
            await update.message.reply_photo(photo=f)

    except PSErrors.Error as e:
        print(e)
        await update.message.reply_text('Error getting raffle data from database!\n\n' +
                                        'Perhaps one is not setup yet for this chat? 🤔')

    except FileNotFoundError:
        await update.message.reply_text(f'No data found for {chat_title}!')

graph_handler = CommandHandler(
    ['kuvaaja', 'graph'], graph, ~Filters.ChatType.PRIVATE)
