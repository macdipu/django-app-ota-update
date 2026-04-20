import hashlib
import json
import shutil
import tempfile
import uuid
from pathlib import Path

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files import File
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.ota.infrastructure.orm_models import (
    MAX_APK_SIZE_BYTES,
    MAX_APK_SIZE_MB,
    AppUpdate,
    MobileApp,
    apk_upload_path,
)
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from apps.ota.interfaces.ui.forms import AppUpdateForm, MobileAppForm, UserCreateForm, UserEditForm
from apps.ota.infrastructure.storage import storage_service

_UPLOAD_TMP = Path(tempfile.gettempdir()) / "ota_uploads"


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
        form = MobileAppForm(request.POST, request.FILES)
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
            try:
                update.refresh_from_db()
            except Exception:
                pass
            bn = getattr(update, "build_number", None)
            bn_str = f" (build #{bn})" if bn is not None else ""
            messages.success(request, f"Version {update.version}{bn_str} uploaded successfully! Storage key: {update.apk_file.name}")
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
    # Compute the next build number we expect to assign for the app (max existing + 1)
    try:
        agg = app.updates.aggregate(max_bn=Max("build_number"))
        max_bn = agg.get("max_bn")
        next_build_number = (max_bn or 0) + 1
    except Exception:
        next_build_number = None

    for rel in updates:
        if getattr(rel, "public_id", None):
            try:
                download_path = reverse("ota-download", args=[app.package_name, rel.public_id])
                rel.download_url = request.build_absolute_uri(download_path)
            except Exception:
                try:
                    rel.download_url = storage_service.url(rel.apk_file.name)
                except Exception:
                    try:
                        rel.download_url = rel.apk_file.url
                    except Exception:
                        rel.download_url = ""
            try:
                share_path = reverse("release-landing", args=[app.package_name, rel.public_id])
                rel.share_url = request.build_absolute_uri(share_path)
            except Exception:
                rel.share_url = rel.download_url
        else:
            try:
                rel.download_url = storage_service.url(rel.apk_file.name)
            except Exception:
                try:
                    rel.download_url = rel.apk_file.url
                except Exception:
                    rel.download_url = ""
            rel.share_url = rel.download_url

        try:
            rel.file_size_cached = rel.apk_file.size
        except Exception:
            rel.file_size_cached = None

    return render(request, "dashboard/app_detail.html", {
        "app": app,
        "form": form,
        "updates": updates,
        "latest": latest,
        "last_upload_ts": last_upload_ts,
        "query": query,
        "force_filter": force_filter,
        "next_build_number": next_build_number,
    })


# ---------------------------------------------------------------------------
# Chunked upload endpoints
# ---------------------------------------------------------------------------

@staff_member_required
def user_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    users = User.objects.order_by("username")
    return render(request, "dashboard/users.html", {"users": users})


@staff_member_required
def user_create(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email", ""),
                password=form.cleaned_data["password"],
            )
            user.is_staff = form.cleaned_data.get("is_staff", False)
            user.is_superuser = form.cleaned_data.get("is_superuser", False)
            user.save()
            messages.success(request, f"User '{user.username}' created.")
            return redirect("ota_admin:ui_user_list")
    else:
        form = UserCreateForm()
    return render(request, "dashboard/user_form.html", {"form": form, "action": "Create"})


