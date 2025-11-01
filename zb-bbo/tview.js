/*
 * Modifies tournament results display.
 *   - Add field strength calculation (based on ACBL players)
 *   - Add players names (when known) and location
 *     (US state, Canadian province, United Kingdom county, or country)
 *   - Add BBO star badge to known BBO stars  
 *   - Add BBO Royal Award badge to known BBO royals
 *   - Add masterpoints and links to BBO popup for clickable names
 * 
 * BBO Helper browser add-on (Matthew Kidd, San Diego)
*/

"use strict";

// For Manifest V3, move away from using a polyfill.
if ( isChromium() ) { var browser = chrome; }

function isChromium() {
	// navigator.userAgentData.brands is the seemingly clean way because it includes
	// brands for both 'Chrome' (etc) and 'Chromium', however Firefox does not yet
	// implement navigator.userAgentData and it is not exposed in Chromium for 
	// insecurely served pages, so provide a fallback mechanism.
	
	return navigator.userAgentData ? 
		navigator.userAgentData.brands.some(data => data.brand === 'Chromium') :
		navigator.userAgent.search('Firefox') === -1;
}

// See https://stackoverflow.com/questions/70474845/inject-javascript-from-content-script-with-a-chrome-extension-v3
function injectCode(src) {
	let s = document.createElement('script');
	s.src = isChromium() ? chrome.runtime.getURL(src) : browser.runtime.getURL(src);
	s.onload = () => s.remove();
	
	// We execute very early, possibly before <head> element has been created,
	// so fallback with document.documentElement root element.
	(document.head || document.documentElement).append(s);
}

// Unlike the main BBO application where the code to intercept WebSocket traffic
// must be injected as early as possible ("document_start"), it's fine to intercept
// XHTTP traffic here at "document_end".
injectCode('tviewinjected.js');

// Triggered in tviewinjected.js when BBO makes fetch for user profile information.
// e.detail is the BBO handle.
document.addEventListener('profile_fetch', function xhr(e) {
	// Clear any old information from a different user.
	const el = document.getElementById('modal-bbohelper');
	if (el) { el.remove(); }
	
	browser.runtime.sendMessage(
		{'type': 'lookup', 'bbohandle': e.detail } ).then(populateProfileModal);
});
	
	
// VAR not LET because APP is referenced in common.js. This primarily used in
// the BBO application (bbov3.js) and standalone BBO Handviewer (handviewer.js)
// but we include it here too to prevent issue when app.prefLoaded is set.
var app = {};

// HTML used to show the BBO star badge
const starHTML = '<span class="star">&starf;</span>';

// HTML used to show the Robot Face emoji (using a font that has the glyph)
const robotFaceHTML = '<span class="emoji">&#x1F916;</span>';

// URL to display a player's WBF page.
const WBF_URL_BASE = 'http://db.worldbridge.org/Repository/peopleforscrappcm/person.asp?qryid=';

// Sponsoring organization, e.g. ACBL or EBU
const host = parseHost();
const isEBU = host == 'EBU';

// Maximum number of players to look up automatically. More than this requires user
// action.
const MAX_HANDLES = 1200;

let allbbohandles = [];
const sc = document.getElementsByClassName('sectiontable');
const hl = document.getElementsByClassName('honorlist');
const ov = document.getElementsByClassName('bbo_tr_o');

// Around February 17, 2025 BBO changed from displaying BBO handles as plaintext to
// wrapping them in a clickable <span> element with class 'clickable-username' which
// when clicked on brings up a display similar to clicking on a player handle in the
// main BBO application. Then there was another change on March 15, 2025 where class
// starts as 'username' for text including all handles in a pair/team with JavaScript
// from BBO modifying the served HTML to split individual handles in 'clickable-username'
// Wrapped elements. Support both old and new display in case the new presentation
// isn't implemented in all scenarios.
let clickableHandles;

