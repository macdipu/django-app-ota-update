from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.ota.infrastructure.orm_models import MobileApp, AppUpdate
from apps.ota.interfaces.ui.forms import MobileAppForm, AppUpdateForm
from django.contrib.admin.views.decorators import staff_member_required
import os

from django.conf import settings


@staff_member_required
def app_delete(request, pk):
    """Confirmation page (GET) and deletion (POST) for a MobileApp."""
    app = get_object_or_404(MobileApp, pk=pk)

    if request.method == "POST":
        # Extra safety: require a checkbox named "confirm" to be present
        if request.POST.get("confirm") == "yes":
            # Remove APK files for all releases belonging to this app
            for rel in app.updates.all():
                try:
                    if rel.apk_file and hasattr(rel.apk_file, 'path'):
                        os.remove(rel.apk_file.path)
                except FileNotFoundError:
                    pass

            app_name = app.name
            app.delete()
            messages.success(request, f"App '{app_name}' and its releases were deleted.")
            return redirect("dashboard")
        else:
            messages.error(request, "Deletion cancelled — confirmation not checked.")
            return redirect("dashboard")

    return render(request, "dashboard/confirm_delete_app.html", {"app": app})


@staff_member_required
def release_delete(request, app_pk, pk):
    """Confirmation page (GET) and deletion (POST) for an AppUpdate (release)."""
    app = get_object_or_404(MobileApp, pk=app_pk)
    release = get_object_or_404(AppUpdate, pk=pk, app=app)

    if request.method == "POST":
        if request.POST.get("confirm") == "yes":
            # Remove APK file from storage
            try:
                if release.apk_file and hasattr(release.apk_file, 'path'):
                    os.remove(release.apk_file.path)
            except FileNotFoundError:
                pass

            version = release.version
            release.delete()
            messages.success(request, f"Release {version} deleted.")
            return redirect("dashboard_app_detail", pk=app.pk)
        else:
            messages.error(request, "Deletion cancelled — confirmation not checked.")
            return redirect("dashboard_app_detail", pk=app.pk)

    return render(request, "dashboard/confirm_delete_release.html", {"app": app, "release": release})

def dashboard(request):
    apps = MobileApp.objects.all()
    return render(request, "dashboard/dashboard.html", {"apps": apps})

def app_create(request):
    if request.method == "POST":
        form = MobileAppForm(request.POST)
        if form.is_valid():
            app = form.save()
            messages.success(request, f"App '{app.name}' created successfully!")
            return redirect("dashboard")
    else:
        form = MobileAppForm()
    
    return render(request, "dashboard/create_app.html", {"form": form})


@staff_member_required
def app_detail(request, pk):
    app = get_object_or_404(MobileApp, pk=pk)
    
    if request.method == "POST":
        form = AppUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            update = form.save(commit=False)
            update.app = app
            update.save()
            messages.success(request, f"Version {update.version} uploaded successfully!")
            return redirect("dashboard_app_detail", pk=app.pk)
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
