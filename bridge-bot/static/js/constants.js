/**
 * Bridge Dashboard Constants
 * Centralized configuration and constant values
 */

const SUIT_SYMBOLS = {
    'S': '♠',
    'H': '♥',
    'D': '♦',
    'C': '♣'
};

const SUIT_COLORS = {
    'S': 'text-gray-900',
    'H': 'text-red-600',
    'D': 'text-orange-500',
    'C': 'text-gray-900'
};

const SUIT_ORDER = ['S', 'H', 'D', 'C'];

const HCP_VALUES = {
    'A': 4,
    'K': 3,
    'Q': 2,
    'J': 1
};

const POSITIONS = ['N', 'E', 'S', 'W'];

const POSITION_NAMES = {
    'N': 'North',
    'E': 'East',
    'S': 'South',
    'W': 'West'
};

const POSITION_STYLES = {
    N: 'top-2 left-1/2 -translate-x-1/2',
    E: 'right-2 top-1/2 -translate-y-1/2',
    S: 'bottom-2 left-1/2 -translate-x-1/2',
    W: 'left-2 top-1/2 -translate-y-1/2'
};

const CARD_SIZES = {
    dimensions: {
        sm: 'w-18 h-26',
        md: 'w-24 h-36'
    },
    text: {
        sm: 'text-sm',
        md: 'text-lg'
    }
};

const SOCKET_EVENTS = {
    // Server -> Client
    GAME_STATE: 'game_state',
    NEW_DEAL: 'new_deal',
    CARD_PLAYED: 'card_played',
    BID_MADE: 'bid_made',
    CONTRACT_SET: 'contract_set',
    RECOMMENDATION: 'recommendation',
    DD_ANALYSIS: 'dd_analysis',
    ACTIVE_PLAYER: 'active_player',
    
    // Client -> Server
    CONNECT: 'connect',
    DISCONNECT: 'disconnect'
};
