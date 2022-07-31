import datetime
import json
import urllib.parse
from decimal import Decimal
from typing import Callable

import numpy as np
import pyairtable
import pyairtable.formulas
import requests.exceptions
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from ..models import (AttendanceRecord, ChoiceQuestion, InputQuestion, Option,
                      Question, TemporaryQuestionSet)
from . import encryption
from .customize import after_entry, after_leave, rank_score_uniquely
from .exceptions import *

question_count = 5

ASK_QUESTIONS_WHEN_ENTERING_AND_LEAVING = getattr(settings, 'ASK_QUESTIONS_WHEN_ENTERING_AND_LEAVING', False)
RECORD_COOKIE_SECURE = getattr(settings, 'RECORD_COOKIE_SECURE', False)
LINK_WITH_AIRTABLE = getattr(settings, 'LINK_WITH_AIRTABLE', False)


def entry_communication(request, entry_data: dict) -> HttpResponse:
    if 'questions' not in entry_data:
        entry_data['questions'] = select_questions(situation=0)
        entry_data['question_order'] = list(entry_data['questions'].keys())
        entry_data['confirmed'] = False
    entry_data, context = process_questions(entry_data)
    if context == None or ASK_QUESTIONS_WHEN_ENTERING_AND_LEAVING == False:
        if entry_data['confirmed'] == True:
            if 'leave_time' in request.session:
                del request.session['leave_time']
            if 'leave_error_code' in request.session:
                del request.session['leave_error_code']
            redirect_url = reverse('s_entry')
            if (processing_result := process_answer_data(request, entry_data, situation=0))[0] == True:
                response = redirect(redirect_url + '?finished=1')
                request.session['entry_time'] = processing_result[2].strftime(r'%Y年%m月%d日 %H時%M分%S秒')
            else:
                response = redirect(redirect_url + '?finished=2')
                request.session['entry_error_code'] = processing_result[1]
            response.delete_cookie('entry_data')
        else:
            response = render(request, 'pages/private/entry_confirmation.html', {})
            response.set_cookie('entry_data', urllib.parse.quote(encryption.encrypt(json.dumps(entry_data).encode(), request.session['record_data_encryption_key'].encode()).decode(), safe='()*!\''), max_age=60 * 60 * 24, secure=RECORD_COOKIE_SECURE)
    else:
        if entry_data['question_number'].startswith('C'):
            response = render(request, 'pages/private/entry_question_page.html', context)
        elif entry_data['question_number'].startswith('I'):
            response = render(request, 'pages/private/entry_report_page.html', context)
        response.set_cookie('entry_data', urllib.parse.quote(encryption.encrypt(json.dumps(entry_data).encode(), request.session['record_data_encryption_key'].encode()).decode(), safe='()*!\''), max_age=60 * 60 * 24, secure=RECORD_COOKIE_SECURE)
    return response


def leave_communication(request, leave_data: dict) -> HttpResponse:
    if 'questions' not in leave_data:
        leave_data['questions'] = select_questions(situation=1)
        leave_data['question_order'] = list(leave_data['questions'].keys())
        leave_data['confirmed'] = False
    leave_data, context = process_questions(leave_data)
    if context == None or ASK_QUESTIONS_WHEN_ENTERING_AND_LEAVING == False:
        if leave_data['confirmed'] == True:
            if 'entry_time' in request.session:
                del request.session['entry_time']
            if 'entry_error_code' in request.session:
                del request.session['entry_error_code']
            redirect_url = reverse('s_leave')
            if (processing_result := process_answer_data(request, leave_data, situation=1))[0] == True:
                response = redirect(redirect_url + '?finished=1')
                request.session['leave_time'] = processing_result[2].strftime(r'%Y年%m月%d日 %H時%M分%S秒')
            else:
                response = redirect(redirect_url + '?finished=2')
                request.session['leave_error_code'] = processing_result[1]
            response.delete_cookie('leave_data')
        else:
            response = render(request, 'pages/private/leave_confirmation.html', {})
            response.set_cookie('leave_data', urllib.parse.quote(encryption.encrypt(json.dumps(leave_data).encode(), request.session['record_data_encryption_key'].encode()).decode(), safe='()*!\''), max_age=60 * 60 * 24, secure=RECORD_COOKIE_SECURE)
    else:
        if leave_data['question_number'].startswith('C'):
            response = render(request, 'pages/private/leave_question_page.html', context)
        elif leave_data['question_number'].startswith('I'):
            response = render(request, 'pages/private/leave_report_page.html', context)
        response.set_cookie('leave_data', urllib.parse.quote(encryption.encrypt(json.dumps(leave_data).encode(), request.session['record_data_encryption_key'].encode()).decode(), safe='()*!\''), max_age=60 * 60 * 24, secure=RECORD_COOKIE_SECURE)
    return response


