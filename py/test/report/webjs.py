
""" javascript source for py.test distributed
"""

import py
from py.__.test.report.web import exported_methods
try:
    from pypy.translator.js.modules import dom
    from pypy.translator.js.helper import __show_traceback
except ImportError:
    py.test.skip("PyPy not found")

def create_elem(s):
    return dom.document.createElement(s)

def get_elem(el):
    return dom.document.getElementById(el)

def create_text_elem(txt):
    return dom.document.createTextNode(txt)

tracebacks = {}
skips = {}
counters = {}
max_items = {}
short_item_names = {}

MAX_COUNTER = 30 # Maximal size of one-line table

class Globals(object):
    def __init__(self):
        self.pending = []
        self.host = ""
        self.data_empty = True

glob = Globals()

class Options(object):
    """ Store global options
    """
    def __init__(self):
        self.scroll = True

opts = Options()

def comeback(msglist):
    if len(msglist) == 0:
        return
    for item in glob.pending[:]:
        if not process(item):
            return
    glob.pending = []
    for msg in msglist:
        if not process(msg):
            return
    exported_methods.show_all_statuses(glob.sessid, comeback)

def show_info(data="aa"):
    info = dom.document.getElementById("info")
    info.style.visibility = "visible"
    while len(info.childNodes):
        info.removeChild(info.childNodes[0])
    txt = create_text_elem(data)
    info.appendChild(txt)
    info.style.backgroundColor = "beige"
    # XXX: Need guido

def hide_info():
    info = dom.document.getElementById("info")
    info.style.visibility = "hidden"

def show_interrupt():
    glob.finished = True
    dom.document.title = "Py.test [interrupted]"
    dom.document.getElementById("Tests").childNodes[0].nodeValue = "Tests [interrupted]"

def show_crash():
    glob.finished = True
    dom.document.title = "Py.test [crashed]"
    dom.document.getElementById("Tests").childNodes[0].nodeValue = "Tests [crashed]"

SCROLL_LINES = 50

def opt_scroll():
    if opts.scroll:
        opts.scroll = False
    else:
        opts.scroll = True

def scroll_down_if_needed(mbox):
    if not opts.scroll:
        return
    #if dom.window.scrollMaxY - dom.window.scrollY < SCROLL_LINES:
    mbox.parentNode.scrollIntoView()

def hide_messagebox():
    mbox = dom.document.getElementById("messagebox")
    while mbox.childNodes:
        mbox.removeChild(mbox.childNodes[0])

def make_module_box(msg):
    tr = create_elem("tr")
    td = create_elem("td")
    tr.appendChild(td)
    td.appendChild(create_text_elem("%s[0/%s]" % (msg['itemname'],
                                                          msg['length'])))
    max_items[msg['fullitemname']] = int(msg['length'])
    short_item_names[msg['fullitemname']] = msg['itemname']
    td.id = '_txt_' + msg['fullitemname']
    #tr.setAttribute("id", msg['fullitemname'])
    td.setAttribute("onmouseover",
    "show_info('%s')" % (msg['fullitemname'],))
    td.setAttribute("onmouseout", "hide_info()")
    td2 = create_elem('td')
    tr.appendChild(td2)
    table = create_elem("table")
    td2.appendChild(table)
    tbody = create_elem('tbody')
    tbody.id = msg['fullitemname']
    table.appendChild(tbody)
    counters[msg['fullitemname']] = 0
    return tr

