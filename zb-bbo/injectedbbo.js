/*
 *  injectedbbo.js - Adds functionality to BBO application
 *  
 *  BBO Helper browser add-on (Matthew Kidd, San Diego)
 *
 *  Additional code that is injected into the BBO's context using chrome.scripting
 *  API for Manifest V3 at document_end. Note: The WebSocket and XMLHttpRequestsniffers
 *  are added very early (document_start); see injectedsniffers.js
 *  
 */


// Listen for user preference updates
document.addEventListener('pref_update', prefUpdate);

// Listen for localization information
document.addEventListener('locale_update', localeUpdate);

// Request initial preferences
document.dispatchEvent( new CustomEvent("pref_request") );

// User can request a specific language for the BBO interface, e.g. Romanian with
// https://www.bridgebase.com/v3/?lang=ro, otherwise it will use the primary language
// set in the browser.
app.lang = new URLSearchParams(window.location.search).get('lang') ?? navigator.language;
if ( app.lang.indexOf('-') !== -1 ) {
	// Convert regional locale designations such as 'en-US' to 'en'. BBO doesn't
	// support regional locale designations such as 'es-419'.
	app.lang = app.lang.substring( 0, app.lang.indexOf('-') );
}
app.isLocaleRomanian = app.lang === 'ro';

const MAX_ALERT_MESSAGE_LENGTH = 39;


function prefUpdate(e) {
	// Load updated user preferences.
	console.info('BBO Helper: received updated user preferences.');
	pref = e.detail;
}

function localeUpdate(e) {
	// Load updated user preferences.
	console.info('BBO Helper: received locale information.');
	app.locale = e.detail;
	
	// Compute once. Used for suit substitution code in the ChatFixer()
	app.locale.honorOrderMatching = 
		app.locale.honorLetters.slice(3,4) + '?' + app.locale.honorLetters.slice(2,3) + '?' +
		app.locale.honorLetters.slice(1,2) + '?' + app.locale.honorLetters.slice(0,1) + '?';
}

function explanationSubs(explanation) {
	// Explanation substitutions for <cs_make_bid> and <cs_bid_explanation>
	// messages.
	
	const substitutions = {
		"c1":   "First round control",
		"c2":   "Second round control",
		"c12":  "First or second round control",
		"cc1":  "Cheapest first round control",
		"cc2":  "Cheapest second round control", 
		"cc12": "Cheapest first or second round control",
		"f1":   "Forcing for one round",
		"gf":   "Game forcing",
		"nf":   "Non-forcing",
		"nfc":  "Non-forcing constructive",
		"nat":	"Natural",
		"p/c":  "Pass or correct",
		"pen":  "Penalty",
		"to":	"Takeout",
		"t/o":	"Takeout",
		"hs":   "Help suit",
		"hsgt": "Help suit game try",
		"xf":   "Transfer",			
		"un":   "Undiscussed" };
	
	const sub = substitutions[ explanation.trim().toLowerCase() ];
	if (sub !== undefined) { auctionAlertMessage(sub, 'sub'); }	
	
	return sub;
}

