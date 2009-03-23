import py
from py.__.misc.rest import convert_rest_html, strip_html_header 
from py.__.misc.difftime import worded_time 

html = py.xml.html 

class Page(object): 
    doctype = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
               ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')

    def __init__(self, project, title, targetpath, stylesheeturl=None,
                 type="text/html", encoding="ISO-8859-1"): 
        self.project = project 
        self.title = project.prefix_title + title 
        self.targetpath = targetpath
        self.stylesheeturl = stylesheeturl 
        self.type = type 
        self.encoding = encoding 

        self.body = html.body()
        self.head = html.head() 
        self._root = html.html(self.head, self.body) 
        self.fill() 

    def a_docref(self, name, relhtmlpath):
        docpath = self.project.docpath
        return html.a(name, class_="menu",
                      href=relpath(self.targetpath.strpath,
                                   docpath.join(relhtmlpath).strpath))

    def a_apigenref(self, name, relhtmlpath):
        apipath = self.project.apigenpath
        return html.a(name, class_="menu",
                      href=relpath(self.targetpath.strpath,
                                   apipath.join(relhtmlpath).strpath))
        
    def fill_menubar(self):
        items = [
            self.a_docref("index", "index.html"),
            #self.a_apigenref("api", "api/index.html"),
            #self.a_apigenref("source", "source/index.html"),
            self.a_docref("contact", "contact.html"),
            self.a_docref("download", "download.html"),
        ]
        items2 = [items.pop(0)]
        sep = " "
        for item in items:
            items2.append(sep)
            items2.append(item)
        self.menubar = html.div(id="menubar", *items2)

    def fill(self):
        content_type = "%s;charset=%s" %(self.type, self.encoding)
        self.head.append(html.title(self.title))
        self.head.append(html.meta(name="Content-Type", content=content_type))
        if self.stylesheeturl:
            self.head.append(
                    html.link(href=self.stylesheeturl,
                              media="screen", rel="stylesheet",
                              type="text/css"))
        self.fill_menubar()

        self.metaspace = html.div(
                html.div(self.title, class_="project_title"),
                self.menubar,
                id='metaspace')

        self.body.append(self.project.logo)
        self.body.append(self.metaspace)
        self.contentspace = html.div(id="contentspace")
        self.body.append(self.contentspace)

    def unicode(self, doctype=True): 
        page = self._root.unicode() 
        if doctype: 
            return self.doctype + page 
        else: 
            return page 

class PyPage(Page): 
    def get_menubar(self):
        menubar = super(PyPage, self).get_menubar()
        # base layout 
        menubar.append(
            html.a("issue", href="https://codespeak.net/issue/py-dev/",
                   class_="menu"),
        )
        return menubar
                            

def getrealname(username):
    try:
        import uconf
    except ImportError:
        return username
    try:
        user = uconf.system.User(username)
    except KeyboardInterrupt:
        raise
    try: 
        return user.realname or username
    except KeyError:
        return username
    

class Project:
    mydir = py.magic.autopath().dirpath()
    title = "py lib"
    prefix_title = ""  # we have a logo already containing "py lib"
    encoding = 'latin1' 
    logo = html.div(
        html.a(
            html.img(alt="py lib", id='pyimg', height=114, width=154, 
                              src="http://codespeak.net/img/pylib.png"), 
                            href="http://codespeak.net"))
    Page = PyPage 

    def __init__(self, sourcepath=None):
        if sourcepath is None:
            sourcepath = self.mydir
        self.setpath(sourcepath)

    def setpath(self, sourcepath, docpath=None, 
                apigenpath=None, stylesheet=None):
        self.sourcepath = sourcepath
        if docpath is None:
            docpath = sourcepath
        self.docpath = docpath
        if apigenpath is None:
            apigenpath = docpath
        self.apigenpath = apigenpath
        if stylesheet is None:
            p = sourcepath.join("style.css")
            if p.check():
                self.stylesheet = p
            else:
                self.stylesheet = None
        else:
            p = sourcepath.join(stylesheet)
            if p.check():
                stylesheet = p
            self.stylesheet = stylesheet
        #assert self.stylesheet
        self.apigen_relpath = relpath(
            self.docpath.strpath + '/', self.apigenpath.strpath + '/')

    def get_content(self, txtpath, encoding):
        return unicode(txtpath.read(), encoding)

    def get_htmloutputpath(self, txtpath):
        reloutputpath = txtpath.new(ext='.html').relto(self.sourcepath)
        return self.docpath.join(reloutputpath)

    def process(self, txtpath): 
        encoding = self.encoding
        content = self.get_content(txtpath, encoding)
        outputpath = self.get_htmloutputpath(txtpath)

        stylesheet = self.stylesheet
        if isinstance(stylesheet, py.path.local):
            if not self.docpath.join(stylesheet.basename).check():
                docpath.ensure(dir=True)
                stylesheet.copy(docpath)
            stylesheet = relpath(outputpath.strpath,
                                 self.docpath.join(stylesheet.basename).strpath)

        content = convert_rest_html(content, txtpath,
                                    stylesheet=stylesheet, encoding=encoding)
        content = strip_html_header(content, encoding=encoding)

        page = self.Page(self, "[%s] " % txtpath.purebasename,
                         outputpath, stylesheeturl=stylesheet)

        try:
            svninfo = txtpath.info() 
            modified = " modified %s by %s" % (worded_time(svninfo.mtime),
                                               getrealname(svninfo.last_author))
        except (KeyboardInterrupt, SystemExit): 
            raise
        except:
            modified = " "

        page.contentspace.append(
            html.div(html.div(modified, style="float: right; font-style: italic;"), 
                     id = 'docinfoline'))

        page.contentspace.append(py.xml.raw(content))
        outputpath.ensure().write(page.unicode().encode(encoding)) 

# XXX this function comes from apigen/linker.py, put it
# somewhere in py lib 
import os
def relpath(p1, p2, sep=os.path.sep, back='..', normalize=True):
    """ create a relative path from p1 to p2

        sep is the seperator used for input and (depending
        on the setting of 'normalize', see below) output

        back is the string used to indicate the parent directory

        when 'normalize' is True, any backslashes (\) in the path
        will be replaced with forward slashes, resulting in a consistent
        output on Windows and the rest of the world

        paths to directories must end on a / (URL style)
    """
    if normalize:
        p1 = p1.replace(sep, '/')
        p2 = p2.replace(sep, '/')
        sep = '/'
        # XXX would be cool to be able to do long filename
        # expansion and drive
        # letter fixes here, and such... iow: windows sucks :(
    if (p1.startswith(sep) ^ p2.startswith(sep)):
        raise ValueError("mixed absolute relative path: %r -> %r" %(p1, p2))
    fromlist = p1.split(sep)
    tolist = p2.split(sep)

    # AA
    # AA BB     -> AA/BB
    #
    # AA BB
    # AA CC     -> CC
    #
    # AA BB 
    # AA      -> ../AA

    diffindex = 0
    for x1, x2 in zip(fromlist, tolist):
        if x1 != x2:
            break
        diffindex += 1
    commonindex = diffindex - 1

    fromlist_diff = fromlist[diffindex:]
    tolist_diff = tolist[diffindex:]

    if not fromlist_diff:
        return sep.join(tolist[commonindex:])
    backcount = len(fromlist_diff)
    if tolist_diff:
        return sep.join([back,]*(backcount-1) + tolist_diff)
    return sep.join([back,]*(backcount) + tolist[commonindex:])


