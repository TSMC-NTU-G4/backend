from app.models.response import Response


def test_response_with_string_data() -> None:
    response = Response[str](message="Success", data="Hello")
    assert response.message == "Success"
    assert response.data == "Hello"


def test_response_with_dict_data() -> None:
    response = Response[dict](message="Got it", data={"key": "value"})
    assert response.message == "Got it"
    assert response.data["key"] == "value"


def test_response_with_none_data() -> None:
    response = Response[str](message="Empty response")
    assert response.message == "Empty response"
    assert response.data is None


def test_response_serialization() -> None:
    response = Response[int](message="Number", data=42)
    serialized = response.model_dump()
    assert serialized == {"message": "Number", "data": 42}
