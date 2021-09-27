from enum import Enum


class TransactionType(Enum):

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class RepaymentType(Enum):

    TWELVE = "12"
    TWENTY_FOUR = "24"
