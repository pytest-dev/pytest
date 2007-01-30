from py.xml import html 

def test_html_name_stickyness(): 
    class my(html.p): 
        pass 
    x = my("hello") 
    assert unicode(x) == '<p>hello</p>' 

def test_stylenames(): 
    class my: 
        class body(html.body): 
            style = html.Style(font_size = "12pt")
    u = unicode(my.body())
    assert u == '<body style="font-size: 12pt"></body>' 

def test_class_None(): 
    t = html.body(class_=None)
    u = unicode(t) 
    assert u == '<body></body>'

def test_alternating_style(): 
    alternating = (
        html.Style(background="white"), 
        html.Style(background="grey"),
    )
    class my(html): 
        class li(html.li): 
            def style(self): 
                i = self.parent.index(self) 
                return alternating[i%2]
            style = property(style) 
    
    x = my.ul(
            my.li("hello"), 
            my.li("world"), 
            my.li("42"))
    u = unicode(x) 
    assert u == ('<ul><li style="background: white">hello</li>'
                     '<li style="background: grey">world</li>'
                     '<li style="background: white">42</li>'
                 '</ul>')

def test_singleton():
    h = html.head(html.link(href="foo"))
    assert unicode(h) == '<head><link href="foo"/></head>'
    
    h = html.head(html.script(src="foo"))
    assert unicode(h) == '<head><script src="foo"></script></head>'

def test_inline():
    h = html.div(html.span('foo'), html.span('bar'))
    assert (h.unicode(indent=2) ==
            '<div><span>foo</span><span>bar</span></div>')