function processAuctionCall(msg) {

	const alertSuffix = ' [B++]';
	let pos = msg.search('\x01bid=');
	let cc = msg.charCodeAt(pos+5);
	let call = (cc < 49 || cc > 55) ? msg.charAt(pos+5) : msg.slice(pos+5, pos+7);
	
	// BBO uses lowercase p,d,r for Pass, Double, and Redouble in 
	// <sc_call_made> and uppercase in <cs_make_bid>. Normalize to lowercase.
	let lowercall = call.length === 2 ? call : call.toLowerCase();
	app.deal.auction.push(lowercall);
	if (app.deal.auctionOpenIx === -1 && call.length === 2) {
		// Record index of opening bid.
		app.deal.auctionOpenIx = app.deal.auction.length - 1;
	}
	
	let hasExplanation = msg.search('\x01explanation=\x01') === -1;
	if ( hasExplanation || pref.appAutoAlerts ) {
		let bModifiedMessage = hasExplanation;
		let alert;
	
		if (pref.appAutoAlerts && !hasExplanation) {
			// See if there is an automatic alert to add. Wrap in a try block
			// because Auto Alerting is complex. Don't let an error cause a 
			// call not to go out.
			try {
				alert = autoAlert();
				if (alert !== undefined && alert.length > 0) {
					// Either fully include the Auto Alert flag or do not include it.
					if (pref.appAutoAlertsFlag &&
						(alert.length + alertSuffix.length <= MAX_ALERT_MESSAGE_LENGTH) ) { 
							alert += alertSuffix;
					}
					console.info('BBO Helper: adding alert:', alert);
					bModifiedMessage = true;
				}
			}
			catch(e) { console.error('BBO Helper: autoAlert() error', e); }
		}
		
		if (bModifiedMessage) {
			// Rebuild the outgoing message.
			let fd = msg.slice(0,-1).split('\x01');
			for (let i=1; i<fd.length; i++) {
				if (fd[i] === 'alert=n') { fd[i] = 'alert=y'; }
				else if (fd[i].startsWith('explanation=') ) {
					if (!hasExplanation) {
						fd[i] = 'explanation=' + alert.slice(0, MAX_ALERT_MESSAGE_LENGTH);
					}
					else if ( pref.appAlertSubstitutions ) {
						let explanation = fd[i].slice('explanation='.length);
						// Convenient substitutions.
						const sub = explanationSubs(explanation);
						if (sub !== undefined) { explanation = sub;	}
						
						// Add explanation mark before bare suit letters. Added apostrophe
						// in 1.4.9 in first class of the regular expression to address issue 
						// reported by Gabe Foster where possessives like "partner's" were
						// getting converted to "partner'!s"
						const rg = /(?<![a-zA-Z!'])([cdhs])(?![a-zA-Z])/gi;
						explanation = explanation.replace(rg, '!$1');
						
						explanation = explanation.slice(0, MAX_ALERT_MESSAGE_LENGTH);
						fd[i] = 'explanation=' + explanation;
					}
				}
			}
			
			msg = fd.join('\x01') + '\x00';
		}
		
		// Inform user that we automatically added an alert.
		if (bModifiedMessage && !hasExplanation) { auctionAlertMessage(alert, 'auto'); }
	}
	
	return msg;
}

function processCallExplanation(msg) {
	// Handle <cs_bid_explanation> messages where user is asked for an explanation
	// of a call or amends their original explanation.
	
	if ( !pref.appAlertSubstitutions ) { return msg; }

	let fd = msg.slice(0,-1).split('\x01');
	for (let i=1; i<fd.length; i++) {
		if ( !fd[i].startsWith('explanation=') ) { continue; }
		
		let explanation = fd[i].slice('explanation='.length);
		let sub = explanationSubs(explanation);
		if (sub !== undefined) { explanation = sub;	}
						
		// Add explanation mark before bare suit letters.
		const rg = /(?<![a-zA-Z!])([cdhs])(?![a-zA-Z])/gi;
		explanation = explanation.replace(rg, '!$1');
			
		explanation = explanation.slice(0, MAX_ALERT_MESSAGE_LENGTH);
		fd[i] = 'explanation=' + explanation;
	}
	
	// Rebuild the outgoing message.
	msg = fd.join('\x01') + '\x00';
	
	return msg;
}	

function chatFixer(t, baresuit) {
	// Improves a chat or claim message by automatically inserting ! for suit symbols
	// when message contains items that look like bids, cards, or hands. For claims
	// bare suit letters are substituted as well.
	
	if (t === '/') { t = app.greeting; }
	else if ( t.startsWith('/')) {
		t = t.slice(1);
		app.greeting = t;
	}
	
	if (pref.appChatNameSubs) {
		// "South" conflicts with "Spades" for substitution. Use 't' instead.
		t = t.replace(/(?<![\w])!([twne])(?!\w)/gui, namesub);
	}
	
	function namesub(match, seat) {
		if (seat.charCodeAt(0) < '96') {
			// Return seat name for uppercase, e.g. !N --> North
			return seat === 'T' ? 'South' : seat === 'W' ? 'West' : seat === 'N' ?
					'North' : 'East';
		}
		else {
			let ix = seat === 't' ? 0 : seat === 'w' ? 1 : seat === 'n' ? 2 : 3;
			if (app.table !== undefined && app.table.players[ix] !== '') {
				return app.table.players[ix];
			}
			return seat === 't' ? 'South' : seat === 'w' ? 'West' : seat === 'n' ?
					'North' : 'East';				
		}
	}
	
	if (!pref.appChatAutoSuits) { return t; }
	
	function uppercase(x) { return x.toUpperCase(); }
	
	// First capitalize anything that looks like a notrump bid. This uses
	// the negative lookbehind (?<!) and negative lookahead (?!) search operators.
	// Using [\p{L}\p{N}] (Unicode attributes for letter-like and number-like),
	// instead of \w which is limited to the Latin alphabet. Using this required
	// the u flag. 
	//
	// See https://unicode.org/reports/tr18/#General_Category_Property

	// Add ! mark to calls. First argument to the anonymous function is the full
	// match which we don't need. The {} destructuring assignment in the first
	// argument avoids a lint warning for an unused argument. Do this before 
	// notrump in case language specific local for notrump starts with an English
	// suit symbol (e.g. 'SA' = 'San Atout' in French starts with 'S' = spades).
	t = t.replace(/(?<![\p{L}\p{N}])([1-7])([cdhs])(?![\p{L}\p{N}])/gui, '$1!$2');

	// Always support NT for notrump for calls, irrespective of language.
	t = t.replace(/(?<![\p{L}\p{N}])[1-7]nt?(?![\p{L}\p{N}])/gui, uppercase);

	if (app.lang !== 'en' && app.locale.nt !== undefined && app.locale.nt !== 'nt') {
		// Locale specific support (e.g. SA in French)
		const re = new RegExp( "(?<![\p{L}\p{N}])[1-7]" + app.locale.nt +
			 "?(?![\p{L}\p{N}])", "gui" );
		t = t.replace(re, uppercase);
	}
	
	// Now look for things that appear to be suits (a single card is a special case)
	function suitfix(match, suit, cards) {
		// Don't convert a bare letter to a suit symbol except in claims.
		if (match.length === 1 && !baresuit) { return match; }
		// Don't convert uppercase SA or CA because SA often means "Standard American"
		// and CA often means California. Also leave Hx for Honor-doubleton.
		if (match === 'SA' || match === 'CA' || match === 'Hx') { return match; }
		
		// Don't convert common Romanian words. Can use cA, dA, or sA instead.
		if ( app.isLocaleRomanian && match.match(/^[cdsCDS]a$/) ) { return match; }
		
		// Don't convert SAT, HAT, DAT (for consistency), or CAT (all common English
		// words), unless exactly sAT, hAT, dAT, cAT
		if (match.search( /^[cdhs]AT$/ ) === -1 &&  match.search( /^[cdhs]at$/i ) === 0) {
			return match;
		}
		
		// Want to cards to be uppercase but any 'x' for small cards as lowercase
		ix = cards.indexOf('x');
		if (ix === -1) { cards = cards.toUpperCase(); }
		else { cards = cards.slice(0,ix).toUpperCase() + cards.slice(ix); }

		return ('!' + suit + cards);
	}

 	// Important again to use [\p{L}\p{N}] instead of \w in the regular expression, for
 	// example so that Danish word for 'East' does not convert 'st' at end of the word;
 	// probably relevant for other languages too. Include apostrophe in the negative look 
 	// behind so that 's' at the end of an a possessive is not converted to a spade symbol 
 	// (assuming other conditions are met. Cards in a suit must be rank ordered for it to 
 	// be recognized. Any number of 'x' symbols may follow last card to indicate small cards.
 	// Added 'https?://\S*'and 'www.' to prevent subsitution in URLs like things that BBO 
 	// automatically hyperlinks, e.g. prevent dk --> !dk for .dk (Denmark). Note: does not 
 	// check for fully compliant URL, just anything resembling one.
 	//
 	// Use RexExp() constructor to break up this long regular expression. Need \\p{L} etc to 
 	// escape \p{L} that we want!
 	const suitRE = new RegExp(
		"(?<![\\p{L}\\p{N}'!]|https?://\\S*|www\\.\\S*)" +
		"([cdhs])(" + app.locale.honorOrderMatching + "(T|10)?9?8?7?6?5?4?3?2?x*)" +
		"(?![\\p{L}\\p{N}])", "giu");

	t = t.replace(suitRE, suitfix);
	
	return t;
}

function websocketReceive(msg) {
	// Track app information that we need on the injection side, e.g. the auction
	// so that we can automatically add alerts for some common auctions.
	
	const mtype = msg.slice(1, msg.search(' '));

	if (mtype === 'sc_card_played') {
		// Tracked just to handle undos properly.
		app.deal.ncardsPlayed++;
	}
	else if (mtype === 'sc_call_made' && app.deal !== undefined) {
		// This is probably faster than the DOM parser for this common message.
		// Include leading space as small defense against 'call=' appearing in
		// the explanation for a call.
		let pos = msg.search(' call=');
		let cc = msg.charCodeAt(pos+7);
		let call = (cc < 49 || cc > 55) ? msg.charAt(pos+7) : msg.slice(pos+7,pos+9);
		app.deal.auction.push(call);
		if (app.deal.auctionOpenIx === -1 && call.length === 2) {
			app.deal.auctionOpenIx = app.deal.auction.length - 1;
		}
	}
	else if (mtype === 'sc_deal') {
		const parser = new DOMParser();
		let doc = parser.parseFromString(msg, "application/xml");
		app.deal = stuffAttributes( doc.getElementsByTagName('sc_deal')[0] );
		app.deal.auction = [];
		app.deal.auctionOpenIx = -1;
		app.deal.ncardsPlayed = 0;
		// Hide auction clock until first call if it is in use.
		let el = document.getElementById('bhAuctionClock');
		if (el !== null) { el.hidden = true; }
	}
	else if (mtype === 'sc_table_node') {
		const parser = new DOMParser();
		let doc = parser.parseFromString(msg, "application/xml");
		app.table = stuffAttributes( doc.getElementsByTagName('sc_table_open')[0] );
		app.table.players = ['', '', '', ''];
	}
	else if (mtype === 'sc_player_sit') {
		const parser = new DOMParser();
		let el = parser.parseFromString(msg, "application/xml").children[0];
		let seat = el.getAttribute('seat');
		let ix = seat === "south" ? 0 : seat === "west" ? 1 : seat === "north" ? 2 : 3;
		app.table.players[ix] = el.getAttribute('username');  // label works too.
	}
	else if (mtype === 'sc_player_stand' && app.table !== undefined) {
		// Need second condition above because when you leave a table, that 
		// generates a <cs_leave_table> message, followed by a <sc_table_close>
		// response from the server. The <sc_player_stand> for you comes after that.
		const parser = new DOMParser();
		let el = parser.parseFromString(msg, "application/xml").children[0];
		let seat = el.getAttribute('seat');
		let ix = seat === "south" ? 0 : seat === "west" ? 1 : seat === "north" ? 2 : 3;
		app.table.players[ix] = '';
	}
	else if (mtype === 'sc_table_close') {
		app.table = undefined;
		app.deal = undefined;
	}
	else if (mtype === 'sc_undo') {
		// Undo handling occurs both in the injected code and in bbov3.js
		// which have independent APP variables, tracking state. The undo is
		// simpler here since we only care about rolling back the auction if
		// necessary (to handle auto alerts properly).	
		let undoCountMatch = msg.match( /(?<= count=")\d+(?=")/ );
		if (undoCountMatch === null) { return; }
		let undoCount = parseInt( undoCountMatch[0] );
		
		const positionMatch = msg.match( /(?<= position=")\W+(?=")/ );
		const position = positionMatch !== null ? positionMatch[0] : undefined;
		
		// Case of count="0" position="*" is confusing. Still looks like one action
		// must be rolled back. Perhaps "*" means next seat has not acted yet.
		if (undoCount === 0 && position === '*') { undoCount = 1; }			

		if (app.deal.ncardsPlayed >= undoCount) {
			app.deal.ncardsPlayed -= undoCount;
		}
		else {
			// Rollback is partly or completely in the auction.
			let nCallsUndone = undoCount - app.deal.ncardsPlayed;
			app.deal.auction.length = app.deal.auction.length - nCallsUndone;
			app.deal.ncardsPlayed = 0;
	
			if (app.deal.auctionOpenIx > app.deal.auction.length - 1) {
				// Rolled back past the opening bid
				app.deal.auctionOpenIx = -1;
			}
		}
	}
	else if (mtype === 'sc_loginok') {
		const parser = new DOMParser();
		let doc = parser.parseFromString(msg, "application/xml");
		let el = doc.getElementsByTagName('sc_loginok')[0];
		app.user = el.getAttribute('user');
		app.usersp = el.getAttribute('sp');
		app.deal = undefined;
	}
}

function stuffAttributes(el) {
	// Stuffs all the attributes of a DOM object into an object. Mostly used
	// for storing components of server to client BBO application XML.
	let ob = {};
	let attr = el.getAttributeNames();
	for (let j=0; j<attr.length; j++) { ob[attr[j]] = el.getAttribute(attr[j]); }
	return ob;
}

function amVul() {
	// Returns whether the user is vulnerable on the deal.
	// Note: This doesn't work right if a player is seated multiple times at
	// a teaching table.
	let v = app.deal.vul;
	if (v === 'o') { return false; }
	if (v === 'b') { return true; }
	let ix;
	for (ix = 0; ix<4; ix++) {
		if ( app.table.players[ix] === app.user ) { break; }
	}
	return ix % 2 ? v === 'e' : v === 'n';
}

function autoAlert(auction, vul) {
	// AUCTION - Array of calls (used for testing)
	// VUL     - Boolean (used for testing)
	
	let au, auctionOpenIx;
	
	if (auction === undefined) {
		// Normal case
		au = app.deal.auction;
		auctionOpenIx = app.deal.auctionOpenIx;
	}
	else {
		// Test mode
		au = auction;
		auctionOpenIx = -1;
		for (let ix=0; ix<au.length; ix++) {
			if (au[ix] !== 'p') { auctionOpenIx = ix; break; }
		}
		// Assume not vulnerable unless otherwise stated.
		if ( vul === undefined ) { vul = false; }
	}
	
	// Supply automatic alerts for certain cases.
	// Note: Pass ('p'), Double ('d'), Redouble ('r') normalized to lowercase upstream.
	const ix2 = au.length-1;
	const call = au[ix2];
	
	// Not handling alerts for forcing pass systems(!)
	if (auctionOpenIx === -1) { return; }
	
	// Not alerting any passes, doubles, or redoubles at this point.
	if (call.length === 1) { return; }
	
	const aa = pref.aa;
	
	const ix1 = auctionOpenIx;
	if (ix1 === au.length-1) {
		// Opening bid
		if (call === '1N') {
			// Special case of different treatment for V vs. NV
			if (vul === undefined) { vul = amVul(); }
			return vul && aa.opening["1NTvul"] ? aa.opening["1NTvul"] : aa.opening[call];
		}
		if (ix1 === 3 && aa.opening.FourthSeat2Bid !== '' && call.charAt(0) === '2' &&
				call !== '2C' && call !== '2N') {
			return aa.opening.FourthSeat2Bid;
		}
		return (aa.opening !== undefined && aa.opening[call] !== undefined) ?
				aa.opening[call] : undefined;
	}
	
	const openingBid = au[ix1];
	if ( (ix2-ix1) === 2 && openingBid === '1N') {
		if (aa.nt === undefined) { return; }
		if ( au[ix1+1] === 'p' ) {
			// Uncontested responses to 1NT
			if (call === '2D') {
				return aa.nt.JacobyTransfers ? 'Hearts (transfer)' : undefined;
			}
			if (call === '2H') {
				return aa.nt.JacobyTransfers ? 'Spades (transfer)' : undefined;
			}
			if (call === '2S' || call === '2N' || call.charAt(0) === '3') 
				{ return aa.nt[call]; }
			if (call === '4D') {
				return aa.nt.TexasTransfers ? 'Hearts (transfer)' : undefined;
			}
			if (call === '4H') {
				return aa.nt.TexasTransfers ? 'Spades (transfer)' : undefined;
			}
		}
		else {
			// Will add Lebensohl and such here.
			return;
		}
	}
	
	if ( (ix2-ix1) === 2 && openingBid === '2N' && au[ix1+1] === 'p' ) {
		if (aa.nt === undefined) { return; }
		
		// Uncontested responses to 2NT
		if (aa.nt === undefined || !aa.nt.JacobyTransfers ) { return; }
		if (call === '3D') {
			return aa.nt.JacobyTransfers ? 'Hearts (transfer)' : undefined;
		}
		if (call === '3H') {
			return aa.nt.JacobyTransfers ? 'Spades (transfer)' : undefined;
		}
		if (call === '4D') {
			return aa.nt.TexasTransfers ? 'Hearts (transfer)' : undefined;
		}
		if (call === '4H') {
			return aa.nt.TexasTransfers ? 'Spades (transfer)' : undefined;
		}
		
		// Could add a user defined meaning for 3C, e.g. 'Puppet'
		return;
	}
	
	if ( (ix2-ix1) === 1 && openingBid === '1N') {
		// Defense to 1NT
		if (aa.ntdef === undefined) { return; }
		return aa.ntdef[call];
	}
	
	if ( (ix2-ix1) === 2 && au[ix1+1] === 'p' ) {
		// Responding w/o interference.

		if (openingBid === '1H' || openingBid === '1S') {
			// Responses to a major suit opening

			if (call === '1N') {
				// Maybe a forcing notrump.
				if (aa.forcingNT === 'forcing') { return 'Forcing'; }
				if (aa.forcingNT === 'semi') { return 'Semi-forcing'; }
				if (aa.forcingNT === 'semi-passed') {
					return ix1 < 2 ? 'Forcing' : 'Semi-forcing';
				}
				// non-forcing case (nothing to alert) or undefined (i.e. user
				// is playing something special that they need to manually alert)
				return;
			}

			else if ( call === '2N' ) {
				// Jacoby 2NT is only applies to an unpassed hand.
				return aa.Jacoby2NT && ix1 < 2 ? 
					'4+ card supp, GF, no shortness (Jacoby)' : undefined;
			}

			else if ( (openingBid === '1H' && call === '3H') ||
					(openingBid === '1S' && call === '3S') ) {
				return aa.majorJumpRaise;
			}

			else if ( call === '4C' || call == '4D' || 
					(openingBid === '1H' && call === '3S') ||
					(openingBid === '1S' && call === '4H') ) {
				return aa.majorSplinters ? 
					'0 or 1 !' + call.slice(-1).toLowerCase() +
					' with 4+ card supp (splinter)' : undefined;
			}
			
			return;
		}
	
		if ( (openingBid === '1C' && call === '2C') ||
			 (openingBid === '1D' && call === '2D') ) {
			return aa.invertedMinors ? 'Inverted' : undefined;
		}
		
		if ( (openingBid === '1C' && call === '3C') ||
			  (openingBid === '1D' && call === '3D') ) {
				return aa.minorJumpRaise;
		}
		
		if (openingBid === '1C' && (call === '2D' || call === '2H' || call === '2S') ) {
			return aa.OneTwoJumpResponse;
		}
		if (openingBid === '1D' && (call === '2H' || call === '2S') ) {
			return aa.OneTwoJumpResponse;
		}
		if (openingBid === '1H' && call === '2S' ) {
			return aa.OneTwoJumpResponse;
		}
		
		if ( (openingBid === '2D' || openingBid === '2H' || openingBid === '2S') && ix1<3) {
			// Response to Weak Two openings. Fourth seat bids are excluded
			// because those are not weak (or at least shouldn't be).
			if (call === '2N') {
				return aa.weak2NT === 'feature' ? 'Asking for an outside A or K' :
					aa.weak2NT === 'OGUST' ? 'OGUST (strength and trump quality ask)' :
					aa.weak2NT === 'natural' ? 'Strong balanced hand' :
					undefined;
			}
		}
		
		return;
	}
	
	if ( (ix2-ix1) === 1 ) {
		// Type of overcalls
		if ( call === '1N' ) { return aa.NTovercall; }
		
		if ( au[ix1].charAt(1) === au[ix2].charAt(1) && call.charAt(0) === "2" ) {
			// Direct cue bid (Michaels, Top and Bottom, and Top and Another)
			let explain;
			const dcb = aa.directCueBid;
			if ( dcb === undefined || dcb.type === undefined ) { return; }
			let denom = au[ix2].charAt(1);
			if ( dcb.type === 'Michaels' ) {
				explain = (denom === 'C' || denom === 'D') ? '!h + !s' :
					( denom === 'H') ? '!s + minor' : '!h + minor';
			}
			else if ( dcb.type === 'Top and Another') {
				explain = (denom === 'C') ? '!s + !d/!h' : (denom === 'D') ? '!s + !c/!h' :
					(denom === 'H') ? '!s + minor' : '!h + minor';
			}
			else if ( dcb.type === 'Top and Bottom') {
				explain = (denom === 'C') ? '!s + !d' : (denom === 'S') ? '!h + !d' :
					'!s + !c';
			}
			else { return; }
			
			let style = twoSuitedStyle(dcb.style, vul);
			if (style !== undefined) { explain += ', ' + style; }
			return explain;
		}
		
		if ( au[ix1].charAt(0) === '1' && call === '2N' ) {
			// Unusual Notrump ("Minors" or "Two Lowest")
			let explain;
			let unu = aa.jump2NT;
			if ( unu === undefined || unu.type === undefined ) { return; }
			if ( unu.type === 'Minors') { explain = '!c + !d'; }
			else if ( unu.type === 'Two Lowest' ) {
				let denom = au[ix1].charAt(1);
				explain = denom === 'C' ? '!d + !h' : denom === 'D' ? '!c + !h' :
					'!c + !d';
			}
			else { return; }
			
			let style = twoSuitedStyle(unu.style, vul);
			if (style !== undefined) { explain += ', ' + style; }
			return explain;
		}
		
		return;
	}
	
	if ( (ix2-ix1) === 3 && au[ix1+1] === 'p' && au[ix1+2] === 'p' ) {
		// Balancing bids
		if ( call === '1N' ) { return aa.NTbalancing; }
	}

}

function twoSuitedStyle(style, vul) {
	// Returns style for two suited calls like Michaels and Unusual Notrump
	if (style === undefined) { return; }
	
	if (style === '5-5') { return '5-5 or better'; }
	else if (style === '5-4') { return '5-4 or better'; }
	else if (style === '5-4-not22') { return '5-4 or better (5-4-2-2 rare)'; }
	
	// Otherwise varies depending on vulnerability
	if (vul === undefined) { vul = amVul(); }
	if (style === '5-4-NV') { return vul ? '5-5 or better' : '5-4 or better'; }
	if (style === '5-4-NV-not5422') {
		return vul ? '5-5 or better' : '5-4 or better (5-4-2-2 rare)';
	}
}

async function auctionAlertMessage(msg, mode) {
	// Display a brief msg centered in the <div> that displays the auction
	// in the main playing area.
	//
	// Mode - 'auto' (for auto alert) or 'sub' (substitution)
	
	let ds = document.getElementsByClassName('dealScreenDivClass');
	if (ds.length === 0) { return; }  // guarding against BBO UI changes
	
	let abb = ds[0].getElementsByClassName('auctionBoxClass');
	if (abb.length == 0) { return; }
	
	let ab = abb[0];
	
	// Escape HTML and substitute in suit symbols.
	msg = msg.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
	msg = msg.replace(/</g, '&lt;').replace(/>/g, '&gt;')
	msg = msg.replace(/!s/gi, '&spades;').replace(/!c/gi, '&clubs;');
	msg = msg.replace(/!d/gi, '<span style="color: red">&diams;</span>');
	msg = msg.replace(/!h/gi, '<span style="color: red">&hearts;</span>');

	let dv = document.createElement('div');
	dv.innerHTML = (mode === 'auto' ? 'Auto alert: ' : 'Sent as: ')  + msg;
	
	dv.style = 'position: absolute; padding: 0.2em 0.5em 0.2em 0.5em; ' + 
		'background: white; color: blue; width: 10em; ' + 
		'font-size: 150%; font-family: sans-serif';
	
	ab.appendChild(dv);
	
	// Display auto-alert msg centered in the auction box.
	const left_px = (ab.offsetWidth - dv.offsetWidth) / 2;
	const top_px = (ab.offsetHeight - dv.offsetHeight) / 2;
	dv.style.left = left_px + 'px';
    dv.style.top  = top_px + 'px';
	
	setTimeout(() => { dv.remove(); }, 1500);
}

function rapSheet(fullname, chURLs) {
	// Create a new window with hyperlinks to all relevant cheating documentation
	// for a given player. This works around a (seemingly undocumented) Chrome issue
	// of only allowing one popup window to be launched from an onclick.
	
	const target = fullname + ' cheating';
	const w = window.open('', target);
	if (!w) {
		console.warn('Failed to open cheating documentation window for %s', fullname);
		return;
	}

	// Now populate it.
	const ljhearings = 'https://lajollabridge.com/Hearings/';
	
	const doc = w.document;
	
	doc.head.innerHTML = `
	<style>
	body { font-size: 150%; max-width: 36em; }
	h1 { font-size: 150%; }
	div { margin-bottom: 0.6em; }
	a { text-decoration: none; }
	.exp { margin-left: 2em; }
	</style>`;
	
	let html = '<h1>' +  fullname + ' cheating documentation' + '</h1>\n';
	
	for (const url of chURLs) {
		const turl = url.startsWith(ljhearings) ? url.substring(ljhearings.length) : url;
		html += `<div><a href="${url}" target="_blank">` + turl + '</a>';
		
		const exp = turl.startsWith('HR_OEOC') ? 'ACBL OEOC Hearing Report' :
			turl.startsWith('HR_AC') ? 'ACBL Appeals and Charges Hearing Report' :
			turl.startsWith('HR') ? 'ACBL Hearing Report' :
			turl.startsWith('NR') ? 'ACBL Negotiated Resolution' : undefined;
			
		if (exp !== undefined) {
			html += '<span class="exp">' + '(' + exp + ')' + '</span>';
		}	
		
		html += '</div>\n';
	}
	
	doc.body.innerHTML = html;
}

console.info('BBO Helper: Code injection succeeded for additional code.');
