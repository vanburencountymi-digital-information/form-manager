import sys
import threading

from django.core.mail.backends.base import BaseEmailBackend


class ReadableConsoleEmailBackend(BaseEmailBackend):
    """Like Django's built-in console backend, but prints the decoded
    plain-text body instead of the raw MIME source. The raw source
    quoted-printable-wraps long lines (e.g. password reset links) with a
    soft break, which corrupts the link if you copy just the visible line
    during manual testing."""

    def __init__(self, *args, **kwargs):
        self.stream = kwargs.pop("stream", sys.stdout)
        self._lock = threading.RLock()
        super().__init__(*args, **kwargs)

    def write_message(self, message):
        self.stream.write(f"Subject: {message.subject}\n")
        self.stream.write(f"From: {message.from_email}\n")
        self.stream.write(f"To: {', '.join(message.to)}\n\n")
        self.stream.write(message.body)
        self.stream.write("\n")
        self.stream.write("-" * 79)
        self.stream.write("\n")

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        msg_count = 0
        with self._lock:
            for message in email_messages:
                self.write_message(message)
                self.stream.flush()
                msg_count += 1
        return msg_count
