/**
 * CurrentTrick Component
 * Displays the cards in the current trick
 */

function CurrentTrick({ trick, winner }) {
    if (!trick || trick.length === 0) {
        return (
            <div className="text-center text-gray-500 py-8">
                Waiting for first card...
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex justify-center items-center gap-4 flex-wrap">
                {trick.map((cardInfo, idx) => {
                    const cardString = Array.isArray(cardInfo.card) 
                        ? cardArrayToString(cardInfo.card)
                        : cardInfo.card;
                    
                    return (
                        <Card
                            key={idx}
                            card={cardString}
                            player={cardInfo.player}
                            size="md"
                        />
                    );
                })}
            </div>
            {winner && trick.length === 4 && (
                <div className="text-center text-green-400 font-bold text-lg animate-pulse">
                    🏆 {winner} wins!
                </div>
            )}
        </div>
    );
}
