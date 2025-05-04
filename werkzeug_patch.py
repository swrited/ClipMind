"""
This is a patch file to make Flask work with newer versions of Werkzeug.
"""

import sys
import werkzeug.urls

# Add url_quote as an alias for quote if it doesn't exist
if not hasattr(werkzeug.urls, 'url_quote'):
    werkzeug.urls.url_quote = werkzeug.urls.quote
    print("Patched werkzeug.urls.url_quote")

# Add url_unquote as an alias for unquote if it doesn't exist
if not hasattr(werkzeug.urls, 'url_unquote'):
    werkzeug.urls.url_unquote = werkzeug.urls.unquote
    print("Patched werkzeug.urls.url_unquote")
