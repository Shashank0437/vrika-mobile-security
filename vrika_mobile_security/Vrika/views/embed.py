"""Vrika dashboard embed bridge: HMAC token auth from vrika-server."""
import base64
import hashlib
import hmac
import json
import logging
import time

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from vrika_mobile_security.Vrika.security import sanitize_redirect
from vrika_mobile_security.Vrika.views.authorization import (
    MAINTAINER_GROUP,
    VIEWER_GROUP,
)

logger = logging.getLogger(__name__)

ROLE_GROUP_MAP = {
    'maintainer': MAINTAINER_GROUP,
    'viewer': VIEWER_GROUP,
}


def _bridge_secret():
    secret = getattr(settings, 'VRIKA_BRIDGE_SECRET', None)
    if not secret:
        return None
    return secret.encode()


def _parse_token(raw):
    """Return (body_dict, error_message)."""
    if not raw or '.' not in raw:
        return None, 'Malformed token.'
    body_b64, sig_hex = raw.rsplit('.', 1)
    secret = _bridge_secret()
    if not secret:
        logger.error('VRIKA_BRIDGE_SECRET is not configured.')
        return None, 'Embed bridge not configured.'
    expected = hmac.new(secret, body_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig_hex):
        return None, 'Invalid token signature.'
    try:
        padded = body_b64.replace('-', '+').replace('_', '/')
        padded += '=' * (-len(padded) % 4)
        body = json.loads(base64.b64decode(padded))
    except (ValueError, json.JSONDecodeError):
        return None, 'Malformed token body.'
    if not isinstance(body, dict):
        return None, 'Malformed token body.'
    email = body.get('email')
    role = body.get('role')
    exp = body.get('exp')
    nonce = body.get('nonce')
    if (not isinstance(email, str) or not email or len(email) > 254
            or role not in ROLE_GROUP_MAP
            or not isinstance(exp, int) or exp <= int(time.time())
            or not isinstance(nonce, str) or not nonce):
        return None, 'Invalid token body.'
    # ponytail: locmem cache nonce is correct only with a single gunicorn
    # worker (scripts/entrypoint.sh --workers=1); move to a shared cache
    # table if workers ever increase.
    if not cache.add(f'vrika_embed_nonce:{nonce}', 1, 60):
        return None, 'Token already used.'
    return body, None


@require_http_methods(['GET'])
def vrika_embed(request):
    """Provision a session from a signed vrika-server embed token."""
    raw = request.GET.get('token', '')
    redirect_to = sanitize_redirect(request.GET.get('redirect', '/'))
    body, error = _parse_token(raw)
    if error:
        return HttpResponse(error, status=400)
    email = body['email']
    role = ROLE_GROUP_MAP[body['role']]
    try:
        user = User.objects.get(username=email)
        if not user.is_active:
            return HttpResponse('This account is inactive.', status=400)
        user.groups.clear()
        user.groups.add(Group.objects.get(name=role))
    except User.DoesNotExist:
        user = User.objects.create_user(username=email, email=email)
        user.is_staff = False
        user.groups.add(Group.objects.get(name=role))
        user.save()
    login(request, user)
    # redirect() does not prepend FORCE_SCRIPT_NAME for literal paths; the
    # browser would resolve Location: /recent_scans/ outside /mobsf/.
    prefix = settings.SCRIPT_PREFIX
    if prefix:
        prefix = prefix.rstrip('/')
    return redirect(f"{prefix}{redirect_to}")
