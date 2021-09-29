from django_cron import CronJobBase, Schedule
from bonus.models import Account, Installment, Loan
from django.conf import settings
from django.utils import timezone


class CalculateDailyInterest(CronJobBase):
    RUN_EVERY_MIN = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MIN)
    code = 'calculate_daily_interest'    # a unique code

    def do(self):
        print('calculate_daily_interest')
        accounts = Account.objects.filter(is_active=True)
        daily_percent = settings.YEARLY_INTEREST_PERCENT
        for account in accounts:
            amount = account.credit
            amount = round(amount + amount * daily_percent / 100 / 365)
            account.credit = amount
            account.save()


class CalculateInstallations(CronJobBase):
    RUN_EVERY_MIN = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MIN)
    code = 'calculate_installments'    # a unique code

    def do(self):
        print('calculate_installments')
        installments = Installment.objects.filter(pay_date__lt=timezone.now(), is_settled=False)
        for installment in installments:
            debtor_account = Account.objects.get(owner=installment.debtor)
            debtor_account.amount = debtor_account.credit - installment.amount
            installment.is_settled = True
            installment.save()
            debtor_account.save()


class CalculateLoans(CronJobBase):
    RUN_EVERY_MIN = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MIN)
    code = 'calculate_loans'    # a unique code

    def do(self):
        print('calculate_loans')
        loans = Loan.objects.filter(is_settled=False)
        for loan in loans:
            if not Installment.objects.filter(loan=loan, is_settled=False):
                loan.is_settled = True
                loan.save()
