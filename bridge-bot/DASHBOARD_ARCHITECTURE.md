# Bridge Bot Dashboard - Architecture Documentation

## Overview

The dashboard has been refactored into a modular, extensible architecture with clear separation of concerns. This makes it easy to add new features, test components independently, and maintain the codebase.

## Directory Structure

```
bridge-bot/
├── web/                          # Python backend modules
│   ├── __init__.py              # Module exports
│   ├── dashboard.py             # Main Flask app and routes
│   ├── broadcaster.py           # Socket.IO event broadcasting
│   └── state.py                 # Game state management
│
├── static/                       # Frontend static files
│   ├── js/
│   │   ├── constants.js         # Shared constants and config
│   │   ├── components/          # React components
│   │   │   ├── Dashboard.js     # Main dashboard container
│   │   │   ├── Hand.js          # Player hand display
│   │   │   ├── Card.js          # Single card display
│   │   │   ├── CurrentTrick.js  # Current trick display
│   │   │   ├── TrickHistory.js  # Trick history panel
│   │   │   └── DDAnalysis.js    # Double dummy analysis
│   │   ├── utils/               # Utility functions
│   │   │   └── cardUtils.js     # Card formatting and calculations
│   │   └── hooks/               # Custom React hooks
│   │       └── useSocket.js     # Socket.IO connection hook
│   └── css/
│       └── (future custom styles)
│
└── templates/                    # HTML templates
    ├── dashboard_react.html      # Original monolithic version
    ├── dashboard_modular.html    # New modular version
    └── dashboard.html            # Classic version

```

## Backend Architecture

### 1. State Management (`web/state.py`)

The `GameState` class centralizes all game state with helper methods:

```python
from web.state import GameState

state = GameState()

# Setting up a new deal
state.set_new_deal(board_number=1, dealer='N', vulnerability='None', hands={...})

# Managing tricks
state.add_card_to_trick('N', 'SA')
state.complete_trick(winner='N')

# Accessing state
current_state = state.get_state()
contract = state.get('contract')
```

**Benefits:**
- Centralized state validation
- Helper methods reduce code duplication
- Easy to add new state fields
- Type-safe operations

### 2. Event Broadcasting (`web/broadcaster.py`)

The `DashboardBroadcaster` class handles all Socket.IO emissions:

```python
from web.broadcaster import DashboardBroadcaster

broadcaster = DashboardBroadcaster(socketio, game_state)

# Broadcasting events
broadcaster.broadcast_new_deal(...)
broadcaster.broadcast_card_played(...)
broadcaster.broadcast_recommendation(...)
```

**Benefits:**
- Separates communication logic from business logic
- Consistent event formatting
- Easy to add new event types
- Testable in isolation

### 3. Main Dashboard Module (`web/dashboard.py`)

Flask app with clean API for the bot:

```python
from web import dashboard

# Start server (in separate thread)
dashboard.start_server(port=5001)

# Update from bot code
dashboard.update_new_deal(...)
dashboard.update_card_played(...)
```

**Benefits:**
- Clean public API
- Routes separated from logic
- Easy to add new endpoints
- Backward compatible

## Frontend Architecture

### 1. Constants (`static/js/constants.js`)

All magic strings and configuration in one place:

```javascript
import { SUIT_SYMBOLS, POSITIONS, SOCKET_EVENTS } from './constants.js';
```

**Benefits:**
- No magic strings scattered in code
- Easy to update styling/config
- Single source of truth

### 2. Utilities (`static/js/utils/cardUtils.js`)

Pure functions for data manipulation:

```javascript
import { formatCard, calculateHCP, organizeBySuit } from './utils/cardUtils.js';

const hcp = calculateHCP(cards);
const suits = organizeBySuit(cards);
```

**Benefits:**
- Reusable across components
- Easy to unit test
- No side effects

### 3. Custom Hooks (`static/js/hooks/useSocket.js`)

React hooks for stateful logic:

```javascript
import { useSocket } from './hooks/useSocket.js';

const { socket, connected } = useSocket({
    onNewDeal: (data) => { /* handle */ },
    onCardPlayed: (data) => { /* handle */ }
});
```

**Benefits:**
- Reusable Socket.IO logic
- Clean component code
- Easy to add event handlers