if ( sc.length ) {
	// Normal case
	clickableHandles = sc[0].getElementsByClassName('clickable-username').length !== 0;
	
	for (let i=0; i<sc.length; i++) {
		if (clickableHandles) {
			const spans = sc[i].getElementsByClassName('clickable-username');
			for (const sp of spans) {
				allbbohandles.push(sp.getAttribute('data-username').toLowerCase());
			}
		}
		else {
			// With March 15, 2025 change, this is now the typical case.
			const teams = sc[i].getElementsByClassName('username');
			for (let j=0; j<teams.length; j++) {
				const players = teams[j].innerHTML.toLowerCase().split('+');
				allbbohandles.push(...players);
			}
		}
	}
}
else if ( hl.length && ov.length ) {
	// Have an Honor List (Overalls only, though that might include all entrants)
	let teams = ov[0].getElementsByClassName('username');
	for (let j=0; j<teams.length; j++) {
		// Pair in a team might be split by a comma, e.g. 'scondrat+Static90,marian5566+franki2013'
		const players = teams[j].innerHTML.toLowerCase().split(/[+,]/);
		allbbohandles.push(...players);
	}	
}

// No need to lookup robots and they should not be counted toward number of players
// that the field strength is based upon.
allbbohandles = allbbohandles.filter(item => item !== 'robot');

if ( allbbohandles.length <= MAX_HANDLES) {
	browser.runtime.sendMessage(
		{'type': 'fs+names', 'bbohandles': allbbohandles, 'host': host} ).then(fsResponse);
}
else {
	// Require user to manually request name and field strength lookup.
	manualMode(allbbohandles.length);
}	

// Give page a more informative title than just "Result".
improveTitle();


function manualMode(nhandles) {
	// For certain very large events, a user reported their device bogging down
	// (a Chromebook, I think)	
	const dvt = document.getElementsByClassName('bbo_tr_t')[0];
	if (dvt === undefined) { return; }
	
	let dv = document.createElement('div');
	dv.innerHTML = '<span>BBO Helper: There are ' + nhandles + ' BBO handles to map to ' +
		'real names. This could bog down some web browsers on small devices, e.g. ' +
		'Chromebooks. Click button to perform lookup.</span>';
	dv.id = 'bh_warning';
	dv.style = 'padding: 0.6em 0.6em; font-size: 125%; color: white; background-color: darkgreen;' +
	  'margin-top: 0.5em; border: px solid #808080';
	  
	// Add Download PBN button.
	let bt = document.createElement('button');
	bt.setAttribute('type', 'button');
	bt.innerText = 'Go';
	bt.style = 'float: right; font-size: 150%; margin-left: 1em; border-radius: 0.3em; ' + 
		'background-color: white';
	
	bt.addEventListener("click", buttongo);
	dv.insertBefore(bt, dv.firstChild);
	
	dvt.insertAdjacentElement('afterend', dv);
	
	function buttongo() {
		browser.runtime.sendMessage(
			{'type': 'fs+names', 'bbohandles': allbbohandles, 'host': host} ).then(fsResponse);		
		
		document.getElementById('bh_warning').remove();	
	}
}

function fsResponse(data) {	
	addFieldStrength(data);
	addLeaderNames(data.players);
	addSectionNames(data.players);
}

function parseHost() {
	const tl = document.getElementsByClassName('bbo_tlv');
	return tl.length >= 2 ? tl[1].innerText : undefined;
}

function improveTitle() {
	const el = document.getElementsByClassName('bbo_t_l')[0];
	if (el === undefined) { return; }   // Guard against BBO changes
	
	// Find correct <tr> in <tbody> of <table>. Need to be careful because for BBO Events
	// (as opposed to say ACBL events), BBO stuffs a logo and a spacer in <td> elements
	// with rowspan=9 (it's horrible HTML)
	const tds = el.children[0].getElementsByClassName('bbo_tlv');
	if (tds.length === 0) { return; }   // Guard against BBO changes
	
	// Use the tournament name title, e.g. '#24714 ACBL Open-Pairs...''
	document.title = 'Results for ' + tds[0].innerText;
}

