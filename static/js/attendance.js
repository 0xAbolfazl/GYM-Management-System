// static/js/attendance.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date picker with today's date
    const dateInput = document.getElementById('attendance-date');
    if (dateInput && !dateInput.value) {
        const today = new Date();
        dateInput.value = today.toISOString().split('T')[0];
    }

    // Handle form submission
    const attendanceForm = document.getElementById('attendance-form');
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', function(e) {
            const athleteSelect = document.getElementById('athlete-select');
            if (!athleteSelect.value) {
                e.preventDefault();
                showAlert('Please select an athlete first', 'warning');
                return false;
            }
            return true;
        });
    }

    // Handle check-in/check-out buttons
    const checkInBtn = document.querySelector('.check-in-button');
    const checkOutBtn = document.querySelector('.check-out-button');
    
    if (checkInBtn) {
        checkInBtn.addEventListener('click', function() {
            const athleteId = document.getElementById('athlete-select').value;
            if (!athleteId) {
                showAlert('Please select an athlete first', 'warning');
                return false;
            }
            // Additional client-side validation can go here
            return true;
        });
    }

    if (checkOutBtn) {
        checkOutBtn.addEventListener('click', function() {
            const athleteId = document.getElementById('athlete-select').value;
            if (!athleteId) {
                showAlert('Please select an athlete first', 'warning');
                return false;
            }
            // Additional validation for check-out
            return true;
        });
    }

    // Search functionality
    const searchInput = document.getElementById('athlete-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            // You can add live search functionality here if needed
        });
    }

    // Helper function to show alerts
    function showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `flash-message flash-${type}`;
        alertDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
            <button class="flash-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to flash messages container
        const flashContainer = document.querySelector('.flash-messages') || document.body;
        flashContainer.prepend(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            alertDiv.style.animation = 'slideOut 0.4s ease forwards';
            setTimeout(() => alertDiv.remove(), 400);
        }, 5000);
        
        // Close button functionality
        alertDiv.querySelector('.flash-close').addEventListener('click', () => {
            alertDiv.style.animation = 'slideOut 0.4s ease forwards';
            setTimeout(() => alertDiv.remove(), 400);
        });
    }

    // Initialize any other UI components
    initCustomSelect();
    
    function initCustomSelect() {
        const customSelects = document.querySelectorAll('.custom-select');
        customSelects.forEach(select => {
            select.addEventListener('click', function(e) {
                e.stopPropagation();
                this.classList.toggle('open');
                
                // Close other open selects
                document.querySelectorAll('.custom-select').forEach(otherSelect => {
                    if (otherSelect !== this) {
                        otherSelect.classList.remove('open');
                    }
                });
            });
            
            // Handle option selection
            const options = select.querySelectorAll('option');
            options.forEach(option => {
                option.addEventListener('click', function() {
                    select.querySelector('select').value = this.value;
                    select.classList.remove('open');
                });
            });
        });
        
        // Close selects when clicking outside
        document.addEventListener('click', function() {
            document.querySelectorAll('.custom-select').forEach(select => {
                select.classList.remove('open');
            });
        });
    }
});