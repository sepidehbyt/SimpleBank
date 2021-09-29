from django_cron import CronJobBase, Schedule
from bonus.models import Account, Installment, Loan, UserStatistic
from django.conf import settings
from django.utils import timezone
from .utils.smsService import manage_sms


class CalculateDailyInterest(CronJobBase):
    RUN_EVERY_MIN = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MIN)
    code = 'calculate_daily_interest'    # a unique code

    def update_user_statistic(self, user, amount):
        user_statistic = UserStatistic.objects.get(user=user)
        user_statistic.credit = amount
        user_statistic.save()

    def do(self):
        print('calculate_daily_interest')
        accounts = Account.objects.filter(is_active=True)
        daily_percent = settings.YEARLY_INTEREST_PERCENT
        for account in accounts:
            interest = round(account.credit * daily_percent / 100 / 365)
            account.credit = account.credit + interest
            self.update_user_statistic(account.owner, account.credit)
            account.save()


class CalculateInstallations(CronJobBase):
    RUN_EVERY_MIN = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MIN)
    code = 'calculate_installments'    # a unique code

    def update_user_statistic(self, user, amount):
        user_statistic = UserStatistic.objects.get(user=user)
        user_statistic.debt = user_statistic.debt + amount
        user_statistic.save()

    def do(self):
        print('calculate_installments')
        installments = Installment.objects.filter(pay_date__lt=timezone.now(), is_settled=False)
        for installment in installments:
            debtor_account = Account.objects.get(owner=installment.debtor)
            if debtor_account.credit > installment.amount:
                debtor_account.credit = debtor_account.credit - installment.amount
                installment.is_settled = True
                loan = installment.loan
                loan.remainder_installment = loan.remainder_installment - installment.amount
                installment.save()
                debtor_account.save()
                loan.save()
                self.update_user_statistic(installment.debtor, -installment.amount)
            else:
                manage_sms(None, installment, "installment")


class CalculateLoans(CronJobBase):
    RUN_EVERY_MIN = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MIN)
    code = 'calculate_loans'    # a unique code

    def update_user_statistic(self, user):
        user_statistic = UserStatistic.objects.get(user=user)
        user_statistic.loans_unsettled = user_statistic.loans_unsettled - 1
        user_statistic.save()

    def do(self):
        print('calculate_loans')
        loans = Loan.objects.filter(is_settled=False)
        for loan in loans:
            if not Installment.objects.filter(loan=loan, is_settled=False):
                loan.is_settled = True
                loan.save()
                self.update_user_statistic(loan.applicant)
