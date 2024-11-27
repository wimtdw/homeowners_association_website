from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from users.models import PersonalAccount, MyUser
from django.contrib.auth import get_user_model
from .forms import AddNewAccountForm, AddReadingsForm, ChooseMonthForm
from .models import MeterReadings, Meters, PaymentRecords, Utilities
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from datetime import date, datetime
from django.urls import reverse
from django.contrib import messages
from .utils import count_meter_dependent_payment
import math

    

def index(request):
    template = 'index.html'
    return render(request, template)

def get_latest_payment_amount(account_number):
    """
    Возвращает сумму самого недавнего платежа для заданного номера лицевого счета.
    Возвращает None, если платежей нет.
    """
    try:
        electricity_utility = Utilities.objects.get(name='Электроснабжение')  
        latest_payment = PaymentRecords.objects.filter(
            account__account_number=account_number,
            utility=electricity_utility
        ).order_by('-payment_date').first()

        if latest_payment:
            return latest_payment.amount_paid
        else:
            return None

    except PersonalAccount.DoesNotExist:
        return None


@login_required
def profile(request):
    template = 'building_service/profile.html'
    user = request.user
    accounts = user.accounts.all().order_by('account_number')
    # account = PersonalAccount.objects.get(id=1)
    # user.accounts.remove(account)
    months = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая",
            6: "июня", 7: "июля", 8: "августа", 9: "сентября", 10: "октября",
            11: "ноября", 12: "декабря"
        }
    date_now = date.today()
    next_month_10th = date(date_now.year + (date_now.month == 12), (date_now.month % 12) + 1, 10)
    diff = next_month_10th - date_now
    context = {'user': user,
               'accounts': accounts,
               'month': date_now.strftime('%m.%Y'),
               'month_text': months[(date_now.month + 1) % 12 or 12],
               'diff': diff.days
               }    
    # try:
    # # Retrieve the account with a specific id (e.g., id=1)
    #     account = PersonalAccount.objects.get(id=1)
    # # Get the users associated with the account
        
    # except PersonalAccount.DoesNotExist:
    #     print("PersonalAccount with id=1 not found.")

    # try:
    # # Retrieve the account with a specific id (e.g., id=1)
    #     user = MyUser.objects.get(id=1)
    #     user2 = MyUser.objects.get(id=3)
    #     user.accounts.add(account)
    #     user2.accounts.add(account)
    #     user.accounts.remove(account)
    #     user2.accounts.remove(account)
    # # Get the users associated with the account
    #     accounts = user.accounts.all()
    # except MyUser.DoesNotExist:
    #     print("User with id=1 not found.")

    # related_users = account.users.all()
    # # Полученный из БД QuerySet передаём в словарь контекста:
    # context = {
    #     'ice_cream_list': related_users,
    #     'accounts': accounts
    # }
    return render(request, template, context)

@login_required
def add_account(request):
    template = 'building_service/add_account_form.html'
    user = request.user
    if request.POST:
        form = AddNewAccountForm(request.POST)
        if form.is_valid():
            account_number = form.cleaned_data['account_number']
            try:
                account = PersonalAccount.objects.get(account_number=account_number)
                if account in user.accounts.all():
                    message = 'Лицевой счёт с таким номером уже добавлен.'
                else:
                    latest_payment = get_latest_payment_amount(account_number)  
                    if latest_payment == form.cleaned_data['previous_payment']:
                        user.accounts.add(account)
                        message = 'Лицевой счет добавлен.' 
                    else:
                        message = 'Данные о платеже не совпали.'            
            except PersonalAccount.DoesNotExist:
                message = 'Лицевого счета с таким номером не существует.'
        else:
            message = 'Неправильно заполнена форма!'    
            
    else:
        form = AddNewAccountForm()
        message = ''

    context = {'user': user,
                'form': form,
                'message': message}  
      
    return render(request, template, context)




