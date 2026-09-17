from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect("/login/")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})

# Create your views here.
