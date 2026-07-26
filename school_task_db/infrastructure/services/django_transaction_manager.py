"""Django transaction boundary adapter."""

from django.db import transaction

from core_logic.interfaces.transaction_manager import ITransactionManager


class DjangoTransactionManager(ITransactionManager):
    def atomic(self):
        return transaction.atomic()
