import enum
from enum import Enum


@enum.unique
class CodeCatalogEnum(Enum):
    ONE_PARAM_REQUIRED = 'At least one input parameter is required'
    DELETING_BRANCH = 'Deleting local branch: '

    def __init__(self, message: str):
        self.message = message