def select_questions(situation: int) -> dict:
    global question_count
    today = datetime.date.today()
    common_question_sets = TemporaryQuestionSet.objects.filter(situation=situation)
    if common_question_sets.exists() == True:
        common_question_set = common_question_sets.filter(created_at__date=today)
        if common_question_set.exists() == True:
            common_question_sets.exclude(pk__in=common_question_set.values_list('pk', flat=True)).delete()
            question_information = {str(question_pk): None for question_pk in common_question_set[0].questions}
            return question_information
        else:
            common_question_sets.delete()
    addable_question_count = question_count
    if situation == 0:
        additional_argument = {'enabled_when_entry': True}
    elif situation == 1:
        additional_argument = {'enabled_when_leave': True}
    first_questions = Question.objects.filter(constantly_first=True, **additional_argument)[:addable_question_count]
    addable_question_count -= len(first_questions)
    last_questions = Question.objects.filter(constantly_last=True, **additional_argument)[:addable_question_count]
    addable_question_count -= len(last_questions)
    random_questions = Question.objects.filter(selection_target=True, constantly_first=False, constantly_last=False, **additional_argument).order_by('?')[:addable_question_count]
    addable_question_count -= len(random_questions)
    question_pks = []
    for questions in [first_questions, random_questions, last_questions]:
        question_pks.extend([question.pk for question in questions])
    TemporaryQuestionSet.objects.create(situation=situation, questions=question_pks)
    question_information = {str(question_pk): None for question_pk in question_pks}
    return question_information


def get_question_information(question: Question) -> dict:
    context = {'question': question}
    if isinstance(question, ChoiceQuestion) == True:
        context['options'] = Option.objects.filter(pk__in=question.options)
    return context


def process_questions(entry_data: dict) -> tuple:
    if 'question_number' in entry_data:
        redo = True
        if entry_data['questions'][entry_data['question_order'][0]] != None:
            if entry_data['questions'][entry_data['question_order'][0]][0] != '':
                redo = False
        if redo == True:
            if entry_data['question_number'].startswith('C'):
                return entry_data, get_question_information(ChoiceQuestion.objects.filter(pk=int(entry_data['question_order'][0]))[0])
            elif entry_data['question_number'].startswith('I'):
                return entry_data, get_question_information(InputQuestion.objects.filter(pk=int(entry_data['question_order'][0]))[0])
        last_question_pk = entry_data['question_order'].pop(0)
        if (last_question := ChoiceQuestion.objects.filter(pk=int(last_question_pk))).exists() == True:
            user_choice_pk = entry_data['questions'][last_question_pk][0]
            user_choice = Option.objects.get(pk=user_choice_pk)
            if user_choice.effect.startswith('#goto#') == True:
                entry_data['question_order'].insert(0, user_choice.effect[6:])
                if (next_question := ChoiceQuestion.objects.filter(pk=int(entry_data['question_order'][0]))).exists() == True:
                    entry_data['question_number'] = 'C' + entry_data['question_order'][0]
                elif (next_question := InputQuestion.objects.filter(pk=int(entry_data['question_order'][0]))).exists() == True:
                    entry_data['question_number'] = 'I' + entry_data['question_order'][0]
                return entry_data, get_question_information(next_question[0])
            elif user_choice.effect.startswith('#score#') == True:
                if 'score' in entry_data:
                    entry_data['score'] = str(int(entry_data['score']) + int(user_choice.effect[7:]))
                else:
                    entry_data['score'] = user_choice.effect[7:]
            if (required_time := entry_data['questions'][last_question_pk][1]) != None:
                required_time = int(required_time)
            if 'score' in entry_data:
                entry_data['score'] = str(int(entry_data['score']) + evaluate_performance(last_question[0], required_time))
            else:
                entry_data['score'] = str(evaluate_performance(last_question[0], required_time))
        elif (last_question := InputQuestion.objects.filter(pk=int(last_question_pk))).exists() == True:
            if last_question[0].is_number == True:
                try:
                    decimal_value = Decimal(entry_data['questions'][last_question_pk][0])
                    if last_question[0].positive_number_only == True:
                        if decimal_value < 0:
                            raise Exception()
                except Exception:
                    raise InputValueValidationError()
            if 'notes' in entry_data:
                entry_data['notes'] += '\n' + last_question[0].record_template.format(value=entry_data['questions'][last_question_pk][0])
            else:
                entry_data['notes'] = last_question[0].record_template.format(value=entry_data['questions'][last_question_pk][0])
    if len(entry_data['question_order']) > 0:
        if (next_question := ChoiceQuestion.objects.filter(pk=int(entry_data['question_order'][0]))).exists() == True:
            entry_data['question_number'] = 'C' + entry_data['question_order'][0]
        elif (next_question := InputQuestion.objects.filter(pk=int(entry_data['question_order'][0]))).exists() == True:
            entry_data['question_number'] = 'I' + entry_data['question_order'][0]
        return entry_data, get_question_information(next_question[0])
    else:
        entry_data.pop('question_number', None)
        return entry_data, None


