from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as login_procedure, logout as logout_procedure
from .models import Token
import binascii, os

# Create your views here.
def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        return render(request, 'app/index.html', {'token':get_token(request.user)})

def generate_token():
    return binascii.hexlify(os.urandom(10)).decode('utf8')

def save_token(user):
    try:
        t = Token.objects.get(user=user)
        t.token = generate_token()
        t.save()
    except Token.DoesNotExist:
        t = Token.objects.create(user=user, token=generate_token())

def get_token(user):
    return Token.objects.get(user=user).token

def login(request):
    data={
        'username':request.POST.get('username',''),
        'password':request.POST.get('password','')
    }

    if(len(data['username'])==0 and len(data['password'])==0):
        data['error_message'] = 'Fill username or password'
    else:
        user = authenticate(request, username=data['username'], password=data['password'])
        if user is not None:
            save_token(user)
            login_procedure(request, user)
            return redirect('index')
        else:
            data['error_message']='Invalid username or password'

    return render(request, 'app/login.html', data)

def logout(request):
    logout_procedure(request)
    return redirect('login')