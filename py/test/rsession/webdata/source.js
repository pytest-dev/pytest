// starts hand written code
MALLOC_ZERO_FILLED = 0

try {
    log;
    print = log;
} catch(e) {
}

Function.prototype.method = function (name, func) {
    this.prototype[name] = func;
    return this;
};

function inherits(child, parent) {
    child.parent = parent;
    for (i in parent.prototype) {
        if (!child.prototype[i]) {
            child.prototype[i] = parent.prototype[i];
        }
    }
}

function isinstanceof(self, what) {
    t = self.constructor;
    while ( t ) {
        if (t == what) {
            return (true);
        }
        t = t.parent;
    }
    return (false);
}

/*function delitem(fn, l, i) {
    for(j = i; j < l.length-1; ++j) {
        l[j] = l[j+1];
    }
    l.length--;
}*/

function strcmp(s1, s2) {
    if ( s1 < s2 ) {
        return ( -1 );
    } else if ( s1 == s2 ) {
        return ( 0 );
    }
    return (1);
}

function startswith(s1, s2) {
    if (s1.length < s2.length) {
        return(false);
    }
    for (i = 0; i < s2.length; ++i){
        if (s1.charAt(i) != s2.charAt(i)) {
            return(false);
        }
    }
    return(true);
}

function endswith(s1, s2) {
    if (s2.length > s1.length) {
        return(false);
    }
    for (i = s1.length-s2.length; i < s1.length; ++i) {
        if (s1.charAt(i) != s2.charAt(i - s1.length + s2.length)) {
            return(false);
        }
    }
    return(true);
}

function splitchr(s, ch) {
    var i, lst, next;
    lst = [];
    next = "";
    for (i = 0; i<s.length; ++i) {
        if (s.charAt(i) == ch) {
            lst.length += 1;
            lst[lst.length-1] = next;
            next = "";
        } else {
            next += s.charAt(i);
        }
    }
    lst.length += 1;
    lst[lst.length-1] = next;
    return (lst);
}

function DictIter() {
}

DictIter.prototype.ll_go_next = function () {
    var ret = this.l.length != 0;
    this.current_key = this.l.pop();
    return ret;
}

DictIter.prototype.ll_current_key = function () {
    return this.current_key;
}

function dict_items_iterator(d) {
    var d2 = new DictIter();
    var l = [];
    for (var i in d) {
        l.length += 1;
        l[l.length-1] = i;
    }
    d2.l = l;
    d2.current_key = undefined;
    return d2;
}

function get_dict_len(d) {
    var count;
    count = 0;
    for (var i in d) {
        count += 1;
    }
    return (count);
}

function StringBuilder() {
    this.l = [];
}

StringBuilder.prototype.ll_append_char = function(s) {
    this.l.length += 1;
    this.l[this.l.length - 1] = s;
}

StringBuilder.prototype.ll_append = function(s) {
    this.l.push(s);
}

StringBuilder.prototype.ll_allocate = function(t) {
}

StringBuilder.prototype.ll_build = function() {
    var s;
    s = "";
    for (i in this.l) {
        s += this.l[i];
    }
    return (s);
}

function time() {
    var d;
    d = new Date();
    return d/1000;
}

var main_clock_stuff;

function clock() {
    if (main_clock_stuff) {
        return (new Date() - main_clock_stuff)/1000;
    } else {
        main_clock_stuff = new Date();
        return 0;
    }
}

function substring(s, l, c) {
    return (s.substring(l, l+c));
}

function clear_dict(d) {
    for (var elem in d) {
        delete(d[elem]);
    }
}
// ends hand written code
function ExportedMethods () {
}


function callback_0 (x, cb) {
   var d;
   if (x.readyState == 4) {
      if (x.responseText) {
         eval ( "d = " + x.responseText );
         cb(d);
      } else {
         cb({});
      }
   }
}

ExportedMethods.prototype.show_all_statuses = function ( sessid,callback ) {
    var data,str;
    var x = new XMLHttpRequest();
    data = {'sessid':sessid};
    str = ""
    for(i in data) {
        if (data[i]) {
            if (str.length == 0) {
                str += "?";
            } else {
                str += "&";
            }
            str += escape(i) + "=" + escape(data[i].toString());
        }
    }
    //logDebug('show_all_statuses'+str);
    x.open("GET", 'show_all_statuses' + str, true);
    x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    x.onreadystatechange = function () { callback_0(x, callback) };
    //x.setRequestHeader("Connection", "close");
    //x.send(data);
    x.send(null);
}

function callback_1 (x, cb) {
   var d;
   if (x.readyState == 4) {
      if (x.responseText) {
         eval ( "d = " + x.responseText );
         cb(d);
      } else {
         cb({});
      }
   }
}

ExportedMethods.prototype.show_skip = function ( item_name,callback ) {
    var data,str;
    var x = new XMLHttpRequest();
    data = {'item_name':item_name};
    str = ""
    for(i in data) {
        if (data[i]) {
            if (str.length == 0) {
                str += "?";
            } else {
                str += "&";
            }
            str += escape(i) + "=" + escape(data[i].toString());
        }
    }
    //logDebug('show_skip'+str);
    x.open("GET", 'show_skip' + str, true);
    x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    x.onreadystatechange = function () { callback_1(x, callback) };
    //x.setRequestHeader("Connection", "close");
    //x.send(data);
    x.send(null);
}

function callback_2 (x, cb) {
   var d;
   if (x.readyState == 4) {
      if (x.responseText) {
         eval ( "d = " + x.responseText );
         cb(d);
      } else {
         cb({});
      }
   }
}

ExportedMethods.prototype.show_sessid = function ( callback ) {
    var data,str;
    var x = new XMLHttpRequest();
    data = {};
    str = ""
    for(i in data) {
        if (data[i]) {
            if (str.length == 0) {
                str += "?";
            } else {
                str += "&";
            }
            str += escape(i) + "=" + escape(data[i].toString());
        }
    }
    //logDebug('show_sessid'+str);
    x.open("GET", 'show_sessid' + str, true);
    x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    x.onreadystatechange = function () { callback_2(x, callback) };
    //x.setRequestHeader("Connection", "close");
    //x.send(data);
    x.send(null);
}

function callback_3 (x, cb) {
   var d;
   if (x.readyState == 4) {
      if (x.responseText) {
         eval ( "d = " + x.responseText );
         cb(d);
      } else {
         cb({});
      }
   }
}

ExportedMethods.prototype.show_hosts = function ( callback ) {
    var data,str;
    var x = new XMLHttpRequest();
    data = {};
    str = ""
    for(i in data) {
        if (data[i]) {
            if (str.length == 0) {
                str += "?";
            } else {
                str += "&";
            }
            str += escape(i) + "=" + escape(data[i].toString());
        }
    }
    //logDebug('show_hosts'+str);
    x.open("GET", 'show_hosts' + str, true);
    x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    x.onreadystatechange = function () { callback_3(x, callback) };
    //x.setRequestHeader("Connection", "close");
    //x.send(data);
    x.send(null);
}

function callback_4 (x, cb) {
   var d;
   if (x.readyState == 4) {
      if (x.responseText) {
         eval ( "d = " + x.responseText );
         cb(d);
      } else {
         cb({});
      }
   }
}

ExportedMethods.prototype.show_fail = function ( item_name,callback ) {
    var data,str;
    var x = new XMLHttpRequest();
    data = {'item_name':item_name};
    str = ""
    for(i in data) {
        if (data[i]) {
            if (str.length == 0) {
                str += "?";
            } else {
                str += "&";
            }
            str += escape(i) + "=" + escape(data[i].toString());
        }
    }
    //logDebug('show_fail'+str);
    x.open("GET", 'show_fail' + str, true);
    x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    x.onreadystatechange = function () { callback_4(x, callback) };
    //x.setRequestHeader("Connection", "close");
    //x.send(data);
    x.send(null);
}
function some_strange_function_which_will_never_be_called () {
    var v2,v4,v6,v9;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            main (  );
            v2 = __consts_0.const_str;
            show_skip ( v2 );
            v4 = __consts_0.const_str;
            show_traceback ( v4 );
            v6 = __consts_0.const_str;
            show_info ( v6 );
            hide_info (  );
            v9 = __consts_0.const_str;
            show_host ( v9 );
            hide_host (  );
            hide_messagebox (  );
            opt_scroll (  );
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function hide_host () {
    var v101,v102,elem_5,v103,v104,v105,v106,v107,elem_6,v110,v111,v112;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v101 = __consts_0.Document;
            v102 = v101.getElementById(__consts_0.const_str__2);
            elem_5 = v102;
            block = 1;
            break;
            case 1:
            v103 = elem_5.childNodes;
            v104 = ll_len__List_ExternalType_ ( v103 );
            v105 = !!v104;
            v106 = elem_5;
            if (v105 == false)
            {
                block = 2;
                break;
            }
            elem_6 = elem_5;
            block = 4;
            break;
            case 2:
            v107 = v106.style;
            v107.visibility = __consts_0.const_str__3;
            __consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__5;
            block = 3;
            break;
            case 4:
            v110 = elem_6;
            v111 = elem_6.childNodes;
            v112 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v111,0 );
            v110.removeChild(v112);
            elem_5 = elem_6;
            block = 1;
            break;
            case 3:
            return ( undefined );
        }
    }
}

function main () {
    var v16,v17,v18,v19,v21,v22,v23;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = false;
            v16 = __consts_0.ExportedMethods;
            v17 = v16.show_hosts(host_init);
            v18 = __consts_0.ExportedMethods;
            v19 = v18.show_sessid(sessid_comeback);
            __consts_0.Document.onkeypress = key_pressed;
            v21 = __consts_0.Document;
            v22 = v21.getElementById(__consts_0.const_str__7);
            v23 = v22;
            v23.setAttribute(__consts_0.const_str__8,__consts_0.const_str__9);
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function hide_messagebox () {
    var v115,v116,mbox_0,v117,v118,mbox_1,v119,v120,v121;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v115 = __consts_0.Document;
            v116 = v115.getElementById(__consts_0.const_str__10);
            mbox_0 = v116;
            block = 1;
            break;
            case 1:
            v117 = mbox_0.childNodes;
            v118 = ll_list_is_true__List_ExternalType_ ( v117 );
            if (v118 == false)
            {
                block = 2;
                break;
            }
            mbox_1 = mbox_0;
            block = 3;
            break;
            case 3:
            v119 = mbox_1;
            v120 = mbox_1.childNodes;
            v121 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v120,0 );
            v119.removeChild(v121);
            mbox_0 = mbox_1;
            block = 1;
            break;
            case 2:
            return ( undefined );
        }
    }
}

function show_traceback (item_name_1) {
    var v29,v30,v31,v32,v33,v35,v38,v41,v44;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v29 = ll_dict_getitem__Dict_String__Record_item2__Str_String ( __consts_0.const_tuple,item_name_1 );
            v30 = v29.item0;
            v31 = v29.item1;
            v32 = v29.item2;
            v33 = new StringBuilder();
            v33.ll_append(__consts_0.const_str__12);
            v35 = ll_str__StringR_StringConst_String ( v30 );
            v33.ll_append(v35);
            v33.ll_append(__consts_0.const_str__13);
            v38 = ll_str__StringR_StringConst_String ( v31 );
            v33.ll_append(v38);
            v33.ll_append(__consts_0.const_str__14);
            v41 = ll_str__StringR_StringConst_String ( v32 );
            v33.ll_append(v41);
            v33.ll_append(__consts_0.const_str__15);
            v44 = v33.ll_build();
            set_msgbox ( item_name_1,v44 );
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__5;
    this.ohost = __consts_0.const_str__5;
    this.orsync_dots = 0;
    this.ofinished = false;
    this.ohost_dict = __consts_0.const_tuple__16;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__18;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals instance>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
function opt_scroll () {
    var v124,v125;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v124 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v125 = v124;
            if (v125 == false)
            {
                block = 1;
                break;
            }
            block = 3;
            break;
            case 1:
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 2;
            break;
            case 3:
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 2;
            break;
            case 2:
            return ( undefined );
        }
    }
}

