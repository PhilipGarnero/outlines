from unittest.mock import MagicMock

import pytest

from outlines.outline import Outline


def test_outline_int_output():
    # Mock the model
    model = MagicMock()
    model.generate.return_value = "6"

    # Define the template function
    def template(a: int) -> str:
        return f"What is 2 times {a}?"

    # Create an instance of Outline
    fn = Outline(model, template, int)

    # Test the callable object
    result = fn(3)
    assert result == 6


def test_outline_str_output():
    # Mock the model
    model = MagicMock()
    model.generate.return_value = "'Hello, world!'"

    # Define the template function
    def template(a: int) -> str:
        return f"Say 'Hello, world!' {a} times"

    # Create an instance of Outline
    fn = Outline(model, template, str)

    # Test the callable object
    result = fn(1)
    assert result == "Hello, world!"


def test_outline_str_input():
    # Mock the model
    model = MagicMock()
    model.generate.return_value = "'Hi, Mark!'"

    # Define the template function
    def template(a: str) -> str:
        return f"Say hi to {a}"

    # Create an instance of Outline
    fn = Outline(model, template, str)

    # Test the callable object
    result = fn(1)
    assert result == "Hi, Mark!"


def test_outline_invalid_output():
    # Mock the model
    model = MagicMock()
    model.generate.return_value = "not a number"

    # Define the template function
    def template(a: int) -> str:
        return f"What is 2 times {a}?"

    # Create an instance of Outline
    fn = Outline(model, template, int)

    # Test the callable object with invalid output
    with pytest.raises(ValueError):
        fn(3)


def test_outline_mismatched_output_type():
    # Mock the model
    model = MagicMock()
    model.generate.return_value = "'Hello, world!'"

    # Define the template function
    def template(a: int) -> str:
        return f"What is 2 times {a}?"

    # Create an instance of Outline
    fn = Outline(model, template, int)

    # Test the callable object with mismatched output type
    with pytest.raises(
        ValueError,
        match="Unable to parse response: 'Hello, world!'",
    ):
        fn(3)
