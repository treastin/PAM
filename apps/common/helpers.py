from random import choices
from string import ascii_letters, digits


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
