function UTF8unmangle(s, suitsub) {
	// BBO doesn't handle Unicode properly on the backend database. The LIN string
	// seems to be stuffed into a Latin-1 column (instead of a proper utf8mb4_unicode_ci)
	// on the Amazon RDS database (essentially MySQL). Thus foreign languages get
	// mangled. Here we unmangle this based on some reverse engineering.
	
	// Quickly figure out if any demangling is required. If not save work.
	const slen = s.length;
	let allASCII = true;
	for (let i=0; i<slen; i++) {
		if ( s.charCodeAt(i) >= 128 ) { allASCII = false; break; }
	}
	if (allASCII) { return(s); }
	
	// Some characters in the Latin-1 Supplement block (U+0080 - U+00FF) also have Unicode
	// codepoints above U+0100. For example the Euro currency symbol is both 0x80 and more
	// formally U+20AC. Part of the unmangling algorithm requires converting the codepoints
	// above U+0100 back to the U+0080 - U+00FF range. This array contains some of the
	// codepoints to convert.
	const map2013 = [0x96, 0x97,,,, 0x91, 0x92, 0x82,, 0x93, 0x94, 0x84,, 0x86, 0x87, 0x95,,,,
		0x85,,,,,,,,,, 0x89,,,,,,,,, 0x8B, 0x9B];	
	
	// Now convert certain codepoints to the values we really need.
	const u16 = new Uint8Array(slen);
	for (let i=0; i<slen; i++) {
		let v = s.charCodeAt(i);
		u16[i] = v;
		
		if (v < 0x0151) { continue; }
				
		let newval;		
		if (v >= 0x2013 && v <= 0x203A) {
			newval = map2013[v - 0x2013];
		}
		else {
			// 0x20ac and 0x2122 are fairly common, so test them first.
			newval = v === 0x20ac ? 0x80 : v === 0x2122 ? 0x99 :
				v === 0x0152 ? 0x8c : v === 0x0153 ? 0x9c : v === 0x0160 ? 0x8a :
				v === 0x0161 ? 0x9a : v === 0x0178 ? 0x9f : v === 0x017d ? 0x8e :
				v === 0x0192 ? 0x83 : v === 0x02c6 ? 0x88 : v === 0x02dc ? 0x98 : undefined;
		}
		if (newval !== undefined) { u16[i] = newval; }
	}
	
	// Finally get what we want.
	const decoder = new TextDecoder();
	let s2 = decoder.decode(u16);
	
	// Now convert any Unicode suit symbols to !s !h !d !c which is the standard
	// BBO convention and which will cause the diamond and hearts symbols to be
	// colored red in the BBO UI.
	if (suitsub) {
		s2 = s2.replace(/\u2660/g, '!s').replace(/\u2665/g, '!h');
		s2 = s2.replace(/\u2666/g, '!d').replace(/\u2663/g, '!c');
	}
	
	return s2;
}