def evaluate_performance(question: Question, required_time: int) -> int:
    if required_time == None:
        return 0
    else:
        if required_time < 0 or required_time > 1000 * 30:
            return 0
    statistics = question.answer_time_data
    if len(statistics) > 0:
        q25, q50, q75 = np.percentile(np.array(statistics), [25, 50, 75])
        if required_time <= q25:
            score = 2
        elif required_time <= q50:
            score = 1
        elif required_time <= q75:
            score = 1
        else:
            score = 0
    else:
        score = 1
    question.answer_time_data.append(required_time)
    question.save()
    return score


def process_answer_data(request, entry_data: dict, situation: int) -> tuple:
    global question_count
    try:
        if 'score' in entry_data:
            score = int(entry_data['score'])
            if score < -2 * question_count or score > 2 * 2 * question_count:
                score = 0
        else:
            score = None
        if 'notes' in entry_data:
            if entry_data['notes'] == '':
                notes = entry_data['notes']
            else:
                if situation == 0:
                    notes = '［出席時］\n' + entry_data['notes']
                elif situation == 1:
                    notes = '［退席時］\n' + entry_data['notes']
        else:
            notes = ''
        if LINK_WITH_AIRTABLE == True:
            airtable_attendance_record_table = pyairtable.Table(settings.AIRTABLE_API_KEY, settings.AIRTABLE_BASE_ID, settings.AIRTABLE_ATTENDANCE_RECORD_TABLE_NAME)
            airtable_attendance_record_table_columns = settings.AIRTABLE_ATTENDANCE_RECORD_TABLE_COLUMNS
        current_time = datetime.datetime.now()
        if situation == 0:
            if LINK_WITH_AIRTABLE == True:
                try:
                    airtable_attendance_record = airtable_attendance_record_table.create({airtable_attendance_record_table_columns['user']: [request.user.other_service_id], airtable_attendance_record_table_columns['entry_time']: pyairtable.utils.datetime_to_iso_str(current_time), airtable_attendance_record_table_columns['mental_score_at_entry']: score, airtable_attendance_record_table_columns['mental_rank_at_entry']: rank_score(score), airtable_attendance_record_table_columns['notes']: notes})
                except requests.exceptions.HTTPError as e:
                    error_info = e.response.json()
                    if e.response.status_code == 422:
                        if error_info['error']['type'] == 'UNKNOWN_FIELD_NAME':
                            raise OtherServiceFieldNameError()
                        else:
                            airtable_user_table = pyairtable.Table(settings.AIRTABLE_API_KEY, settings.AIRTABLE_BASE_ID, settings.AIRTABLE_USER_TABLE_NAME)
                            airtable_user_table_columns = settings.AIRTABLE_USER_TABLE_COLUMNS
                            airtable_user_record = airtable_user_table.first(formula=pyairtable.formulas.match({airtable_user_table_columns['username']: request.user.username}))
                            if airtable_user_record == None:
                                raise OtherServiceHaveNoUserError()
                            request.user.other_service_id = airtable_user_record['id']
                            request.user.save()
                            airtable_attendance_record = airtable_attendance_record_table.create({airtable_attendance_record_table_columns['user']: [request.user.other_service_id], airtable_attendance_record_table_columns['entry_time']: pyairtable.utils.datetime_to_iso_str(current_time), airtable_attendance_record_table_columns['mental_score_at_entry']: score, airtable_attendance_record_table_columns['mental_rank_at_entry']: rank_score(score), airtable_attendance_record_table_columns['notes']: notes})
                    elif e.response.status_code == 404:
                        if 'type' in error_info['error']:
                            if error_info['error']['type'] == 'TABLE_NOT_FOUND':
                                raise OtherServiceTableNotFoundError()
                        else:
                            raise e
                    elif e.response.status_code == 403:
                        if error_info['error']['type'] == 'INVALID_PERMISSIONS':
                            raise OtherServiceInvalidPermissionsError()
                    elif e.response.status_code == 401:
                        if error_info['error']['type'] == 'UNAUTHORIZED' or error_info['error']['type'] == 'AUTHENTICATION_REQUIRED':
                            raise OtherServiceAuthenticationError()
                        else:
                            raise e
                    else:
                        raise e
            else:
                airtable_attendance_record = {'id': ''}
            AttendanceRecord.objects.create(user=request.user, entry_time=current_time, mental_rank_at_entry=rank_score(score), notes=notes, mental_score_at_entry=score, other_service_id=airtable_attendance_record['id'])
        elif situation == 1:
            attendance_record = AttendanceRecord.objects.filter(user=request.user, entry_time__date=current_time.date(), leave_time=None)[0]
            if attendance_record.notes != '':
                notes = '\n' + notes
            attendance_record.notes += notes
            attendance_record.leave_time = current_time
            attendance_record.mental_score_at_leave = score
            attendance_record.mental_rank_at_leave = rank_score(score)
            if LINK_WITH_AIRTABLE == True:
                if attendance_record.other_service_id == '':
                    raise OtherServiceHaveNoAttendanceRecordError()
                try:
                    airtable_attendance_record_table.update(attendance_record.other_service_id, {airtable_attendance_record_table_columns['leave_time']: pyairtable.utils.datetime_to_iso_str(current_time), airtable_attendance_record_table_columns['mental_score_at_leave']: score, airtable_attendance_record_table_columns['mental_rank_at_leave']: rank_score(score), airtable_attendance_record_table_columns['notes']: attendance_record.notes})
                except requests.exceptions.HTTPError as e:
                    error_info = e.response.json()
                    if e.response.status_code == 422:
                        if error_info['error']['type'] == 'UNKNOWN_FIELD_NAME':
                            raise OtherServiceFieldNameError()
                        else:
                            raise e
                    elif e.response.status_code == 404:
                        if 'type' in error_info['error']:
                            if error_info['error']['type'] == 'MODEL_ID_NOT_FOUND':
                                raise OtherServiceHaveNoAttendanceRecordError()
                            elif error_info['error']['type'] == 'TABLE_NOT_FOUND':
                                raise OtherServiceTableNotFoundError()
                            else:
                                raise e
                        else:
                            raise e
                    elif e.response.status_code == 403:
                        if error_info['error']['type'] == 'INVALID_PERMISSIONS':
                            raise OtherServiceInvalidPermissionsError()
                    elif e.response.status_code == 401:
                        if error_info['error']['type'] == 'UNAUTHORIZED' or error_info['error']['type'] == 'AUTHENTICATION_REQUIRED':
                            raise OtherServiceAuthenticationError()
                        else:
                            raise e
                    else:
                        raise e
            attendance_record.save()
        if situation == 0:
            customize_assistant(lambda: after_entry())
        elif situation == 1:
            customize_assistant(lambda: after_leave())
    except Exception as e:
        # raise e
        if hasattr(e, 'error_code') == True:
            return False, e.error_code, current_time
        else:
            return False, UnknownError().error_code, current_time
    return True, None, current_time


def rank_score(score: float) -> str:
    if type(unique_rank := customize_assistant(lambda score=score: rank_score_uniquely(score))) == str:
        return unique_rank
    if score == None:
        return '－'
    else:
        if score <= 0.0:
            return '△'
        elif score <= 5.0:
            return '○'
        else:
            return '◎'


def customize_assistant(func: Callable):
    try:
        return func()
    except Exception as e:
        raise CustomizationError(e)
