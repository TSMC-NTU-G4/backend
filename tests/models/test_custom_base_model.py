from app.models.base import CustomBaseModel


class DummyModel(CustomBaseModel):
    some_field: str
    another_field: int


def test_custom_base_model_alias_and_population() -> None:
    # Populate using snake_case
    obj = DummyModel(some_field="value", another_field=123)
    assert obj.some_field == "value"
    assert obj.another_field == 123

    # Dump using camelCase alias
    dumped = obj.model_dump(by_alias=True)
    assert dumped == {"someField": "value", "anotherField": 123}

    # Populate using camelCase
    obj2 = DummyModel.model_validate({"someField": "value2", "anotherField": 456})
    assert obj2.some_field == "value2"
    assert obj2.another_field == 456
