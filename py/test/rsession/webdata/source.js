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
            v22 = v21.getElementById(__consts_0.const_str__4);
            v23 = v22;
            v23.setAttribute(__consts_0.const_str__5,__consts_0.const_str__6);
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__7;
    this.ohost = __consts_0.const_str__7;
    this.orsync_dots = 0;
    this.ofinished = false;
    this.ohost_dict = __consts_0.const_tuple;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__10;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals instance>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
function hide_messagebox () {
    var v115,v116,mbox_0,v117,v118,mbox_1,v119,v120,v121;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v115 = __consts_0.Document;
            v116 = v115.getElementById(__consts_0.const_str__11);
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

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed (l_1,index_0) {
    var v203,v204,l_2,index_1,v206,v207,v208,index_2,v210,v211,v212;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v204 = (index_0>=0);
            undefined;
            l_2 = l_1;
            index_1 = index_0;
            block = 1;
            break;
            case 1:
            v206 = l_2;
            v207 = v206.length;
            v208 = (index_1<v207);
            undefined;
            index_2 = index_1;
            v210 = l_2;
            block = 2;
            break;
            case 2:
            v211 = v210;
            v212 = v211[index_2];
            v203 = v212;
            block = 3;
            break;
            case 3:
            return ( v203 );
        }
    }
}

function key_pressed (key_1) {
    var v181,v182,v183,v184,v185,v186,v187,v188,v189,v192,v193;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v181 = key_1.charCode;
            v182 = (v181==115);
            v183 = v182;
            if (v183 == false)
            {
                block = 1;
                break;
            }
            block = 2;
            break;
            case 2:
            v184 = __consts_0.Document;
            v185 = v184.getElementById(__consts_0.const_str__4);
            v186 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v187 = v186;
            v188 = v185;
            if (v187 == false)
            {
                block = 3;
                break;
            }
            v192 = v185;
            block = 4;
            break;
            case 3:
            v189 = v188;
            v189.setAttribute(__consts_0.const_str__5,__consts_0.const_str__13);
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 1;
            break;
            case 4:
            v193 = v192;
            v193.removeAttribute(__consts_0.const_str__5);
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 1;
            break;
            case 1:
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
            v66 = v65.getElementById(__consts_0.const_str__14);
            v67 = v66.style;
            v67.visibility = __consts_0.const_str__15;
            block = 1;
            break;
            case 1:
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
            v71 = v70.getElementById(__consts_0.const_str__16);
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
            v74 = create_elem ( __consts_0.const_str__17 );
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
            v81 = create_elem ( __consts_0.const_str__18 );
            v82 = create_elem ( __consts_0.const_str__19 );
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
            v92.visibility = __consts_0.const_str__20;
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

function ll_listnext__Record_index__Signed__iterable_0 (iter_0) {
    var v230,v231,v232,v233,v234,v235,v236,iter_1,index_3,l_3,v237,v239,v240,v241,v242,v243,etype_1,evalue_1;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v231 = iter_0.iterable;
            v232 = iter_0.index;
            v233 = v231;
            v234 = v233.length;
            v235 = (v232>=v234);
            v236 = v235;
            iter_1 = iter_0;
            index_3 = v232;
            l_3 = v231;
            if (v236 == false)
            {
                block = 1;
                break;
            }
            block = 3;
            break;
            case 1:
            v237 = (index_3+1);
            iter_1.index = v237;
            v239 = l_3;
            v240 = v239[index_3];
            v230 = v240;
            block = 2;
            break;
            case 3:
            v241 = __consts_0.exceptions_StopIteration;
            v242 = v241.meta;
            v243 = v241;
            etype_1 = v242;
            evalue_1 = v243;
            block = 4;
            break;
            case 4:
            throw(evalue_1);
            case 2:
            return ( v230 );
        }
    }
}

function show_skip (item_name_0) {
    var v26;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v26 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__22,item_name_0 );
            set_msgbox ( item_name_0,v26 );
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_dict_getitem__Dict_String__List_String___String (d_0,key_2) {
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

function ll_dict_getitem__Dict_String__String__String (d_1,key_4) {
    var v253,v254,v255,v256,v257,v258,v259,etype_2,evalue_2,key_5,v260,v261,v262;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v254 = d_1;
            v255 = (v254[key_4]!=undefined);
            v256 = v255;
            if (v256 == false)
            {
                block = 1;
                break;
            }
            key_5 = key_4;
            v260 = d_1;
            block = 3;
            break;
            case 1:
            v257 = __consts_0.exceptions_KeyError;
            v258 = v257.meta;
            v259 = v257;
            etype_2 = v258;
            evalue_2 = v259;
            block = 2;
            break;
            case 3:
            v261 = v260;
            v262 = v261[key_5];
            v253 = v262;
            block = 4;
            break;
            case 2:
            throw(evalue_2);
            case 4:
            return ( v253 );
        }
    }
}

function create_elem (s_0) {
    var v213,v214,v215;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v214 = __consts_0.Document;
            v215 = v214.createElement(s_0);
            v213 = v215;
            block = 1;
            break;
            case 1:
            return ( v213 );
        }
    }
}

function exceptions_Exception () {
}

exceptions_Exception.prototype.toString = function (){
    return ( '<exceptions_Exception instance>' );
}

inherits(exceptions_Exception,Object);
function exceptions_StandardError () {
}

exceptions_StandardError.prototype.toString = function (){
    return ( '<exceptions_StandardError instance>' );
}

inherits(exceptions_StandardError,exceptions_Exception);
function exceptions_LookupError () {
}

exceptions_LookupError.prototype.toString = function (){
    return ( '<exceptions_LookupError instance>' );
}

inherits(exceptions_LookupError,exceptions_StandardError);
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

function reshow_host () {
    var v248,v249,v250,v251;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v248 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v249 = ll_streq__String_String ( v248,__consts_0.const_str__7 );
            v250 = v249;
            if (v250 == false)
            {
                block = 1;
                break;
            }
            block = 2;
            break;
            case 1:
            v251 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v251 );
            block = 2;
            break;
            case 2:
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
            v48 = v47.getElementById(__consts_0.const_str__14);
            v49 = v48.style;
            v49.visibility = __consts_0.const_str__20;
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
            v58.backgroundColor = __consts_0.const_str__24;
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

function ll_list_is_true__List_ExternalType_ (l_0) {
    var v196,v197,v198,v199,v200,v201,v202;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v197 = !!l_0;
            v198 = v197;
            v196 = v197;
            if (v198 == false)
            {
                block = 1;
                break;
            }
            v199 = l_0;
            block = 2;
            break;
            case 2:
            v200 = v199;
            v201 = v200.length;
            v202 = (v201!=0);
            v196 = v202;
            block = 1;
            break;
            case 1:
            return ( v196 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_String_ (lst_0) {
    var v226,v227;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v227 = new Object();
            v227.iterable = lst_0;
            v227.index = 0;
            v226 = v227;
            block = 1;
            break;
            case 1:
            return ( v226 );
        }
    }
}

function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions_StopIteration instance>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
function py____test_rsession_webjs_Options () {
    this.oscroll = false;
}

py____test_rsession_webjs_Options.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Options instance>' );
}