function show_host (host_name_0) {
    var v70,v71,v72,v73,host_name_1,elem_0,v74,v75,v76,v77,host_name_2,tbody_0,elem_1,v78,v79,last_exc_value_0,host_name_3,tbody_1,elem_2,item_0,v80,v81,v82,v83,v84,v86,v88,host_name_4,tbody_2,elem_3,v90,v92,host_name_5,elem_4,v96,v97,v98;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v70 = __consts_0.Document;
            v71 = v70.getElementById(__consts_0.const_str__2);
            v72 = v71.childNodes;
            v73 = ll_list_is_true__List_ExternalType_ ( v72 );
            host_name_1 = host_name_0;
            elem_0 = v71;
            if (v73 == false)
            {
                block = 1;
                break;
            }
            host_name_5 = host_name_0;
            elem_4 = v71;
            block = 6;
            break;
            case 1:
            v74 = create_elem ( __consts_0.const_str__20 );
            v75 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v76 = ll_dict_getitem__Dict_String__List_String___String ( v75,host_name_1 );
            v77 = ll_listiter__Record_index__Signed__iterable_List_String_ ( v76 );
            host_name_2 = host_name_1;
            tbody_0 = v74;
            elem_1 = elem_0;
            v78 = v77;
            block = 2;
            break;
            case 2:
            try {
                v79 = ll_listnext__Record_index__Signed__iterable_0 ( v78 );
                host_name_3 = host_name_2;
                tbody_1 = tbody_0;
                elem_2 = elem_1;
                item_0 = v79;
                v80 = v78;
                block = 3;
                break;
            }
            catch (exc){
                if (isinstanceof(exc, exceptions_StopIteration))
                {
                    host_name_4 = host_name_2;
                    tbody_2 = tbody_0;
                    elem_3 = elem_1;
                    block = 4;
                    break;
                }
                throw(exc);
            }
            case 3:
            v81 = create_elem ( __consts_0.const_str__21 );
            v82 = create_elem ( __consts_0.const_str__22 );
            v83 = v82;
            v84 = create_text_elem ( item_0 );
            v83.appendChild(v84);
            v86 = v81;
            v86.appendChild(v82);
            v88 = tbody_1;
            v88.appendChild(v81);
            host_name_2 = host_name_3;
            tbody_0 = tbody_1;
            elem_1 = elem_2;
            v78 = v80;
            block = 2;
            break;
            case 4:
            v90 = elem_3;
            v90.appendChild(tbody_2);
            v92 = elem_3.style;
            v92.visibility = __consts_0.const_str__23;
            __consts_0.py____test_rsession_webjs_Globals.ohost = host_name_4;
            setTimeout ( 'reshow_host()',100 );
            block = 5;
            break;
            case 6:
            v96 = elem_4;
            v97 = elem_4.childNodes;
            v98 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v97,0 );
            v96.removeChild(v98);
            host_name_1 = host_name_5;
            elem_0 = elem_4;
            block = 1;
            break;
            case 5:
            return ( undefined );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_String_ (lst_0) {
    var v261,v262;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v262 = new Object();
            v262.iterable = lst_0;
            v262.index = 0;
            v261 = v262;
            block = 1;
            break;
            case 1:
            return ( v261 );
        }
    }
}

function exceptions_Exception () {
}

exceptions_Exception.prototype.toString = function (){
    return ( '<exceptions_Exception instance>' );
}

inherits(exceptions_Exception,Object);
function create_elem (s_1) {
    var v248,v249,v250;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v249 = __consts_0.Document;
            v250 = v249.createElement(s_1);
            v248 = v250;
            block = 1;
            break;
            case 1:
            return ( v248 );
        }
    }
}

function ll_listnext__Record_index__Signed__iterable_0 (iter_0) {
    var v265,v266,v267,v268,v269,v270,v271,iter_1,index_3,l_4,v272,v274,v275,v276,v277,v278,etype_2,evalue_2;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v266 = iter_0.iterable;
            v267 = iter_0.index;
            v268 = v266;
            v269 = v268.length;
            v270 = (v267>=v269);
            v271 = v270;
            iter_1 = iter_0;
            index_3 = v267;
            l_4 = v266;
            if (v271 == false)
            {
                block = 1;
                break;
            }
            block = 3;
            break;
            case 1:
            v272 = (index_3+1);
            iter_1.index = v272;
            v274 = l_4;
            v275 = v274[index_3];
            v265 = v275;
            block = 2;
            break;
            case 3:
            v276 = __consts_0.exceptions_StopIteration;
            v277 = v276.meta;
            v278 = v276;
            etype_2 = v277;
            evalue_2 = v278;
            block = 4;
            break;
            case 4:
            throw(evalue_2);
            case 2:
            return ( v265 );
        }
    }
}

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed (l_1,index_0) {
    var v131,v132,l_2,index_1,v134,v135,v136,index_2,v138,v139,v140;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v132 = (index_0>=0);
            undefined;
            l_2 = l_1;
            index_1 = index_0;
            block = 1;
            break;
            case 1:
            v134 = l_2;
            v135 = v134.length;
            v136 = (index_1<v135);
            undefined;
            index_2 = index_1;
            v138 = l_2;
            block = 2;
            break;
            case 2:
            v139 = v138;
            v140 = v139[index_2];
            v131 = v140;
            block = 3;
            break;
            case 3:
            return ( v131 );
        }
    }
}

function set_msgbox (item_name_2,data_3) {
    var v228,item_name_3,data_4,msgbox_0,v229,v230,v231,item_name_4,data_5,msgbox_1,v232,v233,v234,v235,v236,v238,v240,v241,item_name_5,data_6,msgbox_2,v244,v245,v246;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v228 = get_elem ( __consts_0.const_str__10 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v228;
            block = 1;
            break;
            case 1:
            v229 = msgbox_0.childNodes;
            v230 = ll_len__List_ExternalType_ ( v229 );
            v231 = !!v230;
            item_name_4 = item_name_3;
            data_5 = data_4;
            msgbox_1 = msgbox_0;
            if (v231 == false)
            {
                block = 2;
                break;
            }
            item_name_5 = item_name_3;
            data_6 = data_4;
            msgbox_2 = msgbox_0;
            block = 4;
            break;
            case 2:
            v232 = create_elem ( __consts_0.const_str__25 );
            v233 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__15 );
            v234 = ll_strconcat__String_String ( v233,data_5 );
            v235 = create_text_elem ( v234 );
            v236 = v232;
            v236.appendChild(v235);
            v238 = msgbox_1;
            v238.appendChild(v232);
            v240 = __consts_0.Window.location;
            v241 = v240;
            v241.assign(__consts_0.const_str__27);
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 4:
            v244 = msgbox_2;
            v245 = msgbox_2.childNodes;
            v246 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v245,0 );
            v244.removeChild(v246);
            item_name_3 = item_name_5;
            data_4 = data_6;
            msgbox_0 = msgbox_2;
            block = 1;
            break;
            case 3:
            return ( undefined );
        }
    }
}

function ll_list_is_true__List_ExternalType_ (l_3) {
    var v209,v210,v211,v212,v213,v214,v215;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v210 = !!l_3;
            v211 = v210;
            v209 = v210;
            if (v211 == false)
            {
                block = 1;
                break;
            }
            v212 = l_3;
            block = 2;
            break;
            case 2:
            v213 = v212;
            v214 = v213.length;
            v215 = (v214!=0);
            v209 = v215;
            block = 1;
            break;
            case 1:
            return ( v209 );
        }
    }
}

function reshow_host () {
    var v283,v284,v285,v286;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v283 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v284 = ll_streq__String_String ( v283,__consts_0.const_str__5 );
            v285 = v284;
            if (v285 == false)
            {
                block = 1;
                break;
            }
            block = 2;
            break;
            case 1:
            v286 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v286 );
            block = 2;
            break;
            case 2:
            return ( undefined );
        }
    }
}

function show_skip (item_name_0) {
    var v26;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v26 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__28,item_name_0 );
            set_msgbox ( item_name_0,v26 );
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function show_info (data_0) {
    var v47,v48,v49,data_1,info_0,v51,v52,v53,info_1,v54,v55,v56,v58,data_2,info_2,v60,v61,v62;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v47 = __consts_0.Document;
            v48 = v47.getElementById(__consts_0.const_str__29);
            v49 = v48.style;
            v49.visibility = __consts_0.const_str__23;
            data_1 = data_0;
            info_0 = v48;
            block = 1;
            break;
            case 1:
            v51 = info_0.childNodes;
            v52 = ll_len__List_ExternalType_ ( v51 );
            v53 = !!v52;
            info_1 = info_0;
            v54 = data_1;
            if (v53 == false)
            {
                block = 2;
                break;
            }
            data_2 = data_1;
            info_2 = info_0;
            block = 4;
            break;
            case 2:
            v55 = create_text_elem ( v54 );
            v56 = info_1;
            v56.appendChild(v55);
            v58 = info_1.style;
            v58.backgroundColor = __consts_0.const_str__30;
            block = 3;
            break;
            case 4:
            v60 = info_2;
            v61 = info_2.childNodes;
            v62 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v61,0 );
            v60.removeChild(v62);
            data_1 = data_2;
            info_0 = info_2;
            block = 1;
            break;
            case 3:
            return ( undefined );
        }
    }
}

function create_text_elem (txt_0) {
    var v279,v280,v281;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v280 = __consts_0.Document;
            v281 = v280.createTextNode(txt_0);
            v279 = v281;
            block = 1;
            break;
            case 1:
            return ( v279 );
        }
    }
}

function ll_strconcat__String_String (obj_0,arg0_0) {
    var v291,v292,v293;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v292 = obj_0;
            v293 = (v292+arg0_0);
            v291 = v293;
            block = 1;
            break;
            case 1:
            return ( v291 );
        }
    }
}

function host_init (host_dict_0) {
    var v142,v143,v144,v145,v146,host_dict_1,tbody_3,v147,v148,last_exc_value_1,host_dict_2,tbody_4,host_0,v149,v150,v151,v153,v154,v156,v157,v158,v161,v163,v164,v166,v169,v171,host_dict_3,v177,v179,v180,v181,v182,v183,last_exc_value_2,key_0,v184,v185,v187;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v142 = __consts_0.Document;
            v143 = v142.getElementById(__consts_0.const_str__31);
            v144 = host_dict_0;
            v145 = ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst ( v144 );
            v146 = ll_listiter__Record_index__Signed__iterable_List_String_ ( v145 );
            host_dict_1 = host_dict_0;
            tbody_3 = v143;
            v147 = v146;
            block = 1;
            break;
            case 1:
            try {
                v148 = ll_listnext__Record_index__Signed__iterable_0 ( v147 );
                host_dict_2 = host_dict_1;
                tbody_4 = tbody_3;
                host_0 = v148;
                v149 = v147;
                block = 2;
                break;
            }
            catch (exc){
                if (isinstanceof(exc, exceptions_StopIteration))
                {
                    host_dict_3 = host_dict_1;
                    block = 3;
                    break;
                }
                throw(exc);
            }
            case 2:
            v150 = create_elem ( __consts_0.const_str__21 );
            v151 = tbody_4;
            v151.appendChild(v150);
            v153 = create_elem ( __consts_0.const_str__22 );
            v154 = v153.style;
            v154.background = __consts_0.const_str__32;
            v156 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v157 = create_text_elem ( v156 );
            v158 = v153;
            v158.appendChild(v157);
            v153.id = host_0;
            v161 = v150;
            v161.appendChild(v153);
            v163 = v153;
            v164 = new StringBuilder();
            v164.ll_append(__consts_0.const_str__33);
            v166 = ll_str__StringR_StringConst_String ( host_0 );
            v164.ll_append(v166);
            v164.ll_append(__consts_0.const_str__34);
            v169 = v164.ll_build();
            v163.setAttribute(__consts_0.const_str__35,v169);
            v171 = v153;
            v171.setAttribute(__consts_0.const_str__36,__consts_0.const_str__37);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
            setTimeout ( 'update_rsync()',1000 );
            host_dict_1 = host_dict_2;
            tbody_3 = tbody_4;
            v147 = v149;
            block = 1;
            break;
            case 3:
            __consts_0.py____test_rsession_webjs_Globals.ohost_dict = host_dict_3;
            v177 = ll_newdict__Dict_String__List_String__LlT (  );
            __consts_0.py____test_rsession_webjs_Globals.ohost_pending = v177;
            v179 = host_dict_3;
            v180 = ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst ( v179 );
            v181 = ll_listiter__Record_index__Signed__iterable_List_String_ ( v180 );
            v182 = v181;
            block = 4;
            break;
            case 4:
            try {
                v183 = ll_listnext__Record_index__Signed__iterable_0 ( v182 );
                key_0 = v183;
                v184 = v182;
                block = 5;
                break;
            }
            catch (exc){
                if (isinstanceof(exc, exceptions_StopIteration))
                {
                    block = 6;
                    break;
                }
                throw(exc);
            }
            case 5:
            v185 = new Array();
            v185.length = 0;
            v187 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v187[key_0]=v185;
            v182 = v184;
            block = 4;
            break;
            case 6:
            return ( undefined );
        }
    }
}