@login_required
def add_readings(request, account_number):
    
    template = 'building_service/bill_form.html'
    user = request.user
    

    try:
        
        account = PersonalAccount.objects.get(account_number=account_number)
        if account in user.accounts.all():
            address = f'г. Москва, ул. Новогодняя, д.23, к.{account.building}, кв.{account.apartment_number}'
            #
            utilities_names = ["ХВС", "ГВС", "Электроснабжение"]
            meter_data = {}

            for utility_name in utilities_names:
                try:
                    utility = Utilities.objects.get(name=utility_name)
                    meter = Meters.objects.get(account=account, utility=utility)
                    last_reading = MeterReadings.objects.filter(meter=meter).aggregate(Max('month'))
                    last_month = last_reading['month__max']
                    if last_month:
                        last_reading_value = MeterReadings.objects.get(meter=meter, month=last_month).reading
                    else:
                        last_reading_value = 0

                    meter_data[utility_name] = {
                        "individual_number": meter.individual_number,
                        "last_reading": last_reading_value,
                        "last_month": last_month,
                        "id": meter.id
                    }
                except (Utilities.DoesNotExist, Meters.DoesNotExist, MeterReadings.DoesNotExist):
                    meter_data[utility_name] = {
                        "individual_number": None,
                        "last_reading": 0,
                        "last_month": None
                    }

            initial_data = {
                'cold_water_reading': meter_data['ХВС']['last_reading'],
                'hot_water_reading': meter_data['ГВС']['last_reading'],
                'electricity_reading': meter_data['Электроснабжение']['last_reading']
            }

            if request.POST:
                form = AddReadingsForm(request.POST)
                try:
                    if form.is_valid():
                        cold_water_reading = form.cleaned_data['cold_water_reading']
                        hot_water_reading = form.cleaned_data['hot_water_reading']
                        electricity_reading = form.cleaned_data['electricity_reading']
                        if cold_water_reading >= initial_data['cold_water_reading'] and hot_water_reading >= initial_data['hot_water_reading'] and electricity_reading >= initial_data['electricity_reading']:
                            today = date.today()
                            if today.day in range(1, 11):
                                month = today.month - 1
                            else:
                                month = today.month
                            
                            
                           # get_readings = {}
                            try:
                                if not meter_data['ХВС']['last_month']: 
                                    raise ValueError
                                else:
                                    last_month_cold_water = meter_data['ХВС']['last_month'].month
                                    if month == last_month_cold_water:
                                        meter = Meters.objects.get(id=meter_data['ХВС']['id'])
                                        reading_object = MeterReadings.objects.filter(meter=meter).order_by('-month').first()
                                        reading_object.reading = cold_water_reading
                                        reading_object.save(update_fields=['reading']) 
                                    else:
                                        raise ValueError
                                        #get_readings['ХВС'] = reading_object
                            except ValueError:
                                meter = Meters.objects.get(id=meter_data['ХВС']['id'])
                                date_new = today.replace(month=month)
                                MeterReadings.objects.create(
                                meter=meter,
                                month=date_new, 
                                reading=cold_water_reading
                            )
                                #get_readings['ХВС'] = new_reading
                            try:
                                if not meter_data['ГВС']['last_month']:
                                    raise ValueError
                                else:
                                    last_month_hot_water = meter_data['ГВС']['last_month'].month    
                                    if month == last_month_hot_water:
                                        meter = Meters.objects.get(id=meter_data['ГВС']['id'])
                                        reading_object = MeterReadings.objects.filter(meter=meter).order_by('-month').first()
                                        reading_object.reading = hot_water_reading
                                        reading_object.save(update_fields=['reading']) 
                                        #get_readings['ГВС'] = reading_object
                                    else:
                                        raise ValueError
                            except ValueError:
                                meter = Meters.objects.get(id=meter_data['ГВС']['id'])
                                date_new = today.replace(month=month)
                                MeterReadings.objects.create(
                                meter=meter,
                                month=date_new,  
                                reading=hot_water_reading
                            )
                                    # get_readings['ГВС'] = new_reading
                            try:
                                if not meter_data['Электроснабжение']['last_month']:
                                    raise ValueError
                                else:
                                    last_month_electricity = meter_data['Электроснабжение']['last_month'].month
                                    if month == last_month_electricity:
                                        meter = Meters.objects.get(id=meter_data['Электроснабжение']['id'])
                                        reading_object = MeterReadings.objects.filter(meter=meter).order_by('-month').first()
                                        reading_object.reading = electricity_reading
                                        reading_object.save(update_fields=['reading']) 
                                        # get_readings['Электроснабжение'] = reading_object
                                    else:
                                        raise ValueError
                            except ValueError:
                                meter = Meters.objects.get(id=meter_data['Электроснабжение']['id'])
                                date_new = today.replace(month=month)
                                MeterReadings.objects.create(
                                meter=meter,
                                month=date_new,  
                                reading=electricity_reading
                            )
                                #get_readings['Электроснабжение'] = new_reading

                            context = {'form': form, 
                                        'address': address,
                                        'meter_data': meter_data,
                                        'message': 'Показания счётчиков записаны.'}
                            return render(request, template, context)

                        else:
                            raise ValueError('Неправильно заполнена форма. Текущее показание не может быть меньше предыдущего.')
                    else:
                        raise ValueError('Неправильно заполнена форма.')
                except ValueError as e:
                    template = 'building_service/error.html'
                    message = e
                    context = {'message': message}
                    return render(request, template, context)
            else:
                form = AddReadingsForm(initial=initial_data)
                context = {'form': form, 
                        'address': address,
                        'meter_data': meter_data,
                        'message': None
                        }
                return render(request, template, context)
        #
        else:
            raise PermissionDenied("У вас нет доступа к этому личному счету.")
    except PersonalAccount.DoesNotExist as e:
        template = 'building_service/error.html'
        message = 'Лицевого счета с таким номером не существует.'
        context = {'message': message}
        return render(request, template, context)
    except PermissionDenied as e:
        template = 'building_service/error.html'
        message = e
        context = {'message': message}
        return render(request, template, context)
    


