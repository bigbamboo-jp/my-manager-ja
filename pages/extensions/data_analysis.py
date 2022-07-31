import base64
import calendar
import datetime
import io
import locale
import warnings

import dateutil.relativedelta
import japanize_matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import matplotlib.ticker as ticker
import numpy as np
import scipy.stats
from accounts.models import CustomUser

from ..models import AttendanceRecord

question_count = 5
date_conditions = [['昨日', dateutil.relativedelta.relativedelta(days=1)], ['1週間前', dateutil.relativedelta.relativedelta(weeks=1)], ['1ヶ月前', dateutil.relativedelta.relativedelta(months=1)], ['3ヶ月前', dateutil.relativedelta.relativedelta(months=3)], ['半年前', dateutil.relativedelta.relativedelta(months=6)], ['1年前', dateutil.relativedelta.relativedelta(years=1)]]

locale.setlocale(locale.LC_TIME, 'ja_JP')
plt.switch_backend('agg')
mplstyle.use('fast')
japanize_matplotlib.__name__
warnings.simplefilter('ignore', (RuntimeWarning, UserWarning))


def get_last_week_date(date, target_weekday) -> datetime.date:
    subtract_days = 7 + date.weekday() - target_weekday
    target_date = date - datetime.timedelta(days=subtract_days)
    return target_date


def get_next_week_date(date, target_weekday) -> datetime.date:
    add_days = 7 - date.weekday() + target_weekday
    target_date = date + datetime.timedelta(days=add_days)
    return target_date


def get_main_user(request) -> CustomUser:
    return request.user


def collect_data(request) -> dict:
    global date_conditions
    main_user = get_main_user(request)
    context = {}
    context['general_comment'] = get_general_comment(request)
    context['last_week_attendance_information'], total_working_time, context['last_week_attendance_days'] = collect_last_week_attendance_information(request)
    context['last_week_attendance_times'] = len(context['last_week_attendance_information'])
    if context['last_week_attendance_days'] == 0:
        context['total_working_time'] = 0.0
        context['average_working_time'] = 0.0
    else:
        context['total_working_time'] = float(np.round(total_working_time / datetime.timedelta(hours=1), decimals=1))
        context['average_working_time'] = float(np.round((total_working_time / datetime.timedelta(hours=1)) / context['last_week_attendance_days'], decimals=1))
        context['last_week_activity_graph'] = generate_last_week_activity_graph(request)
    mental_deviation_values_organization_all = calculate_mental_deviation_values(request, False)
    context['mental_deviation_values_organization_all'] = calculate_increases_and_decreases_in_mental_deviation_values(mental_deviation_values_organization_all)
    if main_user.groups.exists() == True:
        context['user_groups'] = '・'.join(main_user.groups.all().values_list('name', flat=True))
        mental_deviation_values_limited_to_group = calculate_mental_deviation_values(request, True)
        context['mental_deviation_values_limited_to_group'] = calculate_increases_and_decreases_in_mental_deviation_values(mental_deviation_values_limited_to_group)
    if mental_deviation_values_organization_all != []:
        context['mental_score_normal_distribution_graph'] = generate_mental_score_normal_distribution_graph(request)
    return context


def calculate_increases_and_decreases_in_mental_deviation_values(mental_deviation_values: list) -> list:
    global date_conditions
    mental_deviation_values = [[mental_deviation_values[i], date_conditions[i]] for i in range(len(mental_deviation_values)) if mental_deviation_values[i] != []]
    for i in range(len(mental_deviation_values)):
        data_name = mental_deviation_values[i][1][0] + '（' + mental_deviation_values[i][0][0].strftime(r'%Y年%m月%d日') + '）'
        if i+1 < len(mental_deviation_values):
            if (difference := mental_deviation_values[i][0][1] - mental_deviation_values[i+1][0][1]) >= 0:
                difference_text = '↑' + str(abs(difference))
            else:
                difference_text = '↓' + str(abs(difference))
            data_value = str(mental_deviation_values[i][0][1]) + '（' + difference_text + '）'
        else:
            data_value = str(mental_deviation_values[i][0][1])
        mental_deviation_values[i] = [data_name, data_value]
    return mental_deviation_values


