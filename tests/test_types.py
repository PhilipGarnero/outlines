import json
import re
from dataclasses import dataclass

import pytest
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel
from typing_extensions import TypedDict

from outlines import types
from outlines.fsm.types import python_types_to_regex


def test_type_json_error():
    with pytest.raises(TypeError, match="The Json definition"):
        a = types.Json(0)
        a.to_json_schema()

    with pytest.raises(SchemaError):
        a = types.Json({"type": "object", "properties": {"foo": "bar"}})
        a.to_json_schema()

    with pytest.raises(SchemaError):
        a = types.Json('{"type": "object", "properties": {"foo": "bar"}}')
        a.to_json_schema()


def test_type_json():
    class Foo(BaseModel):
        bar: int

    json_schema_dict = Foo.model_json_schema()
    json_schema_str = json.dumps(json_schema_dict)

    json_type = types.Json(Foo)
    assert json_type.to_json_schema() == json_schema_dict

    json_type = types.Json(json_schema_dict)
    assert json_type.to_json_schema() == json_schema_dict

    json_type = types.Json(json_schema_str)
    assert json_type.to_json_schema() == json_schema_dict

    class Foo(TypedDict):
        bar: int

    json_type = types.Json(Foo)
    assert json_type.to_json_schema() == json_schema_dict

    @dataclass
    class Foo:
        bar: int

    json_type = types.Json(Foo)
    assert json_type.to_json_schema() == json_schema_dict


def test_type_choice():
    choices = ["a", "b"]
    choice_type = types.Choice(choices)
    assert choice_type.definition.a.value == "a"

    regex_str = choice_type.to_regex()
    assert regex_str == "(a|b)"


def test_type_list():
    class Foo(BaseModel):
        bar: int

    list_type = types.List(Foo)
    with pytest.raises(NotImplementedError, match="Structured"):
        list_type.to_regex()


@pytest.mark.parametrize(
    "custom_type,test_string,should_match",
    [
        (types.phone_numbers.USPhoneNumber, "12", False),
        (types.phone_numbers.USPhoneNumber, "(123) 123-1234", True),
        (types.phone_numbers.USPhoneNumber, "123-123-1234", True),
        (types.zip_codes.USZipCode, "12", False),
        (types.zip_codes.USZipCode, "12345", True),
        (types.zip_codes.USZipCode, "12345-1234", True),
        (types.ISBN, "ISBN 0-1-2-3-4-5", False),
        (types.ISBN, "ISBN 978-0-596-52068-7", True),
        # (types.ISBN, "ISBN 978-0-596-52068-1", True), wrong check digit
        (types.ISBN, "ISBN-13: 978-0-596-52068-7", True),
        (types.ISBN, "978 0 596 52068 7", True),
        (types.ISBN, "9780596520687", True),
        (types.ISBN, "ISBN-10: 0-596-52068-9", True),
        (types.ISBN, "0-596-52068-9", True),
        (types.Email, "eitan@gmail.com", True),
        (types.Email, "99@yahoo.com", True),
        (types.Email, "eitan@.gmail.com", False),
        (types.Email, "myemail", False),
        (types.Email, "eitan@gmail", False),
        (types.Email, "eitan@my.custom.domain", True),
    ],
)
def test_type_regex(custom_type, test_string, should_match):
    class Model(BaseModel):
        attr: custom_type

    schema = Model.model_json_schema()
    assert schema["properties"]["attr"]["type"] == "string"
    regex_str = schema["properties"]["attr"]["pattern"]
    does_match = re.match(regex_str, test_string) is not None
    assert does_match is should_match

    regex_str, format_fn = python_types_to_regex(custom_type)
    assert isinstance(format_fn(1), str)
    does_match = re.match(regex_str, test_string) is not None
    assert does_match is should_match


def test_locale_not_implemented():
    with pytest.raises(NotImplementedError):
        types.locale("fr")


@pytest.mark.parametrize(
    "locale_str,base_types,locale_types",
    [
        (
            "us",
            ["ZipCode", "PhoneNumber"],
            [types.zip_codes.USZipCode, types.phone_numbers.USPhoneNumber],
        )
    ],
)
def test_locale(locale_str, base_types, locale_types):
    for base_type, locale_type in zip(base_types, locale_types):
        type = getattr(types.locale(locale_str), base_type)
        assert type == locale_type


@pytest.mark.parametrize(
    "custom_type,test_string,should_match",
    [
        (types.airports.IATA, "CDG", True),
        (types.airports.IATA, "XXX", False),
        (types.countries.Alpha2, "FR", True),
        (types.countries.Alpha2, "XX", False),
        (types.countries.Alpha3, "UKR", True),
        (types.countries.Alpha3, "XXX", False),
        (types.countries.Numeric, "004", True),
        (types.countries.Numeric, "900", False),
        (types.countries.Name, "Ukraine", True),
        (types.countries.Name, "Wonderland", False),
        (types.countries.Flag, "🇿🇼", True),
        (types.countries.Flag, "🤗", False),
    ],
)
def test_type_enum(custom_type, test_string, should_match):
    type_name = custom_type.__name__

    class Model(BaseModel):
        attr: custom_type

    schema = Model.model_json_schema()
    assert isinstance(schema["$defs"][type_name]["enum"], list)
    does_match = test_string in schema["$defs"][type_name]["enum"]
    assert does_match is should_match

    regex_str, format_fn = python_types_to_regex(custom_type)
    assert isinstance(format_fn(1), str)
    does_match = re.match(regex_str, test_string) is not None
    assert does_match is should_match