@login_required
def get_bill(request, account_number):
    template = 'building_service/bill_form_new.html'
    user = request.user
    try:            
        account = PersonalAccount.objects.get(account_number=account_number)
        if account in user.accounts.all():
            
            payment_results = {}
            utilities_names_no_meters = ['Сод. жилья', 'Обращение с ТКО', 'Взнос на капремонт', 'Отопление']
            for utility_name in utilities_names_no_meters:
                try:
                    utility = Utilities.objects.get(name=utility_name)
                    payment_results[utility_name] = count_meter_dependent_payment(account, utility, meter=None)
                except (Utilities.DoesNotExist):
                    payment_results = {}
            
            
            utilities_names = ["ХВС", "ГВС", "Электроснабжение"]
            for utility_name in utilities_names:
                try:
                    utility = Utilities.objects.get(name=utility_name)
                    meter = Meters.objects.get(account=account, utility=utility)
                    last_reading = MeterReadings.objects.filter(meter=meter).aggregate(Max('month'))
                    last_month = last_reading['month__max']
                    if last_month:
                        last_reading_value = MeterReadings.objects.get(meter=meter, month=last_month).reading
                    else:
                        last_reading_value = 0
                    today = date.today()
                    if today.day in range(1, 11):
                        month = today.month - 1
                    else:
                        month = today.month
                    if last_month and last_month.month == month:
                        address = f'г. Москва, ул. Новогодняя, д.23, к.{account.building}, кв.{account.apartment_number}'
                        payment_results[utility_name] = count_meter_dependent_payment(account, utility, meter)
                        
                    else:
                        messages.success(request, "Для получения квитанции необходимо отправить показания счётчиков!")
                        return redirect(reverse('building_service:add_readings', args=[account_number]))
                    
                except (Utilities.DoesNotExist, Meters.DoesNotExist, MeterReadings.DoesNotExist):
                    payment_results = {}

            utility_water_out = Utilities.objects.get(name='Водоотведение')
            difference = payment_results['ХВС']['difference'] + payment_results['ГВС']['difference']
            result = difference * utility_water_out.tariff

            payment_results['Водоотведение'] = {'tariff': utility_water_out.tariff, 
                                                'units': f'₽/{utility_water_out.units}', 
                                                'new_reading': None, 
                                                'previous_reading':None, 
                                                'norm': utility_water_out.norm, 
                                                'area': account.apartment_area, 
                                                'number_of_people': account.number_of_residents, 
                                                'difference':difference, 
                                                'result':result}
            
            
        else:
            raise PermissionDenied("У вас нет доступа к этому личному счету.")
    except PersonalAccount.DoesNotExist as e:
        template = 'building_service/error.html'
        message = 'Лицевого счета с таким номером не существует.'
        context = {'message': message}
        return render(request, template, context)
    except PermissionDenied as e:
        template = 'building_service/error.html'
        message = e
        context = {'message': message}
        return render(request, template, context)
    
    
    total_sum = 0
    for dict in payment_results.values():
        total_sum += dict['result']
    factor = 10 ** 2
    total_sum = math.ceil(total_sum * factor) / factor
    
    
    context = {        'address': address,
                        'date': today.replace(month=month).strftime("%m.%Y"),
                        'payment_results': payment_results,
                        'total_sum': total_sum
                        }
    return render(request, template, context)

