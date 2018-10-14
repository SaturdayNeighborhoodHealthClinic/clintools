"""Data models for referral system."""
from django.db import models
from django.core.exceptions import ValidationError

from pttrack.models import (
    ReferralType, ReferralLocation, Note, ContactMethod, CompletableMixin,
    CompleteableManager)
from followup.models import ContactResult, NoAptReason, NoShowReason

# pylint: disable=I0011,E1305

class Referral(Note):
    """A record of a particular patient's referral to a particular center."""

    STATUS_SUCCESSFUL = 'S'
    STATUS_PENDING = 'P'
    STATUS_UNSUCCESSFUL = 'U'

    REFERRAL_STATUSES = (
        (STATUS_SUCCESSFUL, 'Completed'),
        (STATUS_PENDING, 'Not completed'),
        (STATUS_UNSUCCESSFUL, 'Unsuccessful referral'),
    )

    location = models.ManyToManyField(ReferralLocation)
    comments = models.TextField(blank=True)
    status = models.CharField(
        max_length=50, choices=REFERRAL_STATUSES, default=STATUS_PENDING)
    kind = models.ForeignKey(
        ReferralType,
        help_text="The kind of care the patient should recieve at the "
                  "referral location.")

    def __unicode__(self):
        formatted_date = self.written_datetime.strftime("%D")
        return "%s referral on %s" % (self.kind, formatted_date)


class FollowupRequest(Note, CompletableMixin):

    referral = models.ForeignKey(Referral)
    contact_instructions = models.TextField()

    objects = CompleteableManager()

    def class_name(self):
        return self.__class__.__name__


class PatientContact(Note):

    followupRequest = models.ForeignKey(FollowupRequest)
    referral = models.ForeignKey(Referral)

    contact_method = models.ForeignKey(
        ContactMethod,
        null=False,
        blank=False,
        help_text="What was the method of contact?")

    contact_status = models.ForeignKey(
        ContactResult,
        blank=False,
        null=False,
        help_text="Did you make contact with the patient about this referral?")

    PTSHOW_OPTS = [("Yes", "Yes"),
                   ("No", "No"),
                   ("Not yet", "Not yet")]

    has_appointment = models.CharField(
        choices=PTSHOW_OPTS,
        blank=True, max_length=7,
        help_text="Did the patient make an appointment?")

    no_apt_reason = models.ForeignKey(
        NoAptReason,
        blank=True,
        null=True,
        "If the patient didn't make an appointment, why not?")

    appointment_location = models.ManyToManyField(
        ReferralLocation,
        blank=True,
        help_text="Where did the patient make an appointment?")

    pt_showed = models.CharField(
        max_length=7,
        choices=PTSHOW_OPTS,
        blank=True,
        null=True,
        help_text="Did the patient show up to the appointment?")

    no_show_reason = models.ForeignKey(
        NoShowReason,
        blank=True,
        null=True,
        help_text="If the patient didn't go to the appointment, why not?")

    def short_text(self):
        '''Return a short text description of this followup and what happened.
        Used on the patient chart view as the text in the list of followups.'''

        text = ""
        locations = " ,".join(map(str, self.appointment_location.all()))
        if self.pt_showed == "Yes":
            text = "Patient went to appointment at " + locations + "."
        else:
            if self.has_appointment == "Yes":
                text = "Patient made appointment at " + locations + "but has not yet gone."
            else:
                if self.contact_status.patient_reached:
                    text = "Successfully contacted patient but the patient has not made an appointment yet."
                else:
                    text = "Did not successfully contact patient"
        return text
