import py
from py.__.misc.rest import convert_rest_html, strip_html_header 
from py.__.misc.difftime import worded_time 
from py.__.doc.conftest import get_apigen_relpath

mydir = py.magic.autopath().dirpath()
html = py.xml.html 

class Page(object): 
    doctype = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
               ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')

    def __init__(self, project, title, stylesheeturl=None, type="text/html", encoding="ISO-8859-1"): 
        self.project = project 
        self.title = project.prefix_title + title 
        self.stylesheeturl = stylesheeturl 
        self.type = type 
        self.encoding = encoding 

        self.body = html.body()
        self.head = html.head() 
        self._root = html.html(self.head, self.body) 
        self.fill() 

    def fill(self): 
        apigen_relpath = get_apigen_relpath()
        content_type = "%s;charset=%s" %(self.type, self.encoding) 
        self.head.append(html.title(self.title)) 
        self.head.append(html.meta(name="Content-Type", content=content_type))
        if self.stylesheeturl: 
            self.head.append(
                    html.link(href=self.stylesheeturl, 
                              media="screen", rel="stylesheet", 
                              type="text/css"))
        self.menubar = html.div(
            html.a("home", href="home.html", class_="menu"), " ",
            html.a("doc", href="index.html", class_="menu"), " ",
            html.a("api", href=apigen_relpath + "api/index.html", class_="menu"),
            " ",
            html.a("source", href=apigen_relpath + "source/index.html",
                   class_="menu"), " ",
            html.a("contact", href="contact.html", class_="menu"), " ", 
            html.a("download", href="download.html", class_="menu"), " ",
            id="menubar", 
        )
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
    def fill(self): 
        super(PyPage, self).fill() 
        # base layout 
        self.menubar.append(
            html.a("issue", href="https://codespeak.net/issue/py-dev/", class_="menu"), 
        ) 
                            

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
    stylesheet = 'style.css'
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

    def process(self, txtpath): 
        encoding = self.encoding
        content = self.get_content(txtpath, encoding)
        stylesheet = self.stylesheet 
        if not stylesheet.startswith('http') and \
           not txtpath.dirpath(stylesheet).check(): 
            stylesheet = None 

        content = convert_rest_html(content, txtpath, stylesheet=stylesheet, encoding=encoding) 
        content = strip_html_header(content, encoding=encoding)

        page = self.Page(self, "[%s] " % txtpath.purebasename, stylesheeturl=stylesheet)

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
        htmlpath = txtpath.new(ext='.html') 
        htmlpath.write(page.unicode().encode(encoding)) 

