import json
import base64
import pytest

from django.conf import settings
settings.configure()

from django.test import RequestFactory
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured

from heartbeat.views import index, details

setattr(settings, 'ROOT_URLCONF', 'heartbeat.urls')


def test_index():
    factory = RequestFactory()
    request = factory.get(reverse('index'))
    response = index(request)
    assert response.status_code == 200


def check(request):
    return {'ping': 'pong'}


class TestDetailsView:

    def setup_method(self, method):
        from heartbeat.settings import HEARTBEAT

        HEARTBEAT.update({
            'checkers': ['tests.test_views'],
            'auth': {
                'username': 'foo',
                'password': 'bar',
                'authorized_ips': ['1.3.3.7'],
            }
        })
        self.heartbeat = HEARTBEAT

        def set_basic_auth():
            credentials = base64.b64encode('{}:{}'.format('foo', 'bar'))
            basic_auth = {'HTTP_AUTHORIZATION': 'Basic {}'.format(credentials)}
            return basic_auth

        self.factory = RequestFactory(**set_basic_auth())

    def test_200OK(self):
        request = self.factory.get(reverse('1337'))
        response = details(request)
        assert response.status_code == 200
        assert response['content-type'] == 'application/json'
        json_response = json.loads(response.content)
        assert json_response['ping'] == 'pong'

    def test_with_invalid_basic_auth_credentials(self):
        self.factory.defaults.pop('HTTP_AUTHORIZATION')
        request = self.factory.get(reverse('1337'))
        response = details(request)
        assert response.status_code == 401

    def test_missing_auth_configuration(self):
        self.heartbeat.pop('auth')
        with pytest.raises(ImproperlyConfigured) as e:
            request = self.factory.get(reverse('1337'))
            details(request)
        msg = 'Missing auth configuration for heartbeat'
        assert msg == str(e.value)

    def test_missing_auth_credentials(self):
        self.heartbeat['auth'] = {'blow': 'fish'}
        with pytest.raises(ImproperlyConfigured) as e:
            request = self.factory.get(reverse('1337'))
            details(request)
        msg = ('Username or password missing from auth configuration '
               'for heartbeat')
        assert msg == str(e.value)

    def test(self):
        self.heartbeat['auth'].update({'username': 'blow', 'password': 'fish'})
        request = self.factory.get(
            reverse('1337'), **{'REMOTE_ADDR': '1.3.3.7'})
        response = details(request)
        assert response.status_code == 200
