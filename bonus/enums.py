from enum import Enum


class TransactionType(Enum):

    DEPOSIT = "DEPOSIT"
    DEPOSIT_CASH = "DEPOSIT_CASH"
    WITHDRAW = "WITHDRAW"


class RepaymentType(Enum):

    TWELVE = "12"
    TWENTY_FOUR = "24"


class RoleType(Enum):

    BANK_OWNER = "BANK_OWNER"
    BRANCH_MANAGER = "BRANCH_MANAGER"
    USER = "USER"
