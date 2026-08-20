from django.contrib import admin
from .models import AuthorizedMember, LabEvent, LoginToken


@admin.register(AuthorizedMember)
class AuthorizedMemberAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'is_active', 'created_at')
    list_filter   = ('is_active',)
    search_fields = ('name', 'email')
    list_editable = ('is_active',)


@admin.register(LabEvent)
class LabEventAdmin(admin.ModelAdmin):
    list_display  = ('date_debut', 'titre', 'type_event', 'projet', 'responsable', 'statut')
    list_filter   = ('statut', 'type_event', 'projet')
    search_fields = ('titre', 'responsable', 'projet', 'description')
    date_hierarchy = 'date_debut'


@admin.register(LoginToken)
class LoginTokenAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'used_at')
