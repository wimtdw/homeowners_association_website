import datetime
from django import forms


class AddNewAccountForm(forms.Form):
    account_number = forms.CharField(label='Номер лицевого счета', max_length=6, help_text='Первые две цифры тип объекта - «01» квартиры, офисы; «02» гараж и т.д. Далее три цифры - это номер квартиры, последняя цифра отвечает за разделение лицевых счетов (0 не разделён, или порядковый номер разделения). Например, для квартиры №1 он будет 010010, для квартиры №10 он будет 010100')
    previous_payment = forms.DecimalField(label='Введите сумму последнего платежа с точностью до копеек, внесенного по услуге "Электроснабжение"')

class AddReadingsForm(forms.Form):
    # period = forms.ChoiceField(choices=[
    #     ('current', 'Текущий период'),
    #     ('previous', 'Предыдущий период'),
    # ], label='Выберите период')
    cold_water_reading = forms.DecimalField(label='Введите текущее показание')
    hot_water_reading = forms.DecimalField(label='Введите текущее показание')
    electricity_reading = forms.DecimalField(label='Введите текущее показание')


def validate_year(value):
    current_year = datetime.datetime.now().year
    if not 2016 <= value <= current_year: # Пример диапазона, измените по необходимости
        raise forms.ValidationError('Год должен быть в диапазоне от 2016 до %(current_year)s', params={'current_year': current_year})


class ChooseMonthForm(forms.Form):
    month = forms.IntegerField(min_value=1, max_value=12, label='Введите номер месяца')
    year = forms.IntegerField(label='Введите год', validators=[validate_year])
