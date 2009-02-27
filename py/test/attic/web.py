
""" web server for py.test
"""

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

import thread, threading
import re
import time
import random
import Queue
import os
import sys
import socket

import py
from py.test import collect 
from py.__.test.report.webdata import json

DATADIR = py.path.local(__file__).dirpath("webdata")
FUNCTION_LIST = ["main", "show_skip", "show_traceback", "show_info", "hide_info",
    "show_host", "hide_host", "hide_messagebox", "opt_scroll"]

try:
    from pypy.rpython.ootypesystem.bltregistry import MethodDesc, BasicExternal
    from pypy.translator.js.main import rpython2javascript
    from pypy.translator.js import commproxy
    from pypy.translator.js.lib.support import callback

    commproxy.USE_MOCHIKIT = False
    IMPORTED_PYPY = True
except (ImportError, NameError):
    class BasicExternal(object):
        pass

    def callback(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    IMPORTED_PYPY = False

def add_item(event):
    """ A little helper
    """
    item = event.item
    itemtype = item.__class__.__name__
    itemname = item.name
    fullitemname = "/".join(item.listnames())
    d = {'fullitemname': fullitemname, 'itemtype': itemtype,
         'itemname': itemname}
    #if itemtype == 'Module':
    try:
        d['length'] = str(len(list(event.item._tryiter())))
    except:
        d['length'] = "?"
    return d

class MultiQueue(object):
    """ a tailor-made queue (internally using Queue) for py.test.dsession.web

        API-wise the main difference is that the get() method gets a sessid
        argument, which is used to determine what data to feed to the client

        when a data queue for a sessid doesn't yet exist, it is created, and
        filled with data that has already been fed to the other clients
    """
    def __init__(self):
        self._cache = []
        self._session_queues = {}
        self._lock = py.std.thread.allocate_lock()

    def put(self, item):
        self._lock.acquire()
        try:
            self._cache.append(item)
            for key, q in self._session_queues.items():
                q.put(item)
        finally:
            self._lock.release()
    
    def _del(self, sessid):
        self._lock.acquire()
        try:
            del self._session_queues[sessid]
        finally:
            self._lock.release()

    def get(self, sessid):
        self._lock.acquire()
        try:
            if not sessid in self._session_queues:
                self._create_session_queue(sessid)
        finally:
            self._lock.release()
        return self._session_queues[sessid].get(sessid)

    def empty(self):
        self._lock.acquire()
        try:
            if not self._session_queues:
                return not len(self._cache)
            for q in self._session_queues.values():
                if not q.empty():
                    return False
        finally:
            self._lock.release()
        return True

    def empty_queue(self, sessid):
        return self._session_queues[sessid].empty()

    def _create_session_queue(self, sessid):
        self._session_queues[sessid] = q = Queue.Queue()
        for item in self._cache:
            q.put(item)

class ExportedMethods(BasicExternal):
    _render_xmlhttp = True
    def __init__(self):
        self.pending_events = MultiQueue()
        self.start_event = threading.Event()
        self.end_event = threading.Event()
        self.skip_reasons = {}
        self.fail_reasons = {}
        self.stdout = {}
        self.stderr = {}
        self.all = 0
        self.to_rsync = {}
    
    def findmodule(self, item):
        # find the most outwards parent which is module
        current = item
        while current:
            if isinstance(current, collect.Module):
                break
            current = current.parent
        
        if current is not None:
            return str(current.name), str("/".join(current.listnames()))
        else:
            return str(item.parent.name), str("/".join(item.parent.listnames()))
    
    def show_hosts(self):
        self.start_event.wait()
        to_send = {}
        for host in self.hosts:
            to_send[host.hostid] = host.hostname
        return to_send
    show_hosts = callback(retval={str:str})(show_hosts)
    
    def show_skip(self, item_name="aa"):
        return {'item_name': item_name,
                           'reason': self.skip_reasons[item_name]}
    show_skip = callback(retval={str:str})(show_skip)
    
    def show_fail(self, item_name="aa"):
        return {'item_name':item_name,
                           'traceback':str(self.fail_reasons[item_name]),
                           'stdout':self.stdout[item_name],
                           'stderr':self.stderr[item_name]}
    show_fail = callback(retval={str:str})(show_fail)
    
    _sessids = None
    _sesslock = py.std.thread.allocate_lock()
    def show_sessid(self):
        if not self._sessids:
            self._sessids = []
        self._sesslock.acquire()
        try:
            while 1:
                sessid = ''.join(py.std.random.sample(
                                 py.std.string.lowercase, 8))
                if sessid not in self._sessids:
                    self._sessids.append(sessid)
                    break
        finally:
            self._sesslock.release()
        return sessid
    show_sessid = callback(retval=str)(show_sessid)
    
    def failed(self, **kwargs):
        if not 'sessid' in kwargs:
            return
        sessid = kwargs['sessid']
        to_del = -1
        for num, i in enumerate(self._sessids):
            if i == sessid:
                to_del = num
        if to_del != -1:
            del self._sessids[to_del]
        self.pending_events._del(kwargs['sessid'])
    
    def show_all_statuses(self, sessid='xx'):
        retlist = [self.show_status_change(sessid)]
        while not self.pending_events.empty_queue(sessid):
            retlist.append(self.show_status_change(sessid))
        retval = retlist
        return retval
    show_all_statuses = callback(retval=[{str:str}])(show_all_statuses)
        
    def show_status_change(self, sessid):
        event = self.pending_events.get(sessid)
        if event is None:
            self.end_event.set()
            return {}
        # some dispatcher here
        if isinstance(event, event.ItemFinish):
            args = {}
            outcome = event.outcome
            for key, val in outcome.__dict__.iteritems():
                args[key] = str(val)
            args.update(add_item(event))
            mod_name, mod_fullname = self.findmodule(event.item)
            args['modulename'] = str(mod_name)
            args['fullmodulename'] = str(mod_fullname)
            fullitemname = args['fullitemname']
            if outcome.skipped:
                self.skip_reasons[fullitemname] = self.repr_failure_tblong(
                    event.item,
                    outcome.skipped,
                    outcome.skipped.traceback)
            elif outcome.excinfo:
                self.fail_reasons[fullitemname] = self.repr_failure_tblong(
                    event.item, outcome.excinfo, outcome.excinfo.traceback)
                self.stdout[fullitemname] = outcome.stdout
                self.stderr[fullitemname] = outcome.stderr
            elif outcome.signal:
                self.fail_reasons[fullitemname] = "Received signal %d" % outcome.signal
                self.stdout[fullitemname] = outcome.stdout
                self.stderr[fullitemname] = outcome.stderr
            if event.channel:
                args['hostkey'] = event.channel.gateway.host.hostid
            else:
                args['hostkey'] = ''
        elif isinstance(event, event.ItemStart):
            args = add_item(event)
        elif isinstance(event, event.TestTestrunFinish):
            args = {}
            args['run'] = str(self.all)
            args['fails'] = str(len(self.fail_reasons))
            args['skips'] = str(len(self.skip_reasons))
        elif isinstance(event, event.SendItem):
            args = add_item(event)
            args['hostkey'] = event.channel.gateway.host.hostid
        elif isinstance(event, event.HostRSyncRootReady):
            self.ready_hosts[event.host] = True
            args = {'hostname' : event.host.hostname, 'hostkey' : event.host.hostid}
        elif isinstance(event, event.FailedTryiter):
            args = add_item(event)
        elif isinstance(event, event.DeselectedItem):
            args = add_item(event)
            args['reason'] = str(event.excinfo.value)
        else:
            args = {}
        args['event'] = str(event)
        args['type'] = event.__class__.__name__
        return args

    def repr_failure_tblong(self, item, excinfo, traceback):
        lines = []
        for index, entry in py.builtin.enumerate(traceback):
            lines.append('----------')
            lines.append("%s: %s" % (entry.path, entry.lineno))
            lines += self.repr_source(entry.relline, entry.source)
        lines.append("%s: %s" % (excinfo.typename, excinfo.value))
        return "\n".join(lines)
    
    def repr_source(self, relline, source):
        lines = []
        for num, line in enumerate(str(source).split("\n")):
            if num == relline:
                lines.append(">>>>" + line)
            else:
                lines.append("    " + line)
        return lines

    def report_ItemFinish(self, event):
        self.all += 1
        self.pending_events.put(event)

    def report_FailedTryiter(self, event):
        fullitemname = "/".join(event.item.listnames())
        self.fail_reasons[fullitemname] = self.repr_failure_tblong(
            event.item, event.excinfo, event.excinfo.traceback)
        self.stdout[fullitemname] = ''
        self.stderr[fullitemname] = ''
        self.pending_events.put(event)
    
    def report_ItemStart(self, event):
        if isinstance(event.item, py.test.collect.Module):
            self.pending_events.put(event)
    
    def report_unknown(self, event):
        # XXX: right now, we just pass it for showing
        self.pending_events.put(event)

    def _host_ready(self, event):
        self.pending_events.put(event)

    def report_HostGatewayReady(self, item):
        self.to_rsync[item.host] = len(item.roots)

    def report_HostRSyncRootReady(self, item):
        self.to_rsync[item.host] -= 1
        if not self.to_rsync[item.host]:
            self._host_ready(item)

    def report_TestStarted(self, event):
        # XXX: It overrides our self.hosts
        self.hosts = {}
        self.ready_hosts = {}
        if not event.hosts:
            self.hosts = []
        else:
            for host in event.hosts:
                self.hosts[host] = host
                self.ready_hosts[host] = False
        self.start_event.set()
        self.pending_events.put(event)

    def report_TestTestrunFinish(self, event):
        self.pending_events.put(event)
        kill_server()

    report_InterruptedExecution = report_TestTestrunFinish
    report_CrashedExecution = report_TestTestrunFinish
    
    def report(self, what):
        repfun = getattr(self, "report_" + what.__class__.__name__,
                         self.report_unknown)
        try:
            repfun(what)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            print "Internal reporting problem"
            excinfo = py.code.ExceptionInfo()
            for i in excinfo.traceback:
                print str(i)[2:-1]
            print excinfo

exported_methods = ExportedMethods()

class TestHandler(BaseHTTPRequestHandler):
    exported_methods = exported_methods
    
    def do_GET(self):
        path = self.path
        if path.endswith("/"):
            path = path[:-1]
        if path.startswith("/"):
            path = path[1:]
        m = re.match('^(.*)\?(.*)$', path)
        if m:
            path = m.group(1)
            getargs = m.group(2)
        else:
            getargs = ""
        name_path = path.replace(".", "_")
        method_to_call = getattr(self, "run_" + name_path, None)
        if method_to_call is None:
            exec_meth = getattr(self.exported_methods, name_path, None)
            if exec_meth is None:
                self.send_error(404, "File %s not found" % path)
            else:
                try:
                    self.serve_data('text/json',
                                json.write(exec_meth(**self.parse_args(getargs))))
                except socket.error:
                    # client happily disconnected
                    exported_methods.failed(**self.parse_args(getargs))
        else:
            method_to_call()
    
    def parse_args(self, getargs):
        # parse get argument list
        if getargs == "":
            return {}
        
        unquote = py.std.urllib.unquote
        args = {}
        arg_pairs = getargs.split("&")
        for arg in arg_pairs:
            key, value = arg.split("=")
            args[unquote(key)] = unquote(value)
        return args
    
    def log_message(self, format, *args):
        # XXX just discard it
        pass
    
    do_POST = do_GET
    
    def run_(self):
        self.run_index()
    
    def run_index(self):
        data = py.path.local(DATADIR).join("index.html").open().read()
        self.serve_data("text/html", data)
    
    def run_jssource(self):
        js_name = py.path.local(__file__).dirpath("webdata").join("source.js")
        web_name = py.path.local(__file__).dirpath().join("webjs.py")
        if IMPORTED_PYPY and web_name.mtime() > js_name.mtime() or \
            (not js_name.check()):
            from py.__.test.dsession import webjs

            javascript_source = rpython2javascript(webjs,
                FUNCTION_LIST, use_pdb=False)
            open(str(js_name), "w").write(javascript_source)
            self.serve_data("text/javascript", javascript_source)
        else:
            js_source = open(str(js_name), "r").read()
            self.serve_data("text/javascript", js_source)
    
    def serve_data(self, content_type, data):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-length", len(data))
        self.end_headers()
        self.wfile.write(data)

class WebReporter(object):
    """ A simple wrapper, this file needs ton of refactoring
    anyway, so this is just to satisfy things below
    (and start to create saner interface as well)
    """
    def __init__(self, config, hosts):
        start_server_from_config(config)

    def was_failure(self):
        return sum(exported_methods.fail_reasons.values()) > 0

    # rebind
    report = exported_methods.report
    __call__ = report

def start_server_from_config(config):
    if config.option.runbrowser:
        port = socket.INADDR_ANY
    else:
        port = 8000

    httpd = start_server(server_address = ('', port))
    port = httpd.server_port
    if config.option.runbrowser:
        import webbrowser, thread
        # webbrowser.open() may block until the browser finishes or not
        url = "http://localhost:%d" % (port,)
        thread.start_new_thread(webbrowser.open, (url,))

    return exported_methods.report

def start_server(server_address = ('', 8000), handler=TestHandler, start_new=True):
    httpd = HTTPServer(server_address, handler)

    if start_new:
        thread.start_new_thread(httpd.serve_forever, ())
        print "Server started, listening on port %d" % (httpd.server_port,)
        return httpd
    else:
        print "Server started, listening on port %d" % (httpd.server_port,)
        httpd.serve_forever()

def kill_server():
    exported_methods.pending_events.put(None)
    while not exported_methods.pending_events.empty():
        time.sleep(.1)
    exported_methods.end_event.wait()

