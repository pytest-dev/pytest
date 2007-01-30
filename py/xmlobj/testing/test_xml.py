
import py

class ns(py.xml.Namespace): 
    pass 

def test_tag_with_text(): 
    x = ns.hello("world") 
    u = unicode(x) 
    assert u == "<hello>world</hello>"
    
def test_class_identity(): 
    assert ns.hello is ns.hello 

def test_tag_with_text_and_attributes(): 
    x = ns.some(name="hello", value="world") 
    assert x.attr.name == 'hello'
    assert x.attr.value == 'world'
    u = unicode(x) 
    assert u == '<some name="hello" value="world"/>' 

def test_tag_with_subclassed_attr_simple(): 
    class my(ns.hello): 
        class Attr(ns.hello.Attr): 
            hello="world" 
    x = my() 
    assert x.attr.hello == 'world' 
    assert unicode(x) == '<my hello="world"/>' 

def test_tag_nested(): 
    x = ns.hello(ns.world())
    unicode(x) # triggers parentifying
    assert x[0].parent is x 
    u = unicode(x) 
    assert u == '<hello><world/></hello>'

def test_tag_xmlname(): 
    class my(ns.hello): 
        xmlname = 'world'
    u = unicode(my())
    assert u == '<world/>'

def test_tag_with_text_entity():
    x = ns.hello('world & rest')
    u = unicode(x)
    assert u == "<hello>world &amp; rest</hello>"

def test_tag_with_text_and_attributes_entity():
    x = ns.some(name="hello & world")
    assert x.attr.name == "hello & world"
    u = unicode(x)
    assert u == '<some name="hello &amp; world"/>'

def test_raw():
    x = ns.some(py.xml.raw("<p>literal</p>"))
    u = unicode(x)
    assert u == "<some><p>literal</p></some>"

