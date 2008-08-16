import py
from py.__.misc.rest import convert_rest_html, strip_html_header 
from py.__.misc.difftime import worded_time 
from py.__.doc.conftest import get_apigenpath, get_docpath
from py.__.apigen.linker import relpath

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
        docpath = self.project.get_docpath()
        return html.a(name, class_="menu",
                      href=relpath(self.targetpath.strpath,
                                   docpath.join(relhtmlpath).strpath))

    def a_apigenref(self, name, relhtmlpath):
        apipath = get_apigenpath()
        return html.a(name, class_="menu",
                      href=relpath(self.targetpath.strpath,
                                   apipath.join(relhtmlpath).strpath))
        
    def fill_menubar(self):
        items = [
            self.a_docref("index", "index.html"),
            self.a_apigenref("api", "api/index.html"),
            self.a_apigenref("source", "source/index.html"),
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
    # string for url, path for local file
    stylesheet = mydir.join('style.css')
    title = "py lib"
    prefix_title = ""  # we have a logo already containing "py lib"
    encoding = 'latin1' 
    logo = html.div(
        html.a(
            html.img(alt="py lib", id='pyimg', height=114, width=154, 
                              src="http://codespeak.net/img/pylib.png"), 
                            href="http://codespeak.net"))
    Page = PyPage 


    def get_content(self, txtpath, encoding):
        return unicode(txtpath.read(), encoding)

    def get_docpath(self):
        return get_docpath()

    def get_htmloutputpath(self, txtpath):
        docpath = self.get_docpath()
        reloutputpath = txtpath.new(ext='.html').relto(self.mydir)
        return docpath.join(reloutputpath)

    def process(self, txtpath): 
        encoding = self.encoding
        content = self.get_content(txtpath, encoding)
        docpath = self.get_docpath()
        outputpath = self.get_htmloutputpath(txtpath)

        stylesheet = self.stylesheet
        if isinstance(self.stylesheet, py.path.local):
            if not docpath.join(stylesheet.basename).check():
                docpath.ensure(dir=True)
                stylesheet.copy(docpath)
            stylesheet = relpath(outputpath.strpath,
                                 docpath.join(stylesheet.basename).strpath)

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

