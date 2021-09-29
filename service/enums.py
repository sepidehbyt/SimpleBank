from enum import Enum


class TransactionType(Enum):

    DEPOSIT = "DEPOSIT"
    DEPOSIT_CASH = "DEPOSIT_CASH"
    WITHDRAW = "WITHDRAW"


class RepaymentType(Enum):

    TWELVE = "12"
    TWENTY_FOUR = "24"
