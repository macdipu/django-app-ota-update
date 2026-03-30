from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from apps.ota.infrastructure.orm_models import MobileApp, AppUpdate
from apps.ota.interfaces.ui.forms import MobileAppForm, AppUpdateForm
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required


def _delete_release_file(file_field):
    if not file_field:
        return
    try:
        file_field.storage.delete(file_field.name)
    except FileNotFoundError:
        # Ignore missing local files to match previous behavior
        pass


@staff_member_required
def app_delete(request, pk):
    """Confirmation page (GET) and deletion (POST) for a MobileApp."""
    app = get_object_or_404(MobileApp, pk=pk)

    if request.method == "POST":
        # Extra safety: require a checkbox named "confirm" to be present
        if request.POST.get("confirm") == "yes":
            # Remove APK files for all releases belonging to this app
            for rel in app.updates.all():
                _delete_release_file(rel.apk_file)

            app_name = app.name
            app.delete()
            messages.success(request, f"App '{app_name}' and its releases were deleted.")
            return redirect("ota_admin:index")
        else:
            messages.error(request, "Deletion cancelled — confirmation not checked.")
            return redirect("ota_admin:index")

    return render(request, "dashboard/confirm_delete_app.html", {"app": app})


@staff_member_required
def release_delete(request, app_pk, pk):
    """Confirmation page (GET) and deletion (POST) for an AppUpdate (release)."""
    app = get_object_or_404(MobileApp, pk=app_pk)
    release = get_object_or_404(AppUpdate, pk=pk, app=app)

    if request.method == "POST":
        if request.POST.get("confirm") == "yes":
            # Remove APK file from storage
            _delete_release_file(release.apk_file)

            version = release.version
            release.delete()
            messages.success(request, f"Release {version} deleted.")
            return redirect("ota_admin:ui_app_detail", pk=app.pk)
        else:
            messages.error(request, "Deletion cancelled — confirmation not checked.")
            return redirect("ota_admin:ui_app_detail", pk=app.pk)

    return render(request, "dashboard/confirm_delete_release.html", {"app": app, "release": release})


@staff_member_required
def release_bulk_delete(request, app_pk):
    app = get_object_or_404(MobileApp, pk=app_pk)
    if request.method != "POST":
        return redirect("ota_admin:ui_app_detail", pk=app.pk)

    ids = request.POST.getlist("release_ids")
    releases = app.updates.filter(pk__in=ids)
    count = releases.count()
    for rel in releases:
        _delete_release_file(rel.apk_file)
    releases.delete()
    if count:
        messages.success(request, f"Deleted {count} release(s).")
    else:
        messages.info(request, "No releases selected for deletion.")
    return redirect("ota_admin:ui_app_detail", pk=app.pk)


@staff_member_required
def release_pin(request, app_pk, pk):
    app = get_object_or_404(MobileApp, pk=app_pk)
    release = get_object_or_404(AppUpdate, pk=pk, app=app)
    if request.method == "POST":
        release.is_pinned = not release.is_pinned
        release.save(update_fields=["is_pinned"])
        state = "pinned" if release.is_pinned else "unpinned"
        messages.success(request, f"Release {release.version} {state}.")
    return redirect("ota_admin:ui_app_detail", pk=app.pk)

@staff_member_required
def app_create(request):
    if request.method == "POST":
        form = MobileAppForm(request.POST)
        if form.is_valid():
            app = form.save()
            messages.success(request, f"App '{app.name}' created successfully!")
            return redirect("ota_admin:index")
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
            messages.success(request, f"Version {update.version} uploaded successfully! Storage key: {update.apk_file.name}")
            return redirect("ota_admin:ui_app_detail", pk=app.pk)
        else:
            messages.error(request, "Failed to upload APK. Please check the form below.")
    else:
        form = AppUpdateForm()
        
    query = request.GET.get("q", "").strip()
    force_filter = request.GET.get("force", "")

    updates = app.updates.all()
    if query:
        updates = updates.filter(Q(version__icontains=query) | Q(changelog__icontains=query))
    if force_filter == "1":
        updates = updates.filter(force_update=True)

    updates = updates.order_by("-is_pinned", "-created_at")
    updates = list(updates)
    latest = app.updates.order_by("-created_at").first()
    last_upload_ts = latest.created_at if latest else None
    storage_backend = getattr(settings, "DEFAULT_FILE_STORAGE", "django.core.files.storage.FileSystemStorage")

    for rel in updates:
        download_path = reverse("ota-download", args=[rel.pk])
        rel.download_url = request.build_absolute_uri(download_path)
    
    return render(request, "dashboard/app_detail.html", {
        "app": app,
        "form": form,
        "updates": updates,
        "latest": latest,
        "last_upload_ts": last_upload_ts,
        "query": query,
        "force_filter": force_filter,
        "storage_backend": storage_backend,
    })
