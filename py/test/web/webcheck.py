import py
import re
from exception import *
from post_multipart import post_multipart
#import css_checker

def check_html(string):
    """check an HTML string for wellformedness and validity"""
    tempdir = py.test.ensuretemp('check_html')
    filename = 'temp%s.html' % (hash(string), )
    tempfile = tempdir.join(filename)
    tempfile.write(string)
    ret = post_multipart('validator.w3.org', '/check', [], 
                [('uploaded_file', 'somehtml.html', string)])
    is_valid = get_validation_result_from_w3_html(ret)
    return is_valid

reg_validation_result = re.compile(
    '<(h2|td)[^>]*class="(in)?valid"[^>]*>([^<]*)<', re.M | re.S)
def get_validation_result_from_w3_html(html):
    match = reg_validation_result.search(html)
    valid = match.group(1) is None
    text = match.group(2).strip()
    if not valid:
        temp = py.test.ensuretemp('/w3_results_%s.html' % hash(html), dir=0)
        temp.write(html)
        raise HTMLError(
            "The html is not valid. See the report file at '%s'" % temp)
    return valid

#def check_css(string, basepath, htmlpath='/'):
#    """check the CSS of an HTML string
#    
#        check whether an HTML string contains CSS rels, and if so check whether
#        any classes defined in the HTML actually have a matching CSS selector 
#    """
#    c = css_checker.css_checker(string, basepath, htmlpath)
#    # raises a CSSError when failing, this is done from the tester class to
#    # allow being more verbose than just 'something went wrong'
#    return c.check()

