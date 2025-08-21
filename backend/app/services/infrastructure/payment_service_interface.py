from abc import ABC, abstractmethod
from typing import Dict, Any
from app.models.job import Job
from app.models.payment import Payment

class PaymentData:
    def __init__(self, grams: float, txn_no: str, picked_up_by: str, staff_name: str):
        self.grams = grams
        self.txn_no = txn_no
        self.picked_up_by = picked_up_by
        self.staff_name = staff_name

class IPaymentService(ABC):
    @abstractmethod
    def record_payment(self, job_id: str, payment_data: PaymentData) -> Payment:
        """Record payment and transition job to PAIDPICKEDUP"""
        pass
    
    @abstractmethod
    def calculate_final_cost(self, material: str, grams: float) -> int:
        """Calculate final cost in cents based on material and weight"""
        pass
