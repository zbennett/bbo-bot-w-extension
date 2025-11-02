/**
 * Dashboard Component
 * Main dashboard container that manages state and renders all sub-components
 */

function Dashboard() {
    const [gameState, setGameState] = React.useState({
        boardNumber: null,
        dealer: null,
        vulnerability: null,
        hands: { N: [], E: [], S: [], W: [] },
        contract: null,
        declarer: null,
        currentTrick: [],
        tricksWon: { NS: 0, EW: 0 },
        allTricks: [],
        lastRecommendation: null,
        bidding: [],
        ddAnalysis: null,
        activePlayer: null,
        bottomSeat: 'S',
        trickWinner: null
    });

    const [godsView, setGodsView] = React.useState(true);

    // Socket.IO connection and event handlers
    const { socket, connected } = useSocket({
        onGameState: (data) => {
            console.log('📊 Received game state:', data);
            setGameState(prevState => ({ ...prevState, ...data }));
        },
        onNewDeal: (data) => {
            console.log('🎴 New deal:', data);
            setGameState(prevState => ({
                ...prevState,
                boardNumber: data.board_number,
                dealer: data.dealer,
                vulnerability: data.vulnerability,
                hands: data.hands || prevState.hands,
                currentTrick: [],
                allTricks: [],
                contract: null,
                declarer: null,
                trickWinner: null,
                bottomSeat: data.bottom_seat || prevState.bottomSeat
            }));
        },
        onCardPlayed: (data) => {
            console.log('🃏 Card played:', data);
            setGameState(prevState => ({
                ...prevState,
                hands: data.hands || prevState.hands,
                currentTrick: data.current_trick || prevState.currentTrick,
                allTricks: data.all_tricks || prevState.allTricks,
                trickWinner: data.winner || null
            }));
        },
        onBidMade: (data) => {
            console.log('📢 Bid made:', data);
            setGameState(prevState => ({
                ...prevState,
                bidding: [...prevState.bidding, data]
            }));
        },
        onContractSet: (data) => {
            console.log('📋 Contract set:', data);
            setGameState(prevState => ({
                ...prevState,
                contract: data.contract,
                declarer: data.declarer
            }));
        },
        onRecommendation: (data) => {
            console.log('💡 Recommendation:', data);
            setGameState(prevState => ({
                ...prevState,
                lastRecommendation: data
            }));
        },
        onDDAnalysis: (data) => {
            console.log('🧠 DD Analysis:', data);
            setGameState(prevState => ({
                ...prevState,
                ddAnalysis: data.analysis
            }));
        },
        onActivePlayer: (data) => {
            console.log('👉 Active player:', data);
            setGameState(prevState => ({
                ...prevState,
                activePlayer: data.player
            }));
        }
    });

    // Get player name for each visual position based on rotation
    const getPlayerName = (visualPosition) => {
        const offset = ['S', 'W', 'N', 'E'].indexOf(gameState.bottomSeat);
        const positions = ['N', 'E', 'S', 'W'];
        const visualIdx = positions.indexOf(visualPosition);
        const actualIdx = (visualIdx + offset) % 4;
        return positions[actualIdx];
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4">
            {/* Header */}
            <div className="max-w-7xl mx-auto mb-4">
                <div className="flex items-center justify-between bg-gray-800/90 rounded-lg p-4 backdrop-blur-sm border border-gray-700">
                    <div>
                        <h1 className="text-2xl font-bold text-white">Bridge Bot Dashboard</h1>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
                            <span>Board {gameState.boardNumber || '—'}</span>
                            <span>•</span>
                            <span>Dealer: {gameState.dealer || '—'}</span>
                            <span>•</span>
                            <span>Vul: {gameState.vulnerability || '—'}</span>
                            {gameState.contract && (
                                <>
                                    <span>•</span>
                                    <span className="text-yellow-400 font-semibold">
                                        {gameState.contract} by {gameState.declarer}
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setGodsView(!godsView)}
                            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold transition-colors flex items-center gap-2"
                        >
                            {godsView ? '👁️' : '🙈'} God's View
                        </button>
                        <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-red-500'}`}></div>
                            <span className="text-sm text-gray-400">
                                {connected ? 'Connected' : 'Disconnected'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Grid */}
            <div className="max-w-7xl mx-auto grid grid-cols-4 gap-4">
                {/* Left Sidebar */}
                <div className="space-y-4">
                    <div className="bg-gray-800/90 rounded-lg p-4 backdrop-blur-sm border border-gray-700">
                        <h3 className="text-lg font-semibold mb-3">Tricks Won</h3>
                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <span>NS:</span>
                                <span className="font-bold text-green-400">{gameState.tricksWon.NS}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>EW:</span>
                                <span className="font-bold text-blue-400">{gameState.tricksWon.EW}</span>
                            </div>
                        </div>
                    </div>

                    {gameState.lastRecommendation && (
                        <div className="bg-gray-800/90 rounded-lg p-4 backdrop-blur-sm border border-gray-700">
                            <h3 className="text-lg font-semibold mb-2">Recommendation</h3>
                            <div className="text-sm space-y-1">
                                <div><strong>Player:</strong> {gameState.lastRecommendation.player}</div>
                                <div><strong>Card:</strong> {gameState.lastRecommendation.card}</div>
                                {gameState.lastRecommendation.reason && (
                                    <div className="text-gray-400 text-xs mt-2">
                                        {gameState.lastRecommendation.reason}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Center - Play Area */}
                <div className="col-span-2">
                    <div className="bg-gradient-to-br from-bridge-green to-bridge-felt rounded-lg shadow-2xl aspect-square relative border-4 border-gray-700">
                        {/* Hands at each position */}
                        {POSITIONS.map(visualPos => {
                            const playerName = getPlayerName(visualPos);
                            const bottomPlayer = getPlayerName('S');
                            return (
                                <Hand
                                    key={visualPos}
                                    cards={gameState.hands[playerName] || []}
                                    position={visualPos}
                                    playerName={playerName}
                                    isVisible={godsView || playerName === bottomPlayer}
                                    declarer={gameState.declarer}
                                    isActivePlayer={gameState.activePlayer === playerName}
                                />
                            );
                        })}

                        {/* Center - Current Trick */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64">
                            <CurrentTrick
                                trick={gameState.currentTrick}
                                winner={gameState.trickWinner}
                            />
                        </div>
                    </div>
                </div>

                {/* Right Sidebar */}
                <div className="space-y-4">
                    <CompactTrickHistory tricks={gameState.allTricks} />
                    <DDAnalysis ddAnalysis={gameState.ddAnalysis} />
                </div>
            </div>
        </div>
    );
}