def get_general_comment(request) -> list:
    today = datetime.date.today()
    main_user = get_main_user(request)
    last_monday = get_last_week_date(today, 0)  # 0=月曜日
    last_sunday = get_last_week_date(today, 6)  # 6=日曜日
    last_week_attendance_records = AttendanceRecord.objects.filter(user=main_user, entry_time__date__range=[last_monday, last_sunday]).order_by('entry_time')
    average_mental_score = None
    if last_week_attendance_records != []:
        last_week_mental_scores_at_entry = last_week_attendance_records.values_list('mental_score_at_entry', flat=True)
        last_week_mental_scores_at_leave = last_week_attendance_records.values_list('mental_score_at_leave', flat=True)
        mental_scores = []
        for i in range(len(last_week_mental_scores_at_entry)):
            if last_week_mental_scores_at_entry[i] != None and last_week_mental_scores_at_leave[i] != None:
                mental_scores.append(last_week_mental_scores_at_entry[i] + last_week_mental_scores_at_leave[i])
            else:
                mental_scores.append(np.nan)
        average_mental_score = float(np.mean(np.array(mental_scores)))
    general_comment = evaluate_score(average_mental_score)
    return general_comment


def evaluate_score(score: float) -> list:
    if np.isnan(score) == True:
        return ['Unknown...', '先週のメンタル情報がないため、傾向を分析できません。']
    else:
        if score <= 0.0:
            return ['Not so good...', 'あんまり良くないです。\n作業量を減らすなどして、精神的な負担を減らしましょう。']
        elif score <= 5.0:
            return ['Good!', 'いい感じです。\n無理のない範囲で改善に努めましょう！']
        else:
            return ['Great!', '精神的にとても健康な状態です。\nこの状態を維持しましょう！']


def collect_last_week_attendance_information(request) -> tuple:
    today = datetime.date.today()
    last_monday = get_last_week_date(today, 0)  # 0=月曜日
    last_sunday = get_last_week_date(today, 6)  # 6=日曜日
    return collect_attendance_information(request, last_monday, last_sunday)


def collect_monthly_attendance_information(request, year: int, month: int) -> tuple:
    monthrange = calendar.monthrange(year, month)
    first_date = datetime.date(year, month, 1)
    last_date = datetime.date(year, month, monthrange[1])
    return collect_attendance_information(request, first_date, last_date)


def collect_attendance_information(request, first_date: datetime.date, last_date: datetime.date) -> tuple:
    main_user = get_main_user(request)
    attendance_records = AttendanceRecord.objects.filter(user=main_user, entry_time__date__range=[first_date, last_date]).order_by('entry_time')
    all_attendance_information = []
    total_working_time = datetime.timedelta()
    attendance_days = len(attendance_records)
    for record in attendance_records:
        attendance_information = [record.entry_time.date(), record.entry_time.strftime('%a')]
        if all_attendance_information != []:
            for _attendance_information in reversed(all_attendance_information):
                if _attendance_information[0] == record.entry_time.date():
                    attendance_information = [None, '']
                    attendance_days -= 1
                    break
        attendance_information.extend([record.entry_time.time(), record.mental_rank_at_entry])
        if record.leave_time == None:
            attendance_information.extend([None, '', None])
        else:
            attendance_information.extend([record.leave_time.time(), record.mental_rank_at_leave, str(record.leave_time - record.entry_time)])
            attendance_information[-1] = attendance_information[-1][:attendance_information[-1].find('.')]
            total_working_time += record.leave_time - record.entry_time
        attendance_information.append(record.notes)
        all_attendance_information.append(attendance_information)
    return all_attendance_information, total_working_time, attendance_days


