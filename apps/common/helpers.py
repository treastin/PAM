from random import choices
from string import ascii_letters, digits
import stripe

from config.settings import env

stripe.api_key = env('STRIPE_SECRET_TEST_API_KEY')


def decimal_to_int_stripe(money):
    """
    Used to format decimal price for charge.
    """
    return int(money * 100)


def generate_code() -> str:
    """Generate a random """
    code_len = 16

    code = ''.join(
        choices(
            ascii_letters +
            digits,
            k=code_len
        )
    )
    return code