@login_required
def readings_history(request, account_number):
    user = request.user
    try:            
        account = PersonalAccount.objects.get(account_number=account_number)
        if account in user.accounts.all():
            result_dict = {}
            if request.GET:
                form = ChooseMonthForm(request.GET)
                if form.is_valid():
                    month = form.cleaned_data['month']
                    year = form.cleaned_data['year']
                    
                    for service_type in ('ХВС', 'ГВС', 'Электроснабжение'):
                        utility = Utilities.objects.get(name=service_type)
                        units = utility.units
                        start_date_current = date(year, month, 1)
                        end_date_current = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
                        meter_readings_current = MeterReadings.objects.filter(
                            meter__account_id=account,
                            meter__utility__name=service_type,
                            month__gte=start_date_current,
                            month__lt=end_date_current
                        )

                        # Previous month readings
                        previous_month = month - 1
                        previous_year = year
                        if previous_month == 0:
                            previous_month = 12
                            previous_year -= 1

                        start_date_previous = date(previous_year, previous_month, 1)
                        end_date_previous = date(previous_year, previous_month + 1, 1) if previous_month < 12 else date(previous_year + 1, 1, 1)
                        meter_readings_previous = MeterReadings.objects.filter(
                            meter__account_id=account,
                            meter__utility__name=service_type,
                            month__gte=start_date_previous,
                            month__lt=end_date_previous
                        )
                        
                        if not meter_readings_current:
                            result_dict[service_type] = None
                        else:
                            if meter_readings_previous:
                                difference = meter_readings_current[0].reading - meter_readings_previous[0].reading
                                obj2 = meter_readings_previous[0]
                                reading_prev = obj2.reading
                            else:
                                difference = meter_readings_current[0].reading
                                reading_prev = None

                            obj = meter_readings_current[0]
                            number = obj.meter.individual_number
                            reading_cur = obj.reading
                            
                            result_dict[service_type] = {'month': month,
                       'year': year, 'number': number, 'difference': difference, 'reading_cur': reading_cur, 'reading_prev': reading_prev, 'units': units}
            
            else:
                today_month = date.today().month
                today_year = date.today().year
                initial_data = {'month': today_month, 'year': today_year}
                form = ChooseMonthForm(initial=initial_data)

            if all(value is None for value in result_dict.values()):
                result_dict = {}
            
            context = {'form': form, 
                       'result_dict': result_dict,
                       'account': account}
                       
            template = 'building_service/readings_history.html'
            return render(request, template, context)

        else:
            raise PermissionDenied("У вас нет доступа к этому личному счету.")
    except PersonalAccount.DoesNotExist as e:
        template = 'building_service/error.html'
        message = 'Лицевого счета с таким номером не существует.'
        context = {'message': message}
        return render(request, template, context)
    except PermissionDenied as e:
        template = 'building_service/error.html'
        message = e
        context = {'message': message}
        return render(request, template, context)
    