function addFieldStrength(data) {
	
	let elfs = document.getElementById('bbo-helper-fs');
	if (elfs !== null) {
		// Field strength was already added by BBO Helper. This should only
		// happen during testing when BBO Helper add-on is reloaded.		
		elfs.remove();
	}
	
	let el = document.getElementsByClassName('bbo_t_l')[0];
	if (el === undefined) { return; }   // Guard against BBO changes.
	
	// The sloppy BBO HTML doesn't include the <tbody> element, but it gets
	// added to the DOM when the HTML is parsed.
	const tds = el.children[0].getElementsByClassName('bbo_tlv');
	if (tds.length === 0) { return; }   // Guard against BBO changes

	elfs = document.createElement('tr');
	elfs.id = 'bbo-helper-fs';
	let fsrow = tds[0].parentNode.insertAdjacentElement('afterend', elfs);

	let fstxt;
	if (data.cnt === 0) {
		fstxt = browser.i18n.getMessage(isEBU ? 'no_EBU_players' : 'no_ACBL_players');
	}
	else if (isEBU) {
		fstxt = data.EBUstrength.toFixed(2) + '% NGS Avg, estimated from ' +
			data.cnt + ' EBU players (' + parseInt(100 * data.cnt/allbbohandles.length) + 
			'% of field)';		
	}
	else {
		fstxt = parseInt(data.fieldStrength) + ' MP, estimated from ' + 
			data.cnt + ' ACBL players (' + parseInt(100 * data.cnt/allbbohandles.length) + 
			'% of field)';
	}
	const html = '<td class="bbo_tll" align="left">Strength</td><td>' + fstxt + '</td>';

	fsrow.innerHTML = html;
}

function addLeaderNames(players) {
	// _o = "Overalls"
	let div = document.getElementsByClassName('bbo_tr_o');
	if (div.length === 0) { return; }  // Guard
	let table = div[0].getElementsByTagName('table')[0];
	if (!table) { return; } // Guard
	
	const colname = browser.i18n.getMessage('player_names');
	
	// The sloppy BBO HTML doesn't include the <tbody> element, but it gets
	// added to the DOM when the HTML is parsed.
	let tr = table.children[0].children;
	let td = tr[0].children;
	let ncols = td.length;
	
	if ( td[td.length-1].innerHTML !== colname ) {
		let el = document.createElement('th');
		el.innerHTML = colname;
		tr[0].appendChild(el);
		ncols++;
	}
	
	for (let j=1; j<tr.length; j++) {
		// Bail if we already added the column (development only situation)
		if ( tr[j].children.length === ncols) { break; }
		
		// BBO handles are in the second column of the leader table.
		let bbohandles = [];
		const spans = tr[j].children[1].getElementsByClassName('clickable-username');
		
		if (spans.length !== 0) {
			for (const sp of spans) {
				bbohandles.push(sp.getAttribute('data-username').toLowerCase());
			}
		}
		else {
			bbohandles = tr[j].children[1].innerHTML.toLowerCase().split(/[+,]/);
		}

		let nfound = 0; let playerList = '';
		for (let k=0; k<bbohandles.length; k++) {
			const bbohandle = bbohandles[k];
			
			if (k) { playerList += ' - '; }
				
			// Use Robot Face emoji for robots
			if (bbohandle === 'robot') { playerList += robotFaceHTML; continue; }
			
			// Contains name, * (if star badge) or ~A/K/Q/J (if letter badge), and (loc)
			const pinfo = players[bbohandle];

			if (pinfo === undefined) { playerList += '?'; continue; }
			
			nfound++;
			playerList += pinfo.name;
			if ( pinfo.badges !== undefined ) {
				if ( pinfo.badges === 's' ) { 
					if ( pinfo.WBFdbid === undefined ) { playerList += starHTML; }
					else {
						const url = WBF_URL_BASE + pinfo.WBFdbid;
						playerList +=  `<a href="${url}" class="nd">` + starHTML + '</a>';
					}
				}
				else if ( pinfo.badges.match(/^[AKQJ]$/) ) {
					playerList += '<span class="letter-badge">' + pinfo.badges + '</span>';
				}
			}

			if (isEBU && pinfo.NGSrank !== undefined) {
				// Sometimes the NGS name is different from the BBO name.
				const NGSname = encodeURIComponent(pinfo.NGSname ?? pinfo.name);
				const url = 'https://www.ebu.co.uk/ngs/search?name=' + NGSname;
				playerList += `<a class="ngs" target="_blank" href="${url}">` +
					'<span>' + pinfo.NGSrank + '</span></a>';
			}
			
			let loc = isEBU ? pinfo.county ?? pinfo.loc : pinfo.loc;
			if (loc === 'Great Britain') { loc = 'GBR'; }
			if (loc === 'United Arab Emirates') { loc = 'UAE'; }
			if ( pinfo.loc !== undefined ) { playerList += ' (' + loc + ')'; }
		}

		const el = document.createElement('td');
		if (nfound) { el.innerHTML = playerList; }
		tr[j].appendChild(el);
	}		

}

