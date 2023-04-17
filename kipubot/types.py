"""Type definitions and classes for Kipubot."""

from typing import NamedTuple

from pandas import DataFrame, Timestamp


class RaffleStatsData(NamedTuple):
    """Data for raffle stats without entry data."""

    start_date: Timestamp
    end_date: Timestamp
    entry_fee: int


class RaffleData(NamedTuple):
    """Data for raffle stats with entry data."""

    start_date: Timestamp
    end_date: Timestamp
    entry_fee: int
    df: DataFrame
