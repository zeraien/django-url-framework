from unittest import TestCase

from django_url_framework.controller import get_controller_name


class TestNames(TestCase):

    def test_without_inflection_TestController(self):
        class TestController(object): pass
        self.assertEqual(get_controller_name(TestController), "test")

    def test_without_inflection_HTTPResponseCodeController(self):
        class HTTPResponseCodeController(object): pass
        self.assertEqual(get_controller_name(HTTPResponseCodeController), "httpresponse_code")

    def test_without_inflection_IDController(self):
        class IDController(object): pass
        self.assertEqual(get_controller_name(IDController), "id")

    def test_without_inflection_IDBarController(self):
        class IDBarController(object): pass
        self.assertEqual(get_controller_name(IDBarController), "idbar")

    def test_with_inflection_IDBarController(self):
        class IDBarController(object):
            use_inflection_library = True
        self.assertEqual(get_controller_name(IDBarController), "id_bar")

    def test_with_inflection_HTTPResponseCodeController(self):
        class HTTPResponseCodeController(object):
            use_inflection_library = True
        self.assertEqual(get_controller_name(HTTPResponseCodeController), "http_response_code")
