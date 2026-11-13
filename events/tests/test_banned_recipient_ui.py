"""Show clear contact restrictions when the recipient is banned."""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, UserBan
from events.models import ContactRequest, Event, EventInterest, Notification


class BannedRecipientContactTests(TestCase):
    """The page and POST handlers must agree about recipient bans."""

    @classmethod
    def setUpTestData(cls):
        cls.sender = User.objects.create_user(
            username="recipient_ban_sender",
            email="recipient_ban_sender@example.com",
            share_profile_with_attendees=True,
        )
        cls.recipient = User.objects.create_user(
            username="recipient_ban_target",
            email="recipient_ban_target@example.com",
            share_profile_with_attendees=True,
        )
        cls.event = Event.objects.create(
            guid="ban-target-event",
            title="Community Walk",
            content_hash="a" * 64,
        )
        for user in (cls.sender, cls.recipient):
            EventInterest.objects.create(event=cls.event, user=user)

    def setUp(self):
        """Sign in as the unbanned sender and ban the recipient."""
        self.client.force_login(self.sender)
        self.ban = UserBan.objects.create(
            user=self.recipient,
            issued_by=self.sender,
            offense_number=1,
            expires_at=timezone.now() + timedelta(days=4),
        )

    def test_event_page_hides_contact_form_for_banned_recipient(self):
        """The event attendee card explains why requests are unavailable."""
        response = self.client.get(reverse("event_detail", args=[self.event.pk]))
        self.assertContains(
            response, "Contact requests are currently unavailable for this member."
        )
        self.assertNotContains(
            response,
            reverse(
                "send_contact_request", args=[self.event.pk, self.recipient.pk]
            ),
        )

    def test_event_post_rejects_banned_recipient_with_feedback(self):
        """A direct submission must not fail silently."""
        response = self.client.post(
            reverse(
                "send_contact_request", args=[self.event.pk, self.recipient.pk]
            ),
            {"message": "Hi"},
            follow=True,
        )
        self.assertContains(response, "Contact requests are currently unavailable")
        self.assertFalse(ContactRequest.objects.exists())
        self.assertFalse(Notification.objects.exists())

    def test_profile_contact_page_disables_form_and_explains_ban(self):
        """Do not claim the users have no shared event."""
        url = reverse("message_user", args=[self.recipient.pk])
        response = self.client.get(url)
        self.assertContains(response, "Contact requests are currently unavailable")
        self.assertNotContains(response, 'class="message-form"')
        self.assertNotContains(response, "You need to share an upcoming event")

        post = self.client.post(
            url, {"event": self.event.pk, "message": "Hi"}
        )
        self.assertContains(post, "Contact requests are currently unavailable")
        self.assertFalse(ContactRequest.objects.exists())
        self.assertFalse(Notification.objects.exists())

    def test_lifted_ban_restores_both_contact_forms(self):
        """An old ban must not keep the recipient unavailable forever."""
        self.ban.lifted_at = timezone.now()
        self.ban.save(update_fields=["lifted_at"])
        response = self.client.get(reverse("event_detail", args=[self.event.pk]))
        self.assertContains(
            response,
            reverse(
                "send_contact_request", args=[self.event.pk, self.recipient.pk]
            ),
        )
        page = self.client.get(reverse("message_user", args=[self.recipient.pk]))
        self.assertContains(page, "Send Contact Request")
        self.assertNotContains(
            page, "Contact requests are currently unavailable for this member."
        )
