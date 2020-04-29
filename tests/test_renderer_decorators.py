import json
import unittest

from django.http import HttpResponseBadRequest

from django_url_framework.decorators import json_action
from django_url_framework import ActionController
from .duf_test_case import DUFTestCase


class TestRendererDecorator(DUFTestCase):
    def test_default_renderer_template(self):
        action_response = {'data':'foo'}
        class TestJsonDecorator(ActionController):
            @json_action()
            def test_action_dict(self, request):
                return action_response

            @json_action()
            def test_action_http_response(self, request):
                return HttpResponseBadRequest()

        self._request_and_test(TestJsonDecorator, "test_action_dict",
                               expected_response=json.dumps({"data":"foo"}))
        self._request_and_test(TestJsonDecorator, "test_action_http_response",
                                          status_code=400)
