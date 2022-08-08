import datetime

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.signing import TimestampSigner
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import *

# Create your views here.

ALLOW_USER_TO_CHANGE_USERNAME = getattr(settings, 'ALLOW_USER_TO_CHANGE_USERNAME', False)


@login_required
def user_information_change(request):
    if request.method == 'POST':
        if ALLOW_USER_TO_CHANGE_USERNAME == True:
            form = CustomUserChangeForm(request.POST, instance=request.user)
        else:
            form = LimitedUserChangeForm(request.POST, instance=request.user)
        changed = None
        if form.is_valid():
            if form.changed_data == []:
                changed = False
            else:
                form.save()
                changed = True
        return render(request, 'account/user_information_change.html', {'form': form, 'changed': changed})
    else:
        if ALLOW_USER_TO_CHANGE_USERNAME == True:
            form = CustomUserChangeForm(instance=request.user)
        else:
            form = LimitedUserChangeForm(instance=request.user)
        return render(request, 'account/user_information_change.html', {'form': form})


@login_required
def issue_tokens(request):
    if 'finished' in request.GET:
        finished = request.GET['finished'] == '1' or request.GET['finished'] == '2'
    else:
        finished = False
    if finished == True:
        return HttpResponse()
    else:
        signer = TimestampSigner()
        if request.method == 'GET':
            try:
                if 'issue_tokens_transaction_id' in request.session and 'tr' in request.GET:
                    if request.session['issue_tokens_transaction_id'] == request.GET['tr']:
                        del request.session['issue_tokens_transaction_id']
                        token = signer.unsign_object(request.GET['tr'], max_age=datetime.timedelta(minutes=5))
                        if token != request.user.pk:
                            raise Exception()
                        refresh_token = RefreshToken.for_user(request.user)
                        access_token = refresh_token.access_token
                        redirect_url = reverse('issue_tokens')
                        return redirect(redirect_url + '?finished=1&access=' + str(access_token) + '&refresh=' + str(refresh_token))
            except Exception as e:
                # raise e
                pass
        elif request.method == 'POST':
            request_user = request.user
            logout(request)
            request.session['issue_tokens_transaction_id'] = signer.sign_object(request_user.pk)
            redirect_url = reverse('issue_tokens')
            return redirect(redirect_url + '?tr=' + request.session['issue_tokens_transaction_id'])
        return render(request, 'account/issue_tokens.html')