inherits(py____test_rsession_webjs_Options,Object);
function show_traceback (item_name_1) {
    var v29,v30,v31,v32,v33,v35,v38,v41,v44;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v29 = ll_dict_getitem__Dict_String__Record_item2__Str_String ( __consts_0.const_tuple__25,item_name_1 );
            v30 = v29.item0;
            v31 = v29.item1;
            v32 = v29.item2;
            v33 = new StringBuilder();
            v33.ll_append(__consts_0.const_str__26);
            v35 = ll_str__StringR_StringConst_String ( v30 );
            v33.ll_append(v35);
            v33.ll_append(__consts_0.const_str__27);
            v38 = ll_str__StringR_StringConst_String ( v31 );
            v33.ll_append(v38);
            v33.ll_append(__consts_0.const_str__28);
            v41 = ll_str__StringR_StringConst_String ( v32 );
            v33.ll_append(v41);
            v33.ll_append(__consts_0.const_str__29);
            v44 = v33.ll_build();
            set_msgbox ( item_name_1,v44 );
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function exceptions_KeyError () {
}

exceptions_KeyError.prototype.toString = function (){
    return ( '<exceptions_KeyError instance>' );
}

inherits(exceptions_KeyError,exceptions_LookupError);
function host_init (host_dict_0) {
    var v129,v130,v131,v132,v133,host_dict_1,tbody_3,v134,v135,last_exc_value_1,host_dict_2,tbody_4,host_0,v136,v137,v138,v140,v141,v143,v144,v145,v148,v150,v151,v153,v156,v158,host_dict_3,v164,v166,v167,v168,v169,v170,last_exc_value_2,key_0,v171,v172,v174;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v129 = __consts_0.Document;
            v130 = v129.getElementById(__consts_0.const_str__30);
            v131 = host_dict_0;
            v132 = ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst ( v131 );
            v133 = ll_listiter__Record_index__Signed__iterable_List_String_ ( v132 );
            host_dict_1 = host_dict_0;
            tbody_3 = v130;
            v134 = v133;
            block = 1;
            break;
            case 1:
            try {
                v135 = ll_listnext__Record_index__Signed__iterable_0 ( v134 );
                host_dict_2 = host_dict_1;
                tbody_4 = tbody_3;
                host_0 = v135;
                v136 = v134;
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
            v137 = create_elem ( __consts_0.const_str__18 );
            v138 = tbody_4;
            v138.appendChild(v137);
            v140 = create_elem ( __consts_0.const_str__19 );
            v141 = v140.style;
            v141.background = __consts_0.const_str__31;
            v143 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v144 = create_text_elem ( v143 );
            v145 = v140;
            v145.appendChild(v144);
            v140.id = host_0;
            v148 = v137;
            v148.appendChild(v140);
            v150 = v140;
            v151 = new StringBuilder();
            v151.ll_append(__consts_0.const_str__32);
            v153 = ll_str__StringR_StringConst_String ( host_0 );
            v151.ll_append(v153);
            v151.ll_append(__consts_0.const_str__33);
            v156 = v151.ll_build();
            v150.setAttribute(__consts_0.const_str__34,v156);
            v158 = v140;
            v158.setAttribute(__consts_0.const_str__35,__consts_0.const_str__36);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
            setTimeout ( 'update_rsync()',1000 );
            host_dict_1 = host_dict_2;
            tbody_3 = tbody_4;
            v134 = v136;
            block = 1;
            break;
            case 3:
            __consts_0.py____test_rsession_webjs_Globals.ohost_dict = host_dict_3;
            v164 = ll_newdict__Dict_String__List_String__LlT (  );
            __consts_0.py____test_rsession_webjs_Globals.ohost_pending = v164;
            v166 = host_dict_3;
            v167 = ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst ( v166 );
            v168 = ll_listiter__Record_index__Signed__iterable_List_String_ ( v167 );
            v169 = v168;
            block = 4;
            break;
            case 4:
            try {
                v170 = ll_listnext__Record_index__Signed__iterable_0 ( v169 );
                key_0 = v170;
                v171 = v169;
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
            v172 = new Array();
            v172.length = 0;
            v174 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v174[key_0]=v172;
            v169 = v171;
            block = 4;
            break;
            case 6:
            return ( undefined );
        }
    }
}

function sessid_comeback (id_0) {
    var v178,v179;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.osessid = id_0;
            v178 = __consts_0.ExportedMethods;
            v179 = v178.show_all_statuses(id_0,comeback);
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function set_msgbox (item_name_2,data_3) {
    var v264,item_name_3,data_4,msgbox_0,v265,v266,v267,item_name_4,data_5,msgbox_1,v268,v269,v270,v271,v272,v274,v276,v277,item_name_5,data_6,msgbox_2,v280,v281,v282;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v264 = get_elem ( __consts_0.const_str__11 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v264;
            block = 1;
            break;
            case 1:
            v265 = msgbox_0.childNodes;
            v266 = ll_len__List_ExternalType_ ( v265 );
            v267 = !!v266;
            item_name_4 = item_name_3;
            data_5 = data_4;
            msgbox_1 = msgbox_0;
            if (v267 == false)
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
            v268 = create_elem ( __consts_0.const_str__37 );
            v269 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__29 );
            v270 = ll_strconcat__String_String ( v269,data_5 );
            v271 = create_text_elem ( v270 );
            v272 = v268;
            v272.appendChild(v271);
            v274 = msgbox_1;
            v274.appendChild(v268);
            v276 = __consts_0.Window.location;
            v277 = v276;
            v277.assign(__consts_0.const_str__39);
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 4:
            v280 = msgbox_2;
            v281 = msgbox_2.childNodes;
            v282 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v281,0 );
            v280.removeChild(v282);
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

function hide_host () {
    var v101,v102,elem_5,v103,v104,v105,v106,v107,elem_6,v110,v111,v112;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v101 = __consts_0.Document;
            v102 = v101.getElementById(__consts_0.const_str__16);
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
            v107.visibility = __consts_0.const_str__15;
            __consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__7;
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

function ll_streq__String_String (s1_0,s2_0) {
    var v284,v285,v286,v287,s2_1,v288,v289,v290,v291,v292,v293;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v285 = !!s1_0;
            v286 = !v285;
            v287 = v286;
            s2_1 = s2_0;
            v288 = s1_0;
            if (v287 == false)
            {
                block = 1;
                break;
            }
            v291 = s2_0;
            block = 3;
            break;
            case 1:
            v289 = v288;
            v290 = (v289==s2_1);
            v284 = v290;
            block = 2;
            break;
            case 3:
            v292 = !!v291;
            v293 = !v292;
            v284 = v293;
            block = 2;
            break;
            case 2:
            return ( v284 );
        }
    }
}

function create_text_elem (txt_0) {
    var v244,v245,v246;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v245 = __consts_0.Document;
            v246 = v245.createTextNode(txt_0);
            v244 = v246;
            block = 1;
            break;
            case 1:
            return ( v244 );
        }
    }
}

function ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst (d_3) {
    var v308,v309,v310,v311,v312,v313,i_0,it_0,length_0,result_0,v314,v315,v316,result_1,v317,v318,v319,v320,v321,v322,v323,etype_4,evalue_4,i_1,it_1,length_1,result_2,v324,v325,v326,it_2,length_2,result_3,v328,v329;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v309 = d_3;
            v310 = get_dict_len ( v309 );
            v311 = ll_newlist__List_String_LlT_Signed ( v310 );
            v312 = d_3;
            v313 = dict_items_iterator ( v312 );
            i_0 = 0;
            it_0 = v313;
            length_0 = v310;
            result_0 = v311;
            block = 1;
            break;
            case 1:
            v314 = it_0;
            v315 = v314.ll_go_next();
            v316 = v315;
            result_1 = result_0;
            v317 = i_0;
            v318 = length_0;
            if (v316 == false)
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
            v319 = (v317==v318);
            v320 = v319;
            if (v320 == false)
            {
                block = 3;
                break;
            }
            v308 = result_1;
            block = 5;
            break;
            case 3:
            v321 = __consts_0.exceptions_AssertionError;
            v322 = v321.meta;
            v323 = v321;
            etype_4 = v322;
            evalue_4 = v323;
            block = 4;
            break;
            case 6:
            v324 = result_2;
            v325 = it_1;
            v326 = v325.ll_current_key();
            v324[i_1]=v326;
            it_2 = it_1;
            length_2 = length_1;
            result_3 = result_2;
            v328 = i_1;
            block = 7;
            break;
            case 7:
            v329 = (v328+1);
            i_0 = v329;
            it_0 = it_2;
            length_0 = length_2;
            result_0 = result_3;
            block = 1;
            break;
            case 4:
            throw(evalue_4);
            case 5:
            return ( v308 );
        }
    }
}

function exceptions_AssertionError () {
}

exceptions_AssertionError.prototype.toString = function (){
    return ( '<exceptions_AssertionError instance>' );
}

inherits(exceptions_AssertionError,exceptions_StandardError);
function ll_len__List_ExternalType_ (l_4) {
    var v294,v295,v296;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v295 = l_4;
            v296 = v295.length;
            v294 = v296;
            block = 1;
            break;
            case 1:
            return ( v294 );
        }
    }
}

function ll_newdict__Dict_String__List_String__LlT () {
    var v364,v365;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v365 = new Object();
            v364 = v365;
            block = 1;
            break;
            case 1:
            return ( v364 );
        }
    }
}

function get_elem (el_0) {
    var v393,v394,v395;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v394 = __consts_0.Document;
            v395 = v394.getElementById(el_0);
            v393 = v395;
            block = 1;
            break;
            case 1:
            return ( v393 );
        }
    }
}

function update_rsync () {
    var v331,v332,v333,v334,v335,v336,v337,v338,elem_7,v339,v340,v341,v342,v343,v345,v346,v347,elem_8,v348,v349,v351,v354,v355,v356,text_0,elem_9,v360,v361,v362;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v331 = __consts_0.py____test_rsession_webjs_Globals.ofinished;
            v332 = v331;
            if (v332 == false)
            {
                block = 1;
                break;
            }
            block = 4;
            break;
            case 1:
            v333 = __consts_0.Document;
            v334 = v333.getElementById(__consts_0.const_str__41);
            v335 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v336 = v335;
            v337 = (v336==1);
            v338 = v337;
            elem_7 = v334;
            if (v338 == false)
            {
                block = 2;
                break;
            }
            v360 = v334;
            block = 6;
            break;
            case 2:
            v339 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v340 = ll_char_mul__Char_Signed ( '.',v339 );
            v341 = ll_strconcat__String_String ( __consts_0.const_str__42,v340 );
            v342 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v343 = (v342+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v343;
            v345 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v346 = (v345>5);
            v347 = v346;
            elem_8 = elem_7;
            v348 = v341;
            if (v347 == false)
            {
                block = 3;
                break;
            }
            text_0 = v341;
            elem_9 = elem_7;
            block = 5;
            break;
            case 3:
            v349 = new StringBuilder();
            v349.ll_append(__consts_0.const_str__43);
            v351 = ll_str__StringR_StringConst_String ( v348 );
            v349.ll_append(v351);
            v349.ll_append(__consts_0.const_str__44);
            v354 = v349.ll_build();
            v355 = elem_8.childNodes;
            v356 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v355,0 );
            v356.nodeValue = v354;
            setTimeout ( 'update_rsync()',1000 );
            block = 4;
            break;
            case 5:
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            elem_8 = elem_9;
            v348 = text_0;
            block = 3;
            break;
            case 6:
            v361 = v360.childNodes;
            v362 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v361,0 );
            v362.nodeValue = __consts_0.const_str__41;
            block = 4;
            break;
            case 4:
            return ( undefined );
        }
    }
}

