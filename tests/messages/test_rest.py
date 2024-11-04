from aact.messages import get_rest_request_class, get_rest_response_class, Text


def test_get_rest_request_class() -> None:
    request_class = get_rest_request_class(Text)

    assert request_class.__name__ == "RestRequest[Text]"
    assert request_class.__annotations__["data"] == Text | None

    response_class = get_rest_response_class(Text)

    assert response_class.__name__ == "RestResponse[Text]"
    assert response_class.__annotations__["data"] == Text | None