@staff_member_required
def user_edit(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    edit_user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserEditForm(request.POST)
        if form.is_valid():
            edit_user.username = form.cleaned_data["username"]
            edit_user.email = form.cleaned_data.get("email", "")
            edit_user.is_staff = form.cleaned_data.get("is_staff", False)
            edit_user.is_superuser = form.cleaned_data.get("is_superuser", False)
            edit_user.is_active = form.cleaned_data.get("is_active", True)
            if form.cleaned_data.get("new_password"):
                edit_user.set_password(form.cleaned_data["new_password"])
            edit_user.save()
            messages.success(request, f"User '{edit_user.username}' updated.")
            return redirect("ota_admin:ui_user_list")
    else:
        form = UserEditForm(initial={
            "username": edit_user.username,
            "email": edit_user.email,
            "is_staff": edit_user.is_staff,
            "is_superuser": edit_user.is_superuser,
            "is_active": edit_user.is_active,
        })
    return render(request, "dashboard/user_form.html", {"form": form, "action": "Edit", "edit_user": edit_user})


@staff_member_required
def user_delete(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    edit_user = get_object_or_404(User, pk=pk)
    if edit_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("ota_admin:ui_user_list")
    if request.method == "POST":
        username = edit_user.username
        edit_user.delete()
        messages.success(request, f"User '{username}' deleted.")
        return redirect("ota_admin:ui_user_list")
    return render(request, "dashboard/user_form.html", {"action": "Delete", "edit_user": edit_user})


# ---------------------------------------------------------------------------
# Chunked upload endpoints
# ---------------------------------------------------------------------------

@staff_member_required
@require_POST
def upload_init(request):
    """Step 1: create a temporary upload session, return upload_id."""
    try:
        app_pk = int(request.POST["app_pk"])
        filename = request.POST["filename"].strip()
        total_chunks = int(request.POST["total_chunks"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid parameters."}, status=400)

    if not filename.lower().endswith(".apk"):
        return JsonResponse({"error": "Only .apk files are allowed."}, status=400)

    upload_id = str(uuid.uuid4())
    tmp_dir = _UPLOAD_TMP / upload_id
    tmp_dir.mkdir(parents=True, exist_ok=True)

    meta = {"app_pk": app_pk, "filename": filename, "total_chunks": total_chunks}
    (tmp_dir / "meta.json").write_text(json.dumps(meta))

    return JsonResponse({"upload_id": upload_id})


@staff_member_required
@require_POST
def upload_chunk(request):
    """Step 2: receive and persist one chunk to temp storage."""
    try:
        upload_id = request.POST["upload_id"]
        chunk_index = int(request.POST["chunk_index"])
        chunk_file = request.FILES["chunk"]
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid parameters."}, status=400)

    tmp_dir = _UPLOAD_TMP / upload_id
    if not tmp_dir.exists():
        return JsonResponse({"error": "Unknown upload session."}, status=400)

    chunk_path = tmp_dir / f"{chunk_index}.chunk"
    with open(chunk_path, "wb") as f:
        for data in chunk_file.chunks():
            f.write(data)

    return JsonResponse({"received": chunk_index})


@staff_member_required
@require_POST
def upload_complete(request):
    """Step 3: assemble chunks, validate, save to storage, create AppUpdate."""
    upload_id = request.POST.get("upload_id", "")
    tmp_dir = _UPLOAD_TMP / upload_id

    if not tmp_dir.exists():
        return JsonResponse({"error": "Unknown upload session."}, status=400)

    try:
        meta = json.loads((tmp_dir / "meta.json").read_text())
    except Exception:
        return JsonResponse({"error": "Corrupt upload session."}, status=400)

    filename = meta["filename"]
    total_chunks = meta["total_chunks"]
    app = get_object_or_404(MobileApp, pk=meta["app_pk"])

    version = request.POST.get("version", "").strip()
    if not version:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return JsonResponse({"error": "Version is required."}, status=400)

    # Check for duplicate version
    if AppUpdate.objects.filter(app=app, version=version).exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return JsonResponse(
            {"error": f"Version {version} already exists for this app."}, status=400
        )

    force_update = request.POST.get("force_update", "false").lower() == "true"
    changelog = request.POST.get("changelog", "").strip()

    # Assemble chunks into a single file
    assembled_path = tmp_dir / filename
    try:
        with open(assembled_path, "wb") as out:
            for i in range(total_chunks):
                chunk_path = tmp_dir / f"{i}.chunk"
                with open(chunk_path, "rb") as cf:
                    shutil.copyfileobj(cf, out)
    except FileNotFoundError as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return JsonResponse({"error": f"Missing chunk: {exc}"}, status=400)

    # Validate assembled size
    file_size = assembled_path.stat().st_size
    if file_size > MAX_APK_SIZE_BYTES:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return JsonResponse(
            {"error": f"APK must not exceed {MAX_APK_SIZE_MB} MB."}, status=400
        )

    # Compute checksum locally before uploading to storage
    hasher = hashlib.sha256()
    with open(assembled_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            hasher.update(block)
    checksum = hasher.hexdigest()

    # Build the AppUpdate and upload file to storage
    update = AppUpdate(
        app=app,
        version=version,
        force_update=force_update,
        changelog=changelog,
        checksum_sha256=checksum,
    )
    storage_name = apk_upload_path(update, filename)

    try:
        with open(assembled_path, "rb") as f:
            # save=True triggers update.save() which sets build_number + public_id
            update.apk_file.save(storage_name, File(f), save=True)
    except Exception as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return JsonResponse({"error": f"Storage error: {exc}"}, status=500)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    try:
        update.refresh_from_db()
    except Exception:
        pass

    bn = getattr(update, "build_number", None)
    bn_str = f" (build #{bn})" if bn is not None else ""
    messages.success(
        request,
        f"Version {update.version}{bn_str} uploaded successfully! "
        f"Storage key: {update.apk_file.name}",
    )

    return JsonResponse(
        {"redirect": reverse("ota_admin:ui_app_detail", args=[app.pk])}
    )


# ---------------------------------------------------------------------------
# Public release landing page (no auth required)
# ---------------------------------------------------------------------------

def release_landing(request, package, public_id):
    release = get_object_or_404(AppUpdate, app__package_name=package, public_id=public_id)
    app = release.app

    try:
        download_url = request.build_absolute_uri(
            reverse("ota-download", args=[package, public_id])
        )
    except Exception:
        download_url = ""

    try:
        file_size = release.apk_file.size
    except Exception:
        file_size = None

    try:
        icon_url = app.icon.url if (app and app.icon) else None
    except Exception:
        icon_url = None

    return render(request, "release_landing.html", {
        "app": app,
        "release": release,
        "download_url": download_url,
        "file_size": file_size,
        "icon_url": icon_url,
    })