function ll_dict_getitem__Dict_String__Record_item2__Str_String (d_2,key_6) {
    var v297,v298,v299,v300,v301,v302,v303,etype_3,evalue_3,key_7,v304,v305,v306;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v298 = d_2;
            v299 = (v298[key_6]!=undefined);
            v300 = v299;
            if (v300 == false)
            {
                block = 1;
                break;
            }
            key_7 = key_6;
            v304 = d_2;
            block = 3;
            break;
            case 1:
            v301 = __consts_0.exceptions_KeyError;
            v302 = v301.meta;
            v303 = v301;
            etype_3 = v302;
            evalue_3 = v303;
            block = 2;
            break;
            case 3:
            v305 = v304;
            v306 = v305[key_7];
            v297 = v306;
            block = 4;
            break;
            case 2:
            throw(evalue_3);
            case 4:
            return ( v297 );
        }
    }
}

function ll_str__StringR_StringConst_String (s_1) {
    var v307;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v307 = s_1;
            block = 1;
            break;
            case 1:
            return ( v307 );
        }
    }
}

function comeback (msglist_0) {
    var v367,v368,v369,msglist_1,v370,v371,v372,v373,msglist_2,v374,v375,last_exc_value_3,msglist_3,v376,v377,v378,v379,msglist_4,v380,v383,v384,v385,last_exc_value_4,v386,v387,v388,v389,v390,v391,v392;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v367 = ll_len__List_Dict_String__String__ ( msglist_0 );
            v368 = (v367==0);
            v369 = v368;
            msglist_1 = msglist_0;
            if (v369 == false)
            {
                block = 1;
                break;
            }
            block = 4;
            break;
            case 1:
            v370 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v371 = 0;
            v372 = ll_listslice_startonly__List_Dict_String__String__LlT_List_Dict_String__String___Signed ( v370,v371 );
            v373 = ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ ( v372 );
            msglist_2 = msglist_1;
            v374 = v373;
            block = 2;
            break;
            case 2:
            try {
                v375 = ll_listnext__Record_index__Signed__iterable ( v374 );
                msglist_3 = msglist_2;
                v376 = v374;
                v377 = v375;
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
            v378 = process ( v377 );
            v379 = v378;
            if (v379 == false)
            {
                block = 4;
                break;
            }
            msglist_2 = msglist_3;
            v374 = v376;
            block = 2;
            break;
            case 5:
            v380 = new Array();
            v380.length = 0;
            __consts_0.py____test_rsession_webjs_Globals.opending = v380;
            v383 = ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ ( msglist_4 );
            v384 = v383;
            block = 6;
            break;
            case 6:
            try {
                v385 = ll_listnext__Record_index__Signed__iterable ( v384 );
                v386 = v384;
                v387 = v385;
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
            v388 = process ( v387 );
            v389 = v388;
            if (v389 == false)
            {
                block = 4;
                break;
            }
            v384 = v386;
            block = 6;
            break;
            case 8:
            v390 = __consts_0.ExportedMethods;
            v391 = __consts_0.py____test_rsession_webjs_Globals.osessid;
            v392 = v390.show_all_statuses(v391,comeback);
            block = 4;
            break;
            case 4:
            return ( undefined );
        }
    }
}

function ll_strconcat__String_String (obj_0,arg0_0) {
    var v396,v397,v398;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v397 = obj_0;
            v398 = (v397+arg0_0);
            v396 = v398;
            block = 1;
            break;
            case 1:
            return ( v396 );
        }
    }
}

function ll_char_mul__Char_Signed (ch_0,times_0) {
    var v403,v404,v405,ch_1,times_1,i_2,buf_0,v407,v408,v409,v410,v411,ch_2,times_2,i_3,buf_1,v412,v414;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v404 = new StringBuilder();
            v405 = v404;
            v405.ll_allocate(times_0);
            ch_1 = ch_0;
            times_1 = times_0;
            i_2 = 0;
            buf_0 = v404;
            block = 1;
            break;
            case 1:
            v407 = (i_2<times_1);
            v408 = v407;
            v409 = buf_0;
            if (v408 == false)
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
            v410 = v409;
            v411 = v410.ll_build();
            v403 = v411;
            block = 3;
            break;
            case 4:
            v412 = buf_1;
            v412.ll_append_char(ch_2);
            v414 = (i_3+1);
            ch_1 = ch_2;
            times_1 = times_2;
            i_2 = v414;
            buf_0 = buf_1;
            block = 1;
            break;
            case 3:
            return ( v403 );
        }
    }
}

function ll_len__List_Dict_String__String__ (l_5) {
    var v415,v416,v417;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v416 = l_5;
            v417 = v416.length;
            v415 = v417;
            block = 1;
            break;
            case 1:
            return ( v415 );
        }
    }
}

function ll_newlist__List_String_LlT_Signed (length_3) {
    var v399,v400,v401;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v400 = new Array();
            v401 = v400;
            v401.length = length_3;
            v399 = v400;
            block = 1;
            break;
            case 1:
            return ( v399 );
        }
    }
}

function ll_listnext__Record_index__Signed__iterable (iter_2) {
    var v440,v441,v442,v443,v444,v445,v446,iter_3,index_4,l_8,v447,v449,v450,v451,v452,v453,etype_5,evalue_5;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v441 = iter_2.iterable;
            v442 = iter_2.index;
            v443 = v441;
            v444 = v443.length;
            v445 = (v442>=v444);
            v446 = v445;
            iter_3 = iter_2;
            index_4 = v442;
            l_8 = v441;
            if (v446 == false)
            {
                block = 1;
                break;
            }
            block = 3;
            break;
            case 1:
            v447 = (index_4+1);
            iter_3.index = v447;
            v449 = l_8;
            v450 = v449[index_4];
            v440 = v450;
            block = 2;
            break;
            case 3:
            v451 = __consts_0.exceptions_StopIteration;
            v452 = v451.meta;
            v453 = v451;
            etype_5 = v452;
            evalue_5 = v453;
            block = 4;
            break;
            case 4:
            throw(evalue_5);
            case 2:
            return ( v440 );
        }
    }
}

function ll_listslice_startonly__List_Dict_String__String__LlT_List_Dict_String__String___Signed (l1_0,start_0) {
    var v418,v419,v420,v421,v423,v425,v427,l1_1,i_4,j_0,l_6,len1_0,v428,v429,l1_2,i_5,j_1,l_7,len1_1,v430,v431,v432,v434,v435;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v419 = l1_0;
            v420 = v419.length;
            v421 = (start_0>=0);
            undefined;
            v423 = (start_0<=v420);
            undefined;
            v425 = (v420-start_0);
            undefined;
            v427 = ll_newlist__List_Dict_String__String__LlT_Signed ( v425 );
            l1_1 = l1_0;
            i_4 = start_0;
            j_0 = 0;
            l_6 = v427;
            len1_0 = v420;
            block = 1;
            break;
            case 1:
            v428 = (i_4<len1_0);
            v429 = v428;
            v418 = l_6;
            if (v429 == false)
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
            v430 = l_7;
            v431 = l1_2;
            v432 = v431[i_5];
            v430[j_1]=v432;
            v434 = (i_5+1);
            v435 = (j_1+1);
            l1_1 = l1_2;
            i_4 = v434;
            j_0 = v435;
            l_6 = l_7;
            len1_0 = len1_1;
            block = 1;
            break;
            case 2:
            return ( v418 );
        }
    }
}

