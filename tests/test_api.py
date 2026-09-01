from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ask_empty_question():

    response = client.post(
        "/ask",
        json={
            "question": "",
            "top_k": 3
        }
    )

    assert response.status_code in [400, 422]


def test_ask_invalid_top_k():

    response = client.post(
        "/ask",
        json={
            "question": "What is the leave policy?",
            "top_k": 0
        }
    )

    assert response.status_code == 422


def test_ask_negative_top_k():

    response = client.post(
        "/ask",
        json={
            "question": "What is the leave policy?",
            "top_k": -1
        }
    )

    assert response.status_code == 422


def test_ask_missing_question():

    response = client.post(
        "/ask",
        json={
            "top_k": 3
        }
    )

    assert response.status_code == 422