function ll_dict_getitem__Dict_String__String__String (d_2,key_6) {
    var v304,v305,v306,v307,v308,v309,v310,etype_3,evalue_3,key_7,v311,v312,v313;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v305 = d_2;
            v306 = (v305[key_6]!=undefined);
            v307 = v306;
            if (v307 == false)
            {
                block = 1;
                break;
            }
            key_7 = key_6;
            v311 = d_2;
            block = 3;
            break;
            case 1:
            v308 = __consts_0.exceptions_KeyError;
            v309 = v308.meta;
            v310 = v308;
            etype_3 = v309;
            evalue_3 = v310;
            block = 2;
            break;
            case 3:
            v312 = v311;
            v313 = v312[key_7];
            v304 = v313;
            block = 4;
            break;
            case 2:
            throw(evalue_3);
            case 4:
            return ( v304 );
        }
    }
}

function ll_newdict__Dict_String__List_String__LlT () {
    var v370,v371;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v371 = new Object();
            v370 = v371;
            block = 1;
            break;
            case 1:
            return ( v370 );
        }
    }
}

function ll_len__List_ExternalType_ (l_0) {
    var v128,v129,v130;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v129 = l_0;
            v130 = v129.length;
            v128 = v130;
            block = 1;
            break;
            case 1:
            return ( v128 );
        }
    }
}

function ll_dict_getitem__Dict_String__List_String___String (d_1,key_4) {
    var v251,v252,v253,v254,v255,v256,v257,etype_1,evalue_1,key_5,v258,v259,v260;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v252 = d_1;
            v253 = (v252[key_4]!=undefined);
            v254 = v253;
            if (v254 == false)
            {
                block = 1;
                break;
            }
            key_5 = key_4;
            v258 = d_1;
            block = 3;
            break;
            case 1:
            v255 = __consts_0.exceptions_KeyError;
            v256 = v255.meta;
            v257 = v255;
            etype_1 = v256;
            evalue_1 = v257;
            block = 2;
            break;
            case 3:
            v259 = v258;
            v260 = v259[key_5];
            v251 = v260;
            block = 4;
            break;
            case 2:
            throw(evalue_1);
            case 4:
            return ( v251 );
        }
    }
}

function sessid_comeback (id_0) {
    var v191,v192;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.osessid = id_0;
            v191 = __consts_0.ExportedMethods;
            v192 = v191.show_all_statuses(id_0,comeback);
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function update_rsync () {
    var v337,v338,v339,v340,v341,v342,v343,v344,elem_7,v345,v346,v347,v348,v349,v351,v352,v353,elem_8,v354,v355,v357,v360,v361,v362,text_0,elem_9,v366,v367,v368;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v337 = __consts_0.py____test_rsession_webjs_Globals.ofinished;
            v338 = v337;
            if (v338 == false)
            {
                block = 1;
                break;
            }
            block = 4;
            break;
            case 1:
            v339 = __consts_0.Document;
            v340 = v339.getElementById(__consts_0.const_str__39);
            v341 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v342 = v341;
            v343 = (v342==1);
            v344 = v343;
            elem_7 = v340;
            if (v344 == false)
            {
                block = 2;
                break;
            }
            v366 = v340;
            block = 6;
            break;
            case 2:
            v345 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v346 = ll_char_mul__Char_Signed ( '.',v345 );
            v347 = ll_strconcat__String_String ( __consts_0.const_str__40,v346 );
            v348 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v349 = (v348+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v349;
            v351 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v352 = (v351>5);
            v353 = v352;
            elem_8 = elem_7;
            v354 = v347;
            if (v353 == false)
            {
                block = 3;
                break;
            }
            text_0 = v347;
            elem_9 = elem_7;
            block = 5;
            break;
            case 3:
            v355 = new StringBuilder();
            v355.ll_append(__consts_0.const_str__41);
            v357 = ll_str__StringR_StringConst_String ( v354 );
            v355.ll_append(v357);
            v355.ll_append(__consts_0.const_str__42);
            v360 = v355.ll_build();
            v361 = elem_8.childNodes;
            v362 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v361,0 );
            v362.nodeValue = v360;
            setTimeout ( 'update_rsync()',1000 );
            block = 4;
            break;
            case 5:
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            elem_8 = elem_9;
            v354 = text_0;
            block = 3;
            break;
            case 6:
            v367 = v366.childNodes;
            v368 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v367,0 );
            v368.nodeValue = __consts_0.const_str__39;
            block = 4;
            break;
            case 4:
            return ( undefined );
        }
    }
}

function comeback (msglist_0) {
    var v373,v374,v375,msglist_1,v376,v377,v378,v379,msglist_2,v380,v381,last_exc_value_3,msglist_3,v382,v383,v384,v385,msglist_4,v386,v389,v390,v391,last_exc_value_4,v392,v393,v394,v395,v396,v397,v398;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v373 = ll_len__List_Dict_String__String__ ( msglist_0 );
            v374 = (v373==0);
            v375 = v374;
            msglist_1 = msglist_0;
            if (v375 == false)
            {
                block = 1;
                break;
            }
            block = 4;
            break;
            case 1:
            v376 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v377 = 0;
            v378 = ll_listslice_startonly__List_Dict_String__String__LlT_List_Dict_String__String___Signed ( v376,v377 );
            v379 = ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ ( v378 );
            msglist_2 = msglist_1;
            v380 = v379;
            block = 2;
            break;
            case 2:
            try {
                v381 = ll_listnext__Record_index__Signed__iterable ( v380 );
                msglist_3 = msglist_2;
                v382 = v380;
                v383 = v381;
                block = 3;
                break;
            }
            catch (exc){
                if (isinstanceof(exc, exceptions_StopIteration))
                {
                    msglist_4 = msglist_2;
                    block = 5;
                    break;
                }
                throw(exc);
            }
            case 3:
            v384 = process ( v383 );
            v385 = v384;
            if (v385 == false)
            {
                block = 4;
                break;
            }
            msglist_2 = msglist_3;
            v380 = v382;
            block = 2;
            break;
            case 5:
            v386 = new Array();
            v386.length = 0;
            __consts_0.py____test_rsession_webjs_Globals.opending = v386;
            v389 = ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ ( msglist_4 );
            v390 = v389;
            block = 6;
            break;
            case 6:
            try {
                v391 = ll_listnext__Record_index__Signed__iterable ( v390 );
                v392 = v390;
                v393 = v391;
                block = 7;
                break;
            }
            catch (exc){
                if (isinstanceof(exc, exceptions_StopIteration))
                {
                    block = 8;
                    break;
                }
                throw(exc);
            }
            case 7:
            v394 = process ( v393 );
            v395 = v394;
            if (v395 == false)
            {
                block = 4;
                break;
            }
            v390 = v392;
            block = 6;
            break;
            case 8:
            v396 = __consts_0.ExportedMethods;
            v397 = __consts_0.py____test_rsession_webjs_Globals.osessid;
            v398 = v396.show_all_statuses(v397,comeback);
            block = 4;
            break;
            case 4:
            return ( undefined );
        }
    }
}

function hide_info () {
    var v65,v66,v67;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v65 = __consts_0.Document;
            v66 = v65.getElementById(__consts_0.const_str__29);
            v67 = v66.style;
            v67.visibility = __consts_0.const_str__3;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_streq__String_String (s1_0,s2_0) {
    var v294,v295,v296,v297,s2_1,v298,v299,v300,v301,v302,v303;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v295 = !!s1_0;
            v296 = !v295;
            v297 = v296;
            s2_1 = s2_0;
            v298 = s1_0;
            if (v297 == false)
            {
                block = 1;
                break;
            }
            v301 = s2_0;
            block = 3;
            break;
            case 1:
            v299 = v298;
            v300 = (v299==s2_1);
            v294 = v300;
            block = 2;
            break;
            case 3:
            v302 = !!v301;
            v303 = !v302;
            v294 = v303;
            block = 2;
            break;
            case 2:
            return ( v294 );
        }
    }
}

function ll_dict_getitem__Dict_String__Record_item2__Str_String (d_0,key_2) {
    var v216,v217,v218,v219,v220,v221,v222,etype_0,evalue_0,key_3,v223,v224,v225;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v217 = d_0;
            v218 = (v217[key_2]!=undefined);
            v219 = v218;
            if (v219 == false)
            {
                block = 1;
                break;
            }
            key_3 = key_2;
            v223 = d_0;
            block = 3;
            break;
            case 1:
            v220 = __consts_0.exceptions_KeyError;
            v221 = v220.meta;
            v222 = v220;
            etype_0 = v221;
            evalue_0 = v222;
            block = 2;
            break;
            case 3:
            v224 = v223;
            v225 = v224[key_3];
            v216 = v225;
            block = 4;
            break;
            case 2:
            throw(evalue_0);
            case 4:
            return ( v216 );
        }
    }
}

function py____test_rsession_webjs_Options () {
    this.oscroll = false;
}

py____test_rsession_webjs_Options.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Options instance>' );
}

inherits(py____test_rsession_webjs_Options,Object);
function key_pressed (key_1) {
    var v194,v195,v196,v197,v198,v199,v200,v201,v202,v205,v206;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v194 = key_1.charCode;
            v195 = (v194==115);
            v196 = v195;
            if (v196 == false)
            {
                block = 1;
                break;
            }
            block = 2;
            break;
            case 2:
            v197 = __consts_0.Document;
            v198 = v197.getElementById(__consts_0.const_str__7);
            v199 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v200 = v199;
            v201 = v198;
            if (v200 == false)
            {
                block = 3;
                break;
            }
            v205 = v198;
            block = 4;
            break;
            case 3:
            v202 = v201;
            v202.setAttribute(__consts_0.const_str__8,__consts_0.const_str__43);
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 1;
            break;
            case 4:
            v206 = v205;
            v206.removeAttribute(__consts_0.const_str__8);
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function exceptions_StandardError () {
}

exceptions_StandardError.prototype.toString = function (){
    return ( '<exceptions_StandardError instance>' );
}

inherits(exceptions_StandardError,exceptions_Exception);
function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions_StopIteration instance>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
function ll_str__StringR_StringConst_String (s_0) {
    var v226;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v226 = s_0;
            block = 1;
            break;
            case 1:
            return ( v226 );
        }
    }
}

function ll_listnext__Record_index__Signed__iterable (iter_2) {
    var v436,v437,v438,v439,v440,v441,v442,iter_3,index_4,l_8,v443,v445,v446,v447,v448,v449,etype_5,evalue_5;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v437 = iter_2.iterable;
            v438 = iter_2.index;
            v439 = v437;
            v440 = v439.length;
            v441 = (v438>=v440);
            v442 = v441;
            iter_3 = iter_2;
            index_4 = v438;
            l_8 = v437;
            if (v442 == false)
            {
                block = 1;
                break;
            }
            block = 3;
            break;
            case 1:
            v443 = (index_4+1);
            iter_3.index = v443;
            v445 = l_8;
            v446 = v445[index_4];
            v436 = v446;
            block = 2;
            break;
            case 3:
            v447 = __consts_0.exceptions_StopIteration;
            v448 = v447.meta;
            v449 = v447;
            etype_5 = v448;
            evalue_5 = v449;
            block = 4;
            break;
            case 4:
            throw(evalue_5);
            case 2:
            return ( v436 );
        }
    }
}

function exceptions_LookupError () {
}

exceptions_LookupError.prototype.toString = function (){
    return ( '<exceptions_LookupError instance>' );
}

inherits(exceptions_LookupError,exceptions_StandardError);
function exceptions_KeyError () {
}

exceptions_KeyError.prototype.toString = function (){
    return ( '<exceptions_KeyError instance>' );
}

inherits(exceptions_KeyError,exceptions_LookupError);
function get_elem (el_0) {
    var v288,v289,v290;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v289 = __consts_0.Document;
            v290 = v289.getElementById(el_0);
            v288 = v290;
            block = 1;
            break;
            case 1:
            return ( v288 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ (lst_1) {
    var v432,v433;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v433 = new Object();
            v433.iterable = lst_1;
            v433.index = 0;
            v432 = v433;
            block = 1;
            break;
            case 1:
            return ( v432 );
        }
    }
}

