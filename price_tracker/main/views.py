from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm


def main(request):
    return render(request, "main/index.html")


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})