function process (msg_0) {
    var v454,v455,v456,v457,msg_1,v458,v459,v460,v461,v462,v463,v464,msg_2,v465,v466,v467,msg_3,v468,v469,v470,msg_4,v471,v472,v473,msg_5,v474,v475,v476,msg_6,v477,v478,v479,msg_7,v480,v481,v482,msg_8,v483,v484,v485,msg_9,v486,v487,v488,v489,v490,v491,v492,v493,v494,v495,v496,msg_10,v501,v502,v503,msg_11,v504,v505,msg_12,module_part_0,v507,v508,v509,v510,v512,v513,v515,v518,v519,v520,v522,v524,msg_13,v526,v527,v528,msg_14,v529,v530,msg_15,module_part_1,v532,v533,v534,v535,v536,v537,v539,v540,v542,v545,v547,v548,v550,v552,v554,v556,v557,v558,msg_16,v559,v560,v561,v562,v566,v567,v568,v569,v571,v574,v577,v580,v582,v584,v586,v588,v590,v593,v594,v595,v596,v597,msg_17,v599,v600,v601,msg_18,v602,v603,v605,v606,msg_19,v608,v609,v610,v611,v613,v614,v615,v616,v618,v619,v620,v623,v624,v625,msg_20,v627,v628,v629,v630,v631,v632,v633,v634,v636,v637,v638,v639,v640,v641,v642,v643,v646,v647,v648,v649,v652,v655,v656,v657,main_t_0,v659,v660,v661;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v455 = get_dict_len ( msg_0 );
            v456 = (v455==0);
            v457 = v456;
            msg_1 = msg_0;
            if (v457 == false)
            {
                block = 1;
                break;
            }
            v454 = false;
            block = 12;
            break;
            case 1:
            v458 = __consts_0.Document;
            v459 = v458.getElementById(__consts_0.const_str__45);
            v460 = __consts_0.Document;
            v461 = v460.getElementById(__consts_0.const_str__46);
            v462 = ll_dict_getitem__Dict_String__String__String ( msg_1,__consts_0.const_str__47 );
            v463 = ll_streq__String_String ( v462,__consts_0.const_str__48 );
            v464 = v463;
            msg_2 = msg_1;
            if (v464 == false)
            {
                block = 2;
                break;
            }
            main_t_0 = v461;
            v659 = msg_1;
            block = 29;
            break;
            case 2:
            v465 = ll_dict_getitem__Dict_String__String__String ( msg_2,__consts_0.const_str__47 );
            v466 = ll_streq__String_String ( v465,__consts_0.const_str__49 );
            v467 = v466;
            msg_3 = msg_2;
            if (v467 == false)
            {
                block = 3;
                break;
            }
            msg_20 = msg_2;
            block = 28;
            break;
            case 3:
            v468 = ll_dict_getitem__Dict_String__String__String ( msg_3,__consts_0.const_str__47 );
            v469 = ll_streq__String_String ( v468,__consts_0.const_str__50 );
            v470 = v469;
            msg_4 = msg_3;
            if (v470 == false)
            {
                block = 4;
                break;
            }
            msg_19 = msg_3;
            block = 27;
            break;
            case 4:
            v471 = ll_dict_getitem__Dict_String__String__String ( msg_4,__consts_0.const_str__47 );
            v472 = ll_streq__String_String ( v471,__consts_0.const_str__51 );
            v473 = v472;
            msg_5 = msg_4;
            if (v473 == false)
            {
                block = 5;
                break;
            }
            msg_17 = msg_4;
            block = 24;
            break;
            case 5:
            v474 = ll_dict_getitem__Dict_String__String__String ( msg_5,__consts_0.const_str__47 );
            v475 = ll_streq__String_String ( v474,__consts_0.const_str__52 );
            v476 = v475;
            msg_6 = msg_5;
            if (v476 == false)
            {
                block = 6;
                break;
            }
            msg_16 = msg_5;
            block = 23;
            break;
            case 6:
            v477 = ll_dict_getitem__Dict_String__String__String ( msg_6,__consts_0.const_str__47 );
            v478 = ll_streq__String_String ( v477,__consts_0.const_str__53 );
            v479 = v478;
            msg_7 = msg_6;
            if (v479 == false)
            {
                block = 7;
                break;
            }
            msg_13 = msg_6;
            block = 20;
            break;
            case 7:
            v480 = ll_dict_getitem__Dict_String__String__String ( msg_7,__consts_0.const_str__47 );
            v481 = ll_streq__String_String ( v480,__consts_0.const_str__54 );
            v482 = v481;
            msg_8 = msg_7;
            if (v482 == false)
            {
                block = 8;
                break;
            }
            msg_10 = msg_7;
            block = 17;
            break;
            case 8:
            v483 = ll_dict_getitem__Dict_String__String__String ( msg_8,__consts_0.const_str__47 );
            v484 = ll_streq__String_String ( v483,__consts_0.const_str__55 );
            v485 = v484;
            msg_9 = msg_8;
            if (v485 == false)
            {
                block = 9;
                break;
            }
            block = 16;
            break;
            case 9:
            v486 = ll_dict_getitem__Dict_String__String__String ( msg_9,__consts_0.const_str__47 );
            v487 = ll_streq__String_String ( v486,__consts_0.const_str__56 );
            v488 = v487;
            v489 = msg_9;
            if (v488 == false)
            {
                block = 10;
                break;
            }
            block = 15;
            break;
            case 10:
            v490 = ll_dict_getitem__Dict_String__String__String ( v489,__consts_0.const_str__47 );
            v491 = ll_streq__String_String ( v490,__consts_0.const_str__57 );
            v492 = v491;
            if (v492 == false)
            {
                block = 11;
                break;
            }
            block = 14;
            break;
            case 11:
            v493 = __consts_0.py____test_rsession_webjs_Globals.odata_empty;
            v494 = v493;
            v454 = true;
            if (v494 == false)
            {
                block = 12;
                break;
            }
            block = 13;
            break;
            case 13:
            v495 = __consts_0.Document;
            v496 = v495.getElementById(__consts_0.const_str__11);
            scroll_down_if_needed ( v496 );
            v454 = true;
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
            v501 = ll_dict_getitem__Dict_String__String__String ( msg_10,__consts_0.const_str__58 );
            v502 = get_elem ( v501 );
            v503 = !!v502;
            msg_11 = msg_10;
            if (v503 == false)
            {
                block = 18;
                break;
            }
            msg_12 = msg_10;
            module_part_0 = v502;
            block = 19;
            break;
            case 18:
            v504 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v505 = v504;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v505,msg_11 );
            v454 = true;
            block = 12;
            break;
            case 19:
            v507 = create_elem ( __consts_0.const_str__18 );
            v508 = create_elem ( __consts_0.const_str__19 );
            v509 = ll_dict_getitem__Dict_String__String__String ( msg_12,__consts_0.const_str__59 );
            v510 = new Object();
            v510.item0 = v509;
            v512 = v510.item0;
            v513 = new StringBuilder();
            v513.ll_append(__consts_0.const_str__60);
            v515 = ll_str__StringR_StringConst_String ( v512 );
            v513.ll_append(v515);
            v513.ll_append(__consts_0.const_str__61);
            v518 = v513.ll_build();
            v519 = create_text_elem ( v518 );
            v520 = v508;
            v520.appendChild(v519);
            v522 = v507;
            v522.appendChild(v508);
            v524 = module_part_0;
            v524.appendChild(v507);
            block = 11;
            break;
            case 20:
            v526 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__58 );
            v527 = get_elem ( v526 );
            v528 = !!v527;
            msg_14 = msg_13;
            if (v528 == false)
            {
                block = 21;
                break;
            }
            msg_15 = msg_13;
            module_part_1 = v527;
            block = 22;
            break;
            case 21:
            v529 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v530 = v529;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v530,msg_14 );
            v454 = true;
            block = 12;
            break;
            case 22:
            v532 = create_elem ( __consts_0.const_str__18 );
            v533 = create_elem ( __consts_0.const_str__19 );
            v534 = create_elem ( __consts_0.const_str__62 );
            v535 = v534;
            v536 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__58 );
            v537 = new Object();
            v537.item0 = v536;
            v539 = v537.item0;
            v540 = new StringBuilder();
            v540.ll_append(__consts_0.const_str__63);
            v542 = ll_str__StringR_StringConst_String ( v539 );
            v540.ll_append(v542);
            v540.ll_append(__consts_0.const_str__33);
            v545 = v540.ll_build();
            v535.setAttribute(__consts_0.const_str__64,v545);
            v547 = create_text_elem ( __consts_0.const_str__65 );
            v548 = v534;
            v548.appendChild(v547);
            v550 = v533;
            v550.appendChild(v534);
            v552 = v532;
            v552.appendChild(v533);
            v554 = module_part_1;
            v554.appendChild(v532);
            v556 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__58 );
            v557 = __consts_0.ExportedMethods;
            v558 = v557.show_fail(v556,fail_come_back);
            block = 11;
            break;
            case 23:
            v559 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__66 );
            v560 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__67 );
            v561 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__68 );
            v562 = new Object();
            v562.item0 = v559;
            v562.item1 = v560;
            v562.item2 = v561;
            v566 = v562.item0;
            v567 = v562.item1;
            v568 = v562.item2;
            v569 = new StringBuilder();
            v569.ll_append(__consts_0.const_str__69);
            v571 = ll_str__StringR_StringConst_String ( v566 );
            v569.ll_append(v571);
            v569.ll_append(__consts_0.const_str__70);
            v574 = ll_str__StringR_StringConst_String ( v567 );
            v569.ll_append(v574);
            v569.ll_append(__consts_0.const_str__71);
            v577 = ll_str__StringR_StringConst_String ( v568 );
            v569.ll_append(v577);
            v569.ll_append(__consts_0.const_str__72);
            v580 = v569.ll_build();
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            v582 = new StringBuilder();
            v582.ll_append(__consts_0.const_str__73);
            v584 = ll_str__StringR_StringConst_String ( v580 );
            v582.ll_append(v584);
            v586 = v582.ll_build();
            __consts_0.Document.title = v586;
            v588 = new StringBuilder();
            v588.ll_append(__consts_0.const_str__43);
            v590 = ll_str__StringR_StringConst_String ( v580 );
            v588.ll_append(v590);
            v588.ll_append(__consts_0.const_str__44);
            v593 = v588.ll_build();
            v594 = __consts_0.Document;
            v595 = v594.getElementById(__consts_0.const_str__41);
            v596 = v595.childNodes;
            v597 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v596,0 );
            v597.nodeValue = v593;
            block = 11;
            break;
            case 24:
            v599 = ll_dict_getitem__Dict_String__String__String ( msg_17,__consts_0.const_str__74 );
            v600 = get_elem ( v599 );
            v601 = !!v600;
            msg_18 = msg_17;
            if (v601 == false)
            {
                block = 25;
                break;
            }
            v605 = msg_17;
            v606 = v600;
            block = 26;
            break;
            case 25:
            v602 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v603 = v602;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v603,msg_18 );
            v454 = true;
            block = 12;
            break;
            case 26:
            add_received_item_outcome ( v605,v606 );
            block = 11;
            break;
            case 27:
            v608 = __consts_0.Document;
            v609 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__75 );
            v610 = v608.getElementById(v609);
            v611 = v610.style;
            v611.background = __consts_0.const_str__76;
            v613 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v614 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__75 );
            v615 = ll_dict_getitem__Dict_String__String__String ( v613,v614 );
            v616 = new Object();
            v616.item0 = v615;
            v618 = v616.item0;
            v619 = new StringBuilder();
            v620 = ll_str__StringR_StringConst_String ( v618 );
            v619.ll_append(v620);
            v619.ll_append(__consts_0.const_str__77);
            v623 = v619.ll_build();
            v624 = v610.childNodes;
            v625 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v624,0 );
            v625.nodeValue = v623;
            block = 11;
            break;
            case 28:
            v627 = __consts_0.Document;
            v628 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v629 = v627.getElementById(v628);
            v630 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v631 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v632 = ll_dict_getitem__Dict_String__List_String___String ( v630,v631 );
            v633 = v632;
            v634 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__58 );
            ll_prepend__List_String__String ( v633,v634 );
            v636 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v637 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v638 = ll_dict_getitem__Dict_String__List_String___String ( v636,v637 );
            v639 = ll_len__List_String_ ( v638 );
            v640 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v641 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v642 = ll_dict_getitem__Dict_String__String__String ( v640,v641 );
            v643 = new Object();
            v643.item0 = v642;
            v643.item1 = v639;
            v646 = v643.item0;
            v647 = v643.item1;
            v648 = new StringBuilder();
            v649 = ll_str__StringR_StringConst_String ( v646 );
            v648.ll_append(v649);
            v648.ll_append(__consts_0.const_str__78);
            v652 = ll_int_str__IntegerR_SignedConst_Signed ( v647 );
            v648.ll_append(v652);
            v648.ll_append(__consts_0.const_str__44);
            v655 = v648.ll_build();
            v656 = v629.childNodes;
            v657 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v656,0 );
            v657.nodeValue = v655;
            block = 11;
            break;
            case 29:
            v660 = make_module_box ( v659 );
            v661 = main_t_0;
            v661.appendChild(v660);
            block = 11;
            break;
            case 12:
            return ( v454 );
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

function ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ (lst_1) {
    var v436,v437;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v437 = new Object();
            v437.iterable = lst_1;
            v437.index = 0;
            v436 = v437;
            block = 1;
            break;
            case 1:
            return ( v436 );
        }
    }
}

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

function fail_come_back (msg_21) {
    var v697,v698,v699,v700,v704;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v697 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__79 );
            v698 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__80 );
            v699 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__81 );
            v700 = new Object();
            v700.item0 = v697;
            v700.item1 = v698;
            v700.item2 = v699;
            v704 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__82 );
            __consts_0.const_tuple__25[v704]=v700;
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
            v878 = create_elem ( __consts_0.const_str__18 );
            v879 = create_elem ( __consts_0.const_str__19 );
            v880 = v878;
            v880.appendChild(v879);
            v882 = v879;
            v883 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__83 );
            v884 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__84 );
            v885 = new Object();
            v885.item0 = v883;
            v885.item1 = v884;
            v888 = v885.item0;
            v889 = v885.item1;
            v890 = new StringBuilder();
            v891 = ll_str__StringR_StringConst_String ( v888 );
            v890.ll_append(v891);
            v890.ll_append(__consts_0.const_str__85);
            v894 = ll_str__StringR_StringConst_String ( v889 );
            v890.ll_append(v894);
            v890.ll_append(__consts_0.const_str__44);
            v897 = v890.ll_build();
            v898 = create_text_elem ( v897 );
            v882.appendChild(v898);
            v900 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__84 );
            v901 = ll_int__String_Signed ( v900,10 );
            v902 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__86[v902]=v901;
            v904 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__83 );
            v905 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__87[v905]=v904;
            v907 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v908 = ll_strconcat__String_String ( __consts_0.const_str__88,v907 );
            v879.id = v908;
            v910 = v879;
            v911 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v912 = new Object();
            v912.item0 = v911;
            v914 = v912.item0;
            v915 = new StringBuilder();
            v915.ll_append(__consts_0.const_str__89);
            v917 = ll_str__StringR_StringConst_String ( v914 );
            v915.ll_append(v917);
            v915.ll_append(__consts_0.const_str__33);
            v920 = v915.ll_build();
            v910.setAttribute(__consts_0.const_str__34,v920);
            v922 = v879;
            v922.setAttribute(__consts_0.const_str__35,__consts_0.const_str__90);
            v924 = create_elem ( __consts_0.const_str__19 );
            v925 = v878;
            v925.appendChild(v924);
            v927 = create_elem ( __consts_0.const_str__91 );
            v928 = v924;
            v928.appendChild(v927);
            v930 = create_elem ( __consts_0.const_str__17 );
            v931 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v930.id = v931;
            v933 = v927;
            v933.appendChild(v930);
            v935 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__92[v935]=0;
            v877 = v878;
            block = 1;
            break;
            case 1:
            return ( v877 );
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

function show_crash () {
    var v675,v676,v677,v678;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__93;
            v675 = __consts_0.Document;
            v676 = v675.getElementById(__consts_0.const_str__41);
            v677 = v676.childNodes;
            v678 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v677,0 );
            v678.nodeValue = __consts_0.const_str__94;
            block = 1;
            break;
            case 1:
            return ( undefined );
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
            v710 = create_elem ( __consts_0.const_str__19 );
            v711 = v710;
            v712 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__58 );
            v713 = new Object();
            v713.item0 = v712;
            v715 = v713.item0;
            v716 = new StringBuilder();
            v716.ll_append(__consts_0.const_str__89);
            v718 = ll_str__StringR_StringConst_String ( v715 );
            v716.ll_append(v718);
            v716.ll_append(__consts_0.const_str__33);
            v721 = v716.ll_build();
            v711.setAttribute(__consts_0.const_str__34,v721);
            v723 = v710;
            v723.setAttribute(__consts_0.const_str__35,__consts_0.const_str__90);
            v725 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__58 );
            v726 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__95 );
            v727 = ll_streq__String_String ( v726,__consts_0.const_str__6 );
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
            v729 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__96 );
            v730 = ll_streq__String_String ( v729,__consts_0.const_str__97 );
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
            v739.ll_append(__consts_0.const_str__33);
            v744 = v739.ll_build();
            v734.setAttribute(__consts_0.const_str__64,v744);
            v746 = create_text_elem ( __consts_0.const_str__98 );
            v747 = v733;
            v747.setAttribute(__consts_0.const_str__99,__consts_0.const_str__100);
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
            v756 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__92,v755 );
            v757 = (v756%30);
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
            v762 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__92,v761 );
            v763 = (v762+1);
            __consts_0.const_tuple__92[v761]=v763;
            v765 = ll_strconcat__String_String ( __consts_0.const_str__88,v761 );
            v766 = get_elem ( v765 );
            v767 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__87,v761 );
            v768 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__92,v761 );
            v769 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__86,v761 );
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
            v777.ll_append(__consts_0.const_str__101);
            v784 = v776.toString();
            v777.ll_append(v784);
            v777.ll_append(__consts_0.const_str__44);
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
            v795 = create_elem ( __consts_0.const_str__18 );
            v796 = module_part_8;
            v796.appendChild(v795);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v760 = msg_27;
            block = 5;
            break;
            case 8:
            v798 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__96 );
            v799 = ll_streq__String_String ( v798,__consts_0.const_str__102 );
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
            v810.ll_append(__consts_0.const_str__103);
            v812 = ll_str__StringR_StringConst_String ( v809 );
            v810.ll_append(v812);
            v810.ll_append(__consts_0.const_str__33);
            v815 = v810.ll_build();
            v805.setAttribute(__consts_0.const_str__64,v815);
            v817 = create_text_elem ( __consts_0.const_str__104 );
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
            v822 = create_text_elem ( __consts_0.const_str__105 );
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
            v845.ll_append(__consts_0.const_str__44);
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

