// Sample selection management across pagination
function initializeSampleSelection(storageKey) {
    // Store selected sample IDs across page navigation
    let selectedSamples = JSON.parse(sessionStorage.getItem(storageKey) || '[]');

    // Restore previously selected checkboxes
    document.querySelectorAll('.sample-checkbox').forEach(function(checkbox) {
        if (selectedSamples.includes(checkbox.value)) {
            checkbox.checked = true;
        }
    });

    // Add hidden inputs for previously selected samples not on current page
    function addHiddenInputs() {
        selectedSamples.forEach(function(sampleId) {
            if (!document.querySelector('.sample-checkbox[value="' + sampleId + '"]')) {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'selected_samples';
                hiddenInput.value = sampleId;
                hiddenInput.classList.add('persistent-selection');
                document.querySelector('form').appendChild(hiddenInput);
            }
        });
    }

    // Update hidden inputs for selections from other pages
    function updatePersistentInputs() {
        // Remove existing hidden inputs
        document.querySelectorAll('.persistent-selection').forEach(el => el.remove());
        // Re-add them
        addHiddenInputs();
        updateSelectionCounter();
    }

    // Update select all checkbox based on current page selections
    function updateSelectAllCheckbox() {
        const checkboxes = document.querySelectorAll('.sample-checkbox');
        const checkedBoxes = document.querySelectorAll('.sample-checkbox:checked');
        const selectAll = document.getElementById('select-all-checkbox');

        if (checkboxes.length > 0 && selectAll) {
            selectAll.checked = checkboxes.length === checkedBoxes.length && checkboxes.length > 0;
            selectAll.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < checkboxes.length;
        }
    }

    // Update selection counter
    function updateSelectionCounter() {
        const counter = document.getElementById('selection-count');
        const number = document.getElementById('selection-number');
        if (counter && number) {
            if (selectedSamples.length > 0) {
                counter.style.display = 'inline-block';
                number.textContent = selectedSamples.length;
            } else {
                counter.style.display = 'none';
            }
        }
    }

    // Handle individual checkbox changes
    document.querySelectorAll('.sample-checkbox').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                if (!selectedSamples.includes(this.value)) {
                    selectedSamples.push(this.value);
                }
            } else {
                const index = selectedSamples.indexOf(this.value);
                if (index > -1) {
                    selectedSamples.splice(index, 1);
                }
            }
            sessionStorage.setItem(storageKey, JSON.stringify(selectedSamples));
            updatePersistentInputs();
            updateSelectAllCheckbox();
        });
    });

    // Handle select all checkbox
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('click', function(event) {
            const isChecked = event.target.checked;
            document.querySelectorAll('.sample-checkbox').forEach(function(checkbox) {
                checkbox.checked = isChecked;
                if (isChecked) {
                    if (!selectedSamples.includes(checkbox.value)) {
                        selectedSamples.push(checkbox.value);
                    }
                } else {
                    const index = selectedSamples.indexOf(checkbox.value);
                    if (index > -1) {
                        selectedSamples.splice(index, 1);
                    }
                }
            });
            sessionStorage.setItem(storageKey, JSON.stringify(selectedSamples));
            updatePersistentInputs();
        });
    }

    // Clear selections when export is complete
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Small delay to ensure form submission completes
            setTimeout(function() {
                sessionStorage.removeItem(storageKey);
            }, 500);
        });
    }

    // Initialize on load
    addHiddenInputs();
    updateSelectAllCheckbox();
    updateSelectionCounter();
}