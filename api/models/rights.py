from enum import Enum


class AccessRightsLVL(Enum):
    BUNNED = -1
    UNREGISTERED = 0
    REGISTERED = 1
    MODERATOR = 2
    ADMIN = 3