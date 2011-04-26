def validate_iphone_udid(udid):
    if not udid or not len(udid) == 40:
        return False
    try:
        int(udid, 16)
    except ValueError:
        return False
    return True
