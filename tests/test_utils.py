#!/usr/bin/env python3

# import pytest

from kipubot.utils import int_price_to_str, remove_emojis


class TestUtils:

    def test_int_price_to_str(self):
        assert int_price_to_str(-100) == '-1'
        assert int_price_to_str(-50) == '-0.5'
        assert int_price_to_str(0) == '0'
        assert int_price_to_str(50) == '0.5'
        assert int_price_to_str(100) == '1'
        assert int_price_to_str(150) == '1.5'
        assert int_price_to_str(10000) == '100'

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
