# -*- coding: utf_8 -*-
"""Vrika REST API V 1."""
from base64 import b64encode
from pathlib import Path

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from vrika_mobile_security.Vrika.utils import is_md5
from vrika_mobile_security.Vrika.views.helpers import request_method
from vrika_mobile_security.Vrika.views.api.api_middleware import make_api_response
from vrika_mobile_security.DynamicAnalyzer.views.android import (
    dynamic_analyzer,
    operations,
    report,
    tests_common,
    tests_frida,
)
from vrika_mobile_security.DynamicAnalyzer.views.common import device
from vrika_mobile_security.DynamicAnalyzer.views.common.frida import views as frida


# Dynamic Analyzer APIs
@request_method(['GET'])
@csrf_exempt
def api_get_apps(request):
    """GET - Get Apps for dynamic analysis API."""
    resp = dynamic_analyzer.android_dynamic_analysis(request, True)
    if 'error' in resp:
        return make_api_response(resp, 500)
    return make_api_response(resp, 200)


@request_method(['POST'])
@csrf_exempt
def api_start_analysis(request):
    """POST - Start Dynamic Analysis."""
    if 'hash' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = dynamic_analyzer.dynamic_analyzer(
        request,
        request.POST['hash'],
        True)
    if 'error' in resp:
        return make_api_response(resp, 500)
    return make_api_response(resp, 200)


@request_method(['POST'])
@csrf_exempt
def api_logcat(request):
    """POST - Get Logcat HTTP Streaming API."""
    if 'package' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    lcat = dynamic_analyzer.logcat(request, True)
    if isinstance(lcat, dict):
        if 'error' in lcat:
            return make_api_response(
                lcat, 500)
    return lcat


# Android Operation APIs
@request_method(['POST'])
@csrf_exempt
def api_mobsfy(request):
    """POST - vrika-fy API."""
    if 'identifier' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = operations.mobsfy(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_screenshot(request):
    """POST - Screenshot API."""
    if 'hash' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = operations.take_screenshot(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_list_screenshots(request):
    """POST - Captured screenshots as data URLs (newest first)."""
    checksum = request.POST.get('hash', '')
    if not is_md5(checksum):
        return make_api_response({'error': 'Invalid Hash'}, 422)
    screen_dir = Path(settings.UPLD_DIR) / checksum / 'screenshots-apk'
    shots = []
    if screen_dir.is_dir():
        files = sorted(
            (f for f in screen_dir.glob('*.png')
             if f.is_file() and not f.is_symlink()),
            key=lambda f: f.stat().st_mtime,
            reverse=True)
        for f in files[:30]:
            shots.append({
                'name': f.name,
                'data': 'data:image/png;base64,' + b64encode(
                    f.read_bytes()).decode()})
    return make_api_response({'screenshots': shots}, 200)


@request_method(['POST'])
@csrf_exempt
def api_adb_execute(request):
    """POST - ADB execute API."""
    if 'cmd' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = operations.execute_adb(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_root_ca(request):
    """POST - Vrika CA actions API."""
    if 'action' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = operations.vrika_ca(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_global_proxy(request):
    """POST - Vrika Global Proxy API."""
    if 'action' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = operations.global_proxy(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


# Android Dynamic Tests APIs
@request_method(['POST'])
@csrf_exempt
def api_act_tester(request):
    """POST - Activity Tester."""
    params = {'test', 'hash'}
    if set(request.POST) < params:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = tests_common.activity_tester(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_start_activity(request):
    """POST - Start Activity."""
    params = {'activity', 'hash'}
    if set(request.POST) < params:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = tests_common.start_activity(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_tls_tester(request):
    """POST - TLS/SSL Security Tester."""
    if 'hash' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = tests_common.tls_tests(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_stop_analysis(request):
    """POST - Stop Dynamic Analysis."""
    if 'hash' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    checksum = request.POST['hash']
    identifier = tests_common.get_analysis_identifier(
        request, checksum)
    logs = tests_common.collect_logs(
        request, True, identifier=identifier)
    if logs['status'] != 'ok':
        return make_api_response(logs, 500)
    resp = tests_common.download_data(
        request, True, identifier=identifier)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


# Android Frida APIs
@request_method(['POST'])
@csrf_exempt
def api_instrument(request):
    """POST - Frida Instrument."""
    params = {
        'hash',
        'default_hooks',
        'auxiliary_hooks',
        'frida_code'}
    if set(request.POST) < params:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = tests_frida.instrument(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_api_monitor(request):
    """POST - Frida API Monitor."""
    if 'hash' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = tests_frida.live_api(request, True)
    # live_api can be json or html
    if resp.get('data'):
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_frida_logs(request):
    """POST - Frida Logs."""
    if 'hash' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = frida.frida_logs(request, True)
    # frida logs can be json or html
    if resp.get('data') or resp.get('message'):
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_list_frida_scripts(request):
    """POST - List Frida Scripts."""
    if 'device' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = frida.list_frida_scripts(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_get_script_content(request):
    """POST - Frida Get Script."""
    if not request.POST.getlist('scripts[]'):
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    if 'device' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = frida.get_script_content(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


@request_method(['POST'])
@csrf_exempt
def api_get_dependencies(request):
    """POST - Frida Get Runtime Dependencies."""
    if 'hash' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = tests_frida.get_runtime_dependencies(request, True)
    if resp['status'] == 'ok':
        return make_api_response(resp, 200)
    return make_api_response(resp, 500)


# Report APIs
@request_method(['POST'])
@csrf_exempt
def api_dynamic_report(request):
    """POST - Dynamic Analysis report."""
    if 'hash' not in request.POST:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = report.view_report(
        request,
        request.POST['hash'],
        True)
    if 'error' in resp:
        return make_api_response(resp, 500)
    return make_api_response(resp, 200)


@request_method(['POST'])
@csrf_exempt
def api_dynamic_view_file(request):
    """POST - Dynamic Analysis report."""
    params = {'hash', 'file', 'type'}
    if set(request.POST) < params:
        return make_api_response(
            {'error': 'Missing Parameters'}, 422)
    resp = device.view_file(request, True)
    if 'error' in resp:
        return make_api_response(resp, 500)
    return make_api_response(resp, 200)
