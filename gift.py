from flask import Flask, render_template, jsonify
import random
import os

app = Flask(__name__)

# Gift configuration with emojis - you can modify this list as needed
GIFTS = [
    ['🏆 Premium Gym Membership (1 Year)', 1, '🏆'],
    ['💪 Personal Training Sessions (10 sessions)', 2, '💪'],
    ['🥗 Sports Nutrition Package', 5, '🥗'],
    ['👕 Branded Sportswear Set', 10, '👕'],
    ['⌚ Fitness Tracker Watch', 15, '⌚'],
    ['🍶 Protein Supplement Pack', 20, '🍶'],
    ['💧 Gym Water Bottle', 25, '💧'],
    ['🏐 Sports Towel', 22, '🏐']
]

class GiftLottery:
    def __init__(self, gifts_list):
        self.gifts = gifts_list
        self._validate_probabilities()
    
    def _validate_probabilities(self):
        """Validate that probabilities sum to 100%"""
        total_prob = sum(gift[1] for gift in self.gifts)
        if total_prob != 100:
            raise ValueError(f"Total probability must be 100%, current sum: {total_prob}%")
    
    def draw_winner(self):
        """Perform a lottery draw and return the winning gift"""
        random_value = random.uniform(0, 100)
        cumulative_prob = 0
        
        for gift_name, probability, emoji in self.gifts:
            cumulative_prob += probability
            if random_value <= cumulative_prob:
                return {
                    'name': gift_name,
                    'emoji': emoji,
                    'full_display': f"{emoji} {gift_name}"
                }
        
        # Fallback - return the last gift if no match
        last_gift = self.gifts[-1]
        return {
            'name': last_gift[0],
            'emoji': last_gift[2],
            'full_display': f"{last_gift[2]} {last_gift[0]}"
        }

# Initialize the lottery system
lottery_system = GiftLottery(GIFTS)

@app.route('/')
def lottery_page():
    """Render the main lottery page"""
    return render_template('gift.html', gifts=GIFTS)

@app.route('/draw', methods=['POST'])
def draw_gift():
    """Handle lottery draw request"""
    try:
        winning_gift = lottery_system.draw_winner()
        return jsonify({
            'success': True,
            'gift': winning_gift['full_display'],
            'gift_name': winning_gift['name'],
            'gift_emoji': winning_gift['emoji'],
            'message': 'Congratulations! You won a prize!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'An error occurred during the draw. Please try again.'
        }), 500

@app.route('/gifts', methods=['GET'])
def get_gifts():
    """Return the list of available gifts"""
    gifts_data = []
    for gift_name, probability, emoji in GIFTS:
        gifts_data.append({
            'name': gift_name,
            'probability': probability,
            'emoji': emoji,
            'display': f"{emoji} {gift_name}"
        })
    
    return jsonify(gifts_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)