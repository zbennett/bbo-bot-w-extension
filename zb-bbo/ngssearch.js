/*
 * Modifies English Bridge Union (EBU) National Grading System (NGS)
 * search page to automatically search for a name by programmatically
 * submitting the form if the NAME URL parameter is specified.
 * 
 * BBO Helper browser add-on (Matthew Kidd, San Diego)
*/

"use strict";

submitform();

function submitform() {

	const URLparams = new URLSearchParams(window.location.search);
	const fullname = URLparams.get('name');
	
	if (fullname === null) { return; }
	console.info('Automatically submitting search for ' + fullname);
	
	const form = document.getElementsByTagName('FORM')[0];
	if (form === undefined) { return; }
	
	const input = form.getElementsByTagName('INPUT')[0];
	if (input === undefined) { return; }
	
	input.value = fullname;
	form.submit();
}