def generate_last_week_activity_graph(request) -> str:
    today = datetime.date.today()
    main_user = get_main_user(request)
    last_monday = get_last_week_date(today, 0)  # 0=月曜日
    last_sunday = get_last_week_date(today, 6)  # 6=日曜日
    weekdays = []
    for i in range(7):
        weekdays.append((last_monday + dateutil.relativedelta.relativedelta(days=i)).strftime(r'%#m/%#d(%a)'))
    last_week_attendance_records = AttendanceRecord.objects.filter(user=main_user, entry_time__date__range=[last_monday, last_sunday]).exclude(leave_time=None).order_by('entry_time')
    if last_week_attendance_records.exists() == False:
        return output_graph(plt.figure())
    last_week_activity = [[0.0, 0.0] for _ in range(7)]
    for record in last_week_attendance_records:
        if record.mental_score_at_entry != None and record.mental_score_at_leave != None:
            mental_score = record.mental_score_at_entry + record.mental_score_at_leave
        else:
            mental_score = np.nan
        last_week_activity[record.entry_time.weekday()] = [last_week_activity[record.entry_time.weekday()][0] + (record.leave_time - record.entry_time) / datetime.timedelta(hours=1), last_week_activity[record.entry_time.weekday()][1] + mental_score]
    for i in range(len(last_week_activity)):
        if last_week_activity[i][1] == 0.0:
            last_week_activity[i] = [np.nan, np.nan]

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    color_1 = mpl.cm.Set1.colors[4]
    color_2 = mpl.cm.Set1.colors[1]
    ax1.bar(weekdays, [activity[0] for activity in last_week_activity],
            color=color_1, width=0.5, label='作業時間')
    ax2.plot(weekdays, [activity[1] for activity in last_week_activity],
             color=color_2, linewidth=2.5, label='メンタルスコア', marker='.', markersize=12)
    ax1.tick_params(labelsize=10)
    ax1.set_title('作業時間とメンタルスコアの関係', fontsize=14)
    ax2.spines['left'].set_color(color_1)
    ax2.spines['right'].set_color(color_2)
    ax1.tick_params(axis='y', colors=color_1)
    ax2.tick_params(axis='y', colors=color_2)
    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%d時間'))
    ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))
    handler1, label1 = ax1.get_legend_handles_labels()
    handler2, label2 = ax2.get_legend_handles_labels()
    ax1.legend(handler1 + handler2, label1 + label2, loc='best')
    ax1_y_max = 1.2 * np.nanmax([activity[0] for activity in last_week_activity])
    ax2_y_max = 1.2 * np.nanmax([activity[1] for activity in last_week_activity])
    if np.isnan(ax2_y_max) == True:
        ax2_y_max = 0
    ax1.set_xlim([-0.5, 6.5])
    ax1.set_ylim([0, ax1_y_max])
    ax2.set_xlim([-0.5, 6.5])
    ax2.set_ylim([0, ax2_y_max])
    return output_graph(fig)


def output_graph():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=200)
    buffer.seek(0)
    img = buffer.getvalue()
    graph = base64.b64encode(img)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph


def calculate_mental_deviation_values(request, in_group: bool) -> list:
    global date_conditions
    previous_day_record_data = []
    for condition in date_conditions:
        previous_day_record_data.append(collect_previous_day_record_data(request, condition[1], in_group))
    mental_deviation_values = []
    for record_data in previous_day_record_data:
        if record_data == []:
            mental_deviation_values.append([])
        else:
            mental_scores_at_entry = record_data[1].values_list('mental_score_at_entry', flat=True)
            mental_scores_at_leave = record_data[1].values_list('mental_score_at_leave', flat=True)
            mental_scores = []
            for i in range(len(mental_scores_at_entry)):
                if mental_scores_at_entry[i] != None and mental_scores_at_leave[i] != None:
                    mental_scores.append(mental_scores_at_entry[i] + mental_scores_at_leave[i])
                else:
                    mental_scores.append(np.nan)
            if record_data[0].mental_score_at_entry != None and record_data[0].mental_score_at_leave != None:
                user_mental_score = record_data[0].mental_score_at_entry + record_data[0].mental_score_at_leave
            else:
                user_mental_score = np.nan
            previous_day_mental_deviation_value = calculate_deviation_value(mental_scores, user_mental_score)
            if np.isnan(previous_day_mental_deviation_value) == True:
                continue
            mental_deviation_values.append([record_data[0].entry_time.date(), previous_day_mental_deviation_value])
    return mental_deviation_values


def collect_previous_day_record_data(request, date_condition: dateutil.relativedelta.relativedelta, in_group: bool) -> list:
    today = datetime.date.today()
    main_user = get_main_user(request)
    previous_day_records = AttendanceRecord.objects.filter(user=main_user, entry_time__date__range=[today - 2 * date_condition + dateutil.relativedelta.relativedelta(days=1), today - date_condition]).exclude(leave_time=None).order_by('-entry_time')
    previous_day_record_data = []
    if in_group == True:
        additional_argument = {'user__groups__in': main_user.groups.all()}
    else:
        additional_argument = {}
    for record in previous_day_records:
        previous_day_all_records = AttendanceRecord.objects.filter(entry_time__date=record.entry_time.date(), **additional_argument).exclude(leave_time=None, user=record.user)
        if previous_day_all_records.exists() == True:
            previous_day_record_data = [record, previous_day_all_records]
            break
    return previous_day_record_data


