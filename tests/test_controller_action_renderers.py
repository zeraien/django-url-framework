import json
import unittest
from io import BytesIO

import yaml
from django.http import HttpRequest
from django.test import RequestFactory, SimpleTestCase
from django.utils.encoding import force_bytes

from .duf_test_case import DUFTestCase
from django_url_framework.decorators import auto, json_action, yaml_action
from django_url_framework.controller import ActionController

class TestController(DUFTestCase):

    def test_default_renderer_template(self):
        action_response = {'data':'foo'}
        class TestTemplateRendererController(ActionController):
            def test_action(self, request):
                return action_response
        response = self._request_and_test(TestTemplateRendererController, "test_action",
                               expected_response="HTML:{data}".format(**action_response))
        self.assertEqual(response['Content-Type'],"text/html; charset=utf-8")

    def test_template_renderer_adds_request_to_template_context(self):
        action_response = {'data':'foo'}
        class TestTemplateRendererAddsRequestController(ActionController):
            def test_has_request(self, request):
                return action_response
        response = self._request_and_test(TestTemplateRendererAddsRequestController, "test_has_request",
                               expected_response="This template &lt;WSGIRequest: GET &#x27;/test/json/&#x27;&gt;")
        self.assertEqual(response['Content-Type'],"text/html; charset=utf-8")

    def test_auto_json_yaml_str(self):
        expected = {'ab':"C",1:"2",None:False}
        yaml_flow = True

        def _run_test(accept, expect, **kwargs):
            class TestTestController(ActionController):
                yaml_default_flow_style=yaml_flow
                @auto()
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

    def test_auto_decorator_with_params(self):
        expected = {'ab':"C",1:"2",None:False}

        class TestDecoratorWithParamsController(ActionController):
            @auto(yaml_default_flow_style=True)
            def test_action(self, request):
                return expected
        self._request_and_test(TestDecoratorWithParamsController, "test_action",
                               HTTP_ACCEPT="application/yaml",
                               expected_response=yaml.dump(expected,default_flow_style=True))

    def test_json_decorator(self):
        expected = {'ab':"C",1:"2",None:False}

        class TestJSONDecoratorController(ActionController):
            @json_action()
            def test_action(self, request):
                return expected
        self._request_and_test(TestJSONDecoratorController, "test_action", expected_response=json.dumps(expected))


    def test_before_filter_redirect(self):
        returned = {"foo":"bar"}

        class TestPrintController(ActionController):
            def _before_filter(self, request):
                return self._go(to_url="/baz/")

            @json_action()
            def test_action(self, request):
                return returned
        response = self._request_and_test(TestPrintController, "test_action", status_code=302)
        self.assertEqual(response['Location'], "/baz/")

    def test_before_filter_none(self):
        returned = {"foo":"bar"}

        class TestPrintController(ActionController):
            def _before_filter(self, request):
                return None
            @json_action()
            def test_action(self, request):
                return returned
        self._request_and_test(TestPrintController, "test_action", expected_response=json.dumps(returned))

    def test_before_filter_dict(self):
        returned = {"foo":"bar"}

        class TestPrintController(ActionController):
            def _before_filter(self, request):
                return {"add":123}
            @json_action()
            def test_action(self, request):
                return returned
        self._request_and_test(TestPrintController, "test_action", expected_response=json.dumps({"foo":"bar", "add":123}))

    def test_print(self):
        expected = [1,2,3,4,5]

        def _run_test(input, expect, **kwargs):
            class TestPrintController(ActionController):
                def test_action(self, request):
                    return self._print(input)
            self._request_and_test(TestPrintController, "test_action", expected_response=expect)

        _run_test(expected, str(expected))
        _run_test("Bajs", "Bajs")
        _run_test({"a":"b"}, str({"a":"b"}))

    def test_as_yaml(self):
        input = {'ab':"C",1:"2",None:False}

        class TestAsYamlController(ActionController):
            def test_action(self, request):
                return self._as_yaml(input, default_flow_style=True)
        self._request_and_test(TestAsYamlController, "test_action", expected_response=yaml.dump(input, default_flow_style=True))

    def test_as_json(self):
        input = {'ab':"C",1:"2",None:False}

        class TestAsJsonController(ActionController):
            def test_action(self, request):
                return self._as_json(input)
        self._request_and_test(TestAsJsonController, "test_action", expected_response=json.dumps(input))

    def test_redirect_action(self):

        class RedirectController(ActionController):
            @json_action()
            def second_action(self, request):
                return {}
            def redirect(self, request):
                return self._go(to_url="/temporary/")
            def redirect_permanent(self, request):
                return self._go(to_url="/permanent/", permanent=True)

        rf =  RequestFactory()
        request = rf.get('/redirecting/')
        controller = RedirectController(site=None, request=request, helper_class=None, url_params=None)
        with self.subTest('302'):
            response = controller._call_action('redirect')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], "/temporary/")
        with self.subTest('301'):
            response = controller._call_action('redirect_permanent')
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response['Location'], "/permanent/")


    def test_yaml_decorator(self):
        expected = {'ab':"C",1:"2",None:False}

        class TestYamlDecoratorController(ActionController):
            yaml_default_flow_style=True
            @yaml_action()
            def test_action(self, request):
                return expected
        self._request_and_test(TestYamlDecoratorController, "test_action", expected_response=yaml.dump(expected,default_flow_style=True))

    def test_yaml_decorator_with_flow_style(self):
        expected = {'ab':"C",1:"2",None:False}

        class TestYamlWithFlowController(ActionController):
            @yaml_action(default_flow_style=True)
            def test_action(self, request):
                return expected
        self._request_and_test(TestYamlWithFlowController, "test_action", expected_response=yaml.dump(expected,default_flow_style=True))

    def test_yaml_decorator_with_flow_style_false(self):
        input = {'ab':"C",1:"2",None:False}

        class TestYamlDecoWithFalseFlowController(ActionController):
            @yaml_action(default_flow_style=False)
            def test_action(self, request):
                return input
        self._request_and_test(TestYamlDecoWithFalseFlowController, "test_action", expected_response=yaml.dump(input,default_flow_style=False))

    def test_after_filter(self):
        input = {'ab':"C",1:"2",None:False}
        after = {'c':'z'}
        class TestAfterFilterController(ActionController):
            def _after_filter(self, request):
                return after
            @json_action()
            def test_action(self, request):
                return input

        copied = input.copy()
        copied.update(after)

        self._request_and_test(
            TestAfterFilterController,
            "test_action",
            expected_response=json.dumps(copied)
        )

    def test_after_filter_can_access_context(self):
        """
        This verifies that `_after_filter` is run, that it has access to the
        context that was returned by an `action`, and that `_after_filter` can modify
        the context before returning it to the client.

        after_filter takes value `foo` from our dictionary,
        and assigns it to key `bar`. It should also replace the original
        `foo` value with `bazinga`

        :return:
        """
        input = {'foo':"123"}
        class TestAfterFilterContextController(ActionController):
            def _after_filter(self, request):
                after = {
                    'bar': self._template_context['foo'],
                    'foo': 'bazinga'
                }
                return after
            @json_action()
            def test_action(self, request):
                return input
        self._request_and_test(
            TestAfterFilterContextController,
            "test_action",
            expected_response=json.dumps({"foo":'bazinga',"bar":"123"}))


    def test_tuple_response_status_code(self):

        expected = "HAIHAIHAI"
        class TupleController(ActionController):
            @json_action()
            def three_three(self, request):
                return expected, 333
        rf =  RequestFactory()
        request = rf.get('/three_three/')
        controller = TupleController(site=None, request=request, helper_class=None, url_params=None)
        response = controller._call_action('three_three')
        self.assertEqual(response.status_code, 333)
        self.assertEqual(response.content.decode('utf8'), json.dumps(expected))

    def test_as_json_tuple_response_status_code(self):

        expected = "HAIHAIHAI"
        class TupleController(ActionController):
            def three_three(self, request):
                return self._as_json(expected), 333
        self._request_and_test(TupleController, "three_three", json.dumps(expected), 333)

    def test_as_json_param_response_status_code(self):

        expected = "HAIHAIHAI"
        class TupleController(ActionController):
            def three_three(self, request):
                return self._as_json(expected, status_code=333)
        self._request_and_test(TupleController, "three_three", json.dumps(expected), 333)

    def test_param_tuple_status_code(self):

        expected = "HAIHAIHAI"
        class TupleController(ActionController):
            def three_three(self, request):
                return self._print(expected),334
        self._request_and_test(TupleController, "three_three", expected, 334)

    def test_as_json_param_and_tuple_response_status_code(self):

        expected = "HAIHAIHAI"
        class TupleController(ActionController):
            def three_three(self, request):
                return self._as_json(expected, status_code=333), 444
        self._request_and_test(TupleController, "three_three", json.dumps(expected), 333)
