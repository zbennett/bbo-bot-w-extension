# Data Structures Reference

## Key Objects and Their Structure

### 1. `app` Object (Extension Side - bbov3.js)

The main state tracking object in the Chrome extension:

```javascript
app = {
    // Core state
    "startTime": 1699000000000,        // Epoch timestamp
    "user": "playerhandle",            // Logged in user
    "lang": "en",                      // UI language
    
    // Current table
    "table": {
        "table_id": "3024185",
        "style": "t-pairs",            // Tournament style
        "type": "7",                   // Table type
        "title": "ACBL Pairs",
        "tkey": "14873~ACBL",
        "h": "hostname",               // Host
        "players": [                   // Clockwise from South
            "south_player",
            "west_player", 
            "north_player",
            "east_player"
        ],
        "myseatix": 0                  // Your seat (0-3)
    },
    
    // Current deal
    "deal": {
        "board": "1",
        "table_id": "3024185",
        "dealer": "N",                 // N, E, S, W
        "vul": "None",                 // None, N-S, E-W, Both
        
        // Hands in LIN format (Spades+Hearts+Diamonds+Clubs)
        "south": "SAKQJHAKQJDAKQJCAKQ",
        "west": "ST98HT98DT98CT9876",
        "north": "S765H765D765C5432",
        "east": "S432H432D432CJQKA",
        
        // Full deal object (for DD)
        "d": {
            "bnum": 1,
            "dealer": "N",
            "vul": "None",
            "hand": [                  // Dot notation
                "S.AKQ.AKQ.AKQJ",      // South
                "S.T98.T98.T987",      // West
                "S.765.765.5432",      // North
                "S.432.432.JQKA"       // East
            ],
            "source": "session"
        },
        
        // Bidding
        "auction": ["1C", "p", "1H", "p", "1N", "p", "3N", "p", "p", "p"],
        "auctionOpenIx": 0,            // Index of opening bid
        "actionTime": [0, 2.5, 3.1, ...], // Time for each action (seconds)
        "lastActionTime": 1234567890,  // Timestamp of last action
        
        // Play
        "play": ["S2", "S3", "SK", "S4", ...], // Cards played
        "seenOpeningLead": true,
        "ncardsPlayed": 12,
        
        // Trick tracking
        "tricks": [
            {
                "leader": 1,           // 0=S, 1=W, 2=N, 3=E
                "cards": ["S2", "S3", "SK", "S4"]
            }
        ],
        
        // Flags
        "blast1_complete": true,       // Deal data received
        "blast2_complete": false,
        "amDummy": false,
        "timingSaved": false,
        "dealkey": "1+south+west+north+east",
        
        // Contract info (populated after auction)
        "contract": "3NT",
        "declarer": 0,                 // Seat index
        "denom": "N"                   // Trump suit or NT
    },
    
    // Double dummy tracking
    "pendingDD": {
        "N:QJ6.K52.J85.A763 AK873.QJ9.6.QJ42 T5.T7643.KT4.K85 942.A8.AQ9732.T9": {
            "requested": 1699000000,
            "callback": function() {...}
        }
    },
    
    // Card play storage (by deal)
    "play": {
        "S.AKQ.AKQ.AKQJ+...+south_player": {
            "cardplay": ["S2", "S3", ...],
            "nclaimed": 2              // Tricks claimed
        }
    },
    
    // Alert storage
    "alert": {
        "S.AKQ.AKQ.AKQJ+...+south_player": [
            "15-17",                   // Alert for 1st bid
            undefined,                 // No alert for 2nd bid
            "4+ spades"                // Alert for 3rd bid
        ]
    },
    
    // Locale/language support
    "locale": {
        "seatName": ["South", "West", "North", "East"],
        "seatLetters": "SWNE",
        "honorLetters": "JQKA",
        "pass": "Pass",
        "dbl": "Dbl",
        "rdbl": "Rdbl",
        "nt": "NT"
    }
}
```

---

## 2. Double Dummy Object

Structure of DD results from BSOL:

