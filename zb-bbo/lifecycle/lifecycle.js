/*
 *  lifecycle.js
 *  
 *  Fills contents of explanation displayed in a new tab when BBO is first installed
 *  or is automatically updated on a Chromium chrome. The explanation is provided in
 *  a different manner for Firefox users. 
 *  
 *  BBO Helper browser add-on (Matthew Kidd, San Diego)
 *  
 */
 
const appstatus = window.location.pathname.search('install') !== -1 ? 'install' : 'update';
createContent(appstatus);

function createContent(appstatus) {
	
	const appname = chrome.i18n.getMessage('appName');
	
	const mf = chrome.runtime.getManifest();
	const ver = mf['version'];
	
	const imgIcon = chrome.runtime.getURL("icons/B++96.png");
	const iconStyle = 'float: left; margin-right: 0.8em; margin-bottom: 0.4em';
	
	const docURL = 'https://lajollabridge.com/Software/BBO-Helper/';
	const viewdoc = chrome.i18n.getMessage('about_viewdoc');
	
	const revURL = 'https://lajollabridge.com/Software/BBO-Helper/revhist.htm';
	const viewrev = chrome.i18n.getMessage('about_viewrev');
	
	let html = `<img src="${imgIcon}" style="${iconStyle}" +
		alt="BBO Helper icon" width="96" height="96"">`;
	
	let msg;
	if (appstatus === 'install') {
		msg = chrome.i18n.getMessage('install').replace('%1', appname);
	}
	else {
		msg = chrome.i18n.getMessage('install_update');
		msg = msg.replace('%1', appname).replace('%2', ver);
	}
	html += msg;
	
	msg = appstatus ==='install' ? chrome.i18n.getMessage('install_chrome_refresh_tab') :
		chrome.i18n.getMessage('update_chrome_refresh_tab');
		
	imgHTML = '<img src="refresh.png" style="display: inline"/>';
	msg = msg.replace('%2', imgHTML);
	
	msg = msg.replace('%1', appname);
	html += '<p>' + msg + '</p>';
	
	html += `<p><a href="${docURL}" target="_blank">${viewdoc}</a><br>`;
	html += `<a href="${revURL}" target="_blank">${viewrev}</a></p>`;
	
	let dv = document.createElement('div');
	dv.innerHTML = html;
		
	dv.style = 'padding: 1em 1em 1em 1em; ' + 
		'background-color: #f5ebd2; color: blue; width: 20em; ' + 
		'font-size: 150%; font-family: sans-serif; border: 2px solid #7f7f7f';
	
	document.body.appendChild(dv);
}