def calculate_deviation_value(scores: list, user_score: int) -> float:
    np_scores = np.array(scores)
    mean = np.mean(np_scores)
    std = np.std(np_scores)
    deviation = (user_score - mean) / std
    deviation_value = 50 + deviation * 10
    return float(np.round(deviation_value, decimals=1))


def generate_mental_score_normal_distribution_graph(request) -> str:
    global date_conditions
    today = datetime.date.today()
    main_user = get_main_user(request)
    for condition in date_conditions:
        previous_day_records_user = AttendanceRecord.objects.filter(user=main_user, entry_time__date__range=[today - 2 * condition[1] + dateutil.relativedelta.relativedelta(days=1), today - condition[1]]).exclude(leave_time=None).order_by('-entry_time')
        completed = False
        for record_user in previous_day_records_user:
            previous_day_records_organization_all = AttendanceRecord.objects.filter(entry_time__date=record_user.entry_time.date()).exclude(leave_time=None)
            if previous_day_records_organization_all.exists() == True:
                data_condition_used = condition
                completed = True
                break
        if completed == True:
            break
    if previous_day_records_user.exists() == False or previous_day_records_organization_all.exists == False:
        return output_graph(plt.figure())
    previous_day_all_records_in_group = AttendanceRecord.objects.none()
    if main_user.groups.exists() == True:
        previous_day_all_records_in_group = AttendanceRecord.objects.filter(entry_time__date=previous_day_records_user[0].entry_time.date(), user__groups__in=main_user.groups.all()).exclude(leave_time=None)
    mental_scores_organization_all = []
    for record in previous_day_records_organization_all:
        mental_scores_organization_all.append(record.mental_score_at_entry + record.mental_score_at_leave)
    if previous_day_all_records_in_group.exists() == True:
        mental_scores_in_group = []
        for record in previous_day_all_records_in_group:
            mental_scores_in_group.append(record.mental_score_at_entry + record.mental_score_at_leave)
    mental_scores_organization_all = np.array(mental_scores_organization_all)
    if previous_day_all_records_in_group.exists() == True:
        mental_scores_in_group = np.array(mental_scores_in_group)
    mean_organization_all = np.mean(mental_scores_organization_all)
    if previous_day_all_records_in_group.exists() == True:
        mean_in_group = np.mean(mental_scores_in_group)
    std_organization_all = np.std(mental_scores_organization_all)
    if previous_day_all_records_in_group.exists() == True:
        std_in_group = np.std(mental_scores_in_group)
    x = np.linspace(-2 * question_count, 2 * 2 * question_count, (abs(-2) + (2 + 2)) * question_count)
    pd_organization_all = scipy.stats.norm.pdf(x, mean_organization_all, std_organization_all)
    if previous_day_all_records_in_group.exists() == True:
        pd_in_group = scipy.stats.norm.pdf(x, mean_in_group, std_in_group)

    fig, ax = plt.subplots()
    ax.plot(x, pd_organization_all, label='組織全体')
    if previous_day_all_records_in_group.exists() == True:
        ax.plot(x, pd_in_group, label='グループ（{}）内'.format('・'.join(main_user.groups.all().values_list('name', flat=True))))
    if previous_day_all_records_in_group.exists() == True:
        pd = np.concatenate([pd_organization_all, pd_in_group])
    else:
        pd = pd_organization_all
    ax.vlines(previous_day_records_user[0].mental_score_at_entry + previous_day_records_user[0].mental_score_at_leave, 0, np.nanmax(pd), linestyles='dotted', label='{}さんのスコア'.format(main_user.full_name))
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
    ax.tick_params(labelsize=10)
    ax.set_title('メンタルスコアの正規分布グラフ（{}のデータ）'.format(data_condition_used[0]), fontsize=14)
    ax.set_xlabel('メンタルスコア')
    ax.set_ylabel('割\n合', rotation=0, va='center', labelpad=12)
    ax.legend(loc='best')
    return output_graph(fig)
