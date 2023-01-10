import barebones as app


class TestSuite:
    def test_version(self) -> None:
        assert app.__version__ == "0.1.0"