def add_received_item_outcome(msg, module_part):
    if msg['hostkey']:
        host_elem = dom.document.getElementById(msg['hostkey'])
        glob.host_pending[msg['hostkey']].pop()
        count = len(glob.host_pending[msg['hostkey']])
        host_elem.childNodes[0].nodeValue = '%s[%s]' % (
            glob.host_dict[msg['hostkey']], count)
        
    td = create_elem("td")
    td.setAttribute("onmouseover", "show_info('%s')" % (
        msg['fullitemname'],))
    td.setAttribute("onmouseout", "hide_info()")
    item_name = msg['fullitemname']
    # TODO: dispatch output
    if msg["passed"] == 'True':
        txt = create_text_elem(".")
        td.appendChild(txt)
    elif msg["skipped"] != 'None' and msg["skipped"] != "False":
        exported_methods.show_skip(item_name, skip_come_back)
        link = create_elem("a")
        link.setAttribute("href", "javascript:show_skip('%s')" % (
                                                msg['fullitemname'],))
        txt = create_text_elem('s')
        link.appendChild(txt)
        td.appendChild(link)
    else:
        link = create_elem("a")
        link.setAttribute("href", "javascript:show_traceback('%s')" % (
                                                msg['fullitemname'],))
        txt = create_text_elem('F')
        link.setAttribute('class', 'error') 
        link.appendChild(txt)
        td.appendChild(link)
        exported_methods.show_fail(item_name, fail_come_back)
        
    if counters[msg['fullmodulename']] == 0:
        tr = create_elem("tr")
        module_part.appendChild(tr)

    name = msg['fullmodulename']
    counters[name] += 1
    counter_part = get_elem('_txt_' + name)
    newcontent = "%s[%d/%d]" % (short_item_names[name], counters[name],
        max_items[name])
    counter_part.childNodes[0].nodeValue = newcontent
    module_part.childNodes[-1].appendChild(td)
    
def process(msg):
    if len(msg) == 0:
        return False
    elem = dom.document.getElementById("testmain")
    #elem.innerHTML += '%s<br/>' % msg['event']
    main_t = dom.document.getElementById("main_table")
    if msg['type'] == 'ItemStart':
        # we start a new directory or what
        #if msg['itemtype'] == 'Module':
        tr = make_module_box(msg)
        main_t.appendChild(tr)
    elif msg['type'] == 'SendItem':
        host_elem = dom.document.getElementById(msg['hostkey'])
        glob.host_pending[msg['hostkey']].insert(0, msg['fullitemname'])
        count = len(glob.host_pending[msg['hostkey']])
        host_elem.childNodes[0].nodeValue = '%s[%s]' % (
                            glob.host_dict[msg['hostkey']], count)
        
    elif msg['type'] == 'HostRSyncRootReady':
        host_elem = dom.document.getElementById(msg['hostkey'])
        host_elem.style.background = \
            "#00ff00"
        host_elem.childNodes[0].nodeValue = '%s[0]' % (
                                    glob.host_dict[msg['hostkey']],)
    elif msg['type'] == 'ItemFinish':
        module_part = get_elem(msg['fullmodulename'])
        if not module_part:
            glob.pending.append(msg)
            return True

        add_received_item_outcome(msg, module_part)
    elif msg['type'] == 'TestTestrunFinish':
        text = "FINISHED %s run, %s failures, %s skipped" % (msg['run'], msg['fails'], msg['skips'])
        glob.finished = True
        dom.document.title = "Py.test %s" % text
        dom.document.getElementById("Tests").childNodes[0].nodeValue = \
                                                    "Tests [%s]" % text
    elif msg['type'] == 'FailedTryiter':
        module_part = get_elem(msg['fullitemname'])
        if not module_part:
            glob.pending.append(msg)
            return True
        tr = create_elem("tr")
        td = create_elem("td")
        a = create_elem("a")
        a.setAttribute("href", "javascript:show_traceback('%s')" % (
                        msg['fullitemname'],))
        txt = create_text_elem("- FAILED TO LOAD MODULE")
        a.appendChild(txt)
        td.appendChild(a)
        tr.appendChild(td)
        module_part.appendChild(tr)
        item_name = msg['fullitemname']
        exported_methods.show_fail(item_name, fail_come_back)
    elif msg['type'] == 'DeselectedItem':
        module_part = get_elem(msg['fullitemname'])
        if not module_part:
            glob.pending.append(msg)
            return True
        tr = create_elem("tr")
        td = create_elem("td")
        txt = create_text_elem("- skipped (%s)" % (msg['reason'],))
        td.appendChild(txt)
        tr.appendChild(td)
        module_part.appendChild(tr)
    elif msg['type'] == 'RsyncFinished':
        glob.rsync_done = True
    elif msg['type'] == 'InterruptedExecution':
        show_interrupt()
    elif msg['type'] == 'CrashedExecution':
        show_crash()
    if glob.data_empty:
        mbox = dom.document.getElementById('messagebox')
        scroll_down_if_needed(mbox)
    return True

