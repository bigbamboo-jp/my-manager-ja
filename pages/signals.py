from django.contrib import admin
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.db.utils import ProgrammingError
from django.dispatch import receiver


@receiver(post_save, sender=Site)
def change_admin_site_title_when_updating_site_name(sender, instance, created, *args, **kwargs):
    try:
        current_site = Site.objects.get_current()
        # admin.site.site_title = current_site.name + ' administration'
        admin.site.site_title = current_site.name + ' サイト管理'
        # admin.site.site_header = current_site.name + ' administration'
        admin.site.site_header = current_site.name + ' 管理サイト'
    except ProgrammingError:
        pass
