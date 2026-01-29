import random
import string

def generate_captcha(length=5):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))