def show_skip(item_name="aa"):
    set_msgbox(item_name, skips[item_name])

def set_msgbox(item_name, data):
    msgbox = get_elem("messagebox")
    while len(msgbox.childNodes):
        msgbox.removeChild(msgbox.childNodes[0])
    pre = create_elem("pre")
    txt = create_text_elem(item_name + "\n" + data)
    pre.appendChild(txt)
    msgbox.appendChild(pre)
    dom.window.location.assign("#message")
    glob.data_empty = False

def show_traceback(item_name="aa"):
    data = ("====== Traceback: =========\n%s\n======== Stdout: ========\n%s\n"
            "========== Stderr: ==========\n%s\n" % tracebacks[item_name])
    set_msgbox(item_name, data)
    
def fail_come_back(msg):
    tracebacks[msg['item_name']] = (msg['traceback'], msg['stdout'],
                                    msg['stderr'])
    
def skip_come_back(msg):
    skips[msg['item_name']] = msg['reason']

def reshow_host():
    if glob.host == "":
        return
    show_host(glob.host)
    
def show_host(host_name="aa"):
    elem = dom.document.getElementById("jobs")
    if elem.childNodes:
        elem.removeChild(elem.childNodes[0])
    tbody = create_elem("tbody")
    for item in glob.host_pending[host_name]:
        tr = create_elem("tr")
        td = create_elem("td")
        td.appendChild(create_text_elem(item))
        tr.appendChild(td)
        tbody.appendChild(tr)
    elem.appendChild(tbody)
    elem.style.visibility = "visible"
    glob.host = host_name
    dom.setTimeout(reshow_host, 100)
    
def hide_host():
    elem = dom.document.getElementById("jobs")
    while len(elem.childNodes):
        elem.removeChild(elem.childNodes[0])
    elem.style.visibility = "hidden"
    glob.host = ""

def update_rsync():
    if glob.finished:
        return
    elem = dom.document.getElementById("Tests")
    if glob.rsync_done is True:
        elem.childNodes[0].nodeValue = "Tests"
        return
    text = "Rsyncing" + '.' * glob.rsync_dots
    glob.rsync_dots += 1
    if glob.rsync_dots > 5:
        glob.rsync_dots = 0
    elem.childNodes[0].nodeValue = "Tests [%s]" % text
    dom.setTimeout(update_rsync, 1000)

def host_init(host_dict):
    tbody = dom.document.getElementById("hostsbody")
    for host in host_dict.keys():
        tr = create_elem('tr')
        tbody.appendChild(tr)
        td = create_elem("td")
        td.style.background = "#ff0000"
        txt = create_text_elem(host_dict[host])
        td.appendChild(txt)
        td.id = host
        tr.appendChild(td)
        td.setAttribute("onmouseover", "show_host('%s')" % host)
        td.setAttribute("onmouseout", "hide_host()")
        glob.rsync_dots = 0
        glob.rsync_done = False
        dom.setTimeout(update_rsync, 1000)
    glob.host_dict = host_dict
    glob.host_pending = {}
    for key in host_dict.keys():
        glob.host_pending[key] = []

def key_pressed(key):
    if key.charCode == ord('s'):
        scroll_box = dom.document.getElementById("opt_scroll")
        if opts.scroll:
            scroll_box.removeAttribute("checked")
            opts.scroll = False
        else:
            scroll_box.setAttribute("checked", "true")
            opts.scroll = True

def sessid_comeback(id):
    glob.sessid = id
    exported_methods.show_all_statuses(id, comeback)

def main():
    glob.finished = False
    exported_methods.show_hosts(host_init)
    exported_methods.show_sessid(sessid_comeback)
    dom.document.onkeypress = key_pressed
    dom.document.getElementById("opt_scroll").setAttribute("checked", "True")
