// Code that is injected into the BBO's context using chrome.scripting API
// for Manifest V3 before the BBO client code loads.

"use strict";


var bh_XHR_counter = 0; // Track number of successful XHR requests;

// It's tricky sharing the preferences defining in the context of the add-on with
// the code injected into the BBO application. The PREF variable defined in the
// add-on is not visible here. If you try to pass it in a Custom Event, you can dump
// the whole thing via console.log(pref) but run into 'Error: Permission denied 
// to access property "x"' when trying to make use of it. So we pass it via a DOM
// object. We don't want to pay the JSON.parse() overhead every time we access PREF
// so keep a local copy here, and update it when a Custom Event informs us that
// it has been updated. Note: we initialize it with a few key values to prevent a
// possible race condition.
let pref = {"appSnifferConsoleLog": false, appChatAutoSuits: true};


// Tracks state of the app based on client-server traffic. This is independent
// of same global in bbov3.js because it's part of the injected code.
let app = {"deal": undefined, "table": undefined, "greeting": "Hi", 
	"lang": "en", "isLocaleRomanian" : false, 
	"locale" : { "honorOrderMatching" : "A?K?Q?J?" } };
	

// Websocket code is based on https://pastebin.com/C2q7WzwB, a fix of the code in 
// the WebSocket Sniffer Firefox extension by Rinat which in turn was based on code 
// for Google Chrome: https://gist.github.com/jeffdrumgod/d2bc277658ac4d94d802b99363a7efce

// Extending WebSocket will throw an error if this is not set (was issue before moving
// class extension to document_start)
// WebSocket.prototype = null; 

const bh_ORIGINAL_WEBSOCKET = WebSocket;

var WebSocket = window.WebSocket = class extends WebSocket {
	constructor(...args) {
		super(...args);
		
		var counter = 0;
		var incompleteMessage = '';
		this.consoleLogging = false;

		this.addEventListener('message', event => {				
			// Number of messages received
			counter++;
			
			// event.data is an ArrayBuffer for BBO. This is determined by the
			// websocket settings which for BBO are this.protocol is "binary"
			// and this.binaryType is "arraybuffer". This appears to be an UTF-8
			// encoded string which explains use of ArrayBuffer so parse it with
			// TextDecoder().
			const view = new Uint8Array(event.data);
			let utf8 = new TextDecoder().decode(view);
			
			// Multiple server to client messages can be pushed down in one websocket
			// message. They are separated by a NULL characters. Normally there is a
			// final NULL but if the message doesn't fit into a single websocket 
			// message (~2500 bytes here? Have seen 3050), then the last byte will be
			// not be NULL. Example: <sc_dump_fe> message if player has many friends 
			// and/or enemies.
			if (incompleteMessage.length) { 
				utf8 = incompleteMessage + utf8;
				incompleteMessage = '';
			}

			let msg = utf8.split('\x00');
			incompleteMessage = msg.pop();   // Almost always an empty string.
			
			for (let i=0; i<msg.length; i++) {
				const s = msg[i];
				if ( !s.startsWith('<sc_ack') && !s.startsWith('<sc_stats') &&
				 	!s.startsWith('<sc_feed') ) {
					if (this.consoleLogging) { console.info(counter, s); }
				}
				
				// Send a custom event that the add-on can listen for
				const ei = { detail: { "msg": msg[i] } };
				const ws_sniff = new CustomEvent("sniffer_ws_receive", ei);
				document.dispatchEvent(ws_sniff);
				
				// This is defined in injectedbbo.js which is loaded later.
				websocketReceive(msg[i]);
			}
		});

		this.addEventListener('open', event => {
			console.info('BBO Helper: BBO opened WebSocket %s', this.url)
			console.info("zach was here!")
			
			// Send a custom event that the add-on can listen for.
			const ei = { detail: { data: event, obj: this } };
			const ws_sniff = new CustomEvent("sniffer_ws_open", ei);
			document.dispatchEvent(ws_sniff);
		});
		
	}
	
	
	send(...args) {
		// typeof(data) is "message", typeof(obj) is "websocket"
		// data.data has the actual message.
		// data.origin is something like "wss://v3proxysl9.bridgebase.com"
		// obj.protocol is "binary"
		// obj.binaryType is "array buffer"
		// obj.url is something like "wss://v3proxysl9.bridgebase.com"
					
		// This is a string. It will start with "cs_", e.g. "cs_ping" or 
		// "cs_scan_reservations" because this is the BBO convention for all
		// messages from the client to the server.
		let msg = args[0];
		if (msg.startsWith('cs_make_bid')) {
			args[0] = processAuctionCall(msg);
		}
		else if (msg.startsWith('cs_play_card')) {
			// Track this just to handle undos properly.
			app.deal.ncardsPlayed++;
		}
		else if (msg.startsWith('cs_bid_explanation')) {
			// User is responding to request for an explanation.
			args[0] = processCallExplanation(msg);
		}			
		else if (msg.startsWith('cs_chat')) {
			// Perform suit symbol substitution. Parameter=Value type field are
			// separated by '\x01' for client to server messages. Terminator is
			// always a NULL byte.

			let channel, message, ixChannel, ixTable, ixUsername;
			let fd = msg.slice(0,msg.length-1).split('\x01');
			for (let i=1; i<fd.length; i++) {
				if ( fd[i].startsWith('message=') ) {
					message = fd[i].slice('message='.length);
					try { fd[i] = 'message=' + chatFixer(message, false); }
					catch(e) { console.error('BBO Helper: chatFixer() error', e); }
				}
				else if ( fd[i].startsWith('channel=') ) {
					// 'lobby', 'table', 'specs' (spectators, i.e. kibitzers), 'private',
					// 'tourney'
					ixChannel = i;
					channel = fd[i].slice('channel='.length);
				}
				else if ( fd[i].startsWith('table_id=') ) { ixTable = i; }
				else if ( fd[i].startsWith('username=') ) { ixUsername = i; } 
			}
			
			if ( message.startsWith('/') && channel !== 'table' && app.table &&
					app.table.table_id ) {
				// Table greeting. Set chat channel to "table" even if the UI is set
				// to another channel (e.g. a user), remove any "username" parameter,
				// and add table_id parameter.
				fd[ixChannel] = 'channel=table';
				if (ixUsername !== undefined) { fd.splice(ixUsername,1); }
				if (ixTable === undefined) {
					fd.splice(fd.length-1, 0, 'table_id=' + app.table.table_id);
				}
			}
			
			let newmsg = fd[0];
			for (let i=1; i<fd.length; i++) { newmsg += '\x01' + fd[i]; }
			args[0] = newmsg + '\x00';
		}
		else if (msg.startsWith('cs_vote_request') && pref.appClaimAutoSuits) {
			// Perform suit symbol substitution in claims.
			const param = 'explanation=';
			let fd = msg.slice(0,msg.length-1).split('\x01');
			for (let i=1; i<fd.length; i++) {
				if (fd[i].slice(0,param.length) === param) {
					try { fd[i] = param + chatFixer(fd[i].slice(param.length), true); }
					catch(e) { console.error('BBO Helper: chatFixer() error', e); }
					break;
				}
			}
			let newmsg = fd[0];
			for (let i=1; i<fd.length; i++) { newmsg += '\x01' + fd[i]; }
			args[0] = newmsg + '\x00';
		}
		
		super.send(...args);
		
		if ( !msg.startsWith('cs_ping') && !msg.startsWith('cs_keepalive') ) {
			if (this.consoleLogging) { console.info(msg); }
		}
		
		// Send a custom event that the add-on can listen for
		const ei = { detail: { "time": Date.now(), "msg": args[0] } };
		const ws_sniff = new CustomEvent("sniffer_ws_send", ei)
		document.dispatchEvent(ws_sniff);
	}
	
}


