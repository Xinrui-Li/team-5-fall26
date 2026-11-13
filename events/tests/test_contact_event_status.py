"""Contact requests must not refer to events that are already over."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from events.contact_services import create_contact_request
from events.models import ContactRequest, Event, EventInterest


class ContactEventStatusTests(TestCase):
    """Recheck real event availability, not just a stale status field."""

    @classmethod
    def setUpTestData(cls):
        cls.sender = User.objects.create_user(
            username="expired_sender", email="expired_sender@example.com"
        )
        cls.recipient = User.objects.create_user(
            username="expired_recipient",
            email="expired_recipient@example.com",
            share_profile_with_attendees=True,
        )

    def event_with_interest(self, guid, **fields):
        """Create a source event that both users marked Interested."""
        event = Event.objects.create(
            guid=guid,
            title=fields.pop("title", guid),
            content_hash="e" * 64,
            **fields,
        )
        for user in (self.sender, self.recipient):
            EventInterest.objects.create(event=event, user=user)
        return event

    def test_stale_upcoming_event_that_ended_is_rejected(self):
        """The event's status can lag behind the actual date."""
        event = self.event_with_interest(
            "past-event",
            start_time=timezone.now() - timedelta(days=3),
        )
        self.assertEqual(event.status, Event.Status.UPCOMING)
        result, created = create_contact_request(
            event, self.sender, self.recipient, "Hello"
        )
        self.assertIsNone(result)
        self.assertFalse(created)
        self.assertFalse(ContactRequest.objects.exists())

    def test_cancelled_feed_title_is_rejected(self):
        """The feed marks cancellations in titles, not in status."""
        event = self.event_with_interest(
            "cancelled-title",
            title="CANCELLED Community Walk",
            start_time=timezone.now() + timedelta(days=4),
        )
        result, created = create_contact_request(
            event, self.sender, self.recipient, "Hello"
        )
        self.assertIsNone(result)
        self.assertFalse(created)

    def test_valid_upcoming_event_still_allows_contact(self):
        """Normal contact requests continue to work."""
        event = self.event_with_interest(
            "future-event",
            start_time=timezone.now() + timedelta(days=4),
        )
        result, created = create_contact_request(
            event, self.sender, self.recipient, "Hello"
        )
        self.assertTrue(created)
        self.assertEqual(result.event, event)
