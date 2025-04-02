"""
Tests for util module.
"""

import json

import mable.util as util


class TestJsonAble:

    def test_to_json(self):
        class TJA(util.JsonAble):
            def __init__(self):
                super().__init__()
                self.A = "A"
                self.B = "B"
        tja = TJA()
        assert tja.to_json() == json.dumps({"A": "A", "B": "B"})
