/**
 * RubberScoreCard Component
 * Displays complete rubber bridge scoring information
 * Shows above/below line scores, games won, vulnerability, rubber history
 */

function RubberScoreCard({ rubberScore }) {
    const [expanded, setExpanded] = React.useState(true);

    if (!rubberScore) {
        return (
            <div className="bg-gray-800/95 rounded-lg p-4 backdrop-blur-sm border border-gray-700">
                <h3 className="text-lg font-semibold mb-2">Rubber Bridge Scoring</h3>
                <div className="text-gray-500 text-sm italic">
                    No rubber in progress. Start a new deal to begin scoring.
                </div>
            </div>
        );
    }

    const { ns, ew, rubber_complete, rubber_number, hand_count, last_hand } = rubberScore;

    // Calculate who's ahead
    const nsTotalScore = ns.total;
    const ewTotalScore = ew.total;
    const leader = nsTotalScore > ewTotalScore ? 'NS' : ewTotalScore > nsTotalScore ? 'EW' : 'Tied';
    const leadAmount = Math.abs(nsTotalScore - ewTotalScore);

    return (
        <div className="bg-gray-800/95 rounded-lg p-4 backdrop-blur-sm border border-gray-700">
            {/* Header */}
            <div 
                className="flex items-center justify-between cursor-pointer mb-3"
                onClick={() => setExpanded(!expanded)}
            >
                <div>
                    <h3 className="text-lg font-semibold">
                        Rubber #{rubber_number} Score
                        {rubber_complete && <span className="ml-2 text-green-400">✓ Complete</span>}
                    </h3>
                    <div className="text-xs text-gray-400">
                        {hand_count} hands played
                    </div>
                </div>
                <button className="text-gray-400 hover:text-gray-200">
                    {expanded ? '▼' : '▶'}
                </button>
            </div>

            {expanded && (
                <>
                    {/* Last Hand Score */}
                    {last_hand && (
                        <div className="bg-gray-700/30 rounded p-3 mb-3 border border-gray-600">
                            <div className="text-xs text-gray-400 mb-1">Last Hand</div>
                            <div className="text-sm">
                                <span className="font-mono font-bold">{last_hand.contract}</span>
                                <span className="text-gray-400"> by </span>
                                <span className="font-bold">{last_hand.declarer}</span>
                                <span className="text-gray-400"> → </span>
                                <span className="font-mono">{last_hand.tricks_made} tricks</span>
                            </div>
                            <div className="text-xs mt-1">
                                <span className={last_hand.score.partnership === 'NS' ? 'text-green-400' : 'text-blue-400'}>
                                    {last_hand.score.partnership}
                                </span>
                                <span className="text-gray-400"> +</span>
                                <span className="font-bold text-yellow-400">{last_hand.score.total}</span>
                                <span className="text-gray-500 ml-2">({last_hand.score.description})</span>
                            </div>
                        </div>
                    )}
                    
                    {/* Score Table */}
                    <div className="mb-4">
                        <div className="grid grid-cols-3 gap-2 text-sm">
                            {/* Header Row */}
                            <div className="font-semibold text-gray-400"></div>
                            <div className="font-semibold text-center text-green-400">NS</div>
                            <div className="font-semibold text-center text-blue-400">EW</div>

                            {/* Games Won */}
                            <div className="text-gray-400">Games Won</div>
                            <div className="text-center font-bold">
                                <span className={ns.games >= 2 ? 'text-green-400' : ''}>
                                    {ns.games}
                                </span>
                            </div>
                            <div className="text-center font-bold">
                                <span className={ew.games >= 2 ? 'text-blue-400' : ''}>
                                    {ew.games}
                                </span>
                            </div>

                            {/* Vulnerability */}
                            <div className="text-gray-400">Vulnerable</div>
                            <div className="text-center">
                                {ns.vulnerable ? (
                                    <span className="text-red-500 font-bold">VUL</span>
                                ) : (
                                    <span className="text-gray-500">—</span>
                                )}
                            </div>
                            <div className="text-center">
                                {ew.vulnerable ? (
                                    <span className="text-red-500 font-bold">VUL</span>
                                ) : (
                                    <span className="text-gray-500">—</span>
                                )}
                            </div>

                            {/* Divider */}
                            <div className="col-span-3 border-t border-gray-600 my-2"></div>

                            {/* Below Line (Game Points) */}
                            <div className="text-gray-400 text-xs">Below Line</div>
                            <div className="text-center font-mono text-xs">{ns.below}</div>
                            <div className="text-center font-mono text-xs">{ew.below}</div>

                            {/* Above Line (Bonuses) */}
                            <div className="text-gray-400 text-xs">Above Line</div>
                            <div className="text-center font-mono text-xs">{ns.above}</div>
                            <div className="text-center font-mono text-xs">{ew.above}</div>

                            {/* Divider */}
                            <div className="col-span-3 border-t border-gray-600 my-2"></div>

                            {/* Total Score */}
                            <div className="text-gray-300 font-semibold">Total Score</div>
                            <div className="text-center font-bold text-lg text-green-400">
                                {nsTotalScore}
                            </div>
                            <div className="text-center font-bold text-lg text-blue-400">
                                {ewTotalScore}
                            </div>
                        </div>
                    </div>

                    {/* Leader Display */}
                    {leader !== 'Tied' && (
                        <div className="bg-gray-700/50 rounded p-2 text-center text-sm mb-3">
                            <span className={leader === 'NS' ? 'text-green-400' : 'text-blue-400'}>
                                {leader}
                            </span>
                            <span className="text-gray-400"> leads by </span>
                            <span className="font-bold">{leadAmount}</span>
                            <span className="text-gray-400"> points</span>
                        </div>
                    )}

                    {/* Rubbers Won (Lifetime) */}
                    {(ns.rubbers > 0 || ew.rubbers > 0) && (
                        <div className="bg-gray-700/50 rounded p-2 text-sm">
                            <div className="text-gray-400 text-xs mb-1">Rubbers Won (Session)</div>
                            <div className="flex justify-between">
                                <span>NS: <span className="font-bold text-green-400">{ns.rubbers}</span></span>
                                <span>EW: <span className="font-bold text-blue-400">{ew.rubbers}</span></span>
                            </div>
                        </div>
                    )}

                    {/* Rubber Complete Message */}
                    {rubber_complete && (
                        <div className="mt-3 bg-yellow-500/20 border border-yellow-500/50 rounded p-3 text-center">
                            <div className="text-yellow-400 font-bold text-lg mb-1">
                                🏆 Rubber Complete!
                            </div>
                            <div className="text-gray-300 text-sm">
                                {leader} wins {ns.games}-{ew.games}
                            </div>
                            <div className="text-gray-400 text-xs mt-1">
                                Final: NS {nsTotalScore} - EW {ewTotalScore}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
