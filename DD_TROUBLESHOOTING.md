# DD Analysis Troubleshooting Guide

## Issue: "💭 No double dummy analysis available"

If you're seeing this message, it means the Python bot isn't receiving DD analysis from the Chrome extension. Here's how to diagnose and fix it.

## Step 1: Check Your Game Mode

**DD Analysis ONLY works when all 4 hands are visible:**

### ✅ Works In:
- **Casual/Social Tables** - All hands shown
- **Teaching Tables** - All hands shown  
- **Solitaire/Practice** - All hands shown
- **Review Mode** - After becoming dummy, reviewing past hands

### ❌ Doesn't Work In (Until You Become Dummy):
- **Tournament Play** - Only 2 hands visible (yours + partner's)
- **Competitive Play** - Can't see opponents' hands
- **Before Bidding Complete** - Not all hands dealt yet

**Why?** The DDS solver needs to know all 52 cards to calculate optimal play. This is a fundamental limitation of double dummy analysis.

## Step 2: Check Chrome Console

1. Open BBO in Chrome
2. Press `F12` to open DevTools
3. Click the "Console" tab
4. Look for these messages:

### What You SHOULD See (Good):
```
🧠 Requesting DD analysis for board 1
🧠 DD callback triggered for board 1 DD data: present
🧠 DD Result sent | Board: 1 | Cached: false
```

### What You MIGHT See (Problems):
```
⚠️ DD callback received but no tricks data
```
**Meaning:** BSOL returned data but it's malformed or missing

```
🧠 DD callback triggered for board 1 DD data: missing
```
**Meaning:** doubledummy() was called but BSOL didn't return data

```
(No messages at all)
```
**Meaning:** doubledummy() is not being called - extension not loaded or hands not complete

## Step 3: Check Extension Loaded

1. Go to `chrome://extensions/`
2. Find "BBO Helper" (or similar)
3. Make sure it's **Enabled** (toggle on)
4. Click the **Reload** button (↻ icon)
5. Go back to BBO tab and refresh (F5)

## Step 4: Join a Casual Table

To test if DD is working:

1. **Leave any tournament/competitive game**
2. Go to "Casual" section on BBO
3. Join a table where you can see all 4 hands
4. Wait for a new deal
5. Check console for "🧠 Requesting DD analysis..."

Within 100-500ms you should see:
- In **Chrome Console**: `🧠 DD Result sent`
- In **Python Terminal**: `🧠 DOUBLE DUMMY ANALYSIS RECEIVED`

## Step 5: Check Python Bot

Make sure your Python bot is running and connected:

### In Python Terminal You Should See:
```
🚀 Server running at ws://localhost:8675
✅ WebSocket client connected.
🎯 Received event: new_deal
============================================================
🃏 NEW DEAL - Board 1
   Dealer: N, Vul: None
============================================================
```

### If DD Analysis Arrives:
```
🧠 DOUBLE DUMMY ANALYSIS RECEIVED
============================================================
Double Dummy Trick Analysis:
                North    East     South    West
Spades:         5        7        5        7
...
```

## Step 6: Check Network

If BSOL service is down or slow:

1. Open Chrome DevTools → Network tab
2. Filter for "bridgewebs"
3. Look for requests to `dds.bridgewebs.com`
4. Check if they're returning 200 OK or timing out

**If requests are failing:**
- BSOL service might be down
- Your firewall might be blocking it
- Try again later

## Common Scenarios

### Scenario 1: Tournament Play
**Symptom:** Playing in a tournament, always shows "No DD analysis"

**Solution:** This is expected! DD only works when all hands are visible. Either:
- Wait until you become dummy (then all hands revealed)
- Review boards after play (all hands shown)
- Play casual games for live DD analysis

### Scenario 2: Extension Not Reloaded
**Symptom:** Made code changes, but still no DD

**Solution:**
1. Go to `chrome://extensions/`
2. Click reload on BBO Helper
3. Refresh BBO tab (F5)
4. Deal a new board

### Scenario 3: Wrong Extension Settings
**Symptom:** Extension has DD turned off

**Solution:** Our bot now **ignores** the extension setting and always requests DD. So this shouldn't be an issue anymore.

### Scenario 4: Python Bot Not Running
**Symptom:** Chrome console shows DD sent, but Python shows nothing

**Solution:**
1. Check Python terminal is running: `python3 bbo_bot.py`
2. Look for: `🚀 Server running at ws://localhost:8675`
3. Check WebSocket connected: `✅ WebSocket client connected.`
4. Check firewall isn't blocking port 8675

## Quick Test

Run this test to verify everything works:

1. **Start Python bot:**
   ```bash
   cd /Users/zbennett/git/bridge-bot-combined/bridge-bot
   python3 bbo_bot.py
   ```
   
2. **Reload extension:**
   - `chrome://extensions/` → Reload BBO Helper

3. **Join casual table:**
   - BBO → Casual → Any table with 4 visible hands

4. **Deal a board**

5. **Check both consoles:**
   - Chrome: Should see "🧠 DD Result sent"
   - Python: Should see "🧠 DOUBLE DUMMY ANALYSIS RECEIVED"

## If Still Not Working

Check these files were updated:

### zb-bbo/bbov3.js
```javascript
// Line ~954: Should NOT check pref.appDoubleDummyMode
if (app.deal.south !== 'SHDC' && app.deal.west !== 'SHDC' &&
    app.deal.north !== 'SHDC' && app.deal.east !== 'SHDC') {
    
    // Should have callback
    doubledummy(d, false, ddResultCallback);
}
```

### zb-bbo/bbov3.js
```javascript
// Line ~119: Callback should exist
function ddResultCallback(d, dd) {
  console.log('🧠 DD callback triggered...');
  // ... parse and send to Python
}
```

If these are correct and you're in a casual game with all hands visible, and it's still not working, there may be an issue with the BSOL service or your network.

## Understanding DD Analysis

Remember:
- **DD = Double Dummy** = Perfect information analysis
- **Requires:** All 4 hands visible
- **Provides:** Optimal trick count for each lead
- **Limitation:** Real bridge isn't double dummy!

In competitive play, you won't get DD until the hand is over or you become dummy. This is by design - you shouldn't see opponents' cards during live play!
