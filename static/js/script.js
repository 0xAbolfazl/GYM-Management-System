// deactive sidebar in phone
document.querySelector('.sidebar-toggle').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('active');
});

// Close notification messages
document.querySelectorAll('.flash-messages > div').forEach(flash => {
    setTimeout(() => {
        flash.style.animation = 'slideOut 0.5s ease forwards';
        setTimeout(() => flash.remove(), 500);
    }, 5000);
    
    // Manual closing
    flash.querySelector('.flash-close')?.addEventListener('click', () => {
        flash.style.animation = 'slideOut 0.5s ease forwards';
        setTimeout(() => flash.remove(), 500);
    });
});

// Calculating a new end date for the renewal form
if (document.getElementById('days') && document.getElementById('new_end_date')) {
    const daysInput = document.getElementById('days');
    const endDateDisplay = document.getElementById('new_end_date');
    
    function calculateNewEndDate(days) {
        if (days > 0) {
            const endDate = new Date();
            endDate.setDate(endDate.getDate() + parseInt(days));
            endDateDisplay.value = endDate.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        } else {
            endDateDisplay.value = '';
        }
    }
    
    daysInput.addEventListener('input', function() {
        calculateNewEndDate(this.value);
    });
    
    
    calculateNewEndDate(daysInput.value);
}


document.querySelectorAll('.day-option').forEach(button => {
    button.addEventListener('click', function() {
        const days = this.getAttribute('data-days');
        document.getElementById('days').value = days;
        

        document.querySelectorAll('.day-option').forEach(btn => {
            btn.classList.remove('active');
        });
        this.classList.add('active');
        
        // Calculate the new date 
        if (document.getElementById('new_end_date')) {
            calculateNewEndDate(days);
        }
    });
});

// Confirm before deleting
document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to delete this athlete?')) {
            e.preventDefault();
        }
    });
});

// Exit animation for messages
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        to {
            transform: translateX(100%);
            opacity: 0;
            max-height: 0;
            padding: 0;
            margin: 0;
            overflow: hidden;
        }
    }
    
    .flash-messages > div {
        transition: all 0.5s ease;
        overflow: hidden;
    }
`;
document.head.appendChild(style);