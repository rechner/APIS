from django.conf import settings

from decimal import *
import json
import os
import uuid
import logging

from .models import *

import squareconnect
from squareconnect.rest import ApiException
from squareconnect.apis.transactions_api import TransactionsApi
from squareconnect.apis.locations_api import LocationsApi

from urllib3.exceptions import ReadTimeoutError

squareconnect.configuration.access_token = settings.SQUARE_ACCESS_TOKEN
logger = logging.getLogger('registration.payments')

def chargePayment(order, ccData, ipAddress):
    """
    Returns two variabies:
        success - general success flag
        message - type of failure.
    """

    try:
        idempotency_key = str(uuid.uuid1())
        convertedTotal = int(order.total*100)

        amount = {'amount': convertedTotal, 'currency': settings.SQUARE_CURRENCY}

        billing_address = {
            'postal_code' : ccData['card_data']['billing_postal_code'],
        }

        try:
            billing_address.update(
                {'address_line_1': ccData["address1"], 'address_line_2': ccData["address2"],
                 'locality': ccData["city"], 'administrative_district_level_1': ccData["state"],
                 'postal_code': ccData["postal"], 'country': ccData["country"],
                 'buyer_email_address': ccData["email"],
                 'first_name': ccData["cc_firstname"], 'last_name': ccData["cc_lastname"]}
            )
        except KeyError as e:
            logger.debug("One or more billing address field omited - skipping")

        body = {
            'idempotency_key': idempotency_key,
            'card_nonce': ccData["nonce"],
            'amount_money': amount,
            'reference_id': order.reference,
            'billing_address': billing_address
        }

        logger.debug("---- Begin Transaction ----")
        logger.debug(body)

        api_instance = TransactionsApi()
        api_instance.api_client.configuration.access_token = settings.SQUARE_ACCESS_TOKEN
        api_response = api_instance.charge(settings.SQUARE_LOCATION_ID, body)

        logger.debug("---- Charge Submitted ----")
        logger.debug(api_response)

        #try:
        #import pdb; pdb.set_trace()
        order.lastFour = api_response.transaction.tenders[0].card_details.card.last_4
        order.apiData = json.dumps(api_response.to_dict())
        order.notes = "Square: #" + api_response.transaction.id[:4]
        #except Exception as e:
        #    logger.debug(dir(api_response))
        #    logger.exception(e)
        order.save()

        if api_response.errors and len(api_response.errors) > 0:
            message = api_response.errors[0].details
            logger.debug("---- Transaction Failed ----")
            return False, message

        logger.debug("---- End Transaction ----")

        return True, ""
    except ReadTimeoutError as e:
        logger.error("Timeout during Square Transaction")
        logger.exception(e)
        return False, "A timeout occurred while contacting our payment processor. Please try again later."
    except ApiException as e:
        logger.debug("---- Transaction Failed ----")
        logger.error("!!Failed Square Transaction!!")
        logger.exception(e)
        logger.debug("---- End Transaction ----")
        try:
            return False, json.loads(e.body)
        except:
            return False, str(e)

# vim: ts=4 sts=4 sw=4 expandtab smartindent