function addSectionNames(players) {
	const sc = document.getElementsByClassName('sectiontable');
	
	const colname = browser.i18n.getMessage('player_names');
	
	for (let i=0; i<sc.length; i++) {
		// The sloppy BBO HTML doesn't include the <tbody> element but DOM has it.
		let tr = sc[i].children[0].children;
		let td = tr[0].children;
		let ncols = td.length;
		
		if ( td[td.length-1].innerHTML !== colname ) {
			let el = document.createElement('th');
			el.innerHTML = colname;
			tr[0].appendChild(el);
			ncols++;
		}
		
		for (let j=1; j<tr.length; j++) {
			// Bail if we already added the column (reloading add-on).
			if ( tr[j].children.length === ncols) { break; }
			
			// BBO handles are in first column in section tables.
			let bbohandles = [];
			const spans = tr[j].children[0].getElementsByClassName('clickable-username');
			
			if (spans.length !== 0) {
				for (const sp of spans) {
					bbohandles.push(sp.getAttribute('data-username').toLowerCase());
				}
				
				// For individual events, the individual clickable usernames are not 
				// enclosed with in a span because there are no plaintext '+' symbols
				if (spans.length === 0) {
					bbohandles = [ tr[j].children[0].getAttribute('data-username').toLowerCase() ];
				}
			}
			else {
				bbohandles = tr[j].children[0].innerHTML.toLowerCase().split('+');
			}

			let nfound = 0; let playerList = '';
			for (let k=0; k<bbohandles.length; k++) {
				const bbohandle = bbohandles[k];

				if (k) { playerList += ' - '; }
				
				// Use Robot Face emoji for robots.
				if (bbohandle === 'robot') { playerList += robotFaceHTML; continue; }
				
				// Contains name, * (if star badge) or ~A/K/Q/J (if letter badge), and (loc)
				const pinfo = players[bbohandle];
				
				if (pinfo === undefined) { playerList += '?'; continue; }
				
				nfound++;
				playerList += pinfo.name;
				if ( pinfo.badges !== undefined ) {
					if ( pinfo.badges === 's' ) { 
						if ( pinfo.WBFdbid === undefined ) { playerList += starHTML; }
						else {
							const url = WBF_URL_BASE + pinfo.WBFdbid;
							playerList +=  `<a href="${url}" class="nd">` + starHTML + '</a>';
						}
					}
					else if ( pinfo.badges.match(/^[AKQJ]$/) ) {
						playerList += '<span class="letter-badge">' + pinfo.badges + '</span>';
					}
				}

				if (isEBU && pinfo.NGSrank !== undefined) {
					// Sometimes the NGS name is different from the BBO name.
					const NGSname = encodeURIComponent(pinfo.NGSname ?? pinfo.name);
					const url = 'https://www.ebu.co.uk/ngs/search?name=' + NGSname;
					playerList += `<a class="ngs" target="_blank" href="${url}">` +
						'<span>' + pinfo.NGSrank + '</span></a>';
				}
				
				let loc = isEBU ? pinfo.county ?? pinfo.loc : pinfo.loc;
				if (loc === 'Great Britain') { loc = 'GBR'; }
				if (loc === 'United Arab Emirates') { loc = 'UAE'; }
				if ( pinfo.loc !== undefined ) { playerList += ' (' + loc + ')'; }
			}

			const el = document.createElement('td');
			if (nfound) { el.innerHTML = playerList; }
			tr[j].appendChild(el);
		}		

	}
}

