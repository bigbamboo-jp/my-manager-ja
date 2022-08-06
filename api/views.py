import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.timezone import make_aware
from pages.models import AttendanceRecord
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Create your views here.


@api_view(['GET'])
@permission_classes((AllowAny, ))
def site_information(request):
    current_site = Site.objects.get_current()
    context = {
        'name': current_site.name,  # str
        'time_zone': getattr(settings, 'TIME_ZONE', 'UTC'),  # str
    }
    return Response(context)


@api_view(['GET'])
def user_profile(request):
    context = {
        'username': request.user.username,  # str
        'first_name': request.user.first_name,  # str
        'last_name': request.user.last_name,  # str
        'full_name_template': r'${last_name} ${first_name}',  # str
        'groups': request.user.groups.all().values_list('name', flat=True),  # list[str]
    }
    return Response(context)


@api_view(['GET'])
def todays_entry_status(request):
    today = datetime.date.today()
    latest_entry_record_today = AttendanceRecord.objects.filter(user=request.user, entry_time__date=today)
    attendance_count = len(latest_entry_record_today)
    if latest_entry_record_today.exists() == False:
        status = 1
        last_entry_time = None
    else:
        latest_entry_record_today = latest_entry_record_today.filter(leave_time=None)
        if len(latest_entry_record_today) == 1:
            status = -1
            last_entry_time = make_aware(latest_entry_record_today.order_by('-entry_time').first().entry_time).isoformat()
        elif len(latest_entry_record_today) > 1:
            status = -2
            last_entry_time = make_aware(latest_entry_record_today.order_by('-entry_time').first().entry_time).isoformat()
        else:
            status = 2
            last_entry_time = None
    context = {
        'status': status,  # int
        'last_entry_time': last_entry_time,  # str
        'attendance_count': attendance_count,  # int
    }
    return Response(context)
