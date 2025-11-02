/**
 * Card Component
 * Displays a single playing card with suit symbol and rank
 */

function Card({ card, player, size = 'md' }) {
    const formatted = formatCard(card);
    
    if (!formatted) {
        return <div className="text-gray-500 text-xs">No card</div>;
    }

    return (
        <div className="text-center">
            <div className={`${CARD_SIZES.dimensions[size]} bg-white rounded shadow-lg flex flex-col items-center justify-center border-2 border-gray-200`}>
                <div className={`${formatted.color} font-bold ${CARD_SIZES.text[size]}`}>
                    {formatted.symbol}
                </div>
                <div className={`${formatted.color} font-bold ${CARD_SIZES.text[size]}`}>
                    {formatted.rank}
                </div>
            </div>
            {player && (
                <div className="text-xs text-gray-400 mt-1">{player}</div>
            )}
        </div>
    );
}
