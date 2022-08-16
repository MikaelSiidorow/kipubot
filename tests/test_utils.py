#!/usr/bin/env python3

# import pytest

from kipubot.utils import int_price_to_str, remove_emojis


class TestUtils:

    def test_int_price_to_str(self):
        test_cases = [-10000, -1001, -101, -100, -99, -50, -10, -1,
                      0,
                      1, 10, 50, 100, 101, 150, 1001, 10001, 100001]

        expected_results = ['-100', '-10.01', '-1.01', '-1', '-0.99', '-0.5', '-0.1', '-0.01',
                            '0',
                            '0.01', '0.1', '0.5', '1', '1.01', '1.5', '10.01', '100.01', '1000.01']

        results = [int_price_to_str(price) for price in test_cases]

        assert results == expected_results

        # for case, ex_res in zip(test_cases, expected_results):
        #    assert int_price_to_str(case) == ex_res

    def test_remove_emojis(self):
        assert remove_emojis('💩') == ' '
        assert remove_emojis(
            'text💩with💩emoji💩in💩the💩middle') == 'text with emoji in the middle'
        assert remove_emojis(
            '💩text with emoji at the start') == ' text with emoji at the start'
        assert remove_emojis(
            'text with emoji at the end💩') == 'text with emoji at the end '
        assert remove_emojis(
            '💩text with emoji💩at the start, middle and end💩') == ' text with emoji at the start, middle and end '
