import json
import unittest
from io import BytesIO

import yaml
from django.conf import settings
from django.http import HttpRequest
from django.test import RequestFactory, SimpleTestCase
from django.utils.encoding import force_bytes
from django_url_framework.decorators import auto, json_action, yaml_action
from django_url_framework.controller import ActionController
settings.configure()

class TestController(unittest.TestCase):

    def _request_and_test(self, ControllerKlass, action_name, expected_response, **headers):
        with self.subTest(**headers):
            rf =  RequestFactory()
            request = rf.get('/test/json/', **headers)

            response = ControllerKlass(site=None, request=request, helper_class=None, url_params=None)._call_action(action_name)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.content.decode('utf8').strip(), expected_response.strip())


    def test_auto_json_yaml_str(self):
        expected = {'ab':"C",1:"2",None:False}
        yaml_flow = True

        def _run_test(accept, expect, **kwargs):
            class TestTestController(ActionController):
                yaml_default_flow_style=yaml_flow
                @auto
                def test_action(self, request):
                    return expected
            self._request_and_test(TestTestController, "test_action", expected_response=expect, HTTP_ACCEPT=accept)

        _run_test("application/json", json.dumps(expected))
        _run_test("application/yaml", yaml.dump(expected, default_flow_style=yaml_flow).strip())
        yaml_flow = False
        _run_test("application/yaml", yaml.dump(expected, default_flow_style=False), flow_style=yaml_flow)

        _run_test("application/yaml, application/json", yaml.dump(expected, default_flow_style=False), flow_style=yaml_flow)
        _run_test(["application/yaml","application/json"], yaml.dump(expected, default_flow_style=False), flow_style=yaml_flow)
        _run_test("application/json, application/yaml", json.dumps(expected))

        _run_test("text/plain", "{None: False, 1: '2', 'ab': 'C'}")

    def test_json_decorator(self):
        expected = {'ab':"C",1:"2",None:False}

        def _run_test(expect, **kwargs):
            class TestTestController(ActionController):
                @json_action
                def test_action(self, request):
                    return expected
            self._request_and_test(TestTestController, "test_action", expected_response=expect)

        _run_test(json.dumps(expected))

    def test_yaml_decorator(self):
        expected = {'ab':"C",1:"2",None:False}

        def _run_test(expect, **kwargs):
            class TestTestController(ActionController):
                yaml_default_flow_style=True
                @yaml_action
                def test_action(self, request):
                    return expected
            self._request_and_test(TestTestController, "test_action", expected_response=expect)

        _run_test(yaml.dump(expected,default_flow_style=True))

if __name__ == '__main__':
    unittest.main()