function ll_char_mul__Char_Signed (ch_0,times_0) {
    var v399,v400,v401,ch_1,times_1,i_2,buf_0,v403,v404,v405,v406,v407,ch_2,times_2,i_3,buf_1,v408,v410;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v400 = new StringBuilder();
            v401 = v400;
            v401.ll_allocate(times_0);
            ch_1 = ch_0;
            times_1 = times_0;
            i_2 = 0;
            buf_0 = v400;
            block = 1;
            break;
            case 1:
            v403 = (i_2<times_1);
            v404 = v403;
            v405 = buf_0;
            if (v404 == false)
            {
                block = 2;
                break;
            }
            ch_2 = ch_1;
            times_2 = times_1;
            i_3 = i_2;
            buf_1 = buf_0;
            block = 4;
            break;
            case 2:
            v406 = v405;
            v407 = v406.ll_build();
            v399 = v407;
            block = 3;
            break;
            case 4:
            v408 = buf_1;
            v408.ll_append_char(ch_2);
            v410 = (i_3+1);
            ch_1 = ch_2;
            times_1 = times_2;
            i_2 = v410;
            buf_0 = buf_1;
            block = 1;
            break;
            case 3:
            return ( v399 );
        }
    }
}

function ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst (d_3) {
    var v314,v315,v316,v317,v318,v319,i_0,it_0,length_0,result_0,v320,v321,v322,result_1,v323,v324,v325,v326,v327,v328,v329,etype_4,evalue_4,i_1,it_1,length_1,result_2,v330,v331,v332,it_2,length_2,result_3,v334,v335;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v315 = d_3;
            v316 = get_dict_len ( v315 );
            v317 = ll_newlist__List_String_LlT_Signed ( v316 );
            v318 = d_3;
            v319 = dict_items_iterator ( v318 );
            i_0 = 0;
            it_0 = v319;
            length_0 = v316;
            result_0 = v317;
            block = 1;
            break;
            case 1:
            v320 = it_0;
            v321 = v320.ll_go_next();
            v322 = v321;
            result_1 = result_0;
            v323 = i_0;
            v324 = length_0;
            if (v322 == false)
            {
                block = 2;
                break;
            }
            i_1 = i_0;
            it_1 = it_0;
            length_1 = length_0;
            result_2 = result_0;
            block = 6;
            break;
            case 2:
            v325 = (v323==v324);
            v326 = v325;
            if (v326 == false)
            {
                block = 3;
                break;
            }
            v314 = result_1;
            block = 5;
            break;
            case 3:
            v327 = __consts_0.py____magic_assertion_AssertionError;
            v328 = v327.meta;
            v329 = v327;
            etype_4 = v328;
            evalue_4 = v329;
            block = 4;
            break;
            case 6:
            v330 = result_2;
            v331 = it_1;
            v332 = v331.ll_current_key();
            v330[i_1]=v332;
            it_2 = it_1;
            length_2 = length_1;
            result_3 = result_2;
            v334 = i_1;
            block = 7;
            break;
            case 7:
            v335 = (v334+1);
            i_0 = v335;
            it_0 = it_2;
            length_0 = length_2;
            result_0 = result_3;
            block = 1;
            break;
            case 4:
            throw(evalue_4);
            case 5:
            return ( v314 );
        }
    }
}

function exceptions_AssertionError () {
}

exceptions_AssertionError.prototype.toString = function (){
    return ( '<exceptions_AssertionError instance>' );
}

inherits(exceptions_AssertionError,exceptions_StandardError);
function ll_len__List_Dict_String__String__ (l_5) {
    var v411,v412,v413;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v412 = l_5;
            v413 = v412.length;
            v411 = v413;
            block = 1;
            break;
            case 1:
            return ( v411 );
        }
    }
}

function ll_newlist__List_String_LlT_Signed (length_3) {
    var v659,v660,v661;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v660 = new Array();
            v661 = v660;
            v661.length = length_3;
            v659 = v660;
            block = 1;
            break;
            case 1:
            return ( v659 );
        }
    }
}

function ll_listslice_startonly__List_Dict_String__String__LlT_List_Dict_String__String___Signed (l1_0,start_0) {
    var v414,v415,v416,v417,v419,v421,v423,l1_1,i_4,j_0,l_6,len1_0,v424,v425,l1_2,i_5,j_1,l_7,len1_1,v426,v427,v428,v430,v431;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v415 = l1_0;
            v416 = v415.length;
            v417 = (start_0>=0);
            undefined;
            v419 = (start_0<=v416);
            undefined;
            v421 = (v416-start_0);
            undefined;
            v423 = ll_newlist__List_Dict_String__String__LlT_Signed ( v421 );
            l1_1 = l1_0;
            i_4 = start_0;
            j_0 = 0;
            l_6 = v423;
            len1_0 = v416;
            block = 1;
            break;
            case 1:
            v424 = (i_4<len1_0);
            v425 = v424;
            v414 = l_6;
            if (v425 == false)
            {
                block = 2;
                break;
            }
            l1_2 = l1_1;
            i_5 = i_4;
            j_1 = j_0;
            l_7 = l_6;
            len1_1 = len1_0;
            block = 3;
            break;
            case 3:
            v426 = l_7;
            v427 = l1_2;
            v428 = v427[i_5];
            v426[j_1]=v428;
            v430 = (i_5+1);
            v431 = (j_1+1);
            l1_1 = l1_2;
            i_4 = v430;
            j_0 = v431;
            l_6 = l_7;
            len1_0 = len1_1;
            block = 1;
            break;
            case 2:
            return ( v414 );
        }
    }
}

function process (msg_0) {
    var v450,v451,v452,v453,msg_1,v454,v455,v456,v457,v458,v459,v460,msg_2,v461,v462,v463,msg_3,v464,v465,v466,msg_4,v467,v468,v469,msg_5,v470,v471,v472,msg_6,v473,v474,v475,msg_7,v476,v477,v478,msg_8,v479,v480,v481,msg_9,v482,v483,v484,v485,v486,v487,v488,v489,v490,v491,v492,msg_10,v497,v498,v499,msg_11,v500,v501,msg_12,module_part_0,v503,v504,v505,v506,v508,v509,v511,v514,v515,v516,v518,v520,msg_13,v522,v523,v524,msg_14,v525,v526,msg_15,module_part_1,v528,v529,v530,v531,v532,v533,v535,v536,v538,v541,v543,v544,v546,v548,v550,v552,v553,v554,msg_16,v555,v556,v557,v558,v562,v563,v564,v565,v567,v570,v573,v576,v578,v580,v582,v584,v586,v589,v590,v591,v592,v593,msg_17,v595,v596,v597,msg_18,v598,v599,v601,v602,msg_19,v604,v605,v606,v607,v609,v610,v611,v612,v614,v615,v616,v619,v620,v621,msg_20,v623,v624,v625,v626,v627,v628,v629,v630,v632,v633,v634,v635,v636,v637,v638,v639,v642,v643,v644,v645,v648,v651,v652,v653,main_t_0,v655,v656,v657;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v451 = get_dict_len ( msg_0 );
            v452 = (v451==0);
            v453 = v452;
            msg_1 = msg_0;
            if (v453 == false)
            {
                block = 1;
                break;
            }
            v450 = false;
            block = 12;
            break;
            case 1:
            v454 = __consts_0.Document;
            v455 = v454.getElementById(__consts_0.const_str__45);
            v456 = __consts_0.Document;
            v457 = v456.getElementById(__consts_0.const_str__46);
            v458 = ll_dict_getitem__Dict_String__String__String ( msg_1,__consts_0.const_str__47 );
            v459 = ll_streq__String_String ( v458,__consts_0.const_str__48 );
            v460 = v459;
            msg_2 = msg_1;
            if (v460 == false)
            {
                block = 2;
                break;
            }
            main_t_0 = v457;
            v655 = msg_1;
            block = 29;
            break;
            case 2:
            v461 = ll_dict_getitem__Dict_String__String__String ( msg_2,__consts_0.const_str__47 );
            v462 = ll_streq__String_String ( v461,__consts_0.const_str__49 );
            v463 = v462;
            msg_3 = msg_2;
            if (v463 == false)
            {
                block = 3;
                break;
            }
            msg_20 = msg_2;
            block = 28;
            break;
            case 3:
            v464 = ll_dict_getitem__Dict_String__String__String ( msg_3,__consts_0.const_str__47 );
            v465 = ll_streq__String_String ( v464,__consts_0.const_str__50 );
            v466 = v465;
            msg_4 = msg_3;
            if (v466 == false)
            {
                block = 4;
                break;
            }
            msg_19 = msg_3;
            block = 27;
            break;
            case 4:
            v467 = ll_dict_getitem__Dict_String__String__String ( msg_4,__consts_0.const_str__47 );
            v468 = ll_streq__String_String ( v467,__consts_0.const_str__51 );
            v469 = v468;
            msg_5 = msg_4;
            if (v469 == false)
            {
                block = 5;
                break;
            }
            msg_17 = msg_4;
            block = 24;
            break;
            case 5:
            v470 = ll_dict_getitem__Dict_String__String__String ( msg_5,__consts_0.const_str__47 );
            v471 = ll_streq__String_String ( v470,__consts_0.const_str__52 );
            v472 = v471;
            msg_6 = msg_5;
            if (v472 == false)
            {
                block = 6;
                break;
            }
            msg_16 = msg_5;
            block = 23;
            break;
            case 6:
            v473 = ll_dict_getitem__Dict_String__String__String ( msg_6,__consts_0.const_str__47 );
            v474 = ll_streq__String_String ( v473,__consts_0.const_str__53 );
            v475 = v474;
            msg_7 = msg_6;
            if (v475 == false)
            {
                block = 7;
                break;
            }
            msg_13 = msg_6;
            block = 20;
            break;
            case 7:
            v476 = ll_dict_getitem__Dict_String__String__String ( msg_7,__consts_0.const_str__47 );
            v477 = ll_streq__String_String ( v476,__consts_0.const_str__54 );
            v478 = v477;
            msg_8 = msg_7;
            if (v478 == false)
            {
                block = 8;
                break;
            }
            msg_10 = msg_7;
            block = 17;
            break;
            case 8:
            v479 = ll_dict_getitem__Dict_String__String__String ( msg_8,__consts_0.const_str__47 );
            v480 = ll_streq__String_String ( v479,__consts_0.const_str__55 );
            v481 = v480;
            msg_9 = msg_8;
            if (v481 == false)
            {
                block = 9;
                break;
            }
            block = 16;
            break;
            case 9:
            v482 = ll_dict_getitem__Dict_String__String__String ( msg_9,__consts_0.const_str__47 );
            v483 = ll_streq__String_String ( v482,__consts_0.const_str__56 );
            v484 = v483;
            v485 = msg_9;
            if (v484 == false)
            {
                block = 10;
                break;
            }
            block = 15;
            break;
            case 10:
            v486 = ll_dict_getitem__Dict_String__String__String ( v485,__consts_0.const_str__47 );
            v487 = ll_streq__String_String ( v486,__consts_0.const_str__57 );
            v488 = v487;
            if (v488 == false)
            {
                block = 11;
                break;
            }
            block = 14;
            break;
            case 11:
            v489 = __consts_0.py____test_rsession_webjs_Globals.odata_empty;
            v490 = v489;
            v450 = true;
            if (v490 == false)
            {
                block = 12;
                break;
            }
            block = 13;
            break;
            case 13:
            v491 = __consts_0.Document;
            v492 = v491.getElementById(__consts_0.const_str__10);
            scroll_down_if_needed ( v492 );
            v450 = true;
            block = 12;
            break;
            case 14:
            show_crash (  );
            block = 11;
            break;
            case 15:
            show_interrupt (  );
            block = 11;
            break;
            case 16:
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = true;
            block = 11;
            break;
            case 17:
            v497 = ll_dict_getitem__Dict_String__String__String ( msg_10,__consts_0.const_str__58 );
            v498 = get_elem ( v497 );
            v499 = !!v498;
            msg_11 = msg_10;
            if (v499 == false)
            {
                block = 18;
                break;
            }
            msg_12 = msg_10;
            module_part_0 = v498;
            block = 19;
            break;
            case 18:
            v500 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v501 = v500;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v501,msg_11 );
            v450 = true;
            block = 12;
            break;
            case 19:
            v503 = create_elem ( __consts_0.const_str__21 );
            v504 = create_elem ( __consts_0.const_str__22 );
            v505 = ll_dict_getitem__Dict_String__String__String ( msg_12,__consts_0.const_str__59 );
            v506 = new Object();
            v506.item0 = v505;
            v508 = v506.item0;
            v509 = new StringBuilder();
            v509.ll_append(__consts_0.const_str__60);
            v511 = ll_str__StringR_StringConst_String ( v508 );
            v509.ll_append(v511);
            v509.ll_append(__consts_0.const_str__61);
            v514 = v509.ll_build();
            v515 = create_text_elem ( v514 );
            v516 = v504;
            v516.appendChild(v515);
            v518 = v503;
            v518.appendChild(v504);
            v520 = module_part_0;
            v520.appendChild(v503);
            block = 11;
            break;
            case 20:
            v522 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__58 );
            v523 = get_elem ( v522 );
            v524 = !!v523;
            msg_14 = msg_13;
            if (v524 == false)
            {
                block = 21;
                break;
            }
            msg_15 = msg_13;
            module_part_1 = v523;
            block = 22;
            break;
            case 21:
            v525 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v526 = v525;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v526,msg_14 );
            v450 = true;
            block = 12;
            break;
            case 22:
            v528 = create_elem ( __consts_0.const_str__21 );
            v529 = create_elem ( __consts_0.const_str__22 );
            v530 = create_elem ( __consts_0.const_str__62 );
            v531 = v530;
            v532 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__58 );
            v533 = new Object();
            v533.item0 = v532;
            v535 = v533.item0;
            v536 = new StringBuilder();
            v536.ll_append(__consts_0.const_str__63);
            v538 = ll_str__StringR_StringConst_String ( v535 );
            v536.ll_append(v538);
            v536.ll_append(__consts_0.const_str__34);
            v541 = v536.ll_build();
            v531.setAttribute(__consts_0.const_str__64,v541);
            v543 = create_text_elem ( __consts_0.const_str__65 );
            v544 = v530;
            v544.appendChild(v543);
            v546 = v529;
            v546.appendChild(v530);
            v548 = v528;
            v548.appendChild(v529);
            v550 = module_part_1;
            v550.appendChild(v528);
            v552 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__58 );
            v553 = __consts_0.ExportedMethods;
            v554 = v553.show_fail(v552,fail_come_back);
            block = 11;
            break;
            case 23:
            v555 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__66 );
            v556 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__67 );
            v557 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__68 );
            v558 = new Object();
            v558.item0 = v555;
            v558.item1 = v556;
            v558.item2 = v557;
            v562 = v558.item0;
            v563 = v558.item1;
            v564 = v558.item2;
            v565 = new StringBuilder();
            v565.ll_append(__consts_0.const_str__69);
            v567 = ll_str__StringR_StringConst_String ( v562 );
            v565.ll_append(v567);
            v565.ll_append(__consts_0.const_str__70);
            v570 = ll_str__StringR_StringConst_String ( v563 );
            v565.ll_append(v570);
            v565.ll_append(__consts_0.const_str__71);
            v573 = ll_str__StringR_StringConst_String ( v564 );
            v565.ll_append(v573);
            v565.ll_append(__consts_0.const_str__72);
            v576 = v565.ll_build();
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            v578 = new StringBuilder();
            v578.ll_append(__consts_0.const_str__73);
            v580 = ll_str__StringR_StringConst_String ( v576 );
            v578.ll_append(v580);
            v582 = v578.ll_build();
            __consts_0.Document.title = v582;
            v584 = new StringBuilder();
            v584.ll_append(__consts_0.const_str__41);
            v586 = ll_str__StringR_StringConst_String ( v576 );
            v584.ll_append(v586);
            v584.ll_append(__consts_0.const_str__42);
            v589 = v584.ll_build();
            v590 = __consts_0.Document;
            v591 = v590.getElementById(__consts_0.const_str__39);
            v592 = v591.childNodes;
            v593 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v592,0 );
            v593.nodeValue = v589;
            block = 11;
            break;
            case 24:
            v595 = ll_dict_getitem__Dict_String__String__String ( msg_17,__consts_0.const_str__74 );
            v596 = get_elem ( v595 );
            v597 = !!v596;
            msg_18 = msg_17;
            if (v597 == false)
            {
                block = 25;
                break;
            }
            v601 = msg_17;
            v602 = v596;
            block = 26;
            break;
            case 25:
            v598 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v599 = v598;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v599,msg_18 );
            v450 = true;
            block = 12;
            break;
            case 26:
            add_received_item_outcome ( v601,v602 );
            block = 11;
            break;
            case 27:
            v604 = __consts_0.Document;
            v605 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__75 );
            v606 = v604.getElementById(v605);
            v607 = v606.style;
            v607.background = __consts_0.const_str__76;
            v609 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v610 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__75 );
            v611 = ll_dict_getitem__Dict_String__String__String ( v609,v610 );
            v612 = new Object();
            v612.item0 = v611;
            v614 = v612.item0;
            v615 = new StringBuilder();
            v616 = ll_str__StringR_StringConst_String ( v614 );
            v615.ll_append(v616);
            v615.ll_append(__consts_0.const_str__77);
            v619 = v615.ll_build();
            v620 = v606.childNodes;
            v621 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v620,0 );
            v621.nodeValue = v619;
            block = 11;
            break;
            case 28:
            v623 = __consts_0.Document;
            v624 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v625 = v623.getElementById(v624);
            v626 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v627 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v628 = ll_dict_getitem__Dict_String__List_String___String ( v626,v627 );
            v629 = v628;
            v630 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__58 );
            ll_prepend__List_String__String ( v629,v630 );
            v632 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v633 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v634 = ll_dict_getitem__Dict_String__List_String___String ( v632,v633 );
            v635 = ll_len__List_String_ ( v634 );
            v636 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v637 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v638 = ll_dict_getitem__Dict_String__String__String ( v636,v637 );
            v639 = new Object();
            v639.item0 = v638;
            v639.item1 = v635;
            v642 = v639.item0;
            v643 = v639.item1;
            v644 = new StringBuilder();
            v645 = ll_str__StringR_StringConst_String ( v642 );
            v644.ll_append(v645);
            v644.ll_append(__consts_0.const_str__78);
            v648 = ll_int_str__IntegerR_SignedConst_Signed ( v643 );
            v644.ll_append(v648);
            v644.ll_append(__consts_0.const_str__42);
            v651 = v644.ll_build();
            v652 = v625.childNodes;
            v653 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v652,0 );
            v653.nodeValue = v651;
            block = 11;
            break;
            case 29:
            v656 = make_module_box ( v655 );
            v657 = main_t_0;
            v657.appendChild(v656);
            block = 11;
            break;
            case 12:
            return ( v450 );
        }
    }
}

