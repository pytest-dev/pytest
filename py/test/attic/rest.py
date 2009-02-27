
""" Rest reporting stuff
"""

import py
import sys
from StringIO import StringIO
from py.__.test.reporter import AbstractReporter
from py.__.test import event
from py.__.rest.rst import *

class RestReporter(AbstractReporter):
    linkwriter = None

    def __init__(self, config, hosts):
        super(RestReporter, self).__init__(config, hosts)
        self.rest = Rest()
        self.traceback_num = 0
        self.failed = dict([(host, 0) for host in hosts])
        self.skipped = dict([(host, 0) for host in hosts])
        self.passed = dict([(host, 0) for host in hosts])
    
    def get_linkwriter(self):
        if self.linkwriter is None:
            try:
                self.linkwriter = self.config.getvalue('linkwriter')
            except KeyError:
                print >>sys.stderr, ('no linkwriter configured, using default '
                                     'one')
                self.linkwriter = RelLinkWriter()
        return self.linkwriter
        
    def report_unknown(self, what):
        if self.config.option.verbose:
            self.add_rest(Paragraph("Unknown report: %s" % what))

    def gethost(self, item):
        if item.channel:
            return item.channel.gateway.host
        return self.hosts[0]

    def report_SendItem(self, item):
        address = self.gethost(item).hostname
        if self.config.option.verbose:
            self.add_rest(Paragraph('sending item %s to %s' % (item.item,
                                                               address)))

    def report_HostRSyncing(self, item):
        self.add_rest(LiteralBlock('%10s: RSYNC ==> %s' % (item.host.hostname[:10],
                                                        item.host.relpath)))

    def _host_ready(self, item):
        self.add_rest(LiteralBlock('%10s: READY' % (item.host.hostname[:10],)))

    def report_TestStarted(self, event):
        txt = "Running tests on hosts: %s" % ", ".join([i.hostname for i in
                                                        event.hosts])
        self.add_rest(Title(txt, abovechar='=', belowchar='='))
        self.timestart = event.timestart

    def report_TestTestrunFinish(self, item):
        self.timeend = item.timeend
        self.summary()
        return len(self.failed_tests_outcome) > 0

    def report_ImmediateFailure(self, item):
        pass

    def report_HostGatewayReady(self, item):
        self.to_rsync[item.host] = len(item.roots)

    def report_ItemStart(self, event):
        item = event.item
        if isinstance(item, py.test.collect.Module):
            lgt = len(list(item._tryiter()))
            lns = item.listnames()[1:]
            name = "/".join(lns)
            link = self.get_linkwriter().get_link(self.get_rootpath(item),
                                                  item.fspath)
            if link:
                name = Link(name, link)
            txt = 'Testing module %s (%d items)' % (name, lgt)
            self.add_rest(Title('Testing module', name, '(%d items)' % (lgt,),
                                belowchar='-'))
    
    def get_rootpath(self, item):
        root = item.parent
        while root.parent is not None:
            root = root.parent
        return root.fspath

    def print_summary(self, total, skipped_str, failed_str):
        self.skips()
        self.failures()

        txt = "%d tests run%s%s in %.2fs (rsync: %.2f)" % \
            (total, skipped_str, failed_str, self.timeend - self.timestart,
             self.timersync - self.timestart)
        self.add_rest(Title(txt, belowchar='-'))

        # since we're rendering each item, the links haven't been rendered
        # yet
        self.out.write(self.rest.render_links())

    def report_ItemFinish(self, event):
        host = self.gethost(event)
        if event.outcome.passed:
            status = [Strong("PASSED")]
            self.passed[host] += 1
        elif event.outcome.skipped:
            status = [Strong("SKIPPED")]
            self.skipped_tests_outcome.append(event)
            self.skipped[host] += 1
        else:
            status = [Strong("FAILED"),
                      InternalLink("traceback%d" % self.traceback_num)]
            self.traceback_num += 1
            self.failed[host] += 1
            self.failed_tests_outcome.append(event)
            # we'll take care of them later
        itempath = self.get_path_from_item(event.item)
        status.append(Text(itempath))
        hostname = host.hostname
        self.add_rest(ListItem(Text("%10s:" % (hostname[:10],)), *status))

    def skips(self):
        # XXX hrmph, copied code
        texts = {}
        for event in self.skipped_tests_outcome:
            colitem = event.item
            if isinstance(event, event.ItemFinish):
                outcome = event.outcome
                text = outcome.skipped
                itemname = self.get_item_name(event, colitem)
            elif isinstance(event, event.DeselectedItem):
                text = str(event.excinfo.value)
                itemname = "/".join(colitem.listnames())
            if text not in texts:
                texts[text] = [itemname]
            else:
                texts[text].append(itemname)
        if texts:
            self.add_rest(Title('Reasons for skipped tests:', belowchar='+'))
            for text, items in texts.items():
                for item in items:
                    self.add_rest(ListItem('%s: %s' % (item, text)))

    def get_host(self, event):
        try:
            return event.channel.gateway.host
        except AttributeError:
            return None

    def failures(self):
        self.traceback_num = 0
        tbstyle = self.config.option.tbstyle
        if self.failed_tests_outcome:
            self.add_rest(Title('Exceptions:', belowchar='+'))
        for i, event in enumerate(self.failed_tests_outcome):
            if i > 0:
                self.add_rest(Transition())
            if isinstance(event, event.ItemFinish):
                host = self.get_host(event)
                itempath = self.get_path_from_item(event.item)
                root = self.get_rootpath(event.item)
                link = self.get_linkwriter().get_link(root, event.item.fspath)
                t = Title(belowchar='+')
                if link:
                    t.add(Link(itempath, link))
                else:
                    t.add(Text(itempath))
                if host:
                    t.add(Text('on %s' % (host.hostname,)))
                self.add_rest(t)
                if event.outcome.signal:
                    self.repr_signal(event.item, event.outcome)
                else:
                    self.repr_failure(event.item, event.outcome, tbstyle)
            else:
                itempath = self.get_path_from_item(event.item)
                root = self.get_rootpath(event.item)
                link = self.get_linkwriter().get_link(root, event.item.fspath)
                t = Title(abovechar='+', belowchar='+')
                if link:
                    t.add(Link(itempath, link))
                else:
                    t.add(Text(itempath))
                out = outcome.Outcome(excinfo=event.excinfo)
                self.repr_failure(event.item,
                                  outcome.ReprOutcome(out.make_repr()),
                                  tbstyle)

    def repr_signal(self, item, outcome):
        signal = outcome.signal
        self.add_rest(Title('Received signal: %d' % (outcome.signal,),
                            abovechar='+', belowchar='+'))
        if outcome.stdout.strip():
            self.add_rest(Paragraph('Captured process stdout:'))
            self.add_rest(LiteralBlock(outcome.stdout))
        if outcome.stderr.strip():
            self.add_rest(Paragraph('Captured process stderr:'))
            self.add_rest(LiteralBlock(outcome.stderr))

    def repr_failure(self, item, outcome, style):
        excinfo = outcome.excinfo
        traceback = excinfo.traceback
        if not traceback:
            self.add_rest(Paragraph('empty traceback from item %r' % (item,)))
            return
        self.repr_traceback(item, excinfo, traceback, style)
        if outcome.stdout:
            self.add_rest(Title('Captured process stdout:', abovechar='+',
                                belowchar='+'))
            self.add_rest(LiteralBlock(outcome.stdout))
        if outcome.stderr:
            self.add_rest(Title('Captured process stderr:', abovechar='+',
                                belowchar='+'))
            self.add_rest(LiteralBlock(outcome.stderr))

    def repr_traceback(self, item, excinfo, traceback, style):
        root = self.get_rootpath(item)
        self.add_rest(LinkTarget('traceback%d' % self.traceback_num, ""))
        self.traceback_num += 1
        if style == 'long':
            for entry in traceback:
                link = self.get_linkwriter().get_link(root,
                                            py.path.local(entry.path))
                if link:
                    self.add_rest(Title(Link(entry.path, link),
                                        'line %d' % (entry.lineno,),
                                        belowchar='+', abovechar='+'))
                else:
                    self.add_rest(Title('%s line %d' % (entry.path,
                                                        entry.lineno,),
                                        belowchar='+', abovechar='+'))
                self.add_rest(LiteralBlock(self.prepare_source(entry.relline,
                                                               entry.source)))
        elif style == 'short':
            text = []
            for entry in traceback:
                text.append('%s line %d' % (entry.path, entry.lineno))
                text.append('  %s' % (entry.source.strip(),))
            self.add_rest(LiteralBlock('\n'.join(text)))
        self.add_rest(Title(excinfo.typename, belowchar='+'))
        self.add_rest(LiteralBlock(excinfo.value))

    def prepare_source(self, relline, source):
        text = []
        for num, line in enumerate(source.split('\n')):
            if num == relline:
                text.append('>>> %s' % (line,))
            else:
                text.append('    %s' % (line,))
        return '\n'.join(text)

    def add_rest(self, item):
        self.rest.add(item)
        self.out.write('%s\n\n' % (item.text(),))

    def get_path_from_item(self, item):
        lns = item.listnames()[1:]
        for i, ln in enumerate(lns):
            if i > 0 and ln != '()':
                lns[i] = '/%s' % (ln,)
        itempath = ''.join(lns)
        return itempath

class AbstractLinkWriter(object):
    def get_link(self, base, path):
        pass

class NoLinkWriter(AbstractLinkWriter):
    def get_link(self, base, path):
        return ''

class LinkWriter(AbstractLinkWriter):
    def __init__(self, baseurl):
        self.baseurl = baseurl

    def get_link(self, base, path):
        relpath = path.relto(base)
        return self.baseurl + relpath

class RelLinkWriter(AbstractLinkWriter):
    def get_link(self, base, path):
        return path.relto(base)

