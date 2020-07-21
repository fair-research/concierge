import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_root():
    client = APIClient()
    response = client.get('/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_unauthenticated_api_request():
    client = APIClient()
    response = client.get(reverse('bag-list'))
    assert response.status_code == 401


@pytest.mark.django_db
def test_bag_list(api_cli):
    response = api_cli.get(reverse('bag-list'))
    assert response.status_code == 200
