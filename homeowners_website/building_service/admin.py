from django.contrib import admin

# Из модуля models импортируем модель Category...
from .models import Utilities
from .models import Meters
from .models import MeterReadings
from .models import PaymentRecords

# ...и регистрируем её в админке:
admin.site.register(Utilities) 
admin.site.register(Meters)
admin.site.register(MeterReadings)
admin.site.register(PaymentRecords)

