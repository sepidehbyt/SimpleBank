from bonus.enums import TransactionType
from bonus.celeryTasks import send_SMS


def manage_sms(user, model, type):
    # we assume we all send this to mobile
    message = "We all Love radkal2 <3"
    if type == 'welcome':
        message = 'Welcome to the Bonus Bank dear %s %s!' % (user.first_name, user.last_name)
    elif type == 'account':
        message = 'Dear %s %s, your account number is:\n%s' % (user.first_name, user.last_name, model.number)
    elif type == 'transaction':
        if model.type == TransactionType.WITHDRAW.value:
            message = 'Dear %s %s, %d toman withdrawn from account number: %s' % \
                      (user.first_name, user.last_name, model.amount, model.dest_account.number)
        elif model.type == TransactionType.DEPOSIT_CASH.value:
            message = 'Dear %s %s, %d toman deposited to account number: %s' % \
                      (user.first_name, user.last_name, model.amount, model.dest_account.number)
        elif model.type == TransactionType.DEPOSIT.value:
            message = ['Dear %s %s, %d toman withdrawn from account number %s to account number %s' %
                       (user.first_name, user.last_name, model.amount, model.dest_account.number,
                        model.src_account.number),
                       'Dear %s %s, %d toman deposited to account number %s' %
                       (model.src_account.owner.first_name, model.src_account.owner.last_name,
                        model.amount, model.src_account.number),
                       ]

    send_SMS.delay(message)
