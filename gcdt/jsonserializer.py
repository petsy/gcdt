from datetime import datetime
from decimal import *


#####################################
# Easy support to add ISO datetime
# serialization for json.dumps

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, Decimal):
        return str(obj)

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")