```javascript
dd = {
    // Optimal contracts
    "cNS": "3NT",              // Best contract for North-South
    "cEW": "4S",               // Best contract for East-West
    "sNS": 400,                // Score for NS contract
    "sEW": -400,               // Score for EW contract
    
    // Trick table - [Seat][Strain]
    "tricks": {
        "N": {                 // North's tricks as declarer in:
            "S": 9,            //   Spades
            "H": 8,            //   Hearts
            "D": 7,            //   Diamonds
            "C": 10,           //   Clubs
            "N": 9             //   Notrump
        },
        "S": { "S": 9, "H": 8, "D": 7, "C": 10, "N": 9 },
        "E": { "S": 4, "H": 5, "D": 6, "C": 3, "N": 4 },
        "W": { "S": 4, "H": 5, "D": 6, "C": 3, "N": 4 }
    },
    
    // Metadata
    "wasCached": false,        // From cache vs fresh request
    "bsolDeal": "N:QJ6.K52...", // Deal string used for BSOL
    "requestTime": 123456789   // When requested
}
```

---

## 3. Deal Object (`d`)

Used for DD requests and board display:

```javascript
d = {
    "bnum": 1,                 // Board number
    "bstr": " 1",              // Board as string (with padding)
    "dealer": "N",             // N, E, S, W
    "vul": "None",             // None, N-S, E-W, Both
    
    // Hands
    "hand": [                  // Dot notation (S.H.D.C)
        "S.AKQ.AKQ.AKQJ",      // South [0]
        "S.T98.T98.T987",      // West  [1]
        "S.765.765.5432",      // North [2]
        "S.432.432.JQKA"       // East  [3]
    ],
    "deal": "W:T98.T98.T987:765.765.5432:432.432.JQKA:AKQ.AKQ.AKQJ",
    // Format: "FirstHand:W:N:E:S" (GIB/PBN format)
    
    // Player names
    "name": ["South", "West", "North", "East"],
    
    // Auction
    "auction": ["1C", "p", "1H", "p", "1N", "p", "3N", "p", "p", "p"],
    "auctionstr": "1C p 1H p; 1N p 3N p; p p",
    
    // Contract (parsed from auction)
    "contract": "3NT",
    "contractLevel": 3,
    "contractDenom": "N",
    "doubled": "",             // "", "X", or "XX"
    "declarer": "S",
    "declarerIx": 0,           // Seat index
    
    // Result (if known)
    "tNS": 9,                  // Tricks taken by NS
    "tEW": 4,                  // Tricks taken by EW
    "result": "+1",            // Over/under contract
    "score": 430,
    
    // Card play
    "cardplay": ["S2", "S3", "SK", "S4", ...],
    "nclaimed": 0,             // Tricks claimed
    
    // HCP info
    "hcp": [12, 8, 10, 10],    // HCP for each seat
    "whohas": {                // Who has each card
        "SA": 0,               // South (seat 0)
        "SK": 0,
        "HA": 2,               // North (seat 2)
        // etc...
    },
    
    // Timing (if available)
    "auctionTimes": [2.5, 3.1, 4.2, ...],
    "playTimes": [2.1, 3.5, 1.8, ...],
    
    // Metadata
    "source": "session",       // "session", "review", "prefetch"
    "isVugraph": false,
    "datestr": "2024-01-01 14:30",
    "title": "ACBL Pairs",
    
    // Double dummy result (if computed)
    "dd": { /* dd object */ }
}
```

---

## 4. Card Formats

### LIN Format (BBO native)
```
SAKQJHAKQJDAKQJCAKQJ
```
- All 13 cards concatenated
- Order: Spades, Hearts, Diamonds, Clubs
- T = 10

### Dot Format (Standard)
```
AKQ.AKQ.AKQJ.AKQ
```
- Suits separated by dots
- Order: Spades.Hearts.Diamonds.Clubs
- Empty suit: just dot (`.`)

