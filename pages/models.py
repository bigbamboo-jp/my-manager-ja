from accounts.models import CustomUser
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.


class AttendanceRecord(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='ユーザー (user)')
    entry_time = models.DateTimeField(verbose_name='出席時刻 (entry_time)')
    leave_time = models.DateTimeField(blank=True, null=True, verbose_name='退席時刻 (leave_time)')
    mental_score_at_entry = models.IntegerField(blank=True, null=True, verbose_name='出席時のメンタルスコア (mental_score_at_entry)')
    mental_score_at_leave = models.IntegerField(blank=True, null=True, verbose_name='退席時のメンタルスコア (mental_score_at_leave)')
    mental_rank_at_entry = models.CharField(max_length=100, verbose_name='出席時のメンタルランク (mental_rank_at_entry)')
    mental_rank_at_leave = models.CharField(max_length=100, blank=True, verbose_name='退席時のメンタルランク (mental_rank_at_leave)')
    notes = models.TextField(blank=True, verbose_name='備考 (notes)')
    other_service_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='Airtable レコードID (other_service_id)', help_text='システムで使用します（通常、変更の必要はありません）。')

    class Meta:
        verbose_name = '出席記録'
        verbose_name_plural = '出席記録'

    def __str__(self) -> str:
        label = self.user.full_name + '｜' + self.entry_time.strftime('%Y/%m/%d') + '｜' + self.entry_time.strftime('%H:%M') + '～'
        if self.leave_time is not None:
            label += self.leave_time.strftime('%H:%M')
        return label


