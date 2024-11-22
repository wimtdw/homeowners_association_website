from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import MyUser
# Register your models here.
UserAdmin.fieldsets += (
    # Добавляем кортеж, где первый элемент — это название раздела в админке,
    # а второй элемент — словарь, где под ключом fields можно указать нужные поля.
    ('Extra Fields', {'fields': ('accounts',)}),
)
# Регистрируем модель в админке:
admin.site.register(MyUser, UserAdmin) 