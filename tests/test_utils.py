import pytest
from pandas import Timestamp
from pandas.testing import assert_frame_equal

from kipubot.db import (
    delete_chat,
    delete_raffle_data,
    init_db,
    register_user,
    save_chat_or_ignore,
    save_user_or_ignore,
)
from kipubot.types import RaffleData
from kipubot.utils import (
    get_raffle,
    int_price_to_str,
    read_excel_to_df,
    remove_emojis,
    save_raffle,
)


class TestUtils:
    def test_int_price_to_str(self):
        test_cases = [
            -10000,
            -1001,
            -101,
            -100,
            -99,
            -50,
            -10,
            -1,
            0,
            1,
            10,
            50,
            100,
            101,
            150,
            1001,
            10001,
            100001,
        ]

        expected_results = [
            "-100",
            "-10.01",
            "-1.01",
            "-1",
            "-0.99",
            "-0.5",
            "-0.1",
            "-0.01",
            "0",
            "0.01",
            "0.1",
            "0.5",
            "1",
            "1.01",
            "1.5",
            "10.01",
            "100.01",
            "1000.01",
        ]

        results = [int_price_to_str(price) for price in test_cases]

        assert results == expected_results

    def test_remove_emojis(self):
        assert remove_emojis("💩") == " "
        assert (
            remove_emojis("text💩with💩emoji💩in💩the💩middle")
            == "text with emoji in the middle"
        )
        assert (
            remove_emojis("💩text with emoji at the start")
            == " text with emoji at the start"
        )
        assert (
            remove_emojis("text with emoji at the end💩")
            == "text with emoji at the end "
        )
        assert (
            remove_emojis("💩text with emoji💩at the start, middle and end💩")
            == " text with emoji at the start, middle and end "
        )


class TestGraphSave:
    @pytest.fixture(autouse=True)
    def create_chat(self):
        init_db()
        save_chat_or_ignore(1, "testing", [1])
        save_user_or_ignore(1)
        register_user(1, 1)
        yield 1
        delete_chat(1)

    def test_graph_save(self):
        file_path = "tests/example_data/example_1.xlsx"
        start_date = Timestamp("2022-08-01 03:15:00")
        end_date = Timestamp("2022-08-12 03:15:00")
        entry_fee = 1
        raffle_dataframe = read_excel_to_df(file_path, start_date, end_date)
        raffle_data = RaffleData(start_date, end_date, entry_fee, raffle_dataframe)
        save_raffle(1, 1, raffle_data)
        raffle_from_db = get_raffle(1)
        delete_raffle_data(1)
        assert start_date == raffle_from_db.start_date
        assert end_date == raffle_from_db.end_date
        assert entry_fee == raffle_from_db.entry_fee

        # behavior that get_raffle returns without index and
        # read returns with probably should be changed.
        raffle_dataframe = raffle_dataframe.set_index("date")
        assert_frame_equal(raffle_dataframe, raffle_from_db.df)
