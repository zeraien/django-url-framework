from unittest import TestCase

from django.test import RequestFactory


class DUFTestCase(TestCase):
    def _request_and_test(self, ControllerKlass, action_name, expected_response=None, status_code=200, **headers):
        with self.subTest(**headers):
            rf =  RequestFactory()
            request = rf.get('/test/json/', **headers)

            response = ControllerKlass(site=None, request=request, helper_class=None, url_params=None)._call_action(action_name)
            self.assertEqual(response.status_code, status_code)
            if expected_response:
                self.assertEqual(response.content.decode('utf8').strip(), expected_response.strip())
            return response