// Adds BBO Helper information to the "modal" (not true modal) popup generated by
// BBO when the user clicks on a clickable handle.
function populateProfileModal(p) {
	
	const pm = document.getElementById('profile-modal');
	if (pm === null) { return; }  // it's been closed already
	
	const mu = document.getElementById('modal-username');
	if (mu === null) { return; }  // guard
	
	const bbohandle = mu.innerText.toLocaleLowerCase();
	
	// Mismatch here mean user has click on another handle before service worker has
	// responded to an earlier handle.
	if (bbohandle !== p.bbohandle) { return; }

	// Don't add any information to robots, or standard tournament hosts
	// (BBO, ACBL, EBU). Lingering information has just been cleared.
	const excludedNames = {'' : 1, 'robot' : 1, 'bbo' : 1, 'aba' : 1, 'acbl' : 1, 
		'bboitalia' : 1, 'bboturkiye' : 1, 'ebu' : 1, 'ffb' : 1, 'galaxyclub' : 1, 
		'sky club' : 1, 'tbric' : 1, 'women_fest' : 1};
	if ( excludedNames[bbohandle] ) { return; }
		
	const imgBBO   = browser.runtime.getURL("images/BBO-5x4-icon.png");
	const imgLive1 = browser.runtime.getURL("images/ACBL-Live-logo.png");
	const imgLive2 = browser.runtime.getURL("images/ACBL-Live-for-Clubs-logo.png");
	const imgWBF   = browser.runtime.getURL("images/WBF-logo-trans.png");
	const imgWBFMP = browser.runtime.getURL("images/WBFMP-logo-trans.png");
	const imgLiveStyle = 'margin-left: 0.2em; display: inline-block; ' +
		'vertical-align: -20%; height: 1.2em';
	const NGSstyle = 'background-color: #2aff55; font-weight: bold; ' +
		'margin-left: 0.3em; padding: 0.1em 0.2em 0.05em 0.2em;';
	const imgWBFstyle = 'margin-left: 0.2em; display: inline-block; ' +
	 	'vertical-align: -20%; height: 1.2em';
	const WBFtitleStyle = 'margin-left: 0.2em; color: #009a4c';
	
	const WBF_URL_BASE = 'http://db.worldbridge.org/Repository/peopleforscrappcm/person.asp?qryid=';
	
	if (p.lookupfail) {
		const html = 'Not in BBO Helper database ' +
			`<a href="${myhandsURL(bbohandle)}" target="_blank">` +
			`<img src="${imgBBO}" style="${imgLiveStyle}"/></a>`;
		insertProfileHTML(html);
		return;
	}
	
	// Good to go.
	let html = p.fullname;
	
	// Add location.
	if (p.county !== undefined) { html += ' (' + p.county + ')'; }
	else if (p.state !== '') { html += ' (' + p.state + ')'; }
	
	html += ' ';
	
	const isACBL = p.pnum > 0;
	if (isACBL) {
		// First round MP total to two digits to avoid meaningless distraction.
		let mp = p.mp;
		if (mp === -1) {
			// Player has ACBL number but did not appear in the monthly masterpoint
			// database used to generate the player database (rare).
			html += 'Unknown MP';
		}
		else {
			// Round to two decimal places.
			const ndigits = mp.toString().length - 2;
			if (ndigits > 0) { mp = Math.round(mp / 10**ndigits) * 10**ndigits; }
			html += '~' + mp + ' MP';
		}
	}
	else {
		html += 'No ACBL #';
	}
	
	html += ' ';
	
	// Always create link to BBO My Hands.
	html += `<a href="${myhandsURL(bbohandle)}" target="_blank">` +
	 `<img src="${imgBBO}" style="${imgLiveStyle}"/></a>`;
	 
	if (isACBL) {
		// Can only create links to ACBL Live and ACBL Live for Clubs for
		// ACBL players.
		const liveURL1 = 'https://live.acbl.org/player-results/' + p.pnum;
		const liveURL2 = 'https://my.acbl.org/club-results/my-results/' + p.pnum;
		html += `<a href="${liveURL1}" target="_blank">` +
		 `<img src="${imgLive1}" style="${imgLiveStyle}"/></a>`;
		html += `<a href="${liveURL2}" target="_blank">` +
		 `<img src="${imgLive2}" style="${imgLiveStyle}"/></a>`;
	}
	
	// Show National Grading System (NGS) rank for English Bridge Union (EBU) players.
	if (p.NGSrank !== undefined) {
		const NGSname = encodeURIComponent(p.NGSname ?? p.fullname);
		const url = 'https://www.ebu.co.uk/ngs/search?name=' + NGSname;
		html += `<a style="text-decoration: none" target="_blank" href="${url}">` +
			`<span style="${NGSstyle}">` + p.NGSrank + '</span></a>';
	}

	// Add cheater status for convicted cheaters.
	if (p.chStatus !== undefined) { html += cheatHTML(p); }

	// Show World Bridge Federation (WBF) logo if we have a code to the player's
	// WBF player page. There are two similar logos, the one with a gold halo
	// indicates the player has WBF masterpoints. Also show WBF titles if any.
	if (p.WBFdbid !== undefined) {
		const url = WBF_URL_BASE + p.WBFdbid;
		const img = p.WBFmpid === undefined?  imgWBF : imgWBFMP;
		html += `<a href="${url}" target="_blank">` +
			`<img src="${img}" style="${imgWBFstyle}"/></a>`;
		if (p.WBFtitles !== undefined) {
			html += `<span style="${WBFtitleStyle}">` + p.WBFtitles + '</span>';
		}
	}

	insertProfileHTML(html);
	
	
	function insertProfileHTML(html) {
		html = '<div id="modal-bbohelper" style="padding: 10px">' + html + '</div>';
		pm.insertAdjacentHTML('beforeend', html);
	}
	
}


