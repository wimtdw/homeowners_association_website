from django.db import models
from users.models import PersonalAccount # Предполагается, что модель Account находится в приложении users

class Utilities(models.Model):
  name = models.CharField(max_length=255, verbose_name="Название")
  tariff = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Тариф")
  units = models.CharField(max_length=10, blank=True, null=True, verbose_name='Единицы измерения')
  norm = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Норматив")

  def __str__(self):
    return self.name
  
  class Meta:
      verbose_name = "Коммунальная услуга"
      verbose_name_plural = "Коммунальные услуги"


class Meters(models.Model):
  individual_number = models.CharField(max_length=50, unique=True, verbose_name="Индивидуальный номер")
  account = models.ForeignKey(PersonalAccount, on_delete=models.CASCADE, related_name='meters', verbose_name="Лицевой счет")
  utility = models.ForeignKey(Utilities, on_delete=models.CASCADE, related_name='meters', verbose_name="Услуга")

  def __str__(self):
    return f"Счетчик №{self.individual_number} (Лицевой счет: {self.account_id}, Услуга: {self.utility.name})"

  class Meta:
      verbose_name = "Счётчик"
      verbose_name_plural = "Счётчики"


class MeterReadings(models.Model):
  meter = models.ForeignKey(Meters, on_delete=models.SET_NULL, related_name='readings', verbose_name="Счетчик", null=True)
  month = models.DateField(verbose_name="Месяц показания")
  reading = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Показание")

  def __str__(self):
    return f"Показания счетчика {self.meter.utility} №{self.meter.individual_number} ({self.meter.account}) за {self.month.strftime('%Y-%m')}: {self.reading}"

  class Meta:
      verbose_name = "Показание счётчика"
      verbose_name_plural = "Показания счётчиков"


class PaymentRecords(models.Model):
  account = models.ForeignKey(PersonalAccount, on_delete=models.SET_NULL, related_name='payments', verbose_name="Лицевой счет", null=True)
  utility = models.ForeignKey(Utilities, on_delete=models.CASCADE, related_name='payments', verbose_name="Услуга")
  amount_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Оплачено (руб.)")
  payment_date = models.DateField(verbose_name="Месяц оплаты")

  def __str__(self):
    return f"Оплата {self.amount_paid} руб. за {self.payment_date.strftime('%Y-%m')} (Лицевой счет: {self.account_id}, Услуга: {self.utility.name})"
  
  class Meta:
      verbose_name = "Запись об оплате"
      verbose_name_plural = "Записи об оплате"