function show_crash () {
    var v675,v676,v677,v678;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__79;
            v675 = __consts_0.Document;
            v676 = v675.getElementById(__consts_0.const_str__39);
            v677 = v676.childNodes;
            v678 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v677,0 );
            v678.nodeValue = __consts_0.const_str__80;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function scroll_down_if_needed (mbox_2) {
    var v666,v667,v668,v669,v670;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v666 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v667 = v666;
            if (v667 == false)
            {
                block = 1;
                break;
            }
            v668 = mbox_2;
            block = 2;
            break;
            case 2:
            v669 = v668.parentNode;
            v670 = v669;
            v670.scrollIntoView();
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function py____magic_assertion_AssertionError () {
}

py____magic_assertion_AssertionError.prototype.toString = function (){
    return ( '<py____magic_assertion_AssertionError instance>' );
}

inherits(py____magic_assertion_AssertionError,exceptions_AssertionError);
function ll_newlist__List_Dict_String__String__LlT_Signed (length_4) {
    var v663,v664;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v664 = ll_newlist__List_Dict_String__String__LlT_Signed_0 ( length_4 );
            v663 = v664;
            block = 1;
            break;
            case 1:
            return ( v663 );
        }
    }
}

function ll_len__List_String_ (l_13) {
    var v872,v873,v874;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v873 = l_13;
            v874 = v873.length;
            v872 = v874;
            block = 1;
            break;
            case 1:
            return ( v872 );
        }
    }
}

function show_interrupt () {
    var v683,v684,v685,v686;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__81;
            v683 = __consts_0.Document;
            v684 = v683.getElementById(__consts_0.const_str__39);
            v685 = v684.childNodes;
            v686 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v685,0 );
            v686.nodeValue = __consts_0.const_str__82;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed_0 (length_5) {
    var v937,v938,v939;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v938 = new Array();
            v939 = v938;
            v939.length = length_5;
            v937 = v938;
            block = 1;
            break;
            case 1:
            return ( v937 );
        }
    }
}