function show_interrupt () {
    var v683,v684,v685,v686;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__106;
            v683 = __consts_0.Document;
            v684 = v683.getElementById(__consts_0.const_str__41);
            v685 = v684.childNodes;
            v686 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v685,0 );
            v686.nodeValue = __consts_0.const_str__107;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_int__String_Signed (s_2,base_0) {
    var v943,v944,v945,v946,v947,v948,etype_6,evalue_6,s_3,base_1,v949,s_4,base_2,v950,v951,s_5,base_3,v952,v953,s_6,base_4,i_8,strlen_0,v954,v955,s_7,base_5,i_9,strlen_1,v956,v957,v958,v959,v960,s_8,base_6,i_10,strlen_2,v961,v962,v963,v964,s_9,base_7,i_11,strlen_3,v965,v966,v967,v968,s_10,base_8,val_0,i_12,sign_0,strlen_4,v969,v970,s_11,val_1,i_13,sign_1,strlen_5,v971,v972,val_2,sign_2,v973,v974,v975,v976,v977,v978,v979,v980,v981,v982,s_12,val_3,i_14,sign_3,strlen_6,v983,v984,v985,v986,s_13,val_4,sign_4,strlen_7,v987,v988,s_14,base_9,val_5,i_15,sign_5,strlen_8,v989,v990,v991,v992,v993,s_15,base_10,c_0,val_6,i_16,sign_6,strlen_9,v994,v995,s_16,base_11,c_1,val_7,i_17,sign_7,strlen_10,v996,v997,s_17,base_12,c_2,val_8,i_18,sign_8,strlen_11,v998,s_18,base_13,c_3,val_9,i_19,sign_9,strlen_12,v999,v1000,s_19,base_14,val_10,i_20,sign_10,strlen_13,v1001,v1002,s_20,base_15,val_11,i_21,digit_0,sign_11,strlen_14,v1003,v1004,s_21,base_16,i_22,digit_1,sign_12,strlen_15,v1005,v1006,v1007,v1008,s_22,base_17,c_4,val_12,i_23,sign_13,strlen_16,v1009,s_23,base_18,c_5,val_13,i_24,sign_14,strlen_17,v1010,v1011,s_24,base_19,val_14,i_25,sign_15,strlen_18,v1012,v1013,v1014,s_25,base_20,c_6,val_15,i_26,sign_16,strlen_19,v1015,s_26,base_21,c_7,val_16,i_27,sign_17,strlen_20,v1016,v1017,s_27,base_22,val_17,i_28,sign_18,strlen_21,v1018,v1019,v1020,s_28,base_23,strlen_22,v1021,v1022,s_29,base_24,strlen_23,v1023,v1024,s_30,base_25,i_29,strlen_24,v1025,v1026,v1027,v1028,s_31,base_26,strlen_25,v1029,v1030;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v944 = (2<=base_0);
            v945 = v944;
            if (v945 == false)
            {
                block = 1;
                break;
            }
            s_3 = s_2;
            base_1 = base_0;
            block = 3;
            break;
            case 1:
            v946 = __consts_0.exceptions_ValueError;
            v947 = v946.meta;
            v948 = v946;
            etype_6 = v947;
            evalue_6 = v948;
            block = 2;
            break;
            case 3:
            v949 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v950 = v949;
            block = 4;
            break;
            case 4:
            v951 = v950;
            if (v951 == false)
            {
                block = 1;
                break;
            }
            s_5 = s_4;
            base_3 = base_2;
            block = 5;
            break;
            case 5:
            v952 = s_5;
            v953 = v952.length;
            s_6 = s_5;
            base_4 = base_3;
            i_8 = 0;
            strlen_0 = v953;
            block = 6;
            break;
            case 6:
            v954 = (i_8<strlen_0);
            v955 = v954;
            s_7 = s_6;
            base_5 = base_4;
            i_9 = i_8;
            strlen_1 = strlen_0;
            if (v955 == false)
            {
                block = 7;
                break;
            }
            s_30 = s_6;
            base_25 = base_4;
            i_29 = i_8;
            strlen_24 = strlen_0;
            block = 35;
            break;
            case 7:
            v956 = (i_9<strlen_1);
            v957 = v956;
            if (v957 == false)
            {
                block = 8;
                break;
            }
            s_8 = s_7;
            base_6 = base_5;
            i_10 = i_9;
            strlen_2 = strlen_1;
            block = 9;
            break;
            case 8:
            v958 = __consts_0.exceptions_ValueError;
            v959 = v958.meta;
            v960 = v958;
            etype_6 = v959;
            evalue_6 = v960;
            block = 2;
            break;
            case 9:
            v961 = s_8;
            v962 = v961.charAt(i_10);
            v963 = (v962=='-');
            v964 = v963;
            s_9 = s_8;
            base_7 = base_6;
            i_11 = i_10;
            strlen_3 = strlen_2;
            if (v964 == false)
            {
                block = 10;
                break;
            }
            s_29 = s_8;
            base_24 = base_6;
            strlen_23 = strlen_2;
            v1023 = i_10;
            block = 34;
            break;
            case 10:
            v965 = s_9;
            v966 = v965.charAt(i_11);
            v967 = (v966=='+');
            v968 = v967;
            s_10 = s_9;
            base_8 = base_7;
            val_0 = 0;
            i_12 = i_11;
            sign_0 = 1;
            strlen_4 = strlen_3;
            if (v968 == false)
            {
                block = 11;
                break;
            }
            s_28 = s_9;
            base_23 = base_7;
            strlen_22 = strlen_3;
            v1021 = i_11;
            block = 33;
            break;
            case 11:
            v969 = (i_12<strlen_4);
            v970 = v969;
            s_11 = s_10;
            val_1 = val_0;
            i_13 = i_12;
            sign_1 = sign_0;
            strlen_5 = strlen_4;
            if (v970 == false)
            {
                block = 12;
                break;
            }
            s_14 = s_10;
            base_9 = base_8;
            val_5 = val_0;
            i_15 = i_12;
            sign_5 = sign_0;
            strlen_8 = strlen_4;
            block = 19;
            break;
            case 12:
            v971 = (i_13<strlen_5);
            v972 = v971;
            val_2 = val_1;
            sign_2 = sign_1;
            v973 = i_13;
            v974 = strlen_5;
            if (v972 == false)
            {
                block = 13;
                break;
            }
            s_12 = s_11;
            val_3 = val_1;
            i_14 = i_13;
            sign_3 = sign_1;
            strlen_6 = strlen_5;
            block = 17;
            break;
            case 13:
            v975 = (v973==v974);
            v976 = v975;
            if (v976 == false)
            {
                block = 14;
                break;
            }
            v980 = sign_2;
            v981 = val_2;
            block = 15;
            break;
            case 14:
            v977 = __consts_0.exceptions_ValueError;
            v978 = v977.meta;
            v979 = v977;
            etype_6 = v978;
            evalue_6 = v979;
            block = 2;
            break;
            case 15:
            v982 = (v980*v981);
            v943 = v982;
            block = 16;
            break;
            case 17:
            v983 = s_12;
            v984 = v983.charAt(i_14);
            v985 = (v984==' ');
            v986 = v985;
            val_2 = val_3;
            sign_2 = sign_3;
            v973 = i_14;
            v974 = strlen_6;
            if (v986 == false)
            {
                block = 13;
                break;
            }
            s_13 = s_12;
            val_4 = val_3;
            sign_4 = sign_3;
            strlen_7 = strlen_6;
            v987 = i_14;
            block = 18;
            break;
            case 18:
            v988 = (v987+1);
            s_11 = s_13;
            val_1 = val_4;
            i_13 = v988;
            sign_1 = sign_4;
            strlen_5 = strlen_7;
            block = 12;
            break;
            case 19:
            v989 = s_14;
            v990 = v989.charAt(i_15);
            v991 = v990.charCodeAt(0);
            v992 = (97<=v991);
            v993 = v992;
            s_15 = s_14;
            base_10 = base_9;
            c_0 = v991;
            val_6 = val_5;
            i_16 = i_15;
            sign_6 = sign_5;
            strlen_9 = strlen_8;
            if (v993 == false)
            {
                block = 20;
                break;
            }
            s_25 = s_14;
            base_20 = base_9;
            c_6 = v991;
            val_15 = val_5;
            i_26 = i_15;
            sign_16 = sign_5;
            strlen_19 = strlen_8;
            block = 30;
            break;
            case 20:
            v994 = (65<=c_0);
            v995 = v994;
            s_16 = s_15;
            base_11 = base_10;
            c_1 = c_0;
            val_7 = val_6;
            i_17 = i_16;
            sign_7 = sign_6;
            strlen_10 = strlen_9;
            if (v995 == false)
            {
                block = 21;
                break;
            }
            s_22 = s_15;
            base_17 = base_10;
            c_4 = c_0;
            val_12 = val_6;
            i_23 = i_16;
            sign_13 = sign_6;
            strlen_16 = strlen_9;
            block = 27;
            break;
            case 21:
            v996 = (48<=c_1);
            v997 = v996;
            s_11 = s_16;
            val_1 = val_7;
            i_13 = i_17;
            sign_1 = sign_7;
            strlen_5 = strlen_10;
            if (v997 == false)
            {
                block = 12;
                break;
            }
            s_17 = s_16;
            base_12 = base_11;
            c_2 = c_1;
            val_8 = val_7;
            i_18 = i_17;
            sign_8 = sign_7;
            strlen_11 = strlen_10;
            block = 22;
            break;
            case 22:
            v998 = (c_2<=57);
            s_18 = s_17;
            base_13 = base_12;
            c_3 = c_2;
            val_9 = val_8;
            i_19 = i_18;
            sign_9 = sign_8;
            strlen_12 = strlen_11;
            v999 = v998;
            block = 23;
            break;
            case 23:
            v1000 = v999;
            s_11 = s_18;
            val_1 = val_9;
            i_13 = i_19;
            sign_1 = sign_9;
            strlen_5 = strlen_12;
            if (v1000 == false)
            {
                block = 12;
                break;
            }
            s_19 = s_18;
            base_14 = base_13;
            val_10 = val_9;
            i_20 = i_19;
            sign_10 = sign_9;
            strlen_13 = strlen_12;
            v1001 = c_3;
            block = 24;
            break;
            case 24:
            v1002 = (v1001-48);
            s_20 = s_19;
            base_15 = base_14;
            val_11 = val_10;
            i_21 = i_20;
            digit_0 = v1002;
            sign_11 = sign_10;
            strlen_14 = strlen_13;
            block = 25;
            break;
            case 25:
            v1003 = (digit_0>=base_15);
            v1004 = v1003;
            s_21 = s_20;
            base_16 = base_15;
            i_22 = i_21;
            digit_1 = digit_0;
            sign_12 = sign_11;
            strlen_15 = strlen_14;
            v1005 = val_11;
            if (v1004 == false)
            {
                block = 26;
                break;
            }
            s_11 = s_20;
            val_1 = val_11;
            i_13 = i_21;
            sign_1 = sign_11;
            strlen_5 = strlen_14;
            block = 12;
            break;
            case 26:
            v1006 = (v1005*base_16);
            v1007 = (v1006+digit_1);
            v1008 = (i_22+1);
            s_10 = s_21;
            base_8 = base_16;
            val_0 = v1007;
            i_12 = v1008;
            sign_0 = sign_12;
            strlen_4 = strlen_15;
            block = 11;
            break;
            case 27:
            v1009 = (c_4<=90);
            s_23 = s_22;
            base_18 = base_17;
            c_5 = c_4;
            val_13 = val_12;
            i_24 = i_23;
            sign_14 = sign_13;
            strlen_17 = strlen_16;
            v1010 = v1009;
            block = 28;
            break;
            case 28:
            v1011 = v1010;
            s_16 = s_23;
            base_11 = base_18;
            c_1 = c_5;
            val_7 = val_13;
            i_17 = i_24;
            sign_7 = sign_14;
            strlen_10 = strlen_17;
            if (v1011 == false)
            {
                block = 21;
                break;
            }
            s_24 = s_23;
            base_19 = base_18;
            val_14 = val_13;
            i_25 = i_24;
            sign_15 = sign_14;
            strlen_18 = strlen_17;
            v1012 = c_5;
            block = 29;
            break;
            case 29:
            v1013 = (v1012-65);
            v1014 = (v1013+10);
            s_20 = s_24;
            base_15 = base_19;
            val_11 = val_14;
            i_21 = i_25;
            digit_0 = v1014;
            sign_11 = sign_15;
            strlen_14 = strlen_18;
            block = 25;
            break;
            case 30:
            v1015 = (c_6<=122);
            s_26 = s_25;
            base_21 = base_20;
            c_7 = c_6;
            val_16 = val_15;
            i_27 = i_26;
            sign_17 = sign_16;
            strlen_20 = strlen_19;
            v1016 = v1015;
            block = 31;
            break;
            case 31:
            v1017 = v1016;
            s_15 = s_26;
            base_10 = base_21;
            c_0 = c_7;
            val_6 = val_16;
            i_16 = i_27;
            sign_6 = sign_17;
            strlen_9 = strlen_20;
            if (v1017 == false)
            {
                block = 20;
                break;
            }
            s_27 = s_26;
            base_22 = base_21;
            val_17 = val_16;
            i_28 = i_27;
            sign_18 = sign_17;
            strlen_21 = strlen_20;
            v1018 = c_7;
            block = 32;
            break;
            case 32:
            v1019 = (v1018-97);
            v1020 = (v1019+10);
            s_20 = s_27;
            base_15 = base_22;
            val_11 = val_17;
            i_21 = i_28;
            digit_0 = v1020;
            sign_11 = sign_18;
            strlen_14 = strlen_21;
            block = 25;
            break;
            case 33:
            v1022 = (v1021+1);
            s_10 = s_28;
            base_8 = base_23;
            val_0 = 0;
            i_12 = v1022;
            sign_0 = 1;
            strlen_4 = strlen_22;
            block = 11;
            break;
            case 34:
            v1024 = (v1023+1);
            s_10 = s_29;
            base_8 = base_24;
            val_0 = 0;
            i_12 = v1024;
            sign_0 = -1;
            strlen_4 = strlen_23;
            block = 11;
            break;
            case 35:
            v1025 = s_30;
            v1026 = v1025.charAt(i_29);
            v1027 = (v1026==' ');
            v1028 = v1027;
            s_7 = s_30;
            base_5 = base_25;
            i_9 = i_29;
            strlen_1 = strlen_24;
            if (v1028 == false)
            {
                block = 7;
                break;
            }
            s_31 = s_30;
            base_26 = base_25;
            strlen_25 = strlen_24;
            v1029 = i_29;
            block = 36;
            break;
            case 36:
            v1030 = (v1029+1);
            s_6 = s_31;
            base_4 = base_26;
            i_8 = v1030;
            strlen_0 = strlen_25;
            block = 6;
            break;
            case 2:
            throw(evalue_6);
            case 16:
            return ( v943 );
        }
    }
}

