import datetime
import json
import urllib.parse

import dateutil.relativedelta
import numpy as np
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import TimestampSigner
from django.shortcuts import redirect, render
from django.urls import reverse

from .extensions import encryption
from .extensions.communicate import entry_communication, leave_communication
from .extensions.data_analysis import (collect_data,
                                       collect_monthly_attendance_information)
from .models import AttendanceRecord

# Create your views here.

SHOW_TERMS_OF_USE = getattr(settings, 'SHOW_TERMS_OF_USE', True)
SHOW_PRIVACY_POLICY = getattr(settings, 'SHOW_PRIVACY_POLICY', True)


# no_login_required, login_required
def home(request):
    if request.user.is_authenticated == True:
        today = datetime.date.today()
        entered = AttendanceRecord.objects.filter(user=request.user, entry_time__date=today, leave_time=None).exists()
        context = {
            'entered': entered,
        }
        return render(request, 'pages/private/home.html', context)
    else:
        return render(request, 'pages/public/home.html')


# no_login_required
def terms(request):
    if SHOW_TERMS_OF_USE == True:
        return render(request, 'pages/public/terms.html')
    else:
        return redirect('home')


# no_login_required
def privacy_policy(request):
    if SHOW_PRIVACY_POLICY == True:
        return render(request, 'pages/public/privacy_policy.html')
    else:
        return redirect('home')


@login_required
def entry_description(request):
    today = datetime.date.today()
    if AttendanceRecord.objects.filter(user=request.user, entry_time__date=today, leave_time=None).exists() == True:
        return redirect('home')
    context = {
        'today': today,
        'todays_attendance_times': len(AttendanceRecord.objects.filter(user=request.user, entry_time__date=today).exclude(leave_time=None)),
    }
    return render(request, 'pages/private/entry_begin.html', context)


@login_required
def leave_description(request):
    today = datetime.date.today()
    if AttendanceRecord.objects.filter(user=request.user, entry_time__date=today, leave_time=None).exists() == False:
        return redirect('home')
    context = {
        'today': today,
    }
    return render(request, 'pages/private/leave_begin.html', context)


@login_required
def entry(request):
    if 'finished' in request.GET:
        finished = request.GET['finished'] == '1' or request.GET['finished'] == '2'
    else:
        finished = False
    if finished == True:
        context = {
            'succeeded': request.GET['finished'] == '1',
        }
        response = render(request, 'pages/private/entry_end.html', context)
    else:
        today = datetime.date.today()
        if AttendanceRecord.objects.filter(user=request.user, entry_time__date=today, leave_time=None).exists() == True:
            return redirect('home')
        signer = TimestampSigner()
        json_data = request.COOKIES.get('entry_data')
        if json_data is None:
            entry_data = {}
            request.session['record_data_encryption_key'] = signer.sign(default_token_generator.make_token(request.user))
        else:
            try:
                token = signer.unsign(request.session['record_data_encryption_key'], max_age=datetime.timedelta(days=1))
                if default_token_generator.check_token(request.user, token) == True:
                    json_data = encryption.decrypt(urllib.parse.unquote(json_data).encode(), request.session['record_data_encryption_key'].encode()).decode()
                    if json_data == '':
                        raise Exception()
                    entry_data = json.loads(json_data)
            except Exception as e:
                # raise e
                entry_data = {}
                request.session['record_data_encryption_key'] = signer.sign(default_token_generator.make_token(request.user))
        response = entry_communication(request, entry_data)
    return response


@login_required
def leave(request):
    if 'finished' in request.GET:
        finished = request.GET['finished'] == '1' or request.GET['finished'] == '2'
    else:
        finished = False
    if finished == True:
        context = {
            'succeeded': request.GET['finished'] == '1',
        }
        response = render(request, 'pages/private/leave_end.html', context)
    else:
        today = datetime.date.today()
        if AttendanceRecord.objects.filter(user=request.user, entry_time__date=today, leave_time=None).exists() == False:
            return redirect('home')
        signer = TimestampSigner()
        json_data = request.COOKIES.get('leave_data')
        if json_data is None:
            leave_data = {}
            request.session['record_data_encryption_key'] = signer.sign(default_token_generator.make_token(request.user))
        else:
            try:
                token = signer.unsign(request.session['record_data_encryption_key'], max_age=datetime.timedelta(days=1))
                if default_token_generator.check_token(request.user, token) == True:
                    json_data = encryption.decrypt(urllib.parse.unquote(json_data).encode(), request.session['record_data_encryption_key'].encode()).decode()
                    if json_data == '':
                        raise Exception()
                    leave_data = json.loads(json_data)
            except Exception as e:
                # raise e
                leave_data = {}
                request.session['record_data_encryption_key'] = signer.sign(default_token_generator.make_token(request.user))
        response = leave_communication(request, leave_data)
    return response


@login_required
def my_report(request):
    context = collect_data(request)
    return render(request, 'pages/private/my_report.html', context)


@login_required
def view_records(request):
    months_to_go_back = 12
    if 'page' in request.GET:
        try:
            page_number = int(request.GET['page'])
            if page_number < 1 or page_number > months_to_go_back:
                raise Exception()
            today = datetime.date.today()
            context = {}
            context['target_date'] = today - dateutil.relativedelta.relativedelta(months=page_number-1)
            context['all_attendance_information'], total_working_time, context['attendance_days'] = collect_monthly_attendance_information(request, context['target_date'].year, context['target_date'].month)
            context['attendance_times'] = len(context['all_attendance_information'])
            if context['attendance_days'] == 0:
                context['total_working_time'] = 0.0
                context['average_working_time'] = 0.0
            else:
                context['total_working_time'] = float(np.round(total_working_time / datetime.timedelta(hours=1), decimals=1))
                context['average_working_time'] = float(np.round((total_working_time / datetime.timedelta(hours=1)) / context['attendance_days'], decimals=1))
            mental_rank_statistics = {}
            for attendance_information in context['all_attendance_information']:
                if attendance_information[3] != '－':
                    if attendance_information[3] in mental_rank_statistics:
                        mental_rank_statistics[attendance_information[3]] += 1
                    else:
                        mental_rank_statistics[attendance_information[3]] = 1
                if attendance_information[5] != '' and attendance_information[5] != '－':
                    if attendance_information[5] in mental_rank_statistics:
                        mental_rank_statistics[attendance_information[5]] += 1
                    else:
                        mental_rank_statistics[attendance_information[5]] = 1
            context['mental_rank_statistics'] = mental_rank_statistics
            return render(request, 'pages/private/view_records.html', context)
        except Exception as e:
            # raise e
            pass
    redirect_url = reverse('s_view_records')
    return redirect(redirect_url + '?page=1')