function add_received_item_outcome (msg_22,module_part_2) {
    var v707,v708,v709,msg_23,module_part_3,v710,v711,v712,v713,v715,v716,v718,v721,v723,v725,v726,v727,v728,msg_24,module_part_4,item_name_6,td_0,v729,v730,v731,v732,msg_25,module_part_5,item_name_7,td_1,v733,v734,v735,v736,v738,v739,v741,v744,v746,v747,v749,v751,v753,v754,msg_26,module_part_6,td_2,v755,v756,v757,v758,v759,module_part_7,td_3,v760,v761,v762,v763,v765,v766,v767,v768,v769,v770,v774,v775,v776,v777,v778,v781,v784,v787,v788,v789,v791,v792,v793,msg_27,module_part_8,td_4,v795,v796,msg_28,module_part_9,item_name_8,td_5,v798,v799,v800,v801,msg_29,module_part_10,item_name_9,td_6,v802,v803,v804,v805,v806,v807,v809,v810,v812,v815,v817,v818,v820,msg_30,module_part_11,td_7,v822,v823,msg_31,module_part_12,v825,v826,v827,v828,v829,v830,v831,v832,v833,v834,v835,v836,v837,v838,v839,v840,v843,v844,v845,v846,v849,v852,v853,v854;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v707 = ll_dict_getitem__Dict_String__String__String ( msg_22,__consts_0.const_str__75 );
            v708 = ll_strlen__String ( v707 );
            v709 = !!v708;
            msg_23 = msg_22;
            module_part_3 = module_part_2;
            if (v709 == false)
            {
                block = 1;
                break;
            }
            msg_31 = msg_22;
            module_part_12 = module_part_2;
            block = 11;
            break;
            case 1:
            v710 = create_elem ( __consts_0.const_str__22 );
            v711 = v710;
            v712 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__58 );
            v713 = new Object();
            v713.item0 = v712;
            v715 = v713.item0;
            v716 = new StringBuilder();
            v716.ll_append(__consts_0.const_str__83);
            v718 = ll_str__StringR_StringConst_String ( v715 );
            v716.ll_append(v718);
            v716.ll_append(__consts_0.const_str__34);
            v721 = v716.ll_build();
            v711.setAttribute(__consts_0.const_str__35,v721);
            v723 = v710;
            v723.setAttribute(__consts_0.const_str__36,__consts_0.const_str__84);
            v725 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__58 );
            v726 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__85 );
            v727 = ll_streq__String_String ( v726,__consts_0.const_str__9 );
            v728 = v727;
            msg_24 = msg_23;
            module_part_4 = module_part_3;
            item_name_6 = v725;
            td_0 = v710;
            if (v728 == false)
            {
                block = 2;
                break;
            }
            msg_30 = msg_23;
            module_part_11 = module_part_3;
            td_7 = v710;
            block = 10;
            break;
            case 2:
            v729 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__86 );
            v730 = ll_streq__String_String ( v729,__consts_0.const_str__87 );
            v731 = !v730;
            v732 = v731;
            msg_25 = msg_24;
            module_part_5 = module_part_4;
            item_name_7 = item_name_6;
            td_1 = td_0;
            if (v732 == false)
            {
                block = 3;
                break;
            }
            msg_28 = msg_24;
            module_part_9 = module_part_4;
            item_name_8 = item_name_6;
            td_5 = td_0;
            block = 8;
            break;
            case 3:
            v733 = create_elem ( __consts_0.const_str__62 );
            v734 = v733;
            v735 = ll_dict_getitem__Dict_String__String__String ( msg_25,__consts_0.const_str__58 );
            v736 = new Object();
            v736.item0 = v735;
            v738 = v736.item0;
            v739 = new StringBuilder();
            v739.ll_append(__consts_0.const_str__63);
            v741 = ll_str__StringR_StringConst_String ( v738 );
            v739.ll_append(v741);
            v739.ll_append(__consts_0.const_str__34);
            v744 = v739.ll_build();
            v734.setAttribute(__consts_0.const_str__64,v744);
            v746 = create_text_elem ( __consts_0.const_str__88 );
            v747 = v733;
            v747.setAttribute(__consts_0.const_str__89,__consts_0.const_str__90);
            v749 = v733;
            v749.appendChild(v746);
            v751 = td_1;
            v751.appendChild(v733);
            v753 = __consts_0.ExportedMethods;
            v754 = v753.show_fail(item_name_7,fail_come_back);
            msg_26 = msg_25;
            module_part_6 = module_part_5;
            td_2 = td_1;
            block = 4;
            break;
            case 4:
            v755 = ll_dict_getitem__Dict_String__String__String ( msg_26,__consts_0.const_str__74 );
            v756 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__91,v755 );
            v757 = (v756%5000);
            v758 = (v757==0);
            v759 = v758;
            module_part_7 = module_part_6;
            td_3 = td_2;
            v760 = msg_26;
            if (v759 == false)
            {
                block = 5;
                break;
            }
            msg_27 = msg_26;
            module_part_8 = module_part_6;
            td_4 = td_2;
            block = 7;
            break;
            case 5:
            v761 = ll_dict_getitem__Dict_String__String__String ( v760,__consts_0.const_str__74 );
            v762 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__91,v761 );
            v763 = (v762+1);
            __consts_0.const_tuple__91[v761]=v763;
            v765 = ll_strconcat__String_String ( __consts_0.const_str__92,v761 );
            v766 = get_elem ( v765 );
            v767 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__93,v761 );
            v768 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__91,v761 );
            v769 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__94,v761 );
            v770 = new Object();
            v770.item0 = v767;
            v770.item1 = v768;
            v770.item2 = v769;
            v774 = v770.item0;
            v775 = v770.item1;
            v776 = v770.item2;
            v777 = new StringBuilder();
            v778 = ll_str__StringR_StringConst_String ( v774 );
            v777.ll_append(v778);
            v777.ll_append(__consts_0.const_str__78);
            v781 = v775.toString();
            v777.ll_append(v781);
            v777.ll_append(__consts_0.const_str__95);
            v784 = v776.toString();
            v777.ll_append(v784);
            v777.ll_append(__consts_0.const_str__42);
            v787 = v777.ll_build();
            v788 = v766.childNodes;
            v789 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v788,0 );
            v789.nodeValue = v787;
            v791 = module_part_7.childNodes;
            v792 = ll_getitem__dum_nocheckConst_List_ExternalType__Signed ( v791,-1 );
            v793 = v792;
            v793.appendChild(td_3);
            block = 6;
            break;
            case 7:
            v795 = create_elem ( __consts_0.const_str__21 );
            v796 = module_part_8;
            v796.appendChild(v795);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v760 = msg_27;
            block = 5;
            break;
            case 8:
            v798 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__86 );
            v799 = ll_streq__String_String ( v798,__consts_0.const_str__96 );
            v800 = !v799;
            v801 = v800;
            msg_25 = msg_28;
            module_part_5 = module_part_9;
            item_name_7 = item_name_8;
            td_1 = td_5;
            if (v801 == false)
            {
                block = 3;
                break;
            }
            msg_29 = msg_28;
            module_part_10 = module_part_9;
            item_name_9 = item_name_8;
            td_6 = td_5;
            block = 9;
            break;
            case 9:
            v802 = __consts_0.ExportedMethods;
            v803 = v802.show_skip(item_name_9,skip_come_back);
            v804 = create_elem ( __consts_0.const_str__62 );
            v805 = v804;
            v806 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__58 );
            v807 = new Object();
            v807.item0 = v806;
            v809 = v807.item0;
            v810 = new StringBuilder();
            v810.ll_append(__consts_0.const_str__97);
            v812 = ll_str__StringR_StringConst_String ( v809 );
            v810.ll_append(v812);
            v810.ll_append(__consts_0.const_str__34);
            v815 = v810.ll_build();
            v805.setAttribute(__consts_0.const_str__64,v815);
            v817 = create_text_elem ( __consts_0.const_str__98 );
            v818 = v804;
            v818.appendChild(v817);
            v820 = td_6;
            v820.appendChild(v804);
            msg_26 = msg_29;
            module_part_6 = module_part_10;
            td_2 = td_6;
            block = 4;
            break;
            case 10:
            v822 = create_text_elem ( __consts_0.const_str__99 );
            v823 = td_7;
            v823.appendChild(v822);
            msg_26 = msg_30;
            module_part_6 = module_part_11;
            td_2 = td_7;
            block = 4;
            break;
            case 11:
            v825 = __consts_0.Document;
            v826 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v827 = v825.getElementById(v826);
            v828 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v829 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v830 = ll_dict_getitem__Dict_String__List_String___String ( v828,v829 );
            v831 = v830;
            v832 = ll_pop_default__dum_nocheckConst_List_String_ ( v831 );
            v833 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v834 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v835 = ll_dict_getitem__Dict_String__List_String___String ( v833,v834 );
            v836 = ll_len__List_String_ ( v835 );
            v837 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v838 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v839 = ll_dict_getitem__Dict_String__String__String ( v837,v838 );
            v840 = new Object();
            v840.item0 = v839;
            v840.item1 = v836;
            v843 = v840.item0;
            v844 = v840.item1;
            v845 = new StringBuilder();
            v846 = ll_str__StringR_StringConst_String ( v843 );
            v845.ll_append(v846);
            v845.ll_append(__consts_0.const_str__78);
            v849 = ll_int_str__IntegerR_SignedConst_Signed ( v844 );
            v845.ll_append(v849);
            v845.ll_append(__consts_0.const_str__42);
            v852 = v845.ll_build();
            v853 = v827.childNodes;
            v854 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v853,0 );
            v854.nodeValue = v852;
            msg_23 = msg_31;
            module_part_3 = module_part_12;
            block = 1;
            break;
            case 6:
            return ( undefined );
        }
    }
}

function fail_come_back (msg_21) {
    var v697,v698,v699,v700,v704;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v697 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__100 );
            v698 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__101 );
            v699 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__102 );
            v700 = new Object();
            v700.item0 = v697;
            v700.item1 = v698;
            v700.item2 = v699;
            v704 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__103 );
            __consts_0.const_tuple[v704]=v700;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_append__List_Dict_String__String___Dict_String__String_ (l_9,newitem_0) {
    var v689,v690,v691,v692,v694;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v689 = l_9;
            v690 = v689.length;
            v691 = l_9;
            v692 = (v690+1);
            v691.length = v692;
            v694 = l_9;
            v694[v690]=newitem_0;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function make_module_box (msg_32) {
    var v877,v878,v879,v880,v882,v883,v884,v885,v888,v889,v890,v891,v894,v897,v898,v900,v901,v902,v904,v905,v907,v908,v910,v911,v912,v914,v915,v917,v920,v922,v924,v925,v927,v928,v930,v931,v933,v935;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v878 = create_elem ( __consts_0.const_str__21 );
            v879 = create_elem ( __consts_0.const_str__22 );
            v880 = v878;
            v880.appendChild(v879);
            v882 = v879;
            v883 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__104 );
            v884 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__105 );
            v885 = new Object();
            v885.item0 = v883;
            v885.item1 = v884;
            v888 = v885.item0;
            v889 = v885.item1;
            v890 = new StringBuilder();
            v891 = ll_str__StringR_StringConst_String ( v888 );
            v890.ll_append(v891);
            v890.ll_append(__consts_0.const_str__106);
            v894 = ll_str__StringR_StringConst_String ( v889 );
            v890.ll_append(v894);
            v890.ll_append(__consts_0.const_str__42);
            v897 = v890.ll_build();
            v898 = create_text_elem ( v897 );
            v882.appendChild(v898);
            v900 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__105 );
            v901 = ll_int__String_Signed ( v900,10 );
            v902 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__94[v902]=v901;
            v904 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__104 );
            v905 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__93[v905]=v904;
            v907 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v908 = ll_strconcat__String_String ( __consts_0.const_str__92,v907 );
            v879.id = v908;
            v910 = v879;
            v911 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v912 = new Object();
            v912.item0 = v911;
            v914 = v912.item0;
            v915 = new StringBuilder();
            v915.ll_append(__consts_0.const_str__83);
            v917 = ll_str__StringR_StringConst_String ( v914 );
            v915.ll_append(v917);
            v915.ll_append(__consts_0.const_str__34);
            v920 = v915.ll_build();
            v910.setAttribute(__consts_0.const_str__35,v920);
            v922 = v879;
            v922.setAttribute(__consts_0.const_str__36,__consts_0.const_str__84);
            v924 = create_elem ( __consts_0.const_str__22 );
            v925 = v878;
            v925.appendChild(v924);
            v927 = create_elem ( __consts_0.const_str__107 );
            v928 = v924;
            v928.appendChild(v927);
            v930 = create_elem ( __consts_0.const_str__20 );
            v931 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v930.id = v931;
            v933 = v927;
            v933.appendChild(v930);
            v935 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__91[v935]=0;
            v877 = v878;
            block = 1;
            break;
            case 1:
            return ( v877 );
        }
    }
}

function ll_int_str__IntegerR_SignedConst_Signed (i_6) {
    var v875,v876;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v876 = ll_int2dec__Signed ( i_6 );
            v875 = v876;
            block = 1;
            break;
            case 1:
            return ( v875 );
        }
    }
}

function ll_prepend__List_String__String (l_10,newitem_1) {
    var v857,v858,v859,v860,l_11,newitem_2,dst_0,v862,v863,newitem_3,v864,v865,l_12,newitem_4,dst_1,v867,v868,v869,v870;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v857 = l_10;
            v858 = v857.length;
            v859 = l_10;
            v860 = (v858+1);
            v859.length = v860;
            l_11 = l_10;
            newitem_2 = newitem_1;
            dst_0 = v858;
            block = 1;
            break;
            case 1:
            v862 = (dst_0>0);
            v863 = v862;
            newitem_3 = newitem_2;
            v864 = l_11;
            if (v863 == false)
            {
                block = 2;
                break;
            }
            l_12 = l_11;
            newitem_4 = newitem_2;
            dst_1 = dst_0;
            block = 4;
            break;
            case 2:
            v865 = v864;
            v865[0]=newitem_3;
            block = 3;
            break;
            case 4:
            v867 = (dst_1-1);
            v868 = l_12;
            v869 = l_12;
            v870 = v869[v867];
            v868[dst_1]=v870;
            l_11 = l_12;
            newitem_2 = newitem_4;
            dst_0 = v867;
            block = 1;
            break;
            case 3:
            return ( undefined );
        }
    }
}

function ll_getitem__dum_nocheckConst_List_ExternalType__Signed (l_14,index_5) {
    var v954,v955,v956,v957,v958,l_15,index_6,length_6,v959,v961,index_7,v963,v964,v965,l_16,length_7,v966,v967;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v955 = l_14;
            v956 = v955.length;
            v957 = (index_5<0);
            v958 = v957;
            l_15 = l_14;
            index_6 = index_5;
            length_6 = v956;
            if (v958 == false)
            {
                block = 1;
                break;
            }
            l_16 = l_14;
            length_7 = v956;
            v966 = index_5;
            block = 4;
            break;
            case 1:
            v959 = (index_6>=0);
            undefined;
            v961 = (index_6<length_6);
            undefined;
            index_7 = index_6;
            v963 = l_15;
            block = 2;
            break;
            case 2:
            v964 = v963;
            v965 = v964[index_7];
            v954 = v965;
            block = 3;
            break;
            case 4:
            v967 = (v966+length_7);
            l_15 = l_16;
            index_6 = v967;
            length_6 = length_7;
            block = 1;
            break;
            case 3:
            return ( v954 );
        }
    }
}

function ll_pop_default__dum_nocheckConst_List_String_ (l_17) {
    var v972,v973,v974,l_18,length_8,v975,v977,v978,v979,res_0,newlength_0,v981,v982;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v973 = l_17;
            v974 = v973.length;
            l_18 = l_17;
            length_8 = v974;
            block = 1;
            break;
            case 1:
            v975 = (length_8>0);
            undefined;
            v977 = (length_8-1);
            v978 = l_18;
            v979 = v978[v977];
            ll_null_item__List_String_ ( l_18 );
            res_0 = v979;
            newlength_0 = v977;
            v981 = l_18;
            block = 2;
            break;
            case 2:
            v982 = v981;
            v982.length = newlength_0;
            v972 = res_0;
            block = 3;
            break;
            case 3:
            return ( v972 );
        }
    }
}

function ll_dict_getitem__Dict_String__Signed__String (d_4,key_8) {
    var v944,v945,v946,v947,v948,v949,v950,etype_6,evalue_6,key_9,v951,v952,v953;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v945 = d_4;
            v946 = (v945[key_8]!=undefined);
            v947 = v946;
            if (v947 == false)
            {
                block = 1;
                break;
            }
            key_9 = key_8;
            v951 = d_4;
            block = 3;
            break;
            case 1:
            v948 = __consts_0.exceptions_KeyError;
            v949 = v948.meta;
            v950 = v948;
            etype_6 = v949;
            evalue_6 = v950;
            block = 2;
            break;
            case 3:
            v952 = v951;
            v953 = v952[key_9];
            v944 = v953;
            block = 4;
            break;
            case 2:
            throw(evalue_6);
            case 4:
            return ( v944 );
        }
    }
}