function ll_int2dec__Signed (i_7) {
    var v941,v942;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v942 = i_7.toString();
            v941 = v942;
            block = 1;
            break;
            case 1:
            return ( v941 );
        }
    }
}

function ll_dict_getitem__Dict_String__Signed__String (d_4,key_8) {
    var v1034,v1035,v1036,v1037,v1038,v1039,v1040,etype_7,evalue_7,key_9,v1041,v1042,v1043;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1035 = d_4;
            v1036 = (v1035[key_8]!=undefined);
            v1037 = v1036;
            if (v1037 == false)
            {
                block = 1;
                break;
            }
            key_9 = key_8;
            v1041 = d_4;
            block = 3;
            break;
            case 1:
            v1038 = __consts_0.exceptions_KeyError;
            v1039 = v1038.meta;
            v1040 = v1038;
            etype_7 = v1039;
            evalue_7 = v1040;
            block = 2;
            break;
            case 3:
            v1042 = v1041;
            v1043 = v1042[key_9];
            v1034 = v1043;
            block = 4;
            break;
            case 2:
            throw(evalue_7);
            case 4:
            return ( v1034 );
        }
    }
}

function ll_pop_default__dum_nocheckConst_List_String_ (l_17) {
    var v1062,v1063,v1064,l_18,length_8,v1065,v1067,v1068,v1069,res_0,newlength_0,v1071,v1072;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1063 = l_17;
            v1064 = v1063.length;
            l_18 = l_17;
            length_8 = v1064;
            block = 1;
            break;
            case 1:
            v1065 = (length_8>0);
            undefined;
            v1067 = (length_8-1);
            v1068 = l_18;
            v1069 = v1068[v1067];
            ll_null_item__List_String_ ( l_18 );
            res_0 = v1069;
            newlength_0 = v1067;
            v1071 = l_18;
            block = 2;
            break;
            case 2:
            v1072 = v1071;
            v1072.length = newlength_0;
            v1062 = res_0;
            block = 3;
            break;
            case 3:
            return ( v1062 );
        }
    }
}

