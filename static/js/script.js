// فعال/غیرفعال کردن سایدبار در حالت موبایل
document.querySelector('.sidebar-toggle').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('active');
});

// بستن پیام‌های اطلاع‌رسانی
document.querySelectorAll('.flash-close').forEach(button => {
    button.addEventListener('click', function() {
        this.parentElement.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
            this.parentElement.remove();
        }, 300);
    });
});

// محاسبه تاریخ پایان جدید برای فرم تمدید
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
    
    // مقداردهی اولیه
    calculateNewEndDate(daysInput.value);
}

// انتخاب گزینه‌های روز
document.querySelectorAll('.day-option').forEach(button => {
    button.addEventListener('click', function() {
        const days = this.getAttribute('data-days');
        document.getElementById('days').value = days;
        
        // به‌روزرسانی حالت فعال
        document.querySelectorAll('.day-option').forEach(btn => {
            btn.classList.remove('active');
        });
        this.classList.add('active');
        
        // محاسبه تاریخ جدید
        if (document.getElementById('new_end_date')) {
            calculateNewEndDate(days);
        }
    });
});

// تایید قبل از حذف
document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to delete this athlete?')) {
            e.preventDefault();
        }
    });
});

// انیمیشن خروج برای پیام‌ها
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);