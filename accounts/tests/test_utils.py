from django.test import SimpleTestCase

from accounts.utils import parse_domain_allowlist


class ParseDomainAllowlistTests(SimpleTestCase):
    def test_single_domain(self) -> None:
        self.assertEqual(parse_domain_allowlist("example.com"), ["example.com"])

    def test_multiple_domains(self) -> None:
        self.assertEqual(
            parse_domain_allowlist("example.com,foo.com"),
            ["example.com", "foo.com"],
        )

    def test_lowercases_domains(self) -> None:
        self.assertEqual(
            parse_domain_allowlist("Example.COM,Foo.Com"),
            ["example.com", "foo.com"],
        )

    def test_strips_whitespace_around_domains(self) -> None:
        self.assertEqual(
            parse_domain_allowlist(" example.com , foo.com "),
            ["example.com", "foo.com"],
        )

    def test_empty_string_returns_empty_list(self) -> None:
        self.assertEqual(parse_domain_allowlist(""), [])

    def test_whitespace_only_string_returns_empty_list(self) -> None:
        self.assertEqual(parse_domain_allowlist("   "), [])

    def test_drops_empty_entries_between_commas(self) -> None:
        self.assertEqual(
            parse_domain_allowlist("example.com,,foo.com"),
            ["example.com", "foo.com"],
        )
