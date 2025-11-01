# System Flow Diagrams

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BridgeBase.com Website                    │
│  (Bridge game running in browser, WebSocket to BBO servers) │
└────────────────────────┬────────────────────────────────────┘
                         │ Native WebSocket traffic
                         │ <sc_deal>, <sc_call_made>, etc.
                         ↓
┌─────────────────────────────────────────────────────────────┐
│               WebSocket Sniffer (Extension)                  │
│  injectedsniffers.js - Extends WebSocket class              │
│  Intercepts ALL messages between BBO client ↔ BBO server    │
└────────────────────────┬────────────────────────────────────┘
                         │ Captured messages
                         ↓
┌─────────────────────────────────────────────────────────────┐
│          Main Extension Logic (bbov3.js)                     │
│  • Tracks game state in `app` object                        │
│  • Processes each message type                              │
│  • Requests Double Dummy from BSOL API                      │
│  • Sends updates via WebSocket                              │
└────────────────────────┬────────────────────────────────────┘
                         │ Custom WebSocket (localhost:8675)
                         │ JSON messages: {type, data}
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Python Bot (bbo_bot.py)                         │
│  • Receives game state updates                              │
│  • Parses hand data                                          │
│  • Displays cards in terminal                               │
│  • [Future] Makes AI decisions                              │
│  • [Future] Sends actions back to extension                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Message Flow

### New Deal Sequence

```
BBO Server                Extension               Python Bot
    │                         │                        │
    │──sc_deal──────────────→│                        │
    │ board="1"               │                        │
    │ south="SAK..."          │                        │
    │                         │                        │
    │                         │─ Parse deal            │
    │                         │─ Store in app.deal     │
    │                         │                        │
    │                         │──app_update───────────→│
    │                         │  {type: "app_update"}  │
    │                         │  {app: {...}}          │
    │                         │                        │
    │                         │                        │─ Display cards
    │                         │                        │
    │                         │─ Request DD from BSOL  │
    │                         │                        │
    │◄─HTTP GET────────────────│                        │
    │  dds.bridgewebs.com     │                        │
    │                         │                        │
    │──DD Results─────────────→│                        │
    │  {tricks: {...}}        │                        │
    │                         │                        │
    │                         │──double_dummy─────────→│
    │                         │  {dd: {...}}           │
    │                         │                        │
    │                         │                        │─ Display DD
```

### Bidding Sequence

```
User clicks "1NT"         Extension               Python Bot
    │                         │                        │
    │──cs_make_bid─────────→│                        │
    │  bid=1NT                │                        │
    │                         │                        │
    │                         │─ Update app.deal.auction
    │                         │                        │
    │                         │──bid_made─────────────→│
    │                         │  {call: "1NT"}         │
    │                         │                        │
    ↓                         ↓                        ↓─ Log bid
BBO Server receives        (Stored in state)      Display auction
```

### Card Play Sequence

```
User clicks card          Extension               Python Bot
    │                         │                        │
    │──cs_play_card────────→│                        │
    │  card=SA                │                        │
    │                         │                        │
    ↓                         │─ Update app.deal.play  │
BBO Server                    │─ Track trick           │
    │                         │                        │
    │──sc_card_played───────→│                        │
    │  card=SA                │                        │
    │                         │                        │
    │                         │──card_played──────────→│
    │                         │  {card: "SA"}          │
    │                         │                        │
    │                         │                        │─ Update display
    │                         │                        │─ Remove from hand
```

---

## Extension Architecture

```
┌───────────────────────────────────────────────────────────┐
│                     Chrome Extension                       │
│                                                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Background Service Worker (service.js)             │  │
│  │  • Extension lifecycle                              │  │
│  │  • Storage management                               │  │
│  │  • Cross-tab messaging                              │  │
│  └────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Injected Code (document_start)                     │  │
│  │  bbov3early.js → injectedsniffers.js                │  │
│  │  • Extends native WebSocket                         │  │
│  │  • Captures ALL BBO traffic                         │  │
│  │  • Fires custom events                              │  │
│  └────────────────────────────────────────────────────┘  │
│         │ Custom events: sniffer_ws_send,                 │
│         │                sniffer_ws_receive               │
│         ↓                                                  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Content Script (document_end)                      │  │
│  │  bbov3.js (Main Logic)                              │  │
│  │  • Listens to sniffer events                        │  │
│  │  • Maintains app.deal state                         │  │
│  │  • Processes message types                          │  │
│  │  • Connects to Python via WebSocket                 │  │
│  └────────────────────────────────────────────────────┘  │
│         │                                                  │
│         ↓                                                  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Injected into BBO context                          │  │
│  │  injectedbbo.js                                     │  │
│  │  • Auto-alerts                                      │  │
│  │  • Chat improvements                                │  │
│  │  • Shares PREF with content script                  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                             │
└───────────────────────────────────────────────────────────┘
```

