from unittest import TestCase

from django_url_framework.controller import _get_arg_name_and_default
from django_url_framework.controller import get_actions
from django_url_framework import ActionController


class TestGetActions(TestCase):
    def test_get_actions_missing_request_param(self):
        class get_actions_missing_request_paramController(ActionController):
            def _after_filter(self, request):
                return None
            def action1(self):
                return input
        actions = get_actions(get_actions_missing_request_paramController)
        self.assertEqual(actions, {})

    def test_get_actions(self):
        class test_get_actionsController(ActionController):
            def _after_filter(self, request):
                return None
            def export_my_unpaid_hours_to_csv(self, request):
                return {}
            def action2(self, request, id):
                return {}
        actions = get_actions(test_get_actionsController)
        self.assertEqual(actions, {'export_my_unpaid_hours_to_csv':test_get_actionsController.export_my_unpaid_hours_to_csv,
                                   'action2':test_get_actionsController.action2})

    def test_has_defaults_request_has_default(self):
        class test_has_defaults1Controller(ActionController):
            def _after_filter(self, request):
                return None
            def action1(self, request="foo"):
                return {}

        action_func,has_default,dt=_get_arg_name_and_default(test_has_defaults1Controller.action1)
        self.assertEqual(None,action_func)
        self.assertEqual(True, has_default)

    def test_has_no_defaults_request_has_default(self):
        class test_has_no_defaults_request_has_defaultController(ActionController):
            def _after_filter(self, request):
                return None
            def action1(self, request):
                return {}

        action_func,has_default,dt=_get_arg_name_and_default(test_has_no_defaults_request_has_defaultController.action1)
        self.assertEqual(None,action_func)
        self.assertEqual(True,has_default)

    def test_has_defaults3(self):
        class test_has_defaults3Controller(ActionController):
            def _after_filter(self, request):
                return None
            def action2(self, request='bar', id:int="id"):
                return {}

        action_func,has_default,dt=_get_arg_name_and_default(test_has_defaults3Controller.action2)
        self.assertEqual('id',action_func)
        self.assertEqual(True, has_default)
