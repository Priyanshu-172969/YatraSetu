/**
 * YatraSetu: Vanilla JavaScript Interactions
 * Handles delete confirmation modals, client-side validation, flash alerts, and stop ordering.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Flash alert auto-dismiss & close button
    const alertCloseButtons = document.querySelectorAll('.alert-close');
    alertCloseButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const alert = this.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 200);
            }
        });
    });

    // 2. Generic Confirmation Modal for Deletion
    const deleteModal = document.getElementById('deleteConfirmModal');
    const deleteForm = document.getElementById('deleteConfirmForm');
    const deleteItemNameSpan = document.getElementById('deleteItemName');
    const deleteCancelBtn = document.getElementById('deleteCancelBtn');
    const deleteWarningText = document.getElementById('deleteWarningText');

    if (deleteModal) {
        // Open modal on clicking any trigger with .btn-delete-trigger
        const deleteTriggers = document.querySelectorAll('.btn-delete-trigger');
        deleteTriggers.forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                const actionUrl = this.getAttribute('data-action');
                const itemName = this.getAttribute('data-name') || 'this item';
                const warningMsg = this.getAttribute('data-warning') || 'This action cannot be undone.';

                if (deleteForm) deleteForm.setAttribute('action', actionUrl);
                if (deleteItemNameSpan) deleteItemNameSpan.textContent = itemName;
                if (deleteWarningText) deleteWarningText.textContent = warningMsg;

                deleteModal.classList.add('active');
            });
        });

        // Close modal on Cancel
        if (deleteCancelBtn) {
            deleteCancelBtn.addEventListener('click', function () {
                deleteModal.classList.remove('active');
            });
        }

        // Close on clicking outside modal-box
        deleteModal.addEventListener('click', function (e) {
            if (e.target === deleteModal) {
                deleteModal.classList.remove('active');
            }
        });
    }

    // 3. Client-side form validation helper
    const validatedForms = document.querySelectorAll('.needs-validation');
    validatedForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            let isValid = true;
            const requiredInputs = form.querySelectorAll('[required]');

            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            // Specific check for positive duration numbers
            const durationInputs = form.querySelectorAll('input[type="number"][name*="days"]');
            durationInputs.forEach(input => {
                if (parseInt(input.value) <= 0) {
                    isValid = false;
                    input.classList.add('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill out all required fields with valid values before submitting.');
            }
        });
    });

    // 4. Quick filter reset helper
    const clearFilterBtn = document.getElementById('clearFiltersBtn');
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', function () {
            const form = this.closest('form');
            if (form) {
                form.querySelectorAll('input[type="text"]').forEach(i => i.value = '');
                form.querySelectorAll('select').forEach(s => s.selectedIndex = 0);
                form.submit();
            }
        });
    }
});
