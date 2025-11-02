/**
 * Hand Component
 * Displays a player's hand with cards organized by suit
 */

function Hand({ cards, position, playerName, isVisible, declarer, isActivePlayer }) {
    const suits = React.useMemo(() => organizeBySuit(cards), [cards]);
    const hcp = React.useMemo(() => calculateHCP(cards), [cards]);
    const isDeclarer = declarer === playerName;

    return (
        <div className={`absolute ${POSITION_STYLES[position]} bg-gray-800/95 rounded-lg shadow-xl p-3 border-2 ${
            isActivePlayer 
                ? 'border-green-400 ring-2 ring-green-400 ring-opacity-50' 
                : isDeclarer 
                    ? 'border-yellow-500' 
                    : 'border-gray-700'
        } transition-all backdrop-blur-sm`}>
            <div className="flex items-center gap-2 mb-2">
                <div className="text-lg font-bold flex items-center gap-1">
                    {playerName}
                    {isActivePlayer && (
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    )}
                </div>
                {isDeclarer && (
                    <div className="text-yellow-500 text-[10px] font-semibold bg-yellow-500/20 px-1.5 py-0.5 rounded">
                        DECLARER
                    </div>
                )}
                <div className="text-gray-400 text-xs ml-auto flex items-center gap-1.5">
                    <span className="text-amber-400 font-bold">{hcp} HCP</span>
                    <span className="text-gray-500">•</span>
                    <span>{cards.length}</span>
                </div>
            </div>
            {isVisible ? (
                <div className="space-y-1">
                    {SUIT_ORDER.map(suit => (
                        <div key={suit} className="flex items-center gap-1">
                            <span className={`text-xl ${SUIT_COLORS[suit]}`}>
                                {SUIT_SYMBOLS[suit]}
                            </span>
                            <span className="text-xs font-mono">
                                {suits[suit].join(' ') || '—'}
                            </span>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-gray-500 text-xs italic">Hidden</div>
            )}
        </div>
    );
}
