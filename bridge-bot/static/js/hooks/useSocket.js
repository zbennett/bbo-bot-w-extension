/**
 * Socket.IO Hook
 * Custom React hook for managing Socket.IO connection and events
 */

/**
 * Custom hook for Socket.IO connection
 * @param {Object} callbacks - Event callbacks
 * @returns {Object} Socket connection and connection status
 */
function useSocket(callbacks = {}) {
    const [socket, setSocket] = React.useState(null);
    const [connected, setConnected] = React.useState(false);

    React.useEffect(() => {
        // Initialize Socket.IO connection
        const newSocket = io();
        
        newSocket.on('connect', () => {
            console.log('✅ Connected to server');
            setConnected(true);
            if (callbacks.onConnect) callbacks.onConnect();
        });

        newSocket.on('disconnect', () => {
            console.log('❌ Disconnected from server');
            setConnected(false);
            if (callbacks.onDisconnect) callbacks.onDisconnect();
        });

        // Register all event handlers
        if (callbacks.onGameState) {
            newSocket.on(SOCKET_EVENTS.GAME_STATE, callbacks.onGameState);
        }
        if (callbacks.onNewDeal) {
            newSocket.on(SOCKET_EVENTS.NEW_DEAL, callbacks.onNewDeal);
        }
        if (callbacks.onCardPlayed) {
            newSocket.on(SOCKET_EVENTS.CARD_PLAYED, callbacks.onCardPlayed);
        }
        if (callbacks.onBidMade) {
            newSocket.on(SOCKET_EVENTS.BID_MADE, callbacks.onBidMade);
        }
        if (callbacks.onContractSet) {
            newSocket.on(SOCKET_EVENTS.CONTRACT_SET, callbacks.onContractSet);
        }
        if (callbacks.onRecommendation) {
            newSocket.on(SOCKET_EVENTS.RECOMMENDATION, callbacks.onRecommendation);
        }
        if (callbacks.onDDAnalysis) {
            newSocket.on(SOCKET_EVENTS.DD_ANALYSIS, callbacks.onDDAnalysis);
        }
        if (callbacks.onActivePlayer) {
            newSocket.on(SOCKET_EVENTS.ACTIVE_PLAYER, callbacks.onActivePlayer);
        }

        setSocket(newSocket);

        // Cleanup on unmount
        return () => {
            newSocket.close();
        };
    }, []); // Empty deps - only run once on mount

    return { socket, connected };
}
