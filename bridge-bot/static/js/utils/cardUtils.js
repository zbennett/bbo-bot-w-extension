/**
 * Card Utility Functions
 * Helper functions for card formatting, calculation, and manipulation
 */

/**
 * Format a card string into an object with suit, rank, symbol, and color
 * @param {string} card - Card string like "SA" or "H10"
 * @returns {Object} Formatted card object
 */
function formatCard(card) {
    if (!card) return null;
    const suit = card[0];
    const rank = card.slice(1);
    return {
        suit,
        rank,
        symbol: SUIT_SYMBOLS[suit] || suit,
        color: SUIT_COLORS[suit] || 'text-gray-900'
    };
}

/**
 * Calculate High Card Points for a hand
 * @param {Array<string>} cards - Array of card strings
 * @returns {number} Total HCP
 */
function calculateHCP(cards) {
    if (!cards || !Array.isArray(cards)) return 0;
    return cards.reduce((sum, card) => {
        const rank = card.slice(1);
        return sum + (HCP_VALUES[rank] || 0);
    }, 0);
}

/**
 * Organize cards by suit
 * @param {Array<string>} cards - Array of card strings
 * @returns {Object} Cards organized by suit
 */
function organizeBySuit(cards) {
    const result = { 'S': [], 'H': [], 'D': [], 'C': [] };
    if (!cards || !Array.isArray(cards)) return result;
    
    cards.forEach(card => {
        const suit = card[0];
        const rank = card.slice(1);
        if (result[suit]) {
            result[suit].push(rank);
        }
    });
    
    return result;
}

/**
 * Sort cards within a suit by rank (high to low)
 * @param {Array<string>} ranks - Array of rank strings
 * @returns {Array<string>} Sorted ranks
 */
function sortRanks(ranks) {
    const order = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
    return [...ranks].sort((a, b) => order.indexOf(a) - order.indexOf(b));
}

/**
 * Convert card array format [suit, rank] to string format
 * @param {Array} cardArray - Card in array format
 * @returns {string} Card string
 */
function cardArrayToString(cardArray) {
    if (!cardArray || !Array.isArray(cardArray) || cardArray.length < 2) return '';
    return `${cardArray[0]}${cardArray[1]}`;
}

/**
 * Convert card string to array format
 * @param {string} cardString - Card string like "SA"
 * @returns {Array} Card in array format [suit, rank]
 */
function cardStringToArray(cardString) {
    if (!cardString || cardString.length < 2) return ['', ''];
    return [cardString[0], cardString.slice(1)];
}

/**
 * Get rotation offset for bottom seat
 * @param {string} bottomSeat - Seat at bottom (N, E, S, W)
 * @returns {number} Rotation offset (0-3)
 */
function getRotationOffset(bottomSeat) {
    const seats = ['S', 'W', 'N', 'E'];
    return seats.indexOf(bottomSeat);
}

/**
 * Rotate position based on bottom seat
 * @param {string} position - Original position (N, E, S, W)
 * @param {string} bottomSeat - Seat at bottom
 * @returns {string} Rotated position
 */
function rotatePosition(position, bottomSeat) {
    const positions = ['N', 'E', 'S', 'W'];
    const seats = ['S', 'W', 'N', 'E'];
    const offset = seats.indexOf(bottomSeat);
    const posIdx = positions.indexOf(position);
    return positions[(posIdx - offset + 4) % 4];
}