---

## Python Bot Architecture (Current)

```
┌─────────────────────────────────────────────────────┐
│              bbo_bot.py (Main Server)                │
│                                                       │
│  ┌────────────────────────────────────────────────┐ │
│  │  WebSocket Server                               │ │
│  │  • Listens on localhost:8675                    │ │
│  │  • Accepts connection from extension            │ │
│  │  • Async message handling                       │ │
│  └────────────────────────────────────────────────┘ │
│           │                                           │
│           ↓                                           │
│  ┌────────────────────────────────────────────────┐ │
│  │  Message Handler                                │ │
│  │  • Parses JSON                                  │ │
│  │  • Routes by type                               │ │
│  │  •   app_update  → analyze_app()                │ │
│  │  •   double_dummy → handle_dd_result()          │ │
│  └────────────────────────────────────────────────┘ │
│           │                                           │
│           ↓                                           │
│  ┌────────────────────────────────────────────────┐ │
│  │  Game State Processing                          │ │
│  │  • Parse deal data                              │ │
│  │  • Convert LIN → Dot format                     │ │
│  │  • Remove played cards                          │ │
│  │  • Calculate HCP                                │ │
│  └────────────────────────────────────────────────┘ │
│           │                                           │
│           ↓                                           │
│  ┌────────────────────────────────────────────────┐ │
│  │  Terminal Display                               │ │
│  │  • Format hands with ANSI colors                │ │
│  │  • Show HCP                                     │ │
│  │  • Display DD results                           │ │
│  │  • Configurable seat rotation                   │ │
│  └────────────────────────────────────────────────┘ │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## Future Architecture (With AI)

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Bot (Enhanced)                     │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  WebSocket Server (Bidirectional)                       ││
│  │  ↓ Receive game state                                   ││
│  │  ↑ Send bot actions                                     ││
│  └─────────────────────────────────────────────────────────┘│
│       │                                       ↑               │
│       ↓                                       │               │
│  ┌─────────────────────────────────┐ ┌──────────────────┐  │
│  │  Game State Manager              │ │  Action Sender   │  │
│  │  • Current deal                  │ │  • Format action │  │
│  │  • Auction history               │ │  • Add timing    │  │
│  │  • Cards played                  │ │  • Send to ext.  │  │
│  │  • DD analysis                   │ └──────────────────┘  │
│  └─────────────────────────────────┘          ↑              │
│       │                                        │              │
│       ↓                                        │              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    AI Decision Engine                    ││
│  │                                                           ││
│  │  ┌──────────────────┐  ┌──────────────────┐            ││
│  │  │ Bidding Logic    │  │ Play Logic       │            ││
│  │  │ • System rules   │  │ • DD-based       │            ││
│  │  │ • HCP eval       │  │ • Legal moves    │            ││
│  │  │ • Shape eval     │  │ • Trick tracking │            ││
│  │  │ • DD integration │  │ • Line of play   │            ││
│  │  └──────────────────┘  └──────────────────┘            ││
│  │                                                           ││
│  │  ┌──────────────────────────────────────────────────┐  ││
│  │  │ Safety Module                                     │  ││
│  │  │ • Human-like timing                               │  ││
│  │  │ • Decision verification                           │  ││
│  │  │ • Error handling                                  │  ││
│  │  └──────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Data Flow Timeline

```
Time    BBO        Extension              Python Bot
────────────────────────────────────────────────────────────────
0.0s    Login      → Intercept            
        
1.0s    Table      → <sc_table_node>
                   → Update app.table
                   → Send table_info  →   Display table
                   
2.0s    Deal       → <sc_deal>
                   → Parse hands
                   → Update app.deal
                   → Request DD from BSOL
                   → Send deal_start  →   Display hands
                   
2.5s    DD         ← DD results
                   → Send double_dummy →  Display DD
                   
5.0s    Bid "1C"   → <sc_call_made>
                   → Update auction
                   → Send bid_made    →   Log auction
                   
8.0s    Bid "p"    → <sc_call_made>
                   → Update auction
                   → Send bid_made    →   Log auction
                   
[... more bidding ...]

20.0s   Card "S2"  → <sc_card_played>
                   → Update play
                   → Track trick
                   → Send card_played →   Update display
                   
