from __future__ import unicode_literals
import json
import random
import string
from decimal import *
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.contrib.sites.models import Site

def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]

# Lookup and supporting tables.
class LookupTable(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
      return self.name

    class Meta:
        abstract = True

class HoldType(LookupTable):
    pass

class ShirtSizes(LookupTable):
    class Meta:
        verbose_name_plural = "Shirt sizes"

class IntegerRangeField(models.IntegerField):
    """
    Integer field which enforces a set minimum or maximum value.
    """
    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)
    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(IntegerRangeField, self).formfield(**defaults)

class Profile(models.Model):
    """
    Extended fields attached to the Django user model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    PIN = models.CharField("PIN", max_length=128, null=True, blank=True)

class SiteOptions(models.Model):
    """
    Extended fields of Django's sites framework.
    Sitewide defaults and multi-tenant options can be defined here.
    """
    class Meta:
        verbose_name = "Site option"
        verbose_name_plural = "Site options"

    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    theme = models.CharField(max_length=256, default="default",
        help_text="Filename (without extension) for site theme CSS")

class Discount(models.Model):
    codeName = models.CharField(max_length=100, verbose_name="Discount code")
    percentOff = models.IntegerField(
        null=True,
        verbose_name="Percent off",
        help_text="Enter 0 if specifying an amount to take off")
    amountOff = models.DecimalField(
        max_digits=6, decimal_places=2, null=True,
        verbose_name="Amount off",
        help_text="Enter 0 if specifying a percentage to take off")
    startDate = models.DateTimeField(verbose_name="Start date")
    endDate = models.DateTimeField(verbose_name="End date")
    notes = models.TextField(blank=True)
    oneTime = models.BooleanField(default=False, verbose_name="One-time use")
    used = models.IntegerField(default=0)
    reason = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.codeName

    def isValid(self):
        now = timezone.now()
        if self.startDate > now or self.endDate < now:
            return False
        if self.oneTime and self.used > 0:
            return False
        return True

def content_file_name(instance, filename):
    return '/'.join(['priceleveloption',str(instance.pk),filename])

class PriceLevelOption(models.Model):
    INT = 'int'
    BOOL = 'bool'
    STRING = 'string'
    PLAINTEXT = 'plaintext'    #What does this do, exactly?
    SHIRTSIZES = 'ShirtSizes'
    TYPE_CHOICES = (
        (BOOL, 'Checkbox'),
        (INT, 'Quantity'),
        (STRING, 'Text'),
        (PLAINTEXT, 'Label'),
        (SHIRTSIZES, 'Shirt size'),
    )

    optionName = models.CharField(max_length=200, verbose_name="Option name")
    optionPrice = models.DecimalField(max_digits=6, decimal_places=2,
        verbose_name="Price")
    optionExtraType = models.CharField(max_length=100, blank=True,
        choices=TYPE_CHOICES, default=BOOL,
        verbose_name="Type",
        help_text="Form type to render")
    optionExtraType2 = models.CharField(max_length=100, blank=True,
        choices=TYPE_CHOICES, default='',
        verbose_name="Type 2",
        help_text="(Unused)")
    optionExtraType3 = models.CharField(max_length=100, blank=True,
        choices=TYPE_CHOICES, default='',
        verbose_name="Type 3",
        help_text="(Unused)")
    optionImage = models.ImageField(upload_to=content_file_name,
        blank=True, null=True,
        verbose_name="Image")
    required = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    rank = models.IntegerField(default=0,
        help_text="Numerical rank for ordering items in form (ascending)")
    description = models.TextField(blank=True,
        help_text="HTML allowed")

    class Meta:
        verbose_name = "Price level option"
        verbose_name_plural = "Price level options (merchandise)"

    def __str__(self):
        return '{0} (${1})'.format(self.optionName, self.optionPrice)

    def getList(self):
        if self.optionExtraType in ["int", "bool", "string"]:
            return []
        elif self.optionExtraType == "ShirtSizes":
            return [{'name':s.name, 'id':s.id} for s in ShirtSizes.objects.all()]
        else:
            return []

    def getOptionImage(self):
        if self.optionImage is None:
            return None
        else:
            try:
                return self.optionImage.url
            except ValueError:
                return None

class PriceLevel(models.Model):
    name = models.CharField(max_length=100)
    priceLevelOptions = models.ManyToManyField(PriceLevelOption, blank=True,
        verbose_name="Level options",
        help_text="Select options or merchandise available as an add-on for this level")
    description = models.TextField()
    basePrice = models.DecimalField(max_digits=6, decimal_places=2,
        verbose_name="Base price")
    startDate = models.DateTimeField(verbose_name="Start date")
    endDate = models.DateTimeField(verbose_name="End date")
    public = models.BooleanField(default=False,
        help_text="If unchecked, level is only available for the on-site form.")
    minAge = IntegerRangeField(min_value=0, default=13,
        verbose_name="Minimum age required",
        help_text="Attendee must be this old by first day of event to select this level")
    maxAge = IntegerRangeField(min_value=0,
        blank=True, null=True,
        verbose_name="Maximum age",
        help_text="Hide this level from anyone over this age by the first day of the event. (Blank to disable).")
    notes = models.TextField(blank=True)
    group = models.TextField(blank=True,
		help_text="'vip' is the only group we know about right now, shown in that report.")
    emailVIP = models.BooleanField(default=False,
        verbose_name="Email VIP notifications",
        help_text="Send an email notification to the below address(es) when anyone registers at this level.")
    emailVIPEmails = models.CharField(max_length=400, blank=True, default='',
        verbose_name="VIP notification emails",
        help_text="Comma-separated list of emails to send a notification to.")
    isMinor = models.BooleanField(default=False, help_text="(Legacy)")

    def __str__(self):
        return self.name

class Charity(LookupTable):
    url = models.CharField(max_length=500,
        verbose_name="URL",
        help_text="Charity link")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Charities"

class Event(LookupTable):
    dealerRegStart = models.DateTimeField(verbose_name="Dealer Registration Start",
        help_text="Start date and time for dealer applications")
    dealerRegEnd = models.DateTimeField(verbose_name="Dealer Registration End")
    staffRegStart = models.DateTimeField(verbose_name="Staff Registration Start",
        help_text="(Not currently enforced)")
    staffRegEnd = models.DateTimeField(verbose_name="Staff Registration End")
    attendeeRegStart = models.DateTimeField(verbose_name="Attendee Registration Start",
        help_text="Start time for standard /registration form")
    attendeeRegEnd = models.DateTimeField(verbose_name="Attendee Registration End")
    onlineRegStart = models.DateTimeField("On-site Registration Start",
        help_text="Start time for /registration/onsite form")
    onlineRegEnd = models.DateTimeField(verbose_name="On-site Registration End")
    eventStart = models.DateField(verbose_name="Event Start Date")
    eventEnd = models.DateField(verbose_name="Event End Date")
    default = models.BooleanField(default=False, verbose_name="Default",
        help_text="The default event will be used as the basis for all current event configuration")
    newStaffDiscount = models.ForeignKey(Discount, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='newStaffEvent',
        verbose_name="New Staff Discount",
        help_text="Apply a discount for new staff registrations")
    staffDiscount = models.ForeignKey(Discount, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="staffEvent",
        verbose_name="Staff Discount",
        help_text="Apply a discount for any staff registrations")
    dealerDiscount = models.ForeignKey(Discount, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="dealerEvent",
        verbose_name="Dealer Discount",
        help_text="Apply a discount for any dealer registrations")
    allowOnlineMinorReg = models.BooleanField(default=False,
        verbose_name="Allow online minor registration",
        help_text="Allow registration for anyone age 13 and older online. "
        "Otherwise, registration is restricted to those {0} or older.".format(settings.APIS_LEGAL_AGE))
    collectAddress = models.BooleanField(default=True,
        verbose_name="Collect Address",
        help_text="Disable to skip collecting a mailing address for each "
        "attendee.")
    collectBillingAddress = models.BooleanField(default=True,
        verbose_name="Collect Billing Address",
        help_text="Disable to skip collecting a billing address for each "
        "order. Note that a billing address and buyer email is required "
        "to qualify for Square's Chargeback protection.")
    registrationEmail = models.CharField(max_length=200,
        verbose_name="Registration Email",
        help_text="Email to display on error messages for attendee registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL)
    staffEmail = models.CharField(max_length=200,
        verbose_name="Staff Email",
        help_text="Email to display on error messages for staff registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL)
    dealerEmail = models.CharField(max_length=200,
        verbose_name="Dealer Email",
        help_text="Email to display on error messages for dealer registration",
        blank=True,
        default=settings.APIS_DEFAULT_EMAIL)
    badgeTheme = models.CharField(max_length=200,
        verbose_name="Badge Theme",
        help_text="Name of badge theme to use for printing",
        blank=False,
        default='apis')
    codeOfConduct = models.CharField(max_length=500,
        verbose_name="Code of Conduct URL",
        help_text="Link to code of conduct agreement",
        blank=True,
        default='/code-of-conduct')

    ATTENDEE_COC = """I agree to abide by the {{ event.name }} <a href="{{ event.codeOfConduct }}" target="_blank">Code of Conduct</a>"""
    attendeeCodeOfConduct = models.TextField(
        default=ATTENDEE_COC,
        verbose_name="Attendee agreement text",
        help_text="HTML template to show for attendee agreement checkbox.")
    dealerCodeOfConduct = models.TextField(
        default=ATTENDEE_COC,
        verbose_name="Dealer agreement text",
        help_text="HTML template to show for dealer agreement checkbox.")
    staffCodeOfConduct = models.TextField(
        default=ATTENDEE_COC,
        verbose_name="Staff agreement text",
        help_text="HTML template to show for staff agreement checkbox.")
    charity = models.ForeignKey(Charity, null=True, blank=True, on_delete=models.SET_NULL)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=1)
    location = models.CharField(max_length=128, null=True, blank=True,
        verbose_name="Event location",
        help_text="e.g. VA for Virginia")
    # See: https://docs.djangoproject.com/en/2.2/ref/contrib/sites/
    #objects = models.Manager()
    #on_site = CurrentSiteManager()

    def save(self, *args, **kwargs):
        if self.default:
            # Unset any other events and make this the new default
            Event.objects.all().update(default=False)
        return super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class TableSize(LookupTable):
    description = models.TextField()
    chairMin = models.IntegerField(default=1, verbose_name="Minimum chairs")
    chairMax = models.IntegerField(default=1, verbose_name="Maximum chairs")
    tableMin = models.IntegerField(default=0, verbose_name="Minimum tables")
    tableMax = models.IntegerField(default=0, verbose_name="Maximum tables")
    partnerMin = models.IntegerField(default=1, verbose_name="Minimum partners")
    partnerMax = models.IntegerField(default=1, verbose_name="Maximium partners")
    basePrice = models.DecimalField(max_digits=6, decimal_places=2, default=0,
        verbose_name="Base price")
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        if self.event is None:
            return self.name
        return u"{0} {1}".format(self.name, self.event.name)

class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
    volunteerListOk = models.BooleanField(default=False,
        verbose_name="Add to volunteer list",
        help_text="If checked, attendees can sign up to volunteer for this department")

    def __str__(self):
        return self.name

#End lookup and supporting tables


def getRegistrationToken():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase+string.digits) for _ in range(15))

def getOrderReference():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase+string.digits) for _ in range(6))

#@python_2_unicode_compatible
class TempToken(models.Model):
    token = models.CharField(max_length=200, default=getRegistrationToken)
    email = models.CharField(max_length=200)
    validUntil = models.DateTimeField()
    used = models.BooleanField(default=False)
    usedDate = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)

class Attendee(models.Model):
    firstName = models.CharField(max_length=200, verbose_name="First name")
    lastName = models.CharField(max_length=200, verbose_name="Last name")
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True, verbose_name="State/Province")
    country = models.CharField(max_length=200, blank=True)
    postalCode = models.CharField(max_length=20, blank=True, verbose_name="Postal code")
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=200)
    birthdate = models.DateField()
    emailsOk = models.BooleanField(default=False,
        verbose_name="Add to mailing list")
    surveyOk = models.BooleanField(default=False,
        verbose_name="Add to survey mailing list")
    volunteerContact = models.BooleanField(default=False,
        verbose_name="Interested in volunteering")
    volunteerDepts = models.CharField(max_length=1000, blank=True,
        verbose_name="Volunteer department interests")
    holdType = models.ForeignKey(HoldType, null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Hold type")
    notes = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    parentFirstName = models.CharField(max_length=200, blank=True,
        verbose_name="Parent first name")
    parentLastName = models.CharField(max_length=200, blank=True,
        verbose_name="Parent last name")
    parentPhone = models.CharField(max_length=20, blank=True,
        verbose_name="Parent phone")
    parentEmail = models.CharField(max_length=200, blank=True,
        verbose_name="Parent email")
    aslRequest = models.BooleanField(default=False,
        verbose_name="ASL services requested")

    def __str__(self):
        if self is None:
            return u"--"
        return u"{0} {1}".format(self.firstName, self.lastName)

class Badge(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registeredDate = models.DateTimeField(null=True, verbose_name="Registered on")
    registrationToken = models.CharField(max_length=200,
        default=getRegistrationToken,
        verbose_name="Registration token")
    badgeName = models.CharField(max_length=200, blank=True,
        verbose_name="Badge name")
    badgeNumber = models.IntegerField(null=True, blank=True,
        verbose_name="Badge number")
    printed = models.BooleanField(default=False)
    printCount = models.IntegerField(default=0,
        verbose_name="Badge print count")

    def __str__(self):
        if self.badgeNumber is not None or self.badgeNumber == '':
            return u'"{0}" #{1} ({2})'.format(self.badgeName, self.badgeNumber, self.event)
        if self.badgeName != '':
            return u'"{0}" ({1})'.format(self.badgeName, self.event)
        if self.registeredDate is not None:
            return u"[Orphan {0}]".format(self.registeredDate)
        return u"Badge object {0}".format(self.registrationToken)

    def isMinor(self):
      birthdate = self.attendee.birthdate
      eventdate = self.event.eventStart
      age_at_event = eventdate.year - birthdate.year - ((eventdate.month, eventdate.day) < (birthdate.month, birthdate.day))
      if age_at_event < settings.APIS_LEGAL_AGE:
        return True
      return False

    def getDiscountCode(self):
      discount = ""
      orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
      for oi in orderItems:
        if oi.order.discount != None:
          discount = oi.order.discount.codeName
      return discount

    def paidTotal(self):
      total = 0
      orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
      for oi in orderItems:
          if oi.order.billingType != Order.UNPAID:
              total += oi.order.total
      return Decimal(total)

    @property
    def abandoned(self):
        if Staff.objects.filter(attendee=self.attendee).exists():
            return 'Staff'
        if Dealer.objects.filter(attendee=self.attendee).exists():
            return 'Dealer'
        if self.paidTotal() > 0:
            return 'Paid'
        level = self.effectiveLevel()
        if level == 'Unpaid':
            return 'Unpaid'
        if level:
            return 'Comp'
        return 'Abandoned'

    def effectiveLevel(self):
        level = None
        orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
        for oi in orderItems:
            if oi.order.billingType == Order.UNPAID:
                return 'Unpaid'
            if not level:
                level = oi.priceLevel
            elif oi.priceLevel.basePrice > level.basePrice:
                level = oi.priceLevel
        return level

    def getOrderItems(self):
        orderItems = OrderItem.objects.filter(badge=self, order__isnull=False)
        return orderItems

    def getOrder(self):
        oi = self.getOrderItems().first()
        return oi.order

    def save(self, *args, **kwargs):
        if not self.id and not self.registeredDate:
            self.registeredDate = timezone.now()
        return super(Badge, self).save(*args, **kwargs)



class Staff(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.CASCADE)
    registrationToken = models.CharField(max_length=200,
        default=getRegistrationToken,
        verbose_name="Registration token")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    supervisor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200, blank=True)
    twitter = models.CharField(max_length=200, blank=True)
    telegram = models.CharField(max_length=200, blank=True)
    shirtsize = models.ForeignKey(ShirtSizes, null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Shirt size")
    timesheetAccess = models.BooleanField(default=False,
        verbose_name="Timesheet access")
    notes = models.TextField(blank=True)
    specialSkills = models.TextField(blank=True,
        verbose_name="Special skills")
    specialFood = models.TextField(blank=True,
        verbose_name="Dietary restrictions")
    specialMedical = models.TextField(blank=True,
        verbose_name="Medical considerations")
    contactName = models.CharField(max_length=200, blank=True,
        verbose_name="Emergency contact name")
    contactPhone = models.CharField(max_length=200, blank=True,
        verbose_name="Emergency contact phone")
    contactRelation = models.CharField(max_length=200, blank=True,
        verbose_name="Emergency contact relation")
    needRoom = models.BooleanField(default=False,
        verbose_name="Need room")
    gender = models.CharField(max_length=50, blank=True)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)
    checkedIn = models.BooleanField(default=False,
        verbose_name="Checked-in")

    class Meta:
        verbose_name_plural = "Staff"

    def __str__(self):
        return u"{0} {1}".format(self.attendee.firstName, self.attendee.lastName)

    def getBadge(self):
        badge = Badge.objects.filter(attendee=self.attendee,event=self.event).last()
        return badge

    def resetToken(self):
        self.registrationToken = getRegistrationToken()
        self.save()
        return


class Dealer(models.Model):
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.SET_NULL)
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken,
        verbose_name="Registration token")
    approved = models.BooleanField(default=False)
    tableNumber = models.IntegerField(null=True, blank=True,
        verbose_name="Table number")
    notes = models.TextField(blank=True)
    businessName = models.CharField(max_length=200,
        verbose_name="Business name")
    website = models.CharField(max_length=500)
    description = models.TextField()
    license = models.CharField(max_length=50)
    needPower = models.BooleanField(default=False,
        verbose_name="Need power")
    needWifi = models.BooleanField(default=False,
        verbose_name="Need Wifi")
    wallSpace = models.BooleanField(default=False,
        verbose_name="Prefer wall-space")
    nearTo = models.CharField(max_length=200, blank=True,
        verbose_name="Near to",
        help_text="Requests to be placed near this vendor")
    farFrom = models.CharField(max_length=200, blank=True,
        verbose_name="Far from",
        help_text="Requests to be placed far from this vendor")
    tableSize = models.ForeignKey(TableSize, on_delete=models.SET_NULL, null=True,
        verbose_name="Table size")
    chairs = models.IntegerField(default=0)
    tables = models.IntegerField(default=0)
    reception = models.BooleanField(default=False)
    artShow = models.BooleanField(default=False, verbose_name="Art show")
    charityRaffle = models.TextField(blank=True, verbose_name="Charity raffle")
    agreeToRules = models.BooleanField(default=False,
        verbose_name="Agrees to Code of Conduct")
    breakfast = models.BooleanField(default=False)
    willSwitch = models.BooleanField(default=False, verbose_name="Will switch")
    partners = models.TextField(blank=True)
    buttonOffer = models.CharField(max_length=200, blank=True)
    discount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    discountReason = models.CharField(max_length=200, blank=True,
        verbose_name="Discount reason")
    emailed = models.BooleanField(default=False)
    asstBreakfast = models.BooleanField(default=False)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)
    logo = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return u"{0} {1}" % (self.attendee.firstName, self.attendee.lastName)

    def getPartnerCount(self):
      partnercount = self.dealerasst_set.count()
      return partnercount

    def paidTotal(self):
          total = 0
          badge = self.getBadge()
          orderItems = OrderItem.objects.filter(badge=badge)
          for oi in orderItems:
              if oi.order:
                  total += oi.order.total
          return Decimal(total)

    def getBadge(self):
        badge = Badge.objects.filter(attendee=self.attendee,event=self.event).last()
        return badge

    def resetToken(self):
        self.registrationToken = getRegistrationToken()
        self.save()
        return


class DealerAsst(models.Model):
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)
    attendee = models.ForeignKey(Attendee, null=True, blank=True, on_delete=models.CASCADE)
    registrationToken = models.CharField(max_length=200, default=getRegistrationToken)
    name = models.CharField(max_length=400)
    email = models.CharField(max_length=200)
    license = models.CharField(max_length=50)
    sent = models.BooleanField(default=False)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Dealer assistant"
        verbose_name_plural = "Dealer assistants"

    def __str__(self):
        return self.name

    def getList(self):
        if self.optionExtraType in ["int", "bool", "string"]:
            return []
        elif self.optionExtraType == "ShirtSizes":
            return [{'name':s.name, 'id':s.id} for s in ShirtSizes.objects.all()]
        else:
            return []

# Start order tables

class Cart(models.Model):
    ATTENDEE = 'Attendee'
    STAFF = 'Staff'
    DEALER = 'Dealer'
    ASST = 'Dealer Assistant'
    FORM_CHOICES = ((ATTENDEE, 'Attendee'), (STAFF, 'Staff'), (DEALER, 'Dealer'), (ASST, 'Dealer Assistant'))
    token = models.CharField(max_length=200, blank=True, null=True)
    form = models.CharField(max_length=50, choices=FORM_CHOICES)
    formData = models.TextField(null=True)    # Deprecated
    formJSON = JSONField(null=True)
    formHeaders = models.TextField(null=True) # Deprecated
    headersJSON = JSONField(null=True)
    enteredDate = models.DateTimeField(auto_now_add=True, null=True)
    transferedDate = models.DateTimeField(null=True)

    def __str__(self):
        return u"{0} {1}".format(self.form, self.enteredDate)


def getReference():
    reference = getOrderReference()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getOrderReference()

#@python_2_unicode_compatible
class Order(models.Model):
    UNPAID = 'Unpaid'
    CREDIT = 'Credit'
    CASH = 'Cash'
    COMP = 'Comp'
    BILLING_TYPE_CHOICES = ((UNPAID, 'Unpaid'), (CREDIT, 'Credit'), (CASH, 'Cash'), (COMP, 'Comp'))
    PENDING = 'Pending'
    COMPLETE = 'Complete'
    PAID = 'Paid'
    STATUS_CHOICES = ((PENDING, 'Pending'), (COMPLETE, 'Complete'), (PAID, 'Paid'))
    total = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=PENDING)
    reference = models.CharField(max_length=50, default=getReference, blank=True)
    createdDate = models.DateTimeField(auto_now_add=True, null=True,
        verbose_name="Created date")
    settledDate = models.DateTimeField(auto_now_add=True, null=True,
        verbose_name="Settled date",
        help_text="(Deprecated)")
    discount = models.ForeignKey(Discount, null=True, on_delete=models.SET_NULL, blank=True)
    orgDonation = models.DecimalField(max_digits=8, decimal_places=2,
        null=True, default=0,
        verbose_name="Organization donation")
    charityDonation = models.DecimalField(max_digits=8, decimal_places=2,
        null=True, default=0,
        verbose_name="Charity donation")
    notes = models.TextField(blank=True)
    billingName = models.CharField(max_length=200, blank=True,
        verbose_name="Billing name")
    billingAddress1 = models.CharField(max_length=200, blank=True,
        verbose_name="Billing address 1")
    billingAddress2 = models.CharField(max_length=200, blank=True,
        verbose_name="Billing address 2")
    billingCity = models.CharField(max_length=200, blank=True,
        verbose_name="Billing city")
    billingState = models.CharField(max_length=200, blank=True,
        verbose_name="Billing state/province")
    billingCountry = models.CharField(max_length=200, blank=True,
        verbose_name="Billing country")
    billingPostal = models.CharField(max_length=20, blank=True,
        verbose_name="Billing postal code")
    billingEmail = models.CharField(max_length=200, blank=True,
        verbose_name="Billing email")
    billingType = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES,
        default=CREDIT, verbose_name="Billing Type")
    lastFour = models.CharField(max_length=4, blank=True)
    apiData = models.TextField(null=True, blank=True) # Legacy
    jsonData = JSONField(null=True, blank=True)

    def __str__(self):
        return u"${0} {1} ({2}) [{3}]".format(
            self.total,
            self.billingType,
            self.status,
            self.reference)

    class Meta:
        permissions = (
            ("issue_refund", "Can issue refunds"),
            ("cash", "Can handle cash transactions"),
            ("cash_admin", "Can open and close cash drawer amounts (manager)"),
            ("discount", "Can create discounts of arbitrary amount"),
        )

class OrderItem(models.Model):
    order = models.ForeignKey(Order, null=True, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, null=True, on_delete=models.CASCADE)
    priceLevel = models.ForeignKey(PriceLevel, null=True,
        on_delete=models.SET_NULL,
        verbose_name="Price level")
    enteredBy = models.CharField(max_length=100,
        verbose_name="Entered by")
    enteredDate = models.DateTimeField(auto_now_add=True, null=True,
        verbose_name="Entered date")

    def getOptions(self):
      return list(AttendeeOptions.objects.filter(orderItem=self).order_by('option__optionName'))

    def __str__(self):
        try:
            return u'{} (${}) - "{}"'.format(
                self.order.status,
                self.order.total,
                self.badge.badgeName,
                )
        except:
            try:
                return u'Incomplete from {}: "{}" ({})'.format(
                    self.enteredBy,
                    self.badge.badgeName,
                    self.priceLevel)
            except:
                return u"OrderItem object"

class AttendeeOptions(models.Model):
    option = models.ForeignKey(PriceLevelOption, on_delete=models.CASCADE)
    orderItem = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    optionValue = models.CharField(max_length=200)
    optionValue2 = models.CharField(max_length=200, blank=True)
    optionValue3 = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Attendee option"
        verbose_name_plural = "Attendee options"

    def getTotal(self):
        if self.option.optionExtraType == "int":
            return int(self.optionValue) * self.option.optionPrice
        return self.option.optionPrice

    def __str__(self):
        return u"[{0}] - {1}".format(self.orderItem, self.option)

class BanList(models.Model):
    firstName = models.CharField(max_length=200, blank=True,
        verbose_name="First name")
    lastName = models.CharField(max_length=200, blank=True,
        verbose_name="Last name")
    email = models.CharField(max_length=400, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Ban list"

class Firebase(models.Model):
    token = models.CharField(max_length=500)
    name = models.CharField(max_length=100)
    closed = models.BooleanField(default=False)
    cashdrawer = models.BooleanField(default=False)

class Cashdrawer(models.Model):
    OPEN = 'Open'
    CLOSE = 'Close'
    TRANSACTION = 'Transaction'
    DEPOSIT = 'Deposit'
    ACTION_CHOICES = ((OPEN, u'Open'), (CLOSE, u'Close'), (TRANSACTION, u'Transaction'), (DEPOSIT, u'Deposit'))
    timestamp = models.DateTimeField(auto_now_add=True)
    # Action: one of - ['OPEN', 'CLOSE', 'TXN', 'DEPOSIT']
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default=OPEN)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    tendered = models.DecimalField(max_digits=8, decimal_places=2, blank=True, default=0)
    user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET(get_sentinel_user),
            null=True,
            blank=True
        )


# vim: ts=4 sts=4 sw=4 expandtab smartindent
