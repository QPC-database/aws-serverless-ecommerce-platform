import json
import uuid
import requests
import requests_mock
import pytest
from fixtures import apigateway_event, context, lambda_module # pylint: disable=import-error


lambda_module = pytest.fixture(scope="module", params=[{
    "function_dir": "validate",
    "module_name": "main",
    "environ": {
        "ENVIRONMENT": "test",
        "3P_API_URL": "mock://3P_API_URL",
        "POWERTOOLS_TRACE_DISABLED": "true"
    }
}])(lambda_module)
context = pytest.fixture(context)


@pytest.fixture
def payment_token():
    return str(uuid.uuid4())


@pytest.fixture
def amount():
    return 3000


def test_validate_payment_token(lambda_module, payment_token, amount):
    """
    Test validate_payment_token()
    """

    url = "mock://3P_API_URL/check"

    with requests_mock.Mocker() as m:
        m.post(url, text=json.dumps({"ok": True}))
        ok = lambda_module.validate_payment_token(payment_token, amount)

    assert m.called
    assert m.call_count == 1
    assert m.request_history[0].method == "POST"
    assert m.request_history[0].url == url
    assert ok == True


def test_validate_payment_false(lambda_module, payment_token, amount):
    """
    Test validate_payment_token() with a not ok result
    """

    url = "mock://3P_API_URL/check"

    with requests_mock.Mocker() as m:
        m.post(url, text=json.dumps({"ok": False}))
        ok = lambda_module.validate_payment_token(payment_token, amount)

    assert m.called
    assert m.call_count == 1
    assert m.request_history[0].method == "POST"
    assert m.request_history[0].url == url
    assert ok == False


def test_validate_payment_fault(lambda_module, payment_token, amount):
    """
    Test validate_payment_token() with a faulty result
    """

    url = "mock://3P_API_URL/check"

    with requests_mock.Mocker() as m:
        m.post(url, text=json.dumps({"message": "Something went wrong"}))
        ok = lambda_module.validate_payment_token(payment_token, amount)

    assert m.called
    assert m.call_count == 1
    assert m.request_history[0].method == "POST"
    assert m.request_history[0].url == url
    assert ok == False


def test_handler(monkeypatch, lambda_module, context, apigateway_event, payment_token, amount):
    """
    Test handler()
    """

    def validate_payment_token(pt: str, a: int) -> bool:
        assert pt == payment_token
        assert a == amount
        return True

    monkeypatch.setattr(lambda_module, "validate_payment_token", validate_payment_token)

    event = apigateway_event(
        iam="USER_ARN",
        body=json.dumps({
            "paymentToken": payment_token,
            "amount": amount
        })
    )

    response = lambda_module.handler(event, context)

    assert response["statusCode"] == 200
    assert "body" in response
    body = json.loads(response["body"])
    assert "ok" in body
    assert body["ok"] == True


def test_handler_no_iam(monkeypatch, lambda_module, context, apigateway_event, payment_token, amount):
    """
    Test handler() without IAM
    """

    def validate_payment_token(payment_token: str, amount: int) -> bool:
        # This should never be called
        assert False
        return True

    monkeypatch.setattr(lambda_module, "validate_payment_token", validate_payment_token)

    event = apigateway_event(
        body=json.dumps({
            "paymentToken": payment_token,
            "amount": amount
        })
    )

    response = lambda_module.handler(event, context)

    assert response["statusCode"] == 401
    assert "body" in response
    body = json.loads(response["body"])
    assert "ok" not in body
    assert "message" in body
    assert isinstance(body["message"], str)


def test_handler_wrong_body(monkeypatch, lambda_module, context, apigateway_event, payment_token, amount):
    """
    Test handler() with a faulty body
    """

    def validate_payment_token(payment_token: str, amount: int) -> bool:
        # This should never be called
        assert False
        return True

    monkeypatch.setattr(lambda_module, "validate_payment_token", validate_payment_token)

    event = apigateway_event(
        iam="USER_ARN",
        body=json.dumps({
            "paymentToken": payment_token,
            "amount": amount
        })+"{"
    )

    response = lambda_module.handler(event, context)

    assert response["statusCode"] == 400
    assert "body" in response
    body = json.loads(response["body"])
    assert "ok" not in body
    assert "message" in body
    assert isinstance(body["message"], str)
    assert "JSON" in body["message"]


def test_handler_missing_payment_token(monkeypatch, lambda_module, context, apigateway_event, payment_token, amount):
    """
    Test handler() with a missing paymentToken
    """

    def validate_payment_token(payment_token: str, amount: int) -> bool:
        # This should never be called
        assert False
        return True

    monkeypatch.setattr(lambda_module, "validate_payment_token", validate_payment_token)

    event = apigateway_event(
        iam="USER_ARN",
        body=json.dumps({
            "amount": amount
        })
    )

    response = lambda_module.handler(event, context)

    assert response["statusCode"] == 400
    assert "body" in response
    body = json.loads(response["body"])
    assert "ok" not in body
    assert "message" in body
    assert isinstance(body["message"], str)
    assert "paymentToken" in body["message"]


def test_handler_missing_amount(monkeypatch, lambda_module, context, apigateway_event, payment_token, amount):
    """
    Test handler() with a missing amount
    """

    def validate_payment_token(payment_token: str, amount: int) -> bool:
        # This should never be called
        assert False
        return True

    monkeypatch.setattr(lambda_module, "validate_payment_token", validate_payment_token)

    event = apigateway_event(
        iam="USER_ARN",
        body=json.dumps({
            "paymentToken": payment_token,
        })
    )

    response = lambda_module.handler(event, context)

    assert response["statusCode"] == 400
    assert "body" in response
    body = json.loads(response["body"])
    assert "ok" not in body
    assert "message" in body
    assert isinstance(body["message"], str)
    assert "amount" in body["message"]