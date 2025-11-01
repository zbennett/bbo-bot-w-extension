/*
 *  bbov3early.js - Adds functionality to BBO application
 *  
 *  BBO Helper browser add-on (Matthew Kidd, San Diego)
 *
 *  Injects WebSocket and XHR inception before the BBO client code.
 *  ("run_at": "document_start" in manifest.json)
 *  
 */

"use strict";


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

injectCode('utf8unmangle.js');
injectCode('injectedsniffers.js');