class Question(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content = models.CharField(max_length=100, verbose_name='質問文 (content)')
    description = models.TextField(max_length=1000, blank=True, verbose_name='質問の説明文 (description)')
    enabled_when_entry = models.BooleanField(verbose_name='出席時に使用 (enabled_when_entry)', help_text='※使用するにはselection_targetも有効になっている必要があります。')
    enabled_when_leave = models.BooleanField(verbose_name='退席時に使用 (enabled_when_leave)', help_text='※使用するにはselection_targetも有効になっている必要があります。')
    selection_target = models.BooleanField(verbose_name='選択対象にする (selection_target)', help_text='※enabled_when_entryまたはenabled_when_leaveが有効になっていないと選択されません。')
    constantly_first = models.BooleanField(verbose_name='（最初に）必ず使用する (constantly_first)')
    constantly_last = models.BooleanField(verbose_name='（最後に）必ず使用する (constantly_last)')

    class Meta:
        verbose_name = '質問'
        verbose_name_plural = '質問'

    @property
    def marks(self) -> str:
        marks = []
        if self.selection_target == True:
            if self.enabled_when_entry == True:
                marks.append('Ⓔ')
            if self.enabled_when_leave == True:
                marks.append('Ⓛ')
            if self.constantly_first == True or self.constantly_last == True:
                marks.append('Ⓒ')
        return marks

    def clean(self):
        if self.constantly_first == True and self.constantly_last == True:
            raise ValidationError('constantly_firstとconstantly_lastを両方有効にすることはできません。')
        if (self.constantly_first == True or self.constantly_last == True) and self.selection_target == False:
            raise ValidationError('constantly_firstまたはconstantly_lastを有効にする場合はselection_targetも有効にする必要があります。')


class Option(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content = models.CharField(max_length=100, verbose_name='選択肢のテキスト (content)')
    effect = models.CharField(max_length=100, blank=True, verbose_name='選択肢のエフェクト (effect)', help_text='以下の２種類のエフェクトが使用可能です（エフェクトは１つだけ設定できます）。<br/>・gotoエフェクト<br/>　このエフェクトは任意の質問へリンクする機能を提供します。ユーザーがこのエフェクトを設定している選択肢を選ぶと、スコアの変更（パフォーマンス測定によるものを含む）を行わずに指定された質問に移ります。<br/>　※リンクされた質問は質問数のカウントの対象になりません。そのため、このエフェクトを多用するとユーザーが記録する際の所要時間が増加します。<br/>　記述例：#goto#1（1は質問のID）<br/>・scoreエフェクト<br/>　このエフェクトはユーザーのメンタルスコアを加算する機能を提供します。ユーザーがこのエフェクトを設定している選択肢を選ぶと、スコアの変更（パフォーマンス測定によるものを含む）を行って質問リストの次の質問に移ります。<br/>　※スコアの加算を行わずに質問リストの次の質問に移るようにしたい場合はエフェクトに何も指定しないでください。<br/>　記述例：#score#5（5は加算するスコア）')
    '''
    以下の２種類のエフェクトが使用可能です（エフェクトは１つだけ設定できます）。
    ・gotoエフェクト
    　このエフェクトは任意の質問へリンクする機能を提供します。ユーザーがこのエフェクトを設定している選択肢を選ぶと、スコアの変更（パフォーマンス測定によるものを含む）を行わずに指定された質問に移ります。
    　※リンクされた質問は質問数のカウントの対象になりません。そのため、このエフェクトを多用するとユーザーが記録する際の所要時間が増加します。
    　記述例：#goto#1（1は質問のID）
    ・scoreエフェクト
    　このエフェクトはユーザーのメンタルスコアを加算する機能を提供します。ユーザーがこのエフェクトを設定している選択肢を選ぶと、スコアの変更（パフォーマンス測定によるものを含む）を行って質問リストの次の質問に移ります。
    　※スコアの加算を行わずに質問リストの次の質問に移るようにしたい場合はエフェクトに何も指定しないでください。
    　記述例：#score#5（5は加算するスコア）
    '''

    class Meta:
        verbose_name = '選択式質問の選択肢'
        verbose_name_plural = '選択式質問の選択肢'

    def __str__(self) -> str:
        if len((marks := self.marks)) == 0:
            return str(self.pk) + '：' + self.content
        else:
            return str(self.pk) + '｜' + ''.join(reversed(marks)) + '：' + self.content

    @property
    def marks(self) -> str:
        marks = []
        if self.effect.startswith('#goto#') == True:
            marks.append('Ⓖ')
        if self.effect.startswith('#score#') == True:
            marks.append('Ⓟ')
        return marks


class ChoiceQuestion(Question):
    options = ArrayField(models.IntegerField(), verbose_name='選択肢のリスト (options)', help_text='それぞれの選択肢のIDを半角カンマ区切りで入力してください。<br/>例：1,2,3')
    answer_time_data = ArrayField(models.IntegerField(), blank=True)

    class Meta:
        verbose_name = '選択式質問'
        verbose_name_plural = '選択式質問'

    def __str__(self) -> str:
        if len((marks := self.marks)) == 0:
            return str(self.pk) + '：' + self.content
        else:
            return str(self.pk) + '｜' + ''.join(reversed(marks)) + '：' + self.content

    @property
    def marks(self) -> str:
        marks = super().marks
        marks.append('Ⓢ')
        return marks


class InputQuestion(Question):
    is_number = models.BooleanField(verbose_name='入力値を数値（少数を含む）に限定する (is_number)')
    positive_number_only = models.BooleanField(verbose_name='（is_numberが有効の場合に）負の数の入力を禁止する (positive_number_only)')
    input_box_placeholder = models.CharField(max_length=100, blank=True, null=True, verbose_name='入力欄のプレースホルダー (input_box_placeholder)')
    data_suffix = models.CharField(max_length=100, blank=True, verbose_name='入力値の単位 (data_suffix)', help_text='例：個、人、円')
    record_template = models.CharField(max_length=100, verbose_name='入力値記録用テンプレート (record_template)', help_text='テンプレートにデータを埋め込んだ値が備考欄に記載されます。テンプレート内の入力値を埋め込みたい場所に「{value}」を入れてください。')

    class Meta:
        verbose_name = '入力式質問'
        verbose_name_plural = '入力式質問'

    def __str__(self) -> str:
        if len((marks := self.marks)) == 0:
            return str(self.pk) + '：' + self.content
        else:
            return str(self.pk) + '｜' + ''.join(reversed(marks)) + '：' + self.content

    @property
    def marks(self) -> str:
        marks = super().marks
        marks.append('Ⓦ')
        return marks

    def clean(self):
        if self.is_number == False and self.positive_number_only == True:
            raise ValidationError('positive_number_onlyを有効にする場合はis_numberも有効にする必要があります。')


class TemporaryQuestionSet(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    situation = models.IntegerField()
    questions = ArrayField(models.IntegerField(), blank=True, verbose_name='質問のリスト (questions)', help_text='この値は各質問のIDを使用する順番で並べたものです。')

    def __str__(self) -> str:
        if self.situation == 0:
            return '出席時に使用'
        else:
            return '退席時に使用'

    class Meta:
        verbose_name = '質問リスト (当日中有効)'
        verbose_name_plural = '質問リスト (当日中有効)'
