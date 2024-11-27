from .models import MeterReadings, Utilities


# def count_monthly_payment(utility, new_readings):

#     if utility == 'ХВС' or utility == 'ГВС' or utility == 'Электроснабжение':
#         #new_readings >= 0!
#         used_resource_amount = new_readings - previous_readings
#         payment_sum = used_resource_amount * utility.tariff
#     elif utility == 'Отопление':
#         payment_sum = utility.norm * area * utility.tariff

def count_meter_dependent_payment(account, utility, meter):
    if utility.name in ('ХВС', 'ГВС', 'Электроснабжение'):
        tariff = utility.tariff
        previous_reading_obj = None if len(MeterReadings.objects.filter(meter=meter).order_by('-month')[:2]) < 2 else MeterReadings.objects.filter(meter=meter).order_by('-month')[:2][1]
        new_reading = MeterReadings.objects.filter(meter=meter).order_by('-month')[:2][0]
        if previous_reading_obj:
            difference = new_reading.reading - previous_reading_obj.reading
            previous_reading = previous_reading_obj.reading
        else: 
            difference = new_reading.reading
            previous_reading = 0
        result = tariff * difference
        new_reading = new_reading.reading

    elif utility.name == 'Сод. жилья':
        tariff = utility.tariff
        result = account.apartment_area * utility.tariff
        difference = None
        new_reading = None
        previous_reading = None

    elif utility.name == 'Обращение с ТКО':
        tariff = utility.tariff
        result = account.number_of_residents * utility.tariff
        difference = None
        new_reading = None
        previous_reading = None
    
    elif utility.name == 'Взнос на капремонт':
        tariff = utility.tariff
        result = account.apartment_area * utility.tariff
        difference = None
        new_reading = None
        previous_reading = None

    elif utility.name == 'Отопление':
        result = account.apartment_area * utility.tariff * utility.norm
        difference = account.apartment_area * utility.norm
        new_reading = None
        previous_reading = None
        tariff = utility.tariff


    return {'tariff': tariff, 
            'units': f'₽/{utility.units}', 
            'new_reading': new_reading, 
            'previous_reading':previous_reading, 
            'norm': utility.norm, 
            'area': account.apartment_area, 
            'number_of_people': account.number_of_residents, 
            'difference':difference, 
            'result':result}