[... more play ...]
```

---

## State Management

### Extension State Hierarchy

```
app
├── user (username)
├── table
│   ├── table_id
│   ├── players [4]
│   └── style
│
├── deal (current board)
│   ├── board
│   ├── dealer, vul
│   ├── auction []
│   ├── play []
│   ├── tricks []
│   ├── hands (SHDC format)
│   └── d (for DD)
│       ├── bnum
│       ├── dealer, vul
│       └── hand [] (dot format)
│
├── pendingDD {} (keyed by deal)
├── play {} (keyed by deal+player)
└── alert {} (keyed by deal+player)
```

### Python State (Proposed)

```
BridgeGameState
├── board_info
│   ├── board
│   ├── dealer
│   └── vul
│
├── hands {} (by seat)
│   ├── South []
│   ├── West []
│   ├── North []
│   └── East []
│
├── auction []
├── played_cards []
├── current_trick []
│
├── contract_info
│   ├── contract
│   ├── declarer
│   └── dummy
│
└── dd_analysis {}
    ├── cNS, cEW
    ├── sNS, sEW
    └── tricks {}
```

---

## Extension Injection Timeline

```
Page Load                    Injection Point               File
─────────────────────────────────────────────────────────────────
BBO page starts loading
                            ↓
                         document_start              bbov3early.js
                            │                             │
                            │ (injected ASAP)            │
                            ↓                             ↓
                         Inject script             injectedsniffers.js
                            │                       (extends WebSocket)
                            ↓
BBO loads its scripts
BBO creates WebSocket  →  Our extended WebSocket
                       ←  (captures all traffic)
                            │
[Page continues loading]    │
                            ↓
                         document_end                bbov3.js
                            │                    (main content script)
                            │ (page mostly ready)      │
                            ↓                          ↓
                         Add event listeners     Listen to sniffers
                         Inject more code        Connect to Python
                            │                          │
                            ↓                          ↓
                         Inject script            injectedbbo.js
                                              (auto-alerts, chat)
                            │
[Page fully loaded]         │
                            ↓
                         User logs in
                            ↓
                         Game starts
                            ↓
                    All systems operational!
```

---

## WebSocket Message Types (BBO → Extension)

```
Server Messages (sc_*)
├── Table Management
│   ├── sc_table_node        (new table)
│   ├── sc_table_close       (leave table)
│   ├── sc_player_sit        (player seated)
│   └── sc_player_stand      (player leaves)
│
├── Deal Management
│   ├── sc_deal              (new board)
│   ├── sc_deal_blast_complete
│   └── sc_dummy_holds       (dummy revealed)
│
├── Auction
│   ├── sc_call_made         (bid made)
│   └── sc_bid_explanation   (explanation added)
│
├── Play
│   ├── sc_card_played       (card played)
│   ├── sc_claim_accepted    (claim accepted)
│   └── sc_undo              (undo approved)
│
├── Info
│   ├── sc_loginok           (login successful)
│   ├── sc_user_details      (player profile)
│   └── sc_board_details     (full hand recap)
│
└── Meta
    ├── sc_context           (state change)
    ├── sc_stats             (statistics)
    └── sc_notify_user       (notification)
```

---

## Performance Considerations

### Current Bottlenecks

```
Extension → Python
│
├─ Problem: Sending full app object
│  Size: ~50-100KB per update
│  Frequency: Every message
│  Impact: HIGH
│  
├─ Solution: Event-based messages
│  Size: ~1-5KB per event
│  Impact: 10-50x reduction
│
└─ Benefit: Faster, cleaner, easier to debug
```

### Double Dummy Requests

```
Extension → BSOL API
│
├─ Latency: ~500-2000ms per request
├─ Caching: Yes (in app.pendingDD)
├─ Optimization: Only request once per deal
│
└─ Alternative: Local DDS solver
   Latency: ~50-200ms
   Tradeoff: Complexity vs speed
```

---

## Future: Bidirectional Flow

```
Python Bot                  Extension              BBO
    │                          │                    │
    │──Analyze game state      │                    │
    │                          │                    │
    │──Make decision           │                    │
    │   "1NT" / "SA"           │                    │
    │                          │                    │
    │──bot_action─────────────→│                    │
    │  {action: "bid",          │                    │
    │   value: "1NT"}           │                    │
    │                          │                    │
    │                          │─Find button        │
    │                          │─Add delay          │
    │                          │─Simulate click     │
    │                          │                    │
    │                          │──cs_make_bid──────→│
    │                          │  bid=1NT           │
    │                          │                    │
    │◄─confirmation────────────│                    │
    │  {success: true}         │                    │
```

---

This visual reference should help you understand the complete system architecture!
