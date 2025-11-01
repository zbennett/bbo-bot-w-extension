// For clickable handles (implemented by BBO around February 17, 2025)
// Reference: https://stackoverflow.com/questions/44440532/fetch-and-addeventlistener

window.fetch = new Proxy(window.fetch, {
    apply(actualFetch, that, args) {
        // Forward function call to the original fetch()
        result = Reflect.apply(actualFetch, that, args);

        // Do whatever you want with the resulting Promise
        result.then((response) => {
	
			const php = '/p_show_profile.php?';
			const ix = response.url.indexOf(php);
			
			if ( ix !== -1 ) {
				// Add our HTML, a placeholder to be filled after a service worker query.
				const bbohandle = decodeURI(response.url).substring(ix + php.length + 2).toLowerCase();
						
				// Throw it over the fence to the main BBO Helper code.
				const ei = { detail: bbohandle };
				document.dispatchEvent( new CustomEvent("profile_fetch", ei) );
			}
	
        });

        return result;
    }
});


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