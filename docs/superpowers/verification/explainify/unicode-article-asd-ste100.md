# Why Unicode exists and what UTF-8 does

**STE-inspired simplified English — approximate, not validated for ASD-STE100 conformity**

This explanation presents one selected part of Joel Spolsky's essay of 2003-10-08: why Unicode exists and what UTF-8 does. Quoted fragments are verbatim from the retrieved article text.

## Letters became numbers

Computers store text as numbers. An encoding is the rule that says which number stands for which character. Early American software used one encoding, called ASCII. ASCII gave every unaccented English character a number between 32 and 127. Space was number 32. The letter "A" was number 65. These numbers fit in 7 bits. Most computers stored them in 8-bit bytes, so one bit was spare.

## 128 numbers were not enough for the world

Many groups then filled the numbers 128 to 255 with letters for their own languages. The same number soon meant different characters on different computers. On some PCs, number 130 displayed as é. In Israel, the same number displayed the Hebrew letter Gimel. Spolsky's example: American résumés arrived in Israel as "rsums".

The industry later standardized these local choices as code pages. A code page is one agreed meaning for the numbers 128 to 255. Israel's DOS used code page 862. Greek users used code page 737. Code pages matched below 128 and differed from 128 up. One byte value could not mean the same character everywhere.

The Internet then moved text between computers constantly. The old habit "one byte equals one English character" stopped working.

## Unicode gives each character one number

Unicode was created as one character list for every reasonable writing system. The list even includes make-believe scripts like Klingon.

A widespread belief says Unicode simply stores each character in 16 bits. The essay says this belief is not correct. Unicode defines letters without a real limit, and it has gone beyond 65,536 characters.

Each character on the list receives a code point. A code point is a number written in hexadecimal, like U+0639. U+0639 is the Arabic letter Ain. The English letter "A" is U+0041.

A code point names the character. A code point does not say how to store the character as bytes. An encoding states how to store each code point as bytes.

## UTF-8: short byte sequences for common characters, longer for rare ones

The earliest Unicode encoding stored each code point in two bytes. This method is called UCS-2, or UTF-16. Programmers complained about the wasted zero bytes in English text. Existing documents in older encodings would also need full conversion.

UTF-8 is an encoding that stores Unicode code points in 8-bit bytes. In UTF-8, every code point from 0 to 127 is stored in a single byte. Only code points 128 and above take 2, 3, or more bytes. The essay, published in 2003, says the longest form reaches 6 bytes.

English letters therefore cost one byte each. Accented, Greek, or Klingon letters cost several bytes per character.

The essay's example: "Hello" is the code points U+0048 U+0065 U+006C U+006C U+006F. UTF-8 stores these code points as the bytes 48 65 6C 6C 6F. Those are exactly the bytes that ASCII used. So English text looks the same in UTF-8 as it did in ASCII.

One extra property protects old programs. Old code that ends a string at a single 0 byte will not truncate UTF-8 strings.

## The single most important fact

The essay's rule: "It does not make sense to have a string without knowing what encoding it uses." You cannot interpret or display a string correctly when you do not know its encoding. In the essay's words, "There Ain’t No Such Thing As Plain Text."

## Source

- Author: Joel Spolsky.
- Title: "The Absolute Minimum Every Software Developer Absolutely, Positively Must Know About Unicode and Character Sets (No Excuses!)".
- Published: 2003-10-08.
- URL: https://www.joelonsoftware.com/2003/10/08/the-absolute-minimum-every-software-developer-absolutely-positively-must-know-about-unicode-and-character-sets-no-excuses/
- Retrieved: 2026-10-03; retrieval status complete (full essay text).

All factual claims above come from this retrieved text. Unquoted sentences are paraphrases; quoted fragments are verbatim.

## Scope and limitations

- This explanation covers one selected scope: why Unicode exists and what UTF-8 does. It is not a summary of the whole essay.
- Omitted essay content: the FogBUGZ and PHP anecdotes; EBCDIC; the WordStar high-bit trick; double-byte character sets; byte-order marks and endianness; UTF-7 and UCS-4; question-mark substitution for missing characters; how email and web pages declare encodings; the browser encoding-guessing story; the CityDesk example.
- The essay predates modern developments. It was published on 2003-10-08.
- Note added outside the essay, from current model knowledge: today's UTF-8 specification caps one character at 4 bytes. The essay's "up to 6 bytes" reflects the 2003 state of the standard, not an error in the essay.
