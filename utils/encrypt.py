import hashlib
import uuid
from django.conf import settings


def md5(srting):
    hash_obj = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    hash_obj.update(srting.encode('utf-8'))
    return hash_obj.hexdigest()


def uid(string):
    data = "{}-{}".format(str(uuid.uuid4()), string)
    return md5(data)