### PBN/GIB Format (for DD solvers)
```
N:QJ6.K52.J85.A763 AK873.QJ9.6.QJ42 T5.T7643.KT4.K85 942.A8.AQ9732.T9
```
- First hand (after colon) is dealer's seat
- Hands in rotation: 1st, 2nd (dealer's LHO), 3rd (partner), 4th (RHO)
- Suits in order: Spades.Hearts.Diamonds.Clubs

### Individual Card
```
"SA"  // Spade Ace
"HK"  // Heart King
"D2"  // Diamond 2
"CT"  // Club 10
```

---

## 5. BBO WebSocket Messages

### Server to Client (sc_*)

#### New Deal
```xml
<sc_deal table_id="123" board="1" dealer="N" vul="None"
  south="SAKQ..." west="..." north="..." east="..."/>
```

#### Bid Made
```xml
<sc_call_made table_id="123" call="1NT" alert="Y" 
  explain="15-17 balanced"/>
```

#### Card Played
```xml
<sc_card_played table_id="123" card="SA"/>
```

#### Dummy Revealed
```xml
<sc_dummy_holds table_id="123" board="1" dummy="S456..."/>
```

#### Claim
```xml
<sc_claim_accepted table_id="123" tricks="10"/>
```

#### Full Board
```xml
<sc_board_details>
  <sc_deal board="1" dealer="N" vul="None" ...>
    <sc_call_made call="1C" explain="..."/>
    <sc_card_played card="S2"/>
    ...
  </sc_deal>
</sc_board_details>
```

### Client to Server (cs_*)

#### Make Bid
```
cs_make_bid|table_id=123|bid=1NT|alert=y|explanation=15-17
```

#### Play Card  
```
cs_play_card|table_id=123|card=SA
```

---

## 6. Seat Indexing

### BBO Convention
```
Seats:  [0]=South, [1]=West, [2]=North, [3]=East
Order:  Clockwise from South
```

### Dealer Notation
```
"N" = North, "E" = East, "S" = South, "W" = West
```

### Vulnerability
```
"None" = No one vulnerable
"N-S"  = North-South vulnerable
"E-W"  = East-West vulnerable  
"Both" = Both vulnerable
```

### Board to Dealer/Vul Mapping
```python
def board_to_dealer_vul(board_num):
    dealer = ["N", "E", "S", "W"][board_num % 4]
    
    vul_map = {
        0: "None",   # Boards 1, 5, 9, 13
        1: "N-S",    # Boards 2, 6, 10, 14
        2: "E-W",    # Boards 3, 7, 11, 15
        3: "Both"    # Boards 4, 8, 12, 16
    }
    vul = vul_map[(board_num - 1) % 4]
    
    return dealer, vul
```

---

## 7. Auction Notation

### Call Types
```
"p"    = Pass
"d"    = Double
"r"    = Redouble
"1C"   = One Club
"1NT"  = One Notrump
"7NT"  = Seven Notrump
```

### Alert Markers
```javascript
auction = ["1C", "p", "1H", "p", "1N!"]  // ! = alerted bid
alerts = [
    "Could be short",  // For 1C
    undefined,         // No alert
    undefined,         // No alert
    undefined,         // No alert
    "15-17"           // For 1NT
]
```

---

## 8. Python Game State

Structure of BridgeGameState in Python bot:

```python
class BridgeGameState:
    def __init__(self):
        # Board info
        self.board = None
        self.dealer = None
        self.vul = None
        
        # Hands (after removing played cards)
        self.hands = {
            'South': ['SA', 'SK', 'SQ', ...],
            'West': [...],
            'North': [...],
            'East': [...]
        }
        
        # Auction
        self.auction = ['1C', 'p', '1H', 'p', '1N', 'p', '3N', 'p', 'p', 'p']
        
        # Play
        self.played_cards = ['S2', 'S3', 'SK', 'S4', ...]
        self.current_trick = ['S2', 'S3', 'SK', 'S4']
        self.tricks_won = {
            'NS': 5,
            'EW': 2
        }
        
        # Contract
        self.contract = '3NT'
        self.declarer = 'South'
        self.dummy = 'North'
        
        # Double Dummy
        self.dd_analysis = {
            'cNS': '3NT',
            'tricks': {...}
        }
```

---

## Conversion Functions

### LIN to Dot Format
```python
def lin_to_dot(lin_hand):
    """Convert SAKQJHAKQJDAKQJCAKQJ to AKQ.AKQ.AKQJ.AKQ"""
    suits = {'S': [], 'H': [], 'D': [], 'C': []}
    current_suit = None
    
    for char in lin_hand:
        if char in 'SHDC':
            current_suit = char
        else:
            suits[current_suit].append(char)
    
    return '.'.join([
        ''.join(suits['S']) or '',
        ''.join(suits['H']) or '',
        ''.join(suits['D']) or '',
        ''.join(suits['C']) or ''
    ])
```

### Dot to LIN Format  
```python
def dot_to_lin(dot_hand):
    """Convert AKQ.AKQ.AKQJ.AKQ to SAKQJHAKQJDAKQJCAKQJ"""
    suits = dot_hand.split('.')
    return ''.join([
        'S' + suits[0],
        'H' + suits[1],
        'D' + suits[2],
        'C' + suits[3]
    ])
```

---

## Additional Resources

- See `ARCHITECTURE.md` for system overview
- See `ROADMAP.md` for development plan
- BBO Helper source: Based on Matthew Kidd's work
