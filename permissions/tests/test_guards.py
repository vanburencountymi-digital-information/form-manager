from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from accounts.tests.factories import UserFactory
from permissions.guards import (
    assert_authenticated_user,
    return_false_if_user_not_authenticated,
)


class ReturnFalseIfUserNotAuthenticatedTests(TestCase):
    def test_calls_func_for_authenticated_user(self) -> None:
        @return_false_if_user_not_authenticated
        def always_true(user: object) -> bool:
            return True

        self.assertTrue(always_true(UserFactory()))

    def test_false_for_anonymous_user_without_calling_func(self) -> None:
        @return_false_if_user_not_authenticated
        def always_true(user: object) -> bool:
            raise AssertionError("func should not be called")

        self.assertFalse(always_true(AnonymousUser()))

    def test_false_for_none_without_calling_func(self) -> None:
        @return_false_if_user_not_authenticated
        def always_true(user: object) -> bool:
            raise AssertionError("func should not be called")

        self.assertFalse(always_true(None))

    def test_finds_user_argument_after_cls(self) -> None:
        class Service:
            @classmethod
            @return_false_if_user_not_authenticated
            def check(cls, user: object) -> bool:
                return True

        self.assertTrue(Service.check(UserFactory()))
        self.assertFalse(Service.check(AnonymousUser()))

    def test_raises_at_decoration_time_if_no_user_parameter(self) -> None:
        with self.assertRaises(TypeError):

            @return_false_if_user_not_authenticated
            def missing_user_param(requesting_user: object) -> bool:
                return True


class AssertAuthenticatedUserTests(TestCase):
    def test_returns_the_user_unchanged_for_a_real_user(self) -> None:
        user = UserFactory()
        self.assertEqual(assert_authenticated_user(user), user)

    def test_raises_for_anonymous_user(self) -> None:
        with self.assertRaises(AssertionError):
            assert_authenticated_user(AnonymousUser())

    def test_raises_for_none(self) -> None:
        with self.assertRaises(AssertionError):
            assert_authenticated_user(None)
