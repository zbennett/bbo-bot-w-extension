/**
 * TrickHistory Component
 * Displays compact history of completed tricks
 */

function CompactTrickHistory({ tricks }) {
    const [collapsed, setCollapsed] = React.useState(false);

    if (!tricks || tricks.length === 0) {
        return null;
    }

    const formatTrickCard = (card) => {
        const formatted = formatCard(card);
        if (!formatted) return '??';
        return `${formatted.symbol}${formatted.rank}`;
    };

    return (
        <div className="bg-gray-800/95 rounded-lg p-3 border border-gray-700 backdrop-blur-sm">
            <div 
                className="flex items-center justify-between cursor-pointer mb-2"
                onClick={() => setCollapsed(!collapsed)}
            >
                <h3 className="text-sm font-semibold text-gray-300">
                    Tricks Played ({tricks.length})
                </h3>
                <button className="text-gray-400 hover:text-gray-200">
                    {collapsed ? '▼' : '▲'}
                </button>
            </div>
            
            {!collapsed && (
                <div className="space-y-1 max-h-48 overflow-y-auto text-xs">
                    {tricks.slice().reverse().map((trick, idx) => (
                        <div 
                            key={tricks.length - idx}
                            className="flex items-center gap-2 py-1 px-2 rounded bg-gray-700/50 hover:bg-gray-700"
                        >
                            <span className="text-gray-400 font-mono w-6">
                                #{tricks.length - idx}
                            </span>
                            <div className="flex gap-1.5 flex-1 font-mono">
                                {trick.cards.map((cardInfo, cardIdx) => {
                                    const cardStr = Array.isArray(cardInfo.card) 
                                        ? `${cardInfo.card[0]}${cardInfo.card[1]}`
                                        : cardInfo.card;
                                    return (
                                        <span 
                                            key={cardIdx}
                                            className="text-gray-300"
                                            title={`${cardInfo.player}: ${cardStr}`}
                                        >
                                            {formatTrickCard(cardStr)}
                                        </span>
                                    );
                                })}
                            </div>
                            <span className="text-green-400 font-semibold w-6">
                                {trick.winner}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
