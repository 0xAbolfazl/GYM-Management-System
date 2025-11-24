class LotterySystem {
    constructor() {
        this.drawButton = document.getElementById('drawButton');
        this.lotteryWheel = document.getElementById('lotteryWheel');
        this.resultSection = document.getElementById('resultSection');
        this.resultGift = document.getElementById('resultGift');
        this.closeResult = document.getElementById('closeResult');
        this.prizesGrid = document.getElementById('prizesGrid');
        
        this.gifts = [];
        this.isDrawing = false;
        
        this.init();
    }
    
    async init() {
        this.drawButton.addEventListener('click', () => this.handleDraw());
        this.closeResult.addEventListener('click', () => this.hideResult());
        
        // Close result when clicking outside
        this.resultSection.addEventListener('click', (e) => {
            if (e.target === this.resultSection) {
                this.hideResult();
            }
        });
        
        // Load gifts from backend
        await this.loadGifts();
        this.createPrizesGrid();
        this.createWheel();
    }
    
    async loadGifts() {
        try {
            const response = await fetch('/gifts');
            this.gifts = await response.json();
        } catch (error) {
            console.error('Failed to load gifts:', error);
            // Fallback to default gifts
            this.gifts = [
                { name: 'Premium Gym Membership (1 Year)', probability: 1, emoji: '🏆', display: '🏆 Premium Gym Membership (1 Year)' },
                { name: 'Personal Training Sessions (10 sessions)', probability: 2, emoji: '💪', display: '💪 Personal Training Sessions (10 sessions)' },
                { name: 'Sports Nutrition Package', probability: 5, emoji: '🥗', display: '🥗 Sports Nutrition Package' },
                { name: 'Branded Sportswear Set', probability: 10, emoji: '👕', display: '👕 Branded Sportswear Set' },
                { name: 'Fitness Tracker Watch', probability: 15, emoji: '⌚', display: '⌚ Fitness Tracker Watch' },
                { name: 'Protein Supplement Pack', probability: 20, emoji: '🍶', display: '🍶 Protein Supplement Pack' },
                { name: 'Gym Water Bottle', probability: 25, emoji: '💧', display: '💧 Gym Water Bottle' },
                { name: 'Sports Towel', probability: 22, emoji: '🏐', display: '🏐 Sports Towel' }
            ];
        }
    }
    
    createPrizesGrid() {
        this.prizesGrid.innerHTML = '';
        
        this.gifts.forEach(gift => {
            const prizeElement = this.createPrizeElement(gift);
            this.prizesGrid.appendChild(prizeElement);
        });
    }
    
    createPrizeElement(gift) {
        const prizeDiv = document.createElement('div');
        prizeDiv.className = 'prize-item';
        
        prizeDiv.innerHTML = `
            <div class="prize-emoji">${gift.emoji}</div>
            <div class="prize-name">${gift.name}</div>
            <div class="prize-probability">${gift.probability}% chance</div>
        `;
        
        return prizeDiv;
    }
    
    createWheel() {
        this.lotteryWheel.innerHTML = '';
        const segmentAngle = 360 / this.gifts.length;
        
        this.gifts.forEach((gift, index) => {
            const segment = document.createElement('div');
            segment.className = 'wheel-segment';
            
            // Calculate segment color based on index
            const hue = (index * (360 / this.gifts.length)) % 360;
            const saturation = 70;
            const lightness = index % 2 === 0 ? 25 : 30;
            segment.style.background = `hsla(${hue}, ${saturation}%, ${lightness}%, 0.8)`;
            segment.style.transform = `rotate(${index * segmentAngle}deg)`;
            segment.style.border = `1px solid hsla(${hue}, ${saturation}%, 40%, 0.6)`;
            
            const content = document.createElement('div');
            content.className = 'wheel-segment-content';
            content.innerHTML = `
                <span class="wheel-emoji">${gift.emoji}</span>
                <div class="wheel-text">${this.shortenText(gift.name)}</div>
            `;
            
            segment.appendChild(content);
            this.lotteryWheel.appendChild(segment);
        });
    }
    
    shortenText(text) {
        const words = text.split(' ');
        if (words.length <= 2) return text;
        return words.slice(0, 2).join(' ') + '...';
    }
    
    async handleDraw() {
        if (this.isDrawing) return;
        
        this.isDrawing = true;
        this.drawButton.disabled = true;
        this.drawButton.innerHTML = '<span class="loading"></span> DRAWING...';
        
        try {
            // Start wheel animation
            this.startWheelAnimation();
            
            // Make API call to backend
            const response = await fetch('/draw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Wait for wheel animation to complete
                setTimeout(() => {
                    this.showResult(result.gift);
                }, 3000);
            } else {
                throw new Error(result.message);
            }
            
        } catch (error) {
            console.error('Draw error:', error);
            this.stopWheelAnimation();
            this.resetButton();
            this.isDrawing = false;
            alert('An error occurred during the draw. Please try again.');
        }
    }
    
    startWheelAnimation() {
        this.lotteryWheel.classList.add('spinning');
    }
    
    stopWheelAnimation() {
        this.lotteryWheel.classList.remove('spinning');
    }
    
    resetButton() {
        this.drawButton.disabled = false;
        this.drawButton.innerHTML = '<span class="button-text">SPIN TO WIN</span><div class="button-glow"></div>';
    }
    
    showResult(gift) {
        this.resultGift.textContent = gift;
        this.resultSection.style.display = 'flex';
        this.stopWheelAnimation();
        this.resetButton();
        this.isDrawing = false;
        
        // Add confetti effect
        this.createConfetti();
    }
    
    hideResult() {
        this.resultSection.style.display = 'none';
    }
    
    createConfetti() {
        const colors = ['#00d4ff', '#ff6b6b', '#4ecdc4', '#ffd166', '#9b59b6'];
        const confettiCount = 150;
        
        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.top = '-20px';
            confetti.style.opacity = '0.8';
            confetti.style.pointerEvents = 'none';
            confetti.style.zIndex = '9999';
            
            document.body.appendChild(confetti);
            
            const animation = confetti.animate([
                { transform: 'translateY(0) rotate(0deg)', opacity: 1 },
                { transform: `translateY(${window.innerHeight + 100}px) rotate(${Math.random() * 360}deg)`, opacity: 0 }
            ], {
                duration: Math.random() * 3000 + 2000,
                easing: 'cubic-bezier(0.1, 0.8, 0.3, 1)'
            });
            
            animation.onfinish = () => confetti.remove();
        }
    }
}

// Initialize the lottery system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LotterySystem();
});