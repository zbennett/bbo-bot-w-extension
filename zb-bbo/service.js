/* 
 * Support operations on the static player database
 *
 * Implement this as a service worker (manifest V3) to avoid possible duplication in 
 * memory of a decent sized database. 
 *
 * BBO Helper browser add-on (Matthew Kidd, San Diego)
*/

import pdata from "./playerdb.js";
import cdata from "./cheatdb.js";
import edata from "./ebudb.js";
import wdata from "./wbfdb.js";

// Default location of Hearings (this is a mirror of Hearing reports from the
// ACBL website because ACBL website overhauls can shiffle around old documents).
const hearingsURLdir = 'https://lajollabridge.com/Hearings/';

chrome.runtime.onMessage.addListener(handler);

function handler(msg, sender, sendResponse) {
	
	if (msg.type === 'lookup') {
		let data;
		const bbohandle = msg.bbohandle.toLowerCase();
		const p = pdata[bbohandle];
		if (p) {
			data = {'bbohandle': bbohandle, 'fullname': p[0], 'state': p[1], 
				'pnum': p[2], 'mp': p[3]};
				
			const ebu = edata[bbohandle];
			if (ebu !== undefined) {
				data.county  = ebu[0];
				data.NGSpct  = ebu[1];
				data.NGSrank = ebu[2];
				if ( ebu[3] !== undefined ) { data.NGSname = ebu[3]; }
			}
			
			const wbf = wdata[bbohandle];	
			if (wbf !== undefined) {
				data.WBFcode = wbf[0];
				data.WBFdbid = wbf[1];
			 	if ( wbf[2] !== undefined ) {
					data.WBFmpid = wbf[2];
					if ( wbf[3] !== undefined ) { data.WBFtitles = wbf[3]; }
				}
			}
			
			// Convicted cheaters are identified by ACBL player number in case they
			// create a new BBO account.
			if ( p[2] !== undefined && p[2] > 0 ) {
				const cheater = cdata[ p[2] ];
				if ( cheater !== undefined ) {
					data.chStatus = cheater[0];
					if ( cheater[1] !== undefined ) { 
						let chURLs = cheater[1];
						for (let i=0; i<chURLs.length; i++) {
							if ( chURLs[i].startsWith('http') ) { continue; }
							chURLs[i] = hearingsURLdir + chURLs[i];
						}
						data.chURLs = chURLs;
					}
				}
			}
		}
		else {
			data = {'bbohandle': bbohandle, 'lookupfail': true};
		}
		sendResponse(data);
	}
	
	if (msg.type === 'lookup_many') {
		const data = { 'bbohandle': [], 'fullname': [], 'state': [], 'pnum': [], 
			'mp': [],  'fail': [] };
		
		for (let i=0; i<msg.bbohandle.length; i++) {
			const bbohandle = msg.bbohandle[i].toLowerCase();
			const p = pdata[bbohandle];
			
			data.fail.push(p === undefined);
			data.bbohandle.push( bbohandle );
			data.fullname.push( p ? p[0] : undefined );
			data.state.push( p ? p[1] : undefined );
			data.pnum.push( p ? p[2] : undefined );
			data.mp.push( p ? p[3] : undefined );
		}
		sendResponse(data);
	}

	if (msg.type === 'vugraph_name') {	
		const url = 'https://webutil.bridgebase.com/v2/evp.php' + 
			'?voe=' + encodeURIComponent(msg.vgPresenter) + 
			'&u=' + encodeURIComponent(msg.name);

		// A service worker isn't allowed to access to the DOM and unfortunately
		// this include DOMParser(). Instead of doing sloppy parsing here (or 
		// folding in the third party XML parsing library like tXml (see
		// https://github.com/tobiasnickel/tXml), just send the full HTML back.
		// https://developer.chrome.com/docs/extensions/mv3/migrating_to_service_workers/

		fetch(url)
			.then( (response) => response.text() )
			.then( (html) => { sendResponse(html) })
			.catch( (error) => {
				console.warn('Failed processing URL:', url, 'error:', error);
				sendResponse('');
			});

		// Very important. See https://chowdera.com/2022/01/202201081929442512.html
		return true;
	}

	if (msg.type === 'fs+names') {
		let players = {};
		let cnt = 0;
		let mpLogTotal = 0;
		let NGSpctsum = 0;
		const bbohandles = msg.bbohandles;
		const isEBU = msg.host === 'EBU';
		
		for (let i=0; i<bbohandles.length; i++) {
			const bbohandle = bbohandles[i];
			const p = pdata[ bbohandle ];
			if (!p) { continue; }
						
			let pinfo = { "name": p[0] };
			// Add location if known.
			if ( p[1] !== '' ) { pinfo.loc = p[1]; }
			
			// Add badge info if player is a BBO star or has A, K, Q, or J rank badge.
			// Also add WBF player database id if available. For efficiency, we only do 
			// this for strong players who are likely to have a WBF pages.
			if ( p[4] ) {
				pinfo.badges = p[4];
				const wbf = wdata[bbohandle];
				if (wbf !== undefined) { pinfo.WBFdbid = wbf[1]; }
			}

			players[ bbohandle ] = pinfo;
	
			if (isEBU && edata[bbohandle] ) {
				// Add National Grading System data.
				const ebu = edata[bbohandle];
				pinfo.county  = ebu[0];
				pinfo.NGSpct  = ebu[1];
				pinfo.NGSrank = ebu[2];
				if ( ebu[3] !== undefined ) { pinfo.NGSname = ebu[3]; } 
				NGSpctsum += pinfo.NGSpct;
			}
			else {
				let mp = p[3];
				if (mp === -1) { continue; }
				if (mp < 1) { mp = 1; }
				mpLogTotal += Math.log(mp);
			}
			
			cnt++;
		}
			
		const fieldStrength = cnt === 0 ? undefined : Math.exp(mpLogTotal/cnt);
		const EBUstrength = cnt === 0 || msg.host !== 'EBU' ? undefined : NGSpctsum / cnt;
		const data = {cnt, fieldStrength, EBUstrength, players};
		sendResponse(data);
	}

	if (msg.type === 'fieldstrength') {
		// Not using this "API" any more. But keep it for now.
		
		let cnt = 0;
		let mpLogTotal = 0;
		const bbohandles = msg.bbohandles;
		for (let i=0; i<bbohandles.length; i++) {
			const p = pdata[ bbohandles[i] ];
			if (!p) { continue; }
			let mp = p[3];
			if (mp === -1) { continue; }
			if (mp < 1) { mp = 1; }
			
			cnt++;
			mpLogTotal += Math.log(mp);
		}
			
		const fieldStrength = cnt === 0 ? undefined : Math.exp(mpLogTotal/cnt);
		let data = {'cnt': cnt, 'fieldStrength': fieldStrength};
		sendResponse(data);
	}
}


// Note installation of the extension and any updates that are automatically
// downloaded by the browser (and also reloads from about:debugging during testing).
// This is for displaying the need to reload any BBO application tab(s). For
// Firefox we use a slightly different method: see appUpdate() in bbov3.js
chrome.runtime.onInstalled.addListener( (d) => {
	if (d.reason !== 'install' && d.reason !== 'update') { return; }
	
	console.info('onInstalled handler received message: ', d.reason);
	
	// Don't display the message during for reloads from chrome://extensions/ 
	// during evelopment. Comment out conditional to test changes to this functionality.
	const mf = chrome.runtime.getManifest();
	const ver = mf['version'];
	if (d.previousVersion === ver) { return; }
	
	const url = chrome.runtime.getURL("lifecycle/" + d.reason + ".html");
	
	chrome.tabs.create( { "url": url } );
});