### 4. Components (`static/js/components/`)

Self-contained React components:

```javascript
import { Hand } from './components/Hand.js';
import { Card } from './components/Card.js';
import { Dashboard } from './components/Dashboard.js';
```

Each component is in its own file with clear responsibilities.

**Benefits:**
- Easy to understand
- Easy to modify
- Easy to test
- Reusable

## Adding New Features

### Adding a New Component

1. Create file in `static/js/components/NewComponent.js`:

```javascript
/**
 * NewComponent
 * Description of what it does
 */

import { SOME_CONSTANT } from '../constants.js';

export function NewComponent({ prop1, prop2 }) {
    return (
        <div>
            {/* Component JSX */}
        </div>
    );
}
```

2. Import in Dashboard.js:

```javascript
import { NewComponent } from './NewComponent.js';
```

### Adding a New Socket Event

1. Add event name to `constants.js`:

```javascript
export const SOCKET_EVENTS = {
    // ... existing events
    NEW_EVENT: 'new_event'
};
```

2. Add handler to `useSocket.js`:

```javascript
if (callbacks.onNewEvent) {
    newSocket.on(SOCKET_EVENTS.NEW_EVENT, callbacks.onNewEvent);
}
```

3. Add broadcaster method in `web/broadcaster.py`:

```python
def broadcast_new_event(self, data):
    """Broadcast new event"""
    self.socketio.emit('new_event', data)
```

4. Add public API in `web/dashboard.py`:

```python
def update_new_event(data):
    """Update dashboard with new event"""
    broadcaster.broadcast_new_event(data)
```

### Adding a New State Field

1. Add to `GameState.__init__()` in `web/state.py`:

```python
self._state = {
    # ... existing fields
    'new_field': None
}
```

2. Optionally add helper method:

```python
def set_new_field(self, value):
    """Set the new field"""
    self._state['new_field'] = value
```

## Migration Guide

The old `web_dashboard.py` is still available for backward compatibility. To migrate your bot code:

**Old way:**
```python
import web_dashboard as DashboardBroadcaster
DashboardBroadcaster.update_new_deal(...)
```

**New way:**
```python
from web import dashboard
dashboard.update_new_deal(...)
```

The API is identical, so migration is a simple import change.

## Testing

### Testing Components (Future)

Components are now testable with React Testing Library:

```javascript
import { render, screen } from '@testing-library/react';
import { Hand } from './Hand.js';

test('displays HCP correctly', () => {
    render(<Hand cards={['SA', 'SK']} ... />);
    expect(screen.getByText('7 HCP')).toBeInTheDocument();
});
```

### Testing Backend (Future)

State and broadcaster can be unit tested:

```python
def test_complete_trick():
    state = GameState()
    state.set_new_deal(...)
    state.add_card_to_trick('N', 'SA')
    state.complete_trick('N')
    assert state.get('tricks_won')['NS'] == 1
```

## Performance Considerations

- Components use `React.useMemo` to avoid unnecessary recalculations
- Socket.IO events are throttled where appropriate
- State updates are batched
- CDN resources cached by browser

## Future Enhancements

Possible additions with the new architecture:

1. **Build System**: Add Vite or Webpack for bundling
2. **TypeScript**: Add type safety to JavaScript
3. **Testing**: Add Jest + React Testing Library
4. **Linting**: Add ESLint + Prettier
5. **State Management**: Add Redux or Zustand if state grows
6. **Persistence**: Add database for game history
7. **Authentication**: Add user accounts
8. **Real-time Chat**: Add player communication
9. **Hand Analysis**: Add more detailed analysis views
10. **Replay System**: Review past games

## Troubleshooting

### Module Import Errors

If you see "Failed to resolve module", check:
- File paths are correct relative to HTML
- Files have `.js` extension in imports
- Flask static folder is configured correctly

### Socket.IO Connection Issues

If dashboard doesn't connect:
- Check Flask server is running
- Check port 5001 is not blocked
- Check browser console for errors
- Verify Socket.IO version matches client/server

### Component Not Rendering

If a component doesn't show:
- Check browser console for errors
- Verify props are passed correctly
- Check that component is exported/imported
- Use React DevTools to inspect component tree