function myhandsURL(bbohandle) {
	// Constructs URL to retreive last 6 days of boards from BBO MyHands for a
	// given BBO user.
	const oneday =  86400000;   // mS in a day
	
	const d = Date.now();
	const tzoff = new Date(Date.now()).getTimezoneOffset();   // In minutes
	
	// Standard BBO MyHands query retrieves hands from midnight to midnight in
	// the current timezone.
	const ms = d % oneday;
	let dEnd = (d - ms) + tzoff * 60000;
	if (dEnd < d) { dEnd += oneday; }
	
	// JavaScript use mS UNIX timestamp but BBO endpoint uses original 1 sec 
	// resolution UNIX timestamp.
	dEnd = dEnd / 1000;
	const dStart = dEnd - 6 * oneday / 1000;
	
	// Some BBO handles contain spaces so use encodeURIComponent()
	const url = 'https://www.bridgebase.com/myhands/hands.php?username=' +
		encodeURIComponent(bbohandle) + '&start_time=' + dStart +
		'&end_time=' + dEnd;
	
	return url;
}

// Generate HTML for cheating icon (C = Convicted , R = Resigned) and the pages
// that open when the icon is clicked on.
function cheatHTML(p) {
	const imgName =  p.chStatus === 'Convicted' ? 'scarlett-C.png' :
		'Resigned' ? 'scarlett-R.png' : undefined;
	if (imgName === undefined) { return ''; }   // Unsupported cheater status

	const imgCheat = browser.runtime.getURL('images/' + imgName);
	let imgCheatStyle = 'margin-left: 0.2em; display: inline-block; ' +
		'vertical-align: -20%; height: 1.2em';

	// Using onclick instead of wrapping element in <a> because clicking can
	// open multiple URLs.
	let js = '';
	if (p.chURLs !== undefined) {
		const chURLs = p.chURLs;
		
		if ( !isChromium || chURLs.length < 2 ) {
			for (let i=0; i<chURLs.length; i++) {
				const url = chURLs[i];
				// Want to specify a target here so that repeated clicks on the icon
				// don't open multiple tab, multiple times.
				const target = p.pnum.toString() + '_' + i;
				js += `window.open("${url}", "${target}"); `;
			}
		}
		else {
			// Chrome only allows an onclick to launch one popup window though
			// this behavior does not seem to be documented. rapSheet() will create
			// a single popup with links to each URL documenting the cheating.
			// rapSheet() has to be defined in the injected code (injectedbbo.js)
			js = 'rapSheet("' + p.fullname + '", ' + JSON.stringify(chURLs) + ')';
		}
	}
	
	const onclick = p.chURLs === undefined || p.chURLs.length === 0 ? '' :
		` onclick='${js}'`;
	if (onclick !== '') { imgCheatStyle += '; cursor: pointer'; }

	return `<img src="${imgCheat}" style="${imgCheatStyle}"${onclick}/>`;
}