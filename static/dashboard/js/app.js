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
                btn.textContent = 'Failed';
                setTimeout(() => btn.textContent = 'Copy', 1500);
            }
        });
    });
});

// Simple upload progress indicator (non-XHR): show spinner on submit
document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector('#upload form');
    if (!form) return;
    const submitBtn = document.getElementById('upload-submit');
    const progress = document.getElementById('upload-progress');
    form.addEventListener('submit', () => {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading…';
        }
        if (progress) progress.style.display = 'inline';
    });
});

