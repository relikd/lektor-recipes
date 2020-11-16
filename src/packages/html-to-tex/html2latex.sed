# character set translations for LaTex special chars
s?&gt.?>?g
s?&lt.?<?g
s?\\?\\backslash ?g
s?{?\\{?g
s?}?\\}?g
s?%?\\%?g
s?\$?\\$?g
s?&?\\&?g
s?#?\\#?g
s?_?\\_?g
s?~?\\~?g
s?\^?\\^?g
s? ?~?g
# Paragraph borders
s?<p>?\\par ?g
s?</p>??g
# Headings
s?<title>\([^<]*\)</title>?\\section*{\1}?g
s?<hn>?\\part{?g
s?</hn>?}?g
s?<h1>?\\section*{?g
s?</h[0-9]>?}?g
s?<h2>?\\subsection*{?g
s?<h3>?\\subsubsection*{?g
s?<h4>?\\paragraph*{?g
s?<h5>?\\paragraph*{?g
s?<h6>?\\subparagraph*{?g
# UL is itemize
s?<ul>?\\begin{itemize}?g
s?</ul>?\\end{itemize}?g
s?<ol>?\\begin{enumerate}?g
s?</ol>?\\end{enumerate}?g
s?<li>?\\item ?g
s?</li>??g
# DL is description
s?<dl>?\\begin{description}?g
s?</dl>?\\end{description}?g
# closing delimiter for DT is first < or end of line which ever comes first NO
#s?<dt>\([^<]*\)<?\\item[\1]<?g
#s?<dt>\([^<]*\)$?\\item[\1]?g
#s?<dd>??g
#s?<dt>?\\item[?g
#s?<dd>?]?g
s?<dt>\([^<]*\)</dt>?\\item[\1]?g
s?<dd>??g
s?</dd>??g
# Italics
s?<it>\([^<]*\)</it>?{\\it \1}?g
s?<em>\([^<]*\)</em>?{\\it \1}?g
s?<b>\([^<]*\)</b>?{\\bf \1}?g
s?<strong>\([^<]*\)</strong>?{\\bf \1}?g
# recipe specific
s?<a href="../\([^"/]*\)/*">\([^<]*\)</a>?\\recipelink{\1}{\2}?g
# Get rid of Anchors
s?<a href="\(http[^"]*\)">\([^<]*\)</a>?\\external{\1}{\2}?g
s?<a[^>]*>??g
s?</a>??g
# quotes (replace after href)
s?\([[:space:]]\)"\([^[:space:]]\)?\1``\2?g
s?"?''?g