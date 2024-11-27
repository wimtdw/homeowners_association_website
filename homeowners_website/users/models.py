from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator, RegexValidator

class PersonalAccount(models.Model):
  account_number = models.CharField(
    max_length=8,
    unique=True,
    validators=[
      RegexValidator(r'^\d{6}$', 'Номер лицевого счета должен состоять из 8 цифр.'),
      MinLengthValidator(6),
      MaxLengthValidator(6)
    ],
    verbose_name='Номер лицевого счета'
  )
  building = models.CharField(max_length=3, verbose_name='Корпус дома')
  apartment_number = models.CharField(max_length=5, verbose_name='Номер квартиры')
  apartment_area = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Площадь квартиры')
  number_of_residents = models.PositiveIntegerField(verbose_name='Кол-во проживающих человек')

  def __str__(self):
    return f"Лицевой счет №{self.account_number}"

  class Meta:
    verbose_name = "Лицевой счет"
    verbose_name_plural = "Лицевые счета"


class MyUser(AbstractUser):
    accounts = models.ManyToManyField(PersonalAccount, verbose_name='Лицевые счета', related_name='users')

    