// Extending XMLHttpRequest() will throw an error if this is not set (was issue before moving
// class extension to document_start)
// XMLHttpRequest.prototype = null;

const bh_ORIGINAL_XMLHttpRequest = XMLHttpRequest;

var XMLHttpRequest = window.XMLHttpRequest = class extends XMLHttpRequest {
	
	constructor(...args) {
		super(...args);
		
		this.bboHelper = {};   // Our extras
		this.consoleLogging = pref.appSnifferConsoleLog;
		
		this.addEventListener('load', () => {
			bh_XHR_counter++;
			
			// Only want responses from https://webutil.bridgebase.com/ and
			// https://webutil.bridgebase.com/ (GIB double dummy engine).
			// Other XHR requests download icons, images, SVG and other things we
			// don't care about. Since responseType is always 'text' from the
			// webutil server, this.response will be text.
			const url = this.bboHelper.url;
			const re = /^https?:\/\/(webutil|gibrest|bboardapi|dev-api)\.bridgebase\.com\//;
			if ( url.search(re) !== - 1 ) {
				this.bboHelper.responseTime = Date.now();
				this.bboHelper.responseType = this.responseType;
				if (this.consoleLogging) {
					const s = this.bboHelper.method === 'POST' ? this.bboHelper.formdata : '';
					console.info(bh_XHR_counter, this.bboHelper.method, this.bboHelper.url, s);
					console.info(this.response);
				}
				
				if ( this.responseURL.endsWith('/mh_hand.php') ) {
					// Fix LIN string inside <linhand> element of PHP response BEFORE
					// it arrives at the BBO client. Okay to operate on the entire XML
					// response rather than specifically pulling out the LIN string.
					// This should always succeed but it is important to guard against
					// errors when tweaking the main BBO application.
					try {
						const fixed = UTF8unmangle(this.response);
						if (fixed !== this.response) {
							// Normally this is a read only property... so fix this. Making it
							// writeable resets its value to undefined.
							Object.defineProperty(this, 'response', { writable: true } );
							this.response = fixed;
						}
					}
					catch(e) {
						console.error('BBO Helper: UTF8unmangle exception: %s', e);
					}
				}
				
				this.bboHelper.response = this.response;

				// EventInit object
				const ei = { detail: this.bboHelper };
				const sniffer_xhr_load = new CustomEvent("sniffer_xhr_load", ei);
				document.dispatchEvent(sniffer_xhr_load);
			}
			
		});
	}

	open(...args) {
		// args[0] is the method, e.g. 'GET' or 'POST', arg[1] is the URL.
		this.bboHelper.method = args[0];
		this.bboHelper.url = args[1];
		if (this.consoleLogging) { console.info('XHR open', this.bboHelper); }
		
		super.open(...args);
	}
	
	send(...args) {				
		// Not currently altering or squashing any outgoing requests.
		// The form data for a POST pops up in args[0];
		this.bboHelper.sendTime = Date.now();
		if (this.bboHelper.method === 'POST') {
			this.bboHelper.formdata = args.length ? args[0] : '';
		}

		const ei = { detail: this.bboHelper };
		const sniffer_xhr_send = new CustomEvent("sniffer_xhr_send", ei);
		document.dispatchEvent(sniffer_xhr_send);
		if (this.consoleLogging) { console.info('XHR send', this.bboHelper); }
		
		super.send(...args);
	}
}


console.info('BBO Helper: Early code injection succeeded for Websocket and XHR sniffing ' + 
	'(monitors BBO client-server traffic).');