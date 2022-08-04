#import logging
import psycopg
from config import DATABASE_URL

_CON = None

#_logger = logging.getLogger(__name__)


def get_con():
    global _CON  # pylint: disable=global-statement

    if not _CON:
        #_logger.info('Connecting to DB...')
        #logging.info('Connecting to DB')
        # print('Connnecting')
        _CON = psycopg.connect(DATABASE_URL)
        # _logger.info('Connected!')
        # print('Connected')

    return _CON


__all__ = (
    'get_con',
)
