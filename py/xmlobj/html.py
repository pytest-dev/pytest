"""


""" 
from py.xml import Namespace, Tag
from py.__.xmlobj.visit import SimpleUnicodeVisitor 

class HtmlVisitor(SimpleUnicodeVisitor): 
    
    single = dict([(x, 1) for x in 
                ('br,img,area,param,col,hr,meta,link,base,'
                    'input,frame').split(',')])
    inline = dict([(x, 1) for x in
                ('a abbr acronym b basefont bdo big br cite code dfn em font '
                 'i img input kbd label q s samp select small span strike '
                 'strong sub sup textarea tt u var'.split(' '))])

    def repr_attribute(self, attrs, name): 
        if name == 'class_':
            value = getattr(attrs, name) 
            if value is None: 
                return
        return super(HtmlVisitor, self).repr_attribute(attrs, name) 

    def _issingleton(self, tagname):
        return tagname in self.single

    def _isinline(self, tagname):
        return tagname in self.inline

class HtmlTag(Tag): 
    def unicode(self, indent=2):
        l = []
        HtmlVisitor(l.append, indent, shortempty=False).visit(self) 
        return u"".join(l) 

# exported plain html namespace 
class html(Namespace):
    __tagclass__ = HtmlTag
    __stickyname__ = True 
    __tagspec__ = dict([(x,1) for x in ( 
        'a,abbr,acronym,address,applet,area,b,bdo,big,blink,'
        'blockquote,body,br,button,caption,center,cite,code,col,'
        'colgroup,comment,dd,del,dfn,dir,div,dl,dt,em,embed,'
        'fieldset,font,form,frameset,h1,h2,h3,h4,h5,h6,head,html,'
        'i,iframe,img,input,ins,kbd,label,legend,li,link,listing,'
        'map,marquee,menu,meta,multicol,nobr,noembed,noframes,'
        'noscript,object,ol,optgroup,option,p,pre,q,s,script,'
        'select,small,span,strike,strong,style,sub,sup,table,'
        'tbody,td,textarea,tfoot,th,thead,title,tr,tt,u,ul,xmp,'
        'base,basefont,frame,hr,isindex,param,samp,var'
    ).split(',') if x])

    class Style(object): 
        def __init__(self, **kw): 
            for x, y in kw.items():
                x = x.replace('_', '-')
                setattr(self, x, y) 

