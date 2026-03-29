from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.ota.infrastructure.orm_models import MobileApp, AppUpdate
from apps.ota.interfaces.ui.forms import MobileAppForm, AppUpdateForm
from django.contrib.admin.views.decorators import staff_member_required

def dashboard(request):
    apps = MobileApp.objects.all()
    return render(request, "dashboard/dashboard.html", {"apps": apps})

def app_create(request):
    if request.method == "POST":
        form = MobileAppForm(request.POST)
        if form.is_valid():
            app = form.save()
            messages.success(request, f"App '{app.name}' created successfully!")
            return redirect("admin:index")
    else:
        form = MobileAppForm()
    
    return render(request, "dashboard/create_app.html", {"form": form})

def app_detail(request, pk):
    app = get_object_or_404(MobileApp, pk=pk)
    
    if request.method == "POST":
        form = AppUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            update = form.save(commit=False)
            update.app = app
            update.save()
            messages.success(request, f"Version {update.version} uploaded successfully!")
            return redirect("admin:ui_app_detail", pk=app.pk)
        else:
            messages.error(request, "Failed to upload APK. Please check the form below.")
    else:
        form = AppUpdateForm()
        
    updates = app.updates.all()
    
    return render(request, "dashboard/app_detail.html", {
        "app": app,
        "form": form,
        "updates": updates,
    })
