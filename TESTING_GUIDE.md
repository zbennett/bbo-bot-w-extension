# Testing Guide - Event-Based Messaging

## Quick Test Steps

### 1. Start the Python Bot

```bash
cd /Users/zbennett/git/bridge-bot-combined/bridge-bot
python bbo_bot.py
```

You should see:
```
🚀 Server running at ws://localhost:8675
```

### 2. Load Chrome Extension

1. Open Chrome/Edge browser
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select folder: `/Users/zbennett/git/bridge-bot-combined/zb-bbo`
6. Extension should load with B++ icon

### 3. Visit BridgeBase Online

1. Go to https://www.bridgebase.com/
2. Log in (or play as guest)
3. Join any table (practice, solitaire, or real game)

### 4. Watch for Events

In your terminal where Python bot is running, you should see:

#### When Board Starts:
```
============================================================
🃏 NEW DEAL - Board 1
   Dealer: N, Vul: None
============================================================

                    North (HCP: 12)
              ♠: AKQ
              ♥: JT9
              ♦: 8765
              ♣: 432

West (HCP: 8)                       East (HCP: 14)
♠: 9876                             ♠: JT
♥: 8765                             ♥: AKQ
♦: KQ                               ♦: AJT9
♣: 987                              ♣: KQJ

                    South (HCP: 6)
              ♠: 5432
              ♥: 432
              ♦: 432
              ♣: AT6
```

#### When Bid Made:
```
📢 Bid: 1NT (after 3.45s)
```

#### When Card Played:
```
🎴 Card played: ♠A (1 cards played)
[Hand display updates with card removed]
```

#### When Claim Accepted:
```
✅ Claim accepted: 9 tricks
============================================================
```

### 5. Check Chrome DevTools Console

1. Press F12 in Chrome
2. Go to Console tab
3. You should see BBO Helper messages like:
   ```
   1NT call made after 3.450 sec
   BBO Helper: board 1 dealt at table 12345
   ```

### 6. Verify WebSocket Connection

In Chrome DevTools Console, you can check connection status:
```javascript
// This is automatically available if extension loaded correctly
console.log("WebSocket connected:", socket && socket.readyState === WebSocket.OPEN);
```

## Expected Event Sequence

A typical board will generate these events in order:

1. `new_deal` - Board dealt, all hands received
2. `bid_made` - First bid (dealer)
3. `bid_made` - Second bid
4. `bid_made` - Third bid
5. ... (more bids until auction ends)
6. `card_played` - Opening lead
7. `card_played` - Second card
8. ... (52 cards total, or until claim)
9. `claim_accepted` - If someone claims (optional)

## Troubleshooting

### Python Bot Not Connecting

**Problem:** Extension loads but Python bot shows no connection

**Check:**
1. Is Python bot running? (Should show "Server running...")
2. Is port 8675 free? Bot will auto-find next port if busy
3. Does extension have correct port? Check `bbov3.js` line ~45: `const socket = new WebSocket('ws://localhost:8675');`

**Solution:**
```bash
# Check if port is in use
lsof -i :8675

# Kill process using port (if needed)
kill -9 <PID>
```

### No Events Appearing

**Problem:** Bot connects but no events show up

**Check:**
1. Are you at an active BBO table? (Not just logged in)
2. Check Chrome DevTools Console for JavaScript errors
3. Check Python terminal for error messages

**Solution:**
- Refresh BBO page (F5)
- Reload extension (chrome://extensions/)
- Restart Python bot

### Wrong Hand Format

**Problem:** Hands display incorrectly or show "?"

**Check:**
1. LIN format parsing in `parse_lin_hand()` 
2. Hands might be in different format than expected

**Debug:**
```python
# Add this to handle_game_event() in new_deal section:
print("DEBUG - Raw hands:", event_data.get("hands"))
```

### Cards Not Removing When Played

**Problem:** Card played events received but display doesn't update

**Check:**
1. Is `hands_dict_cache` populated?
2. Are suit/rank being parsed correctly from card string?

**Debug:**
```python
# Add to card_played handler:
print(f"DEBUG - Removing {suit}{rank} from hands")
print(f"DEBUG - Hands before:", hands_dict_cache)
```

## Performance Testing

### Measure Data Transfer

**Before (old system):**
```javascript
// In Chrome DevTools, monitor WebSocket frames
// Each message ~50-100KB

// Add this temporarily to bbov3.js after sendAppToPython():
console.log("Sent app object:", JSON.stringify(app).length, "bytes");
```

**After (new system):**
```javascript
// Add this temporarily after sendGameEvent():
console.log("Sent event:", eventType, JSON.stringify(data).length, "bytes");
```

You should see 90-95% reduction in bytes sent!

### Expected Sizes

- `new_deal`: ~500-1000 bytes (has 4 hands)
- `bid_made`: ~100-200 bytes
- `card_played`: ~50-100 bytes  
- `claim_accepted`: ~50-100 bytes

## Next Tests (After Basic Events Work)

1. **Test becoming dummy** - See if hands update correctly
2. **Test different table types** - Solitaire, practice, tournament
3. **Test bidding tables** - Do bid events work?
4. **Test teaching tables** - Do all events fire?
5. **Stress test** - Join fast-paced game, ensure no events dropped

## Advanced: Monitor All Traffic

To see ALL WebSocket traffic (BBO and our bot):

```javascript
// Paste in Chrome DevTools Console:
const originalSend = WebSocket.prototype.send;
WebSocket.prototype.send = function(data) {
    console.log('WS SEND:', data);
    return originalSend.apply(this, arguments);
};
```

This will show you every message sent, helpful for debugging!

## Success Criteria

✅ Python bot starts without errors  
✅ Extension loads in Chrome  
✅ WebSocket connects (see "WebSocket client connected")  
✅ New deal displays board and hands  
✅ Bids are logged in real-time  
✅ Cards removed from hands when played  
✅ Claim ends board cleanly  
✅ No JavaScript errors in console  
✅ No Python exceptions in terminal  

If all these pass, Step 1 is COMPLETE! 🎉