function ll_getitem__dum_nocheckConst_List_ExternalType__Signed (l_14,index_5) {
    var v1044,v1045,v1046,v1047,v1048,l_15,index_6,length_6,v1049,v1051,index_7,v1053,v1054,v1055,l_16,length_7,v1056,v1057;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1045 = l_14;
            v1046 = v1045.length;
            v1047 = (index_5<0);
            v1048 = v1047;
            l_15 = l_14;
            index_6 = index_5;
            length_6 = v1046;
            if (v1048 == false)
            {
                block = 1;
                break;
            }
            l_16 = l_14;
            length_7 = v1046;
            v1056 = index_5;
            block = 4;
            break;
            case 1:
            v1049 = (index_6>=0);
            undefined;
            v1051 = (index_6<length_6);
            undefined;
            index_7 = index_6;
            v1053 = l_15;
            block = 2;
            break;
            case 2:
            v1054 = v1053;
            v1055 = v1054[index_7];
            v1044 = v1055;
            block = 3;
            break;
            case 4:
            v1057 = (v1056+length_7);
            l_15 = l_16;
            index_6 = v1057;
            length_6 = length_7;
            block = 1;
            break;
            case 3:
            return ( v1044 );
        }
    }
}

function exceptions_ValueError () {
}

exceptions_ValueError.prototype.toString = function (){
    return ( '<exceptions_ValueError instance>' );
}

inherits(exceptions_ValueError,exceptions_StandardError);
function ll_strlen__String (obj_1) {
    var v1031,v1032,v1033;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1032 = obj_1;
            v1033 = v1032.length;
            v1031 = v1033;
            block = 1;
            break;
            case 1:
            return ( v1031 );
        }
    }
}

function skip_come_back (msg_33) {
    var v1059,v1060;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1059 = ll_dict_getitem__Dict_String__String__String ( msg_33,__consts_0.const_str__59 );
            v1060 = ll_dict_getitem__Dict_String__String__String ( msg_33,__consts_0.const_str__82 );
            __consts_0.const_tuple__22[v1060]=v1059;
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
function py____test_rsession_webjs_Options_meta () {
}

py____test_rsession_webjs_Options_meta.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Options_meta instance>' );
}

inherits(py____test_rsession_webjs_Options_meta,Object_meta);
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
function exceptions_AssertionError_meta () {
}

exceptions_AssertionError_meta.prototype.toString = function (){
    return ( '<exceptions_AssertionError_meta instance>' );
}

inherits(exceptions_AssertionError_meta,exceptions_StandardError_meta);
__consts_0 = {};
__consts_0.const_str__71 = ' failures, ';
__consts_0.const_str__32 = "show_host('";
__consts_0.const_str__70 = ' run, ';
__consts_0.exceptions_StopIteration__116 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.const_str__62 = 'a';
__consts_0.const_str__99 = 'class';
__consts_0.const_str__44 = ']';
__consts_0.const_tuple__10 = undefined;
__consts_0.const_str__72 = ' skipped';
__consts_0.const_tuple__86 = {};
__consts_0.const_str__51 = 'ReceivedItemOutcome';
__consts_0.const_str__89 = "show_info('";
__consts_0.const_str__60 = '- skipped (';
__consts_0.const_str__36 = 'hide_host()';
__consts_0.const_str__90 = 'hide_info()';
__consts_0.const_str__39 = '#message';
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__17 = 'tbody';
__consts_0.exceptions_AssertionError__112 = exceptions_AssertionError;
__consts_0.exceptions_AssertionError_meta = new exceptions_AssertionError_meta();
__consts_0.exceptions_AssertionError = new exceptions_AssertionError();
__consts_0.const_str__61 = ')';
__consts_0.const_str__46 = 'main_table';
__consts_0.const_str__107 = 'Tests [interrupted]';
__consts_0.exceptions_KeyError__114 = exceptions_KeyError;
__consts_0.const_str__33 = "')";
__consts_0.const_str__55 = 'RsyncFinished';
__consts_0.Window = window;
__consts_0.const_str__88 = '_txt_';
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.const_str__80 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_str__100 = 'error';
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_str__69 = 'FINISHED ';
__consts_0.const_tuple = undefined;
__consts_0.const_str__42 = 'Rsyncing';
__consts_0.const_str__14 = 'info';
__consts_0.const_str__15 = 'hidden';
__consts_0.const_str__13 = 'true';
__consts_0.exceptions_ValueError__110 = exceptions_ValueError;
__consts_0.const_str__98 = 'F';
__consts_0.const_str__35 = 'onmouseout';
__consts_0.const_str__47 = 'type';
__consts_0.const_str__95 = 'passed';
__consts_0.const_str__105 = '.';
__consts_0.const_str__53 = 'FailedTryiter';
__consts_0.const_str__31 = '#ff0000';
__consts_0.const_str__5 = 'checked';
__consts_0.const_str__11 = 'messagebox';
__consts_0.const_str__58 = 'fullitemname';
__consts_0.const_str__91 = 'table';
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.const_str__73 = 'Py.test ';
__consts_0.const_str__68 = 'skips';
__consts_0.const_str__57 = 'CrashedExecution';
__consts_0.const_str__29 = '\n';
__consts_0.const_tuple__22 = {};
__consts_0.const_str__37 = 'pre';
__consts_0.const_str__106 = 'Py.test [interrupted]';
__consts_0.const_str__27 = '\n======== Stdout: ========\n';
__consts_0.const_str__76 = '#00ff00';
__consts_0.const_str__24 = 'beige';
__consts_0.const_str__84 = 'length';
__consts_0.py____test_rsession_webjs_Globals__121 = py____test_rsession_webjs_Globals;
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.const_list__120 = [];
__consts_0.const_str__7 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.const_str__79 = 'traceback';
__consts_0.const_str__45 = 'testmain';
__consts_0.const_str__103 = "javascript:show_skip('";
__consts_0.const_str__78 = '[';
__consts_0.const_str__94 = 'Tests [crashed]';
__consts_0.const_str__59 = 'reason';
__consts_0.const_str__63 = "javascript:show_traceback('";
__consts_0.const_str__41 = 'Tests';
__consts_0.const_tuple__87 = {};
__consts_0.const_str__104 = 's';
__consts_0.const_str__66 = 'run';
__consts_0.const_str__54 = 'SkippedTryiter';
__consts_0.const_str__97 = 'None';
__consts_0.const_str__6 = 'True';
__consts_0.const_str__101 = '/';
__consts_0.const_tuple__25 = {};
__consts_0.const_str__75 = 'hostkey';
__consts_0.const_str__67 = 'fails';
__consts_0.const_tuple__92 = {};
__consts_0.const_str__48 = 'ItemStart';
__consts_0.const_str__83 = 'itemname';
__consts_0.const_str__52 = 'TestFinished';
__consts_0.const_str__16 = 'jobs';
__consts_0.py____test_rsession_webjs_Options__118 = py____test_rsession_webjs_Options;
__consts_0.const_str__28 = '\n========== Stderr: ==========\n';
__consts_0.py____test_rsession_webjs_Options_meta = new py____test_rsession_webjs_Options_meta();
__consts_0.py____test_rsession_webjs_Options = new py____test_rsession_webjs_Options();
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.const_str__81 = 'stderr';
__consts_0.const_str__64 = 'href';
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.const_str__20 = 'visible';
__consts_0.const_str__102 = 'False';
__consts_0.const_str__50 = 'HostRSyncRootReady';
__consts_0.const_str__34 = 'onmouseover';
__consts_0.const_str__65 = '- FAILED TO LOAD MODULE';
__consts_0.const_str__85 = '[0/';
__consts_0.const_str__49 = 'SendItem';
__consts_0.const_str__74 = 'fullmodulename';
__consts_0.const_str__96 = 'skipped';
__consts_0.const_str__30 = 'hostsbody';
__consts_0.const_str__77 = '[0]';
__consts_0.const_list = undefined;
__consts_0.const_str__19 = 'td';
__consts_0.const_str__26 = '====== Traceback: =========\n';
__consts_0.const_str__18 = 'tr';
__consts_0.const_str__82 = 'item_name';
__consts_0.const_str__43 = 'Tests [';
__consts_0.Document = document;
__consts_0.const_str__93 = 'Py.test [crashed]';
__consts_0.const_str__56 = 'InterruptedExecution';
__consts_0.const_str__4 = 'opt_scroll';
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__116;
__consts_0.exceptions_AssertionError_meta.class_ = __consts_0.exceptions_AssertionError__112;
__consts_0.exceptions_AssertionError.meta = __consts_0.exceptions_AssertionError_meta;
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__114;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__110;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__121;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__7;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__7;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ofinished = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__120;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__10;
__consts_0.py____test_rsession_webjs_Options_meta.class_ = __consts_0.py____test_rsession_webjs_Options__118;
__consts_0.py____test_rsession_webjs_Options.meta = __consts_0.py____test_rsession_webjs_Options_meta;
__consts_0.py____test_rsession_webjs_Options.oscroll = true;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
