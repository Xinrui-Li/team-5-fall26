"""Tests for the restyled log-in and sign-up pages."""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .test_google_sso import GOOGLE_TEST_PROVIDERS


class AuthPageStyleTests(TestCase):
    """Both pages use the site design and Google's branded button."""

    def test_pages_load_site_styles(self):
        """Log-in and sign-up load the design tokens and auth stylesheet."""
        for name in ("login", "register"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, 'class="auth-page"')
                self.assertContains(response, "events/search.css")
                self.assertContains(response, "accounts/auth.css")
                self.assertContains(response, 'class="auth-form"')
                self.assertContains(response, 'class="button primary"')

    def test_login_links_to_reset_and_sign_up(self):
        """The log-in page links to password reset and sign-up."""
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("password_reset"))
        self.assertContains(response, reverse("register"))
        self.assertContains(response, 'autocomplete="current-password"')

    @override_settings(
        GOOGLE_OAUTH_ENABLED=True, SOCIALACCOUNT_PROVIDERS=GOOGLE_TEST_PROVIDERS
    )
    def test_google_button_follows_branding(self):
        """The Google button uses the standard logo and approved labels."""
        labels = {"login": "Sign in with Google", "register": "Sign up with Google"}
        for name, label in labels.items():
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, 'class="gsi-button"')
                self.assertContains(response, f"<span>{label}</span>")
                for colour in ("#EA4335", "#4285F4", "#FBBC05", "#34A853"):
                    self.assertContains(response, colour)


class AuthPageIntegrationTests(TestCase):
    """Signing up and logging in still work through the restyled pages."""

    def test_sign_up_then_log_in(self):
        """A visitor signs up, logs out and logs back in."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newbie",
                "email": "newbie@example.com",
                "display_name": "Newbie",
                "password1": "a-Strong-pass-123",
                "password2": "a-Strong-pass-123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="newbie").exists())
        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {"username": "newbie", "password": "a-Strong-pass-123"},
            follow=True,
        )
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertContains(response, 'class="topbar site-header"')
