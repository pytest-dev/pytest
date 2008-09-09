import py

def check(mod):
    try:
        import pypy
        from pypy.translator.js.modules import dom
        from pypy.translator.js.tester import schedule_callbacks
        dom.Window # check whether dom was properly imported or is just a 
                   # leftover in sys.modules
    except (ImportError, AttributeError):
        py.test.skip('PyPy not found')
    mod.dom = dom
    mod.schedule_callbacks = schedule_callbacks

    from py.__.test.report import webjs
    from py.__.test.report.web import exported_methods
    mod.webjs = webjs
    mod.exported_methods = exported_methods
    mod.here = py.magic.autopath().dirpath()

def setup_module(mod):
    check(mod)

    # load HTML into window object
    html = here.join('../webdata/index.html').read()
    mod.html = html
    from pypy.translator.js.modules import dom
    mod.dom = dom
    dom.window = dom.Window(html)
    dom.document = dom.window.document
    from py.__.test.report import webjs
    from py.__.test.report.web import exported_methods
    mod.webjs = webjs
    mod.exported_methods = exported_methods

def setup_function(f):
    dom.window = dom.Window(html)
    dom.document = dom.window.document

def test_html_loaded():
    body = dom.window.document.getElementsByTagName('body')[0]
    assert len(body.childNodes) > 0
    assert str(body.childNodes[1].nodeName) == 'A'

def test_set_msgbox():
    py.test.skip("not implemented in genjs")
    msgbox = dom.window.document.getElementById('messagebox')
    assert len(msgbox.childNodes) == 0
    webjs.set_msgbox('foo', 'bar')
    assert len(msgbox.childNodes) == 1
    assert msgbox.childNodes[0].nodeName == 'PRE'
    assert msgbox.childNodes[0].childNodes[0].nodeValue == 'foo\nbar'

def test_show_info():
    info = dom.window.document.getElementById('info')
    info.style.visibility = 'hidden'
    info.innerHTML = ''
    webjs.show_info('foobar')
    content = info.innerHTML
    assert content == 'foobar'
    bgcolor = info.style.backgroundColor
    assert bgcolor == 'beige'

def test_hide_info():
    info = dom.window.document.getElementById('info')
    info.style.visibility = 'visible'
    webjs.hide_info()
    assert info.style.visibility == 'hidden'

def test_process():
    main_t = dom.window.document.getElementById('main_table')
    assert len(main_t.getElementsByTagName('tr')) == 0
    assert not webjs.process({})

    msg = {'type': 'ItemStart',
           'itemtype': 'Module',
           'itemname': 'foo.py',
           'fullitemname': 'modules/foo.py',
           'length': 10,
           }
    assert webjs.process(msg)
    trs = main_t.getElementsByTagName('tr')
    assert len(trs) == 1
    tr = trs[0]
    assert len(tr.childNodes) == 2
    assert tr.childNodes[0].nodeName == 'TD'
    assert tr.childNodes[0].innerHTML == 'foo.py[0/10]'
    assert tr.childNodes[1].nodeName == 'TD'
    assert tr.childNodes[1].childNodes[0].nodeName == 'TABLE'
    assert len(tr.childNodes[1].getElementsByTagName('tr')) == 0

def test_process_two():
    main_t = dom.window.document.getElementById('main_table')
    msg = {'type': 'ItemStart',
           'itemtype': 'Module',
           'itemname': 'foo.py',
           'fullitemname': 'modules/foo.py',
           'length': 10,
           }
    webjs.process(msg)
    msg = {'type': 'ItemFinish',
           'fullmodulename': 'modules/foo.py',
           'passed' : 'True',
           'fullitemname' : 'modules/foo.py/test_item',
           'hostkey': None,
           }
    webjs.process(msg)
    trs = main_t.getElementsByTagName('tr')
    tds = trs[0].getElementsByTagName('td')
    # two cells in the row, one in the table inside one of the cells
    assert len(tds) == 3
    html = tds[0].innerHTML
    assert html == 'foo.py[1/10]'
    assert tds[2].innerHTML == '.'

def test_signal():
    main_t = dom.window.document.getElementById('main_table')
    msg = {'type': 'ItemStart',
           'itemtype': 'Module',
           'itemname': 'foo.py',
           'fullitemname': 'modules/foo.py',
           'length': 10,
           }
    webjs.process(msg)
    msg = {'type': 'ItemFinish',
           'fullmodulename': 'modules/foo.py',
           'passed' : 'False',
           'fullitemname' : 'modules/foo.py/test_item',
           'hostkey': None,
           'signal': '10',
           'skipped': 'False',
           }
    exported_methods.fail_reasons['modules/foo.py/test_item'] = 'Received signal 10'
    exported_methods.stdout['modules/foo.py/test_item'] = ''
    exported_methods.stderr['modules/foo.py/test_item'] = ''
    webjs.process(msg)
    schedule_callbacks(exported_methods)
    # ouch
    assert dom.document.getElementById('modules/foo.py').childNodes[0].\
        childNodes[0].childNodes[0].childNodes[0].nodeValue == 'F'

# XXX: Write down test for full run