function ll_int2dec__Signed (i_29) {
    var v1072,v1073;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1073 = i_29.toString();
            v1072 = v1073;
            block = 1;
            break;
            case 1:
            return ( v1072 );
        }
    }
}

function ll_strlen__String (obj_1) {
    var v941,v942,v943;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v942 = obj_1;
            v943 = v942.length;
            v941 = v943;
            block = 1;
            break;
            case 1:
            return ( v941 );
        }
    }
}

function skip_come_back (msg_33) {
    var v969,v970;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v969 = ll_dict_getitem__Dict_String__String__String ( msg_33,__consts_0.const_str__59 );
            v970 = ll_dict_getitem__Dict_String__String__String ( msg_33,__consts_0.const_str__103 );
            __consts_0.const_tuple__28[v970]=v969;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_null_item__List_String_ (lst_2) {
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            undefined;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_int__String_Signed (s_2,base_0) {
    var v984,v985,v986,v987,v988,v989,etype_7,evalue_7,s_3,base_1,v990,s_4,base_2,v991,v992,s_5,base_3,v993,v994,s_6,base_4,i_7,strlen_0,v995,v996,s_7,base_5,i_8,strlen_1,v997,v998,v999,v1000,v1001,s_8,base_6,i_9,strlen_2,v1002,v1003,v1004,v1005,s_9,base_7,i_10,strlen_3,v1006,v1007,v1008,v1009,s_10,base_8,val_0,i_11,sign_0,strlen_4,v1010,v1011,s_11,val_1,i_12,sign_1,strlen_5,v1012,v1013,val_2,sign_2,v1014,v1015,v1016,v1017,v1018,v1019,v1020,v1021,v1022,v1023,s_12,val_3,i_13,sign_3,strlen_6,v1024,v1025,v1026,v1027,s_13,val_4,sign_4,strlen_7,v1028,v1029,s_14,base_9,val_5,i_14,sign_5,strlen_8,v1030,v1031,v1032,v1033,v1034,s_15,base_10,c_0,val_6,i_15,sign_6,strlen_9,v1035,v1036,s_16,base_11,c_1,val_7,i_16,sign_7,strlen_10,v1037,v1038,s_17,base_12,c_2,val_8,i_17,sign_8,strlen_11,v1039,s_18,base_13,c_3,val_9,i_18,sign_9,strlen_12,v1040,v1041,s_19,base_14,val_10,i_19,sign_10,strlen_13,v1042,v1043,s_20,base_15,val_11,i_20,digit_0,sign_11,strlen_14,v1044,v1045,s_21,base_16,i_21,digit_1,sign_12,strlen_15,v1046,v1047,v1048,v1049,s_22,base_17,c_4,val_12,i_22,sign_13,strlen_16,v1050,s_23,base_18,c_5,val_13,i_23,sign_14,strlen_17,v1051,v1052,s_24,base_19,val_14,i_24,sign_15,strlen_18,v1053,v1054,v1055,s_25,base_20,c_6,val_15,i_25,sign_16,strlen_19,v1056,s_26,base_21,c_7,val_16,i_26,sign_17,strlen_20,v1057,v1058,s_27,base_22,val_17,i_27,sign_18,strlen_21,v1059,v1060,v1061,s_28,base_23,strlen_22,v1062,v1063,s_29,base_24,strlen_23,v1064,v1065,s_30,base_25,i_28,strlen_24,v1066,v1067,v1068,v1069,s_31,base_26,strlen_25,v1070,v1071;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v985 = (2<=base_0);
            v986 = v985;
            if (v986 == false)
            {
                block = 1;
                break;
            }
            s_3 = s_2;
            base_1 = base_0;
            block = 3;
            break;
            case 1:
            v987 = __consts_0.exceptions_ValueError;
            v988 = v987.meta;
            v989 = v987;
            etype_7 = v988;
            evalue_7 = v989;
            block = 2;
            break;
            case 3:
            v990 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v991 = v990;
            block = 4;
            break;
            case 4:
            v992 = v991;
            if (v992 == false)
            {
                block = 1;
                break;
            }
            s_5 = s_4;
            base_3 = base_2;
            block = 5;
            break;
            case 5:
            v993 = s_5;
            v994 = v993.length;
            s_6 = s_5;
            base_4 = base_3;
            i_7 = 0;
            strlen_0 = v994;
            block = 6;
            break;
            case 6:
            v995 = (i_7<strlen_0);
            v996 = v995;
            s_7 = s_6;
            base_5 = base_4;
            i_8 = i_7;
            strlen_1 = strlen_0;
            if (v996 == false)
            {
                block = 7;
                break;
            }
            s_30 = s_6;
            base_25 = base_4;
            i_28 = i_7;
            strlen_24 = strlen_0;
            block = 35;
            break;
            case 7:
            v997 = (i_8<strlen_1);
            v998 = v997;
            if (v998 == false)
            {
                block = 8;
                break;
            }
            s_8 = s_7;
            base_6 = base_5;
            i_9 = i_8;
            strlen_2 = strlen_1;
            block = 9;
            break;
            case 8:
            v999 = __consts_0.exceptions_ValueError;
            v1000 = v999.meta;
            v1001 = v999;
            etype_7 = v1000;
            evalue_7 = v1001;
            block = 2;
            break;
            case 9:
            v1002 = s_8;
            v1003 = v1002.charAt(i_9);
            v1004 = (v1003=='-');
            v1005 = v1004;
            s_9 = s_8;
            base_7 = base_6;
            i_10 = i_9;
            strlen_3 = strlen_2;
            if (v1005 == false)
            {
                block = 10;
                break;
            }
            s_29 = s_8;
            base_24 = base_6;
            strlen_23 = strlen_2;
            v1064 = i_9;
            block = 34;
            break;
            case 10:
            v1006 = s_9;
            v1007 = v1006.charAt(i_10);
            v1008 = (v1007=='+');
            v1009 = v1008;
            s_10 = s_9;
            base_8 = base_7;
            val_0 = 0;
            i_11 = i_10;
            sign_0 = 1;
            strlen_4 = strlen_3;
            if (v1009 == false)
            {
                block = 11;
                break;
            }
            s_28 = s_9;
            base_23 = base_7;
            strlen_22 = strlen_3;
            v1062 = i_10;
            block = 33;
            break;
            case 11:
            v1010 = (i_11<strlen_4);
            v1011 = v1010;
            s_11 = s_10;
            val_1 = val_0;
            i_12 = i_11;
            sign_1 = sign_0;
            strlen_5 = strlen_4;
            if (v1011 == false)
            {
                block = 12;
                break;
            }
            s_14 = s_10;
            base_9 = base_8;
            val_5 = val_0;
            i_14 = i_11;
            sign_5 = sign_0;
            strlen_8 = strlen_4;
            block = 19;
            break;
            case 12:
            v1012 = (i_12<strlen_5);
            v1013 = v1012;
            val_2 = val_1;
            sign_2 = sign_1;
            v1014 = i_12;
            v1015 = strlen_5;
            if (v1013 == false)
            {
                block = 13;
                break;
            }
            s_12 = s_11;
            val_3 = val_1;
            i_13 = i_12;
            sign_3 = sign_1;
            strlen_6 = strlen_5;
            block = 17;
            break;
            case 13:
            v1016 = (v1014==v1015);
            v1017 = v1016;
            if (v1017 == false)
            {
                block = 14;
                break;
            }
            v1021 = sign_2;
            v1022 = val_2;
            block = 15;
            break;
            case 14:
            v1018 = __consts_0.exceptions_ValueError;
            v1019 = v1018.meta;
            v1020 = v1018;
            etype_7 = v1019;
            evalue_7 = v1020;
            block = 2;
            break;
            case 15:
            v1023 = (v1021*v1022);
            v984 = v1023;
            block = 16;
            break;
            case 17:
            v1024 = s_12;
            v1025 = v1024.charAt(i_13);
            v1026 = (v1025==' ');
            v1027 = v1026;
            val_2 = val_3;
            sign_2 = sign_3;
            v1014 = i_13;
            v1015 = strlen_6;
            if (v1027 == false)
            {
                block = 13;
                break;
            }
            s_13 = s_12;
            val_4 = val_3;
            sign_4 = sign_3;
            strlen_7 = strlen_6;
            v1028 = i_13;
            block = 18;
            break;
            case 18:
            v1029 = (v1028+1);
            s_11 = s_13;
            val_1 = val_4;
            i_12 = v1029;
            sign_1 = sign_4;
            strlen_5 = strlen_7;
            block = 12;
            break;
            case 19:
            v1030 = s_14;
            v1031 = v1030.charAt(i_14);
            v1032 = v1031.charCodeAt(0);
            v1033 = (97<=v1032);
            v1034 = v1033;
            s_15 = s_14;
            base_10 = base_9;
            c_0 = v1032;
            val_6 = val_5;
            i_15 = i_14;
            sign_6 = sign_5;
            strlen_9 = strlen_8;
            if (v1034 == false)
            {
                block = 20;
                break;
            }
            s_25 = s_14;
            base_20 = base_9;
            c_6 = v1032;
            val_15 = val_5;
            i_25 = i_14;
            sign_16 = sign_5;
            strlen_19 = strlen_8;
            block = 30;
            break;
            case 20:
            v1035 = (65<=c_0);
            v1036 = v1035;
            s_16 = s_15;
            base_11 = base_10;
            c_1 = c_0;
            val_7 = val_6;
            i_16 = i_15;
            sign_7 = sign_6;
            strlen_10 = strlen_9;
            if (v1036 == false)
            {
                block = 21;
                break;
            }
            s_22 = s_15;
            base_17 = base_10;
            c_4 = c_0;
            val_12 = val_6;
            i_22 = i_15;
            sign_13 = sign_6;
            strlen_16 = strlen_9;
            block = 27;
            break;
            case 21:
            v1037 = (48<=c_1);
            v1038 = v1037;
            s_11 = s_16;
            val_1 = val_7;
            i_12 = i_16;
            sign_1 = sign_7;
            strlen_5 = strlen_10;
            if (v1038 == false)
            {
                block = 12;
                break;
            }
            s_17 = s_16;
            base_12 = base_11;
            c_2 = c_1;
            val_8 = val_7;
            i_17 = i_16;
            sign_8 = sign_7;
            strlen_11 = strlen_10;
            block = 22;
            break;
            case 22:
            v1039 = (c_2<=57);
            s_18 = s_17;
            base_13 = base_12;
            c_3 = c_2;
            val_9 = val_8;
            i_18 = i_17;
            sign_9 = sign_8;
            strlen_12 = strlen_11;
            v1040 = v1039;
            block = 23;
            break;
            case 23:
            v1041 = v1040;
            s_11 = s_18;
            val_1 = val_9;
            i_12 = i_18;
            sign_1 = sign_9;
            strlen_5 = strlen_12;
            if (v1041 == false)
            {
                block = 12;
                break;
            }
            s_19 = s_18;
            base_14 = base_13;
            val_10 = val_9;
            i_19 = i_18;
            sign_10 = sign_9;
            strlen_13 = strlen_12;
            v1042 = c_3;
            block = 24;
            break;
            case 24:
            v1043 = (v1042-48);
            s_20 = s_19;
            base_15 = base_14;
            val_11 = val_10;
            i_20 = i_19;
            digit_0 = v1043;
            sign_11 = sign_10;
            strlen_14 = strlen_13;
            block = 25;
            break;
            case 25:
            v1044 = (digit_0>=base_15);
            v1045 = v1044;
            s_21 = s_20;
            base_16 = base_15;
            i_21 = i_20;
            digit_1 = digit_0;
            sign_12 = sign_11;
            strlen_15 = strlen_14;
            v1046 = val_11;
            if (v1045 == false)
            {
                block = 26;
                break;
            }
            s_11 = s_20;
            val_1 = val_11;
            i_12 = i_20;
            sign_1 = sign_11;
            strlen_5 = strlen_14;
            block = 12;
            break;
            case 26:
            v1047 = (v1046*base_16);
            v1048 = (v1047+digit_1);
            v1049 = (i_21+1);
            s_10 = s_21;
            base_8 = base_16;
            val_0 = v1048;
            i_11 = v1049;
            sign_0 = sign_12;
            strlen_4 = strlen_15;
            block = 11;
            break;
            case 27:
            v1050 = (c_4<=90);
            s_23 = s_22;
            base_18 = base_17;
            c_5 = c_4;
            val_13 = val_12;
            i_23 = i_22;
            sign_14 = sign_13;
            strlen_17 = strlen_16;
            v1051 = v1050;
            block = 28;
            break;
            case 28:
            v1052 = v1051;
            s_16 = s_23;
            base_11 = base_18;
            c_1 = c_5;
            val_7 = val_13;
            i_16 = i_23;
            sign_7 = sign_14;
            strlen_10 = strlen_17;
            if (v1052 == false)
            {
                block = 21;
                break;
            }
            s_24 = s_23;
            base_19 = base_18;
            val_14 = val_13;
            i_24 = i_23;
            sign_15 = sign_14;
            strlen_18 = strlen_17;
            v1053 = c_5;
            block = 29;
            break;
            case 29:
            v1054 = (v1053-65);
            v1055 = (v1054+10);
            s_20 = s_24;
            base_15 = base_19;
            val_11 = val_14;
            i_20 = i_24;
            digit_0 = v1055;
            sign_11 = sign_15;
            strlen_14 = strlen_18;
            block = 25;
            break;
            case 30:
            v1056 = (c_6<=122);
            s_26 = s_25;
            base_21 = base_20;
            c_7 = c_6;
            val_16 = val_15;
            i_26 = i_25;
            sign_17 = sign_16;
            strlen_20 = strlen_19;
            v1057 = v1056;
            block = 31;
            break;
            case 31:
            v1058 = v1057;
            s_15 = s_26;
            base_10 = base_21;
            c_0 = c_7;
            val_6 = val_16;
            i_15 = i_26;
            sign_6 = sign_17;
            strlen_9 = strlen_20;
            if (v1058 == false)
            {
                block = 20;
                break;
            }
            s_27 = s_26;
            base_22 = base_21;
            val_17 = val_16;
            i_27 = i_26;
            sign_18 = sign_17;
            strlen_21 = strlen_20;
            v1059 = c_7;
            block = 32;
            break;
            case 32:
            v1060 = (v1059-97);
            v1061 = (v1060+10);
            s_20 = s_27;
            base_15 = base_22;
            val_11 = val_17;
            i_20 = i_27;
            digit_0 = v1061;
            sign_11 = sign_18;
            strlen_14 = strlen_21;
            block = 25;
            break;
            case 33:
            v1063 = (v1062+1);
            s_10 = s_28;
            base_8 = base_23;
            val_0 = 0;
            i_11 = v1063;
            sign_0 = 1;
            strlen_4 = strlen_22;
            block = 11;
            break;
            case 34:
            v1065 = (v1064+1);
            s_10 = s_29;
            base_8 = base_24;
            val_0 = 0;
            i_11 = v1065;
            sign_0 = -1;
            strlen_4 = strlen_23;
            block = 11;
            break;
            case 35:
            v1066 = s_30;
            v1067 = v1066.charAt(i_28);
            v1068 = (v1067==' ');
            v1069 = v1068;
            s_7 = s_30;
            base_5 = base_25;
            i_8 = i_28;
            strlen_1 = strlen_24;
            if (v1069 == false)
            {
                block = 7;
                break;
            }
            s_31 = s_30;
            base_26 = base_25;
            strlen_25 = strlen_24;
            v1070 = i_28;
            block = 36;
            break;
            case 36:
            v1071 = (v1070+1);
            s_6 = s_31;
            base_4 = base_26;
            i_7 = v1071;
            strlen_0 = strlen_25;
            block = 6;
            break;
            case 2:
            throw(evalue_7);
            case 16:
            return ( v984 );
        }
    }
}

