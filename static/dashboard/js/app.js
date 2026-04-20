document.addEventListener("DOMContentLoaded", function () {
    const dropzones = document.querySelectorAll(".dropzone");

    dropzones.forEach(dropzone => {
        const input = dropzone.querySelector("input[type='file']");
        const defaultText = dropzone.querySelector(".dropzone-text");
        const hintText = dropzone.querySelector(".dropzone-hint");

        // Drag events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.add("dragover");
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.remove("dragover");
            }, false);
        });

        // Drop handling
        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length) {
                input.files = files; // Assign files to input
                updateFileInfo(files[0]);
            }
        });

        // Click handling
        input.addEventListener("change", (e) => {
            if (input.files.length) {
                updateFileInfo(input.files[0]);
            }
        });

        // Keyboard accessibility
        dropzone.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                input.click();
            }
        });

        // Highlight dropzone on validation errors
        if (dropzone.parentElement.querySelector('.dropzone-error')) {
            dropzone.classList.add('dropzone-error-state');
        }

        function updateFileInfo(file) {
            defaultText.textContent = file.name;
            const sizeInMb = (file.size / (1024 * 1024)).toFixed(2);
            hintText.innerHTML = `<span style="color:var(--success)">File ready to upload (${sizeInMb} MB) — max 500 MB</span>`;
        }
    });
});

// Overflow menu (three-dot) toggle for app cards
document.addEventListener("DOMContentLoaded", function () {
    // Delegate to all .more-btn buttons
    const moreButtons = document.querySelectorAll('.more-btn');

    moreButtons.forEach(btn => {
        const container = btn.closest('.more-menu');
        const dropdown = container && container.querySelector('.more-dropdown');

        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = dropdown.style.display === 'block';
            // Close any other open dropdowns
            document.querySelectorAll('.more-dropdown').forEach(d => d.style.display = 'none');
            dropdown.style.display = isOpen ? 'none' : 'block';
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function (e) {
        document.querySelectorAll('.more-dropdown').forEach(d => d.style.display = 'none');
    });
});

// Select-all checkboxes
document.addEventListener("DOMContentLoaded", function () {
    const selectAll = document.getElementById('select-all');
    if (!selectAll) return;
    const checkboxes = document.querySelectorAll('.release-checkbox');
    selectAll.addEventListener('change', () => {
        checkboxes.forEach(cb => { cb.checked = selectAll.checked; });
    });
});

// Copy buttons (checksum and URL)
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const val = btn.getAttribute('data-copy');
            try {
                await navigator.clipboard.writeText(val);
                btn.textContent = 'Copied';
                setTimeout(() => btn.textContent = 'Copy', 1500);
            } catch (err) {
                // Fallback for browsers that don't support clipboard API
                const textArea = document.createElement('textarea');
                textArea.value = val;
                textArea.style.position = 'fixed';
                textArea.style.left = '-9999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {
                    document.execCommand('copy');
                    btn.textContent = 'Copied';
                } catch (fallbackErr) {
                    btn.textContent = 'Failed';
                }
                document.body.removeChild(textArea);
                setTimeout(() => btn.textContent = 'Copy', 1500);
            }
        });
    });
});

// Chunked upload with real progress bar
document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector('#upload form');
    if (!form) return;

    const CHUNK_SIZE = 5 * 1024 * 1024; // 5 MB per chunk

    const submitBtn   = document.getElementById('upload-submit');
    const progressWrap = document.getElementById('upload-progress-wrap');
    const progressBar  = document.getElementById('upload-progress-bar');
    const progressPct  = document.getElementById('upload-progress-pct');
    const progressMsg  = document.getElementById('upload-progress-msg');

    function setProgress(pct, msg) {
        if (progressBar) progressBar.style.width = pct + '%';
        if (progressPct) progressPct.textContent = pct + '%';
        if (progressMsg) progressMsg.textContent = msg;
    }

    function showError(msg) {
        setProgress(0, msg);
        if (progressBar) progressBar.classList.add('progress-bar-error');
        if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Upload Release'; }
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const fileInput = form.querySelector('input[type="file"][name="apk_file"]');
        const file = fileInput && fileInput.files[0];
        const version = form.querySelector('[name=version]').value.trim();

        // Fallback to normal submit if JS chunking is unavailable
        if (!file || !version || !form.dataset.initUrl) {
            form.submit();
            return;
        }

        const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Uploading…'; }
        if (progressWrap) progressWrap.style.display = 'block';
        if (progressBar) progressBar.classList.remove('progress-bar-error');
        setProgress(0, 'Initializing…');

        try {
            // 1. Init
            const initRes = await fetch(form.dataset.initUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
                body: new URLSearchParams({
                    app_pk: form.dataset.appPk,
                    filename: file.name,
                    total_chunks: totalChunks,
                }),
            });
            if (!initRes.ok) { showError('Init failed — server error.'); return; }
            const { upload_id, error: initErr } = await initRes.json();
            if (initErr) { showError(initErr); return; }

            // 2. Upload chunks
            for (let i = 0; i < totalChunks; i++) {
                const start = i * CHUNK_SIZE;
                const fd = new FormData();
                fd.append('upload_id', upload_id);
                fd.append('chunk_index', i);
                fd.append('chunk', file.slice(start, start + CHUNK_SIZE), file.name);

                const chunkRes = await fetch(form.dataset.chunkUrl, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrf },
                    body: fd,
                });
                if (!chunkRes.ok) { showError(`Chunk ${i + 1}/${totalChunks} failed.`); return; }

                const pct = Math.round(((i + 1) / totalChunks) * 85);
                setProgress(pct, `Uploading… ${i + 1} / ${totalChunks} chunks`);
            }

            // 3. Complete
            setProgress(90, 'Saving release…');
            const fd = new FormData();
            fd.append('upload_id', upload_id);
            fd.append('version', version);
            fd.append('force_update', form.querySelector('[name=force_update]').checked ? 'true' : 'false');
            fd.append('changelog', form.querySelector('[name=changelog]').value);

            const completeRes = await fetch(form.dataset.completeUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
                body: fd,
            });
            const result = await completeRes.json();
            if (!completeRes.ok || result.error) { showError(result.error || 'Complete failed.'); return; }

            setProgress(100, 'Upload complete! Redirecting…');
            setTimeout(() => { window.location.href = result.redirect; }, 600);

        } catch (err) {
            showError('Upload failed: ' + err.message);
        }
    });
});
