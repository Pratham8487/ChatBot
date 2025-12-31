from django.db import models

class Lead(models.Model):
    INTENT_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)

    problem = models.TextField(null=True, blank=True)
    intent_level = models.CharField(
        max_length=10,
        choices=INTENT_CHOICES,
        null=True,
        blank=True
    )

    qualified = models.BooleanField(default=False)

    source = models.CharField(
        max_length=100,
        default="website"
    )  # website, linkedin, email, internal_tool

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email or self.name or f"Lead {self.id}"

class Conversation(models.Model):
    STAGE_CHOICES = [
        ("greeting", "Greeting"),
        ("discovery", "Discovery"),
        ("qualification", "Qualification"),
        ("contact", "Contact"),
        ("closing", "Closing"),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True
    )

    session_id = models.CharField(max_length=255, unique=True)
    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default="greeting"
    )

    channel = models.CharField(
        max_length=50,
        default="website"
    )  # website, internal, linkedin, email

    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("bot", "Bot"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )

    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