function exceptions_ValueError () {
}

exceptions_ValueError.prototype.toString = function (){
    return ( '<exceptions_ValueError instance>' );
}

inherits(exceptions_ValueError,exceptions_StandardError);
function Object_meta () {
    this.class_ = __consts_0.None;
}

Object_meta.prototype.toString = function (){
    return ( '<Object_meta instance>' );
}

function exceptions_Exception_meta () {
}

exceptions_Exception_meta.prototype.toString = function (){
    return ( '<exceptions_Exception_meta instance>' );
}

inherits(exceptions_Exception_meta,Object_meta);
function exceptions_StopIteration_meta () {
}

exceptions_StopIteration_meta.prototype.toString = function (){
    return ( '<exceptions_StopIteration_meta instance>' );
}

inherits(exceptions_StopIteration_meta,exceptions_Exception_meta);
function py____test_rsession_webjs_Options_meta () {
}

py____test_rsession_webjs_Options_meta.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Options_meta instance>' );
}

inherits(py____test_rsession_webjs_Options_meta,Object_meta);
function exceptions_StandardError_meta () {
}

exceptions_StandardError_meta.prototype.toString = function (){
    return ( '<exceptions_StandardError_meta instance>' );
}

inherits(exceptions_StandardError_meta,exceptions_Exception_meta);
function exceptions_LookupError_meta () {
}

exceptions_LookupError_meta.prototype.toString = function (){
    return ( '<exceptions_LookupError_meta instance>' );
}

inherits(exceptions_LookupError_meta,exceptions_StandardError_meta);
function exceptions_KeyError_meta () {
}

exceptions_KeyError_meta.prototype.toString = function (){
    return ( '<exceptions_KeyError_meta instance>' );
}

inherits(exceptions_KeyError_meta,exceptions_LookupError_meta);
function exceptions_AssertionError_meta () {
}

exceptions_AssertionError_meta.prototype.toString = function (){
    return ( '<exceptions_AssertionError_meta instance>' );
}

inherits(exceptions_AssertionError_meta,exceptions_StandardError_meta);
function py____magic_assertion_AssertionError_meta () {
}

py____magic_assertion_AssertionError_meta.prototype.toString = function (){
    return ( '<py____magic_assertion_AssertionError_meta instance>' );
}

inherits(py____magic_assertion_AssertionError_meta,exceptions_AssertionError_meta);
function exceptions_ValueError_meta () {
}

exceptions_ValueError_meta.prototype.toString = function (){
    return ( '<exceptions_ValueError_meta instance>' );
}

inherits(exceptions_ValueError_meta,exceptions_StandardError_meta);
function py____test_rsession_webjs_Globals_meta () {
}

py____test_rsession_webjs_Globals_meta.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals_meta instance>' );
}

inherits(py____test_rsession_webjs_Globals_meta,Object_meta);
__consts_0 = {};
__consts_0.const_str__71 = ' failures, ';
__consts_0.const_str__33 = "show_host('";
__consts_0.const_str__70 = ' run, ';
__consts_0.const_str__62 = 'a';
__consts_0.const_str__89 = 'class';
__consts_0.const_str__42 = ']';
__consts_0.const_tuple__16 = undefined;
__consts_0.py____test_rsession_webjs_Options__118 = py____test_rsession_webjs_Options;
__consts_0.py____test_rsession_webjs_Options_meta = new py____test_rsession_webjs_Options_meta();
__consts_0.py____test_rsession_webjs_Options = new py____test_rsession_webjs_Options();
__consts_0.const_str__51 = 'ReceivedItemOutcome';
__consts_0.const_str__83 = "show_info('";
__consts_0.const_str__60 = '- skipped (';
__consts_0.const_str__37 = 'hide_host()';
__consts_0.const_str__84 = 'hide_info()';
__consts_0.const_str__27 = '#message';
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__20 = 'tbody';
__consts_0.const_str__79 = 'Py.test [crashed]';
__consts_0.const_str__61 = ')';
__consts_0.const_str__46 = 'main_table';
__consts_0.const_str__82 = 'Tests [interrupted]';
__consts_0.exceptions_KeyError__114 = exceptions_KeyError;
__consts_0.const_str__34 = "')";
__consts_0.const_str__55 = 'RsyncFinished';
__consts_0.exceptions_StopIteration__116 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.const_list__120 = [];
__consts_0.Window = window;
__consts_0.const_str__92 = '_txt_';
__consts_0.exceptions_ValueError__110 = exceptions_ValueError;
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.py____test_rsession_webjs_Globals__121 = py____test_rsession_webjs_Globals;
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.const_str__101 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_str__90 = 'error';
__consts_0.const_str__72 = ' skipped';
__consts_0.const_str__69 = 'FINISHED ';
__consts_0.const_str__40 = 'Rsyncing';
__consts_0.const_str__29 = 'info';
__consts_0.const_str__22 = 'td';
__consts_0.const_str__43 = 'true';
__consts_0.const_tuple__91 = {};
__consts_0.py____magic_assertion_AssertionError__112 = py____magic_assertion_AssertionError;
__consts_0.const_str__88 = 'F';
__consts_0.const_str__36 = 'onmouseout';
__consts_0.const_str__47 = 'type';
__consts_0.const_str__105 = 'length';
__consts_0.const_str__85 = 'passed';
__consts_0.const_str__99 = '.';
__consts_0.const_str__53 = 'FailedTryiter';
__consts_0.const_tuple__93 = {};
__consts_0.const_str__32 = '#ff0000';
__consts_0.const_str__8 = 'checked';
__consts_0.const_str__10 = 'messagebox';
__consts_0.const_str__58 = 'fullitemname';
__consts_0.const_str__107 = 'table';
__consts_0.const_str__64 = 'href';
__consts_0.const_str__68 = 'skips';
__consts_0.const_str__57 = 'CrashedExecution';
__consts_0.const_tuple__28 = {};
__consts_0.const_str__15 = '\n';
__consts_0.const_tuple__18 = undefined;
__consts_0.const_str__5 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.const_str__25 = 'pre';
__consts_0.const_str__81 = 'Py.test [interrupted]';
__consts_0.const_str__13 = '\n======== Stdout: ========\n';
__consts_0.const_str__76 = '#00ff00';
__consts_0.const_str__30 = 'beige';
__consts_0.const_str__98 = 's';
__consts_0.py____magic_assertion_AssertionError_meta = new py____magic_assertion_AssertionError_meta();
__consts_0.const_str__100 = 'traceback';
__consts_0.const_str__45 = 'testmain';
__consts_0.const_str__97 = "javascript:show_skip('";
__consts_0.const_str__78 = '[';
__consts_0.const_str__80 = 'Tests [crashed]';
__consts_0.const_str__59 = 'reason';
__consts_0.const_str__63 = "javascript:show_traceback('";
__consts_0.const_str__39 = 'Tests';
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.const_str__66 = 'run';
__consts_0.const_str__54 = 'SkippedTryiter';
__consts_0.const_str__87 = 'None';
__consts_0.const_str__9 = 'True';
__consts_0.const_str__95 = '/';
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.const_str__75 = 'hostkey';
__consts_0.const_str__67 = 'fails';
__consts_0.const_str__48 = 'ItemStart';
__consts_0.const_str__104 = 'itemname';
__consts_0.const_str__52 = 'TestFinished';
__consts_0.const_str__2 = 'jobs';
__consts_0.const_str__14 = '\n========== Stderr: ==========\n';
__consts_0.py____magic_assertion_AssertionError = new py____magic_assertion_AssertionError();
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_list = undefined;
__consts_0.const_str__102 = 'stderr';
__consts_0.const_str__73 = 'Py.test ';
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.const_str__23 = 'visible';
__consts_0.const_str__96 = 'False';
__consts_0.const_str__50 = 'HostRSyncRootReady';
__consts_0.const_str__35 = 'onmouseover';
__consts_0.const_str__65 = '- FAILED TO LOAD MODULE';
__consts_0.const_str__106 = '[0/';
__consts_0.const_tuple = {};
__consts_0.const_str__49 = 'SendItem';
__consts_0.const_str__74 = 'fullmodulename';
__consts_0.const_str__86 = 'skipped';
__consts_0.const_str__31 = 'hostsbody';
__consts_0.const_str__77 = '[0]';
__consts_0.const_str__3 = 'hidden';
__consts_0.const_str__12 = '====== Traceback: =========\n';
__consts_0.const_str__21 = 'tr';
__consts_0.const_str__103 = 'item_name';
__consts_0.const_str__41 = 'Tests [';
__consts_0.Document = document;
__consts_0.const_tuple__94 = {};
__consts_0.const_str__56 = 'InterruptedExecution';
__consts_0.const_str__7 = 'opt_scroll';
__consts_0.py____test_rsession_webjs_Options_meta.class_ = __consts_0.py____test_rsession_webjs_Options__118;
__consts_0.py____test_rsession_webjs_Options.meta = __consts_0.py____test_rsession_webjs_Options_meta;
__consts_0.py____test_rsession_webjs_Options.oscroll = true;
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__116;
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__110;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__121;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__5;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__5;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ofinished = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple__16;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__120;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__18;
__consts_0.py____magic_assertion_AssertionError_meta.class_ = __consts_0.py____magic_assertion_AssertionError__112;
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__114;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
__consts_0.py____magic_assertion_AssertionError.meta = __consts_0.py____magic_assertion_AssertionError_meta;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
