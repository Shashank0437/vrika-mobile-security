"""Tests for the Vrika dashboard embed bridge."""
import base64
import hashlib
import hmac as hmac_mod
import json
import time

from django.test import TestCase, override_settings
from django.conf import settings
from django.contrib.auth.models import Group, User

from vrika_mobile_security.Vrika.views import embed


import secrets


def _mint(email='test@example.com', role='maintainer', exp=None,
          nonce=None, secret='test-secret'):
    body = json.dumps({
        'email': email,
        'role': role,
        'exp': exp if exp is not None else int(time.time()) + 60,
        'nonce': nonce if nonce is not None else secrets.token_urlsafe(16),
    }).encode()
    b64 = base64.urlsafe_b64encode(body).rstrip(b'=').decode()
    sig = hmac_mod.new(
        secret.encode(), b64.encode(), hashlib.sha256).hexdigest()
    return f'{b64}.{sig}'


@override_settings(VRIKA_BRIDGE_SECRET='test-secret')
class VrikaEmbedViewTests(TestCase):
    databases = {'default'}

    def setUp(self):
        self.user = User.objects.create_user(
            username='test@example.com', email='test@example.com')
        self.user.set_unusable_password()
        self.user.save()
        Group.objects.get_or_create(name='Maintainer')
        Group.objects.get_or_create(name='Viewer')

    def expected(self, path):
        prefix = getattr(settings, 'SCRIPT_PREFIX', '')
        return f"{prefix.rstrip('/') if prefix else ''}{path}"

    def test_valid_token_302_auth_group(self):
        token = _mint()
        resp = self.client.get(
            '/vrika-embed/', {'token': token, 'redirect': '/'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], self.expected('/'))
        self.assertEqual(
            int(self.client.session['_auth_user_id']), self.user.id)
        self.assertTrue(self.user.groups.filter(name='Maintainer').exists())

    def test_tampered_sig_400(self):
        token = _mint()
        tampered = token[:-1] + ('0' if token[-1] != '0' else '1')
        resp = self.client.get('/vrika-embed/', {'token': tampered})
        self.assertEqual(resp.status_code, 400)

    def test_replayed_nonce_400(self):
        token = _mint()
        boot = self.client.get('/vrika-embed/', {'token': token})
        self.assertEqual(boot.status_code, 302)
        self.client.logout()
        resp = self.client.get('/vrika-embed/', {'token': token})
        self.assertEqual(resp.status_code, 400)

    def test_open_redirect_blocked(self):
        token = _mint()
        resp = self.client.get(
            '/vrika-embed/', {'token': token, 'redirect': '//evil.com'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], self.expected('/'))

    def test_expired_400(self):
        token = _mint(exp=int(time.time()) - 10)
        resp = self.client.get('/vrika-embed/', {'token': token})
        self.assertEqual(resp.status_code, 400)

    def test_no_token_400(self):
        resp = self.client.get('/vrika-embed/')
        self.assertEqual(resp.status_code, 400)

    def test_inactive_account_400(self):
        self.user.is_active = False
        self.user.save()
        token = _mint()
        resp = self.client.get('/vrika-embed/', {'token': token})
        self.assertEqual(resp.status_code, 400)

    def test_is_staff_never_granted(self):
        token = _mint()
        self.client.get('/vrika-embed/', {'token': token})
        self.assertFalse(User.objects.get(
            username='test@example.com').is_staff)

    def test_created_user_viewer_group(self):
        User.objects.filter(username='new@example.com').delete()
        token = _mint(email='new@example.com', role='viewer')
        resp = self.client.get('/vrika-embed/', {'token': token})
        self.assertEqual(resp.status_code, 302)
        created = User.objects.filter(username='new@example.com').exists()
        self.assertTrue(created)
        self.assertTrue(User.objects.get(
            username='new@example.com').groups.filter(name='Viewer').exists())
