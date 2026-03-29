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

        function updateFileInfo(file) {
            defaultText.textContent = file.name;
            const sizeInMb = (file.size / (1024 * 1024)).toFixed(2);
            hintText.innerHTML = `<span style="color:var(--success)">File ready to upload (${sizeInMb} MB)</span>`;
        }
    });
});
