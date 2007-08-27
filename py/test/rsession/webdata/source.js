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
    if (!self) {
        return (false);
    }
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

function findIndexOf(s1, s2, start, end) {
    if (start > end || start > s1.length) {
        return -1;
    }
    s1 = s1.substr(start, end-start);
    res = s1.indexOf(s2);
    if (res == -1) {
        return -1;
    }
    return res + start;
}

function findIndexOfTrue(s1, s2) {
    return findIndexOf(s1, s2, 0, s1.length) != -1;
}

function countCharOf(s, c, start, end) {
    s = s.substring(start, end);
    var i = 0;
    for (c1 in s) {
        if (s[c1] == c) {
            i++;
        }
    }
    return(i);
}

function countOf(s, s1, start, end) {
    var ret = findIndexOf(s, s1, start, end);
    var i = 0;
    var lgt = 1;
    if (s1.length > 0) {
        lgt = s1.length;
    }
    while (ret != -1) {
        i++;
        ret = findIndexOf(s, s1, ret + lgt, end);
    }
    return (i);
}

function convertToString(stuff) {
    if (stuff === undefined) {
       return ("undefined");
    }
    return (stuff.toString());
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
            v22.setAttribute(__consts_0.const_str__5,__consts_0.const_str__6);
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function opt_scroll () {
    var v124,v125;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v124 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            if (v124 == false)
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

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__8;
    this.ohost = __consts_0.const_str__8;
    this.orsync_dots = 0;
    this.ofinished = false;
    this.ohost_dict = __consts_0.const_tuple;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__11;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py.__.test.rsession.webjs.Globals object>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
function show_info (data_0) {
    var v47,v48,v49,data_1,info_0,v51,v52,v53,info_1,v54,v55,v56,v58,data_2,info_2,v60,v61,v62;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v47 = __consts_0.Document;
            v48 = v47.getElementById(__consts_0.const_str__12);
            v49 = v48.style;
            v49.visibility = __consts_0.const_str__13;
            data_1 = data_0;
            info_0 = v48;
            block = 1;
            break;
            case 1:
            v51 = info_0.childNodes;
            v52 = ll_len__List_ExternalType_Element__ ( v51 );
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
            info_1.appendChild(v55);
            v58 = info_1.style;
            v58.backgroundColor = __consts_0.const_str__14;
            block = 3;
            break;
            case 4:
            v61 = info_2.childNodes;
            v62 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v61,0 );
            info_2.removeChild(v62);
            data_1 = data_2;
            info_0 = info_2;
            block = 1;
            break;
            case 3:
            return ( undefined );
        }
    }
}

function show_host (host_name_0) {
    var v70,v71,v72,v73,host_name_1,elem_0,v74,v75,v76,v77,host_name_2,elem_1,tbody_0,v78,v79,last_exc_value_0,host_name_3,elem_2,tbody_1,item_0,v80,v81,v82,v83,v84,v86,v88,host_name_4,elem_3,tbody_2,v90,v92,host_name_5,elem_4,v96,v97,v98;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v70 = __consts_0.Document;
            v71 = v70.getElementById(__consts_0.const_str__15);
            v72 = v71.childNodes;
            v73 = ll_list_is_true__List_ExternalType_Element__ ( v72 );
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
            v74 = create_elem ( __consts_0.const_str__16 );
            v75 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v76 = ll_dict_getitem__Dict_String__List_String___String ( v75,host_name_1 );
            v77 = ll_listiter__Record_index__Signed__iterable_List_String_ ( v76 );
            host_name_2 = host_name_1;
            elem_1 = elem_0;
            tbody_0 = v74;
            v78 = v77;
            block = 2;
            break;
            case 2:
            try {
                v79 = ll_listnext__Record_index__Signed__iterable_0 ( v78 );
                host_name_3 = host_name_2;
                elem_2 = elem_1;
                tbody_1 = tbody_0;
                item_0 = v79;
                v80 = v78;
                block = 3;
                break;
            }
            catch (exc){
                if (isinstanceof(exc, exceptions_StopIteration))
                {
                    host_name_4 = host_name_2;
                    elem_3 = elem_1;
                    tbody_2 = tbody_0;
                    block = 4;
                    break;
                }
                throw(exc);
            }
            case 3:
            v81 = create_elem ( __consts_0.const_str__17 );
            v82 = create_elem ( __consts_0.const_str__18 );
            v84 = create_text_elem ( item_0 );
            v82.appendChild(v84);
            v81.appendChild(v82);
            tbody_1.appendChild(v81);
            host_name_2 = host_name_3;
            elem_1 = elem_2;
            tbody_0 = tbody_1;
            v78 = v80;
            block = 2;
            break;
            case 4:
            elem_3.appendChild(tbody_2);
            v92 = elem_3.style;
            v92.visibility = __consts_0.const_str__13;
            __consts_0.py____test_rsession_webjs_Globals.ohost = host_name_4;
            setTimeout ( 'reshow_host()',100 );
            block = 5;
            break;
            case 6:
            v97 = elem_4.childNodes;
            v98 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v97,0 );
            elem_4.removeChild(v98);
            host_name_1 = host_name_5;
            elem_0 = elem_4;
            block = 1;
            break;
            case 5:
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
            v26 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__19,item_name_0 );
            set_msgbox ( item_name_0,v26 );
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_list_is_true__List_ExternalType_Element__ (l_3) {
    var v212,v213,v214,v215,v216,v217,v218;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v213 = !!l_3;
            v212 = v213;
            if (v213 == false)
            {
                block = 1;
                break;
            }
            v215 = l_3;
            block = 2;
            break;
            case 2:
            v217 = v215.length;
            v218 = (v217!=0);
            v212 = v218;
            block = 1;
            break;
            case 1:
            return ( v212 );
        }
    }
}

function exceptions_Exception () {
}

exceptions_Exception.prototype.toString = function (){
    return ( '<exceptions.Exception object>' );
}

inherits(exceptions_Exception,Object);
function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions.StopIteration object>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
function hide_host () {
    var v101,v102,elem_5,v103,v104,v105,v106,v107,elem_6,v110,v111,v112;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v101 = __consts_0.Document;
            v102 = v101.getElementById(__consts_0.const_str__15);
            elem_5 = v102;
            block = 1;
            break;
            case 1:
            v103 = elem_5.childNodes;
            v104 = ll_len__List_ExternalType_Element__ ( v103 );
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
            v107.visibility = __consts_0.const_str__20;
            __consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__8;
            block = 3;
            break;
            case 4:
            v111 = elem_6.childNodes;
            v112 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v111,0 );
            elem_6.removeChild(v112);
            elem_5 = elem_6;
            block = 1;
            break;
            case 3:
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
            v29 = ll_dict_getitem__Dict_String__Record_item2__Str_String ( __consts_0.const_tuple__21,item_name_1 );
            v30 = v29.item0;
            v31 = v29.item1;
            v32 = v29.item2;
            v33 = new StringBuilder();
            v33.ll_append(__consts_0.const_str__22);
            v35 = ll_str__StringR_StringConst_String ( v30 );
            v33.ll_append(v35);
            v33.ll_append(__consts_0.const_str__23);
            v38 = ll_str__StringR_StringConst_String ( v31 );
            v33.ll_append(v38);
            v33.ll_append(__consts_0.const_str__24);
            v41 = ll_str__StringR_StringConst_String ( v32 );
            v33.ll_append(v41);
            v33.ll_append(__consts_0.const_str__25);
            v44 = v33.ll_build();
            set_msgbox ( item_name_1,v44 );
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_str__StringR_StringConst_String (s_1) {
    var v297;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v297 = s_1;
            block = 1;
            break;
            case 1:
            return ( v297 );
        }
    }
}

function host_init (host_dict_0) {
    var v129,v130,v131,v132,v133,host_dict_1,tbody_3,v134,v135,last_exc_value_1,host_dict_2,tbody_4,host_0,v136,v137,v138,v140,v141,v143,v144,v145,v148,v150,v151,v153,v156,v158,host_dict_3,v164,v166,v167,v168,v169,v170,last_exc_value_2,key_0,v171,v172,v174;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v129 = __consts_0.Document;
            v130 = v129.getElementById(__consts_0.const_str__26);
            v132 = ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst ( host_dict_0 );
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
            v137 = create_elem ( __consts_0.const_str__17 );
            tbody_4.appendChild(v137);
            v140 = create_elem ( __consts_0.const_str__18 );
            v141 = v140.style;
            v141.background = __consts_0.const_str__27;
            v143 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v144 = create_text_elem ( v143 );
            v140.appendChild(v144);
            v140.id = host_0;
            v137.appendChild(v140);
            v151 = new StringBuilder();
            v151.ll_append(__consts_0.const_str__28);
            v153 = ll_str__StringR_StringConst_String ( host_0 );
            v151.ll_append(v153);
            v151.ll_append(__consts_0.const_str__29);
            v156 = v151.ll_build();
            v140.setAttribute(__consts_0.const_str__30,v156);
            v140.setAttribute(__consts_0.const_str__31,__consts_0.const_str__32);
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
            v167 = ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst ( host_dict_3 );
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

function hide_messagebox () {
    var v115,v116,mbox_0,v117,v118,mbox_1,v119,v120,v121;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v115 = __consts_0.Document;
            v116 = v115.getElementById(__consts_0.const_str__33);
            mbox_0 = v116;
            block = 1;
            break;
            case 1:
            v117 = mbox_0.childNodes;
            v118 = ll_list_is_true__List_ExternalType_Element__ ( v117 );
            if (v118 == false)
            {
                block = 2;
                break;
            }
            mbox_1 = mbox_0;
            block = 3;
            break;
            case 3:
            v120 = mbox_1.childNodes;
            v121 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v120,0 );
            mbox_1.removeChild(v121);
            mbox_0 = mbox_1;
            block = 1;
            break;
            case 2:
            return ( undefined );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_String_ (lst_0) {
    var v232,v233;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v233 = new Object();
            v233.iterable = lst_0;
            v233.index = 0;
            v232 = v233;
            block = 1;
            break;
            case 1:
            return ( v232 );
        }
    }
}

function reshow_host () {
    var v251,v252,v253,v254;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v251 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v252 = ll_streq__String_String ( v251,__consts_0.const_str__8 );
            if (v252 == false)
            {
                block = 1;
                break;
            }
            block = 2;
            break;
            case 1:
            v254 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v254 );
            block = 2;
            break;
            case 2:
            return ( undefined );
        }
    }
}

function py____test_rsession_webjs_Options () {
    this.oscroll = false;
}

py____test_rsession_webjs_Options.prototype.toString = function (){
    return ( '<py.__.test.rsession.webjs.Options object>' );
}

inherits(py____test_rsession_webjs_Options,Object);
function ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst (d_3) {
    var v298,v299,v300,v301,v302,v303,length_0,result_0,it_0,i_0,v304,v305,v306,result_1,v307,v308,v309,v310,v311,v312,v313,etype_4,evalue_4,length_1,result_2,it_1,i_1,v314,v315,v316,length_2,result_3,it_2,v318,v319;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v300 = get_dict_len ( d_3 );
            v301 = ll_newlist__List_String_LlT_Signed ( v300 );
            v303 = dict_items_iterator ( d_3 );
            length_0 = v300;
            result_0 = v301;
            it_0 = v303;
            i_0 = 0;
            block = 1;
            break;
            case 1:
            v305 = it_0.ll_go_next();
            result_1 = result_0;
            v307 = i_0;
            v308 = length_0;
            if (v305 == false)
            {
                block = 2;
                break;
            }
            length_1 = length_0;
            result_2 = result_0;
            it_1 = it_0;
            i_1 = i_0;
            block = 6;
            break;
            case 2:
            v309 = (v307==v308);
            if (v309 == false)
            {
                block = 3;
                break;
            }
            v298 = result_1;
            block = 5;
            break;
            case 3:
            v311 = __consts_0.py____magic_assertion_AssertionError;
            v312 = v311.meta;
            etype_4 = v312;
            evalue_4 = v311;
            block = 4;
            break;
            case 6:
            v316 = it_1.ll_current_key();
            result_2[i_1]=v316;
            length_2 = length_1;
            result_3 = result_2;
            it_2 = it_1;
            v318 = i_1;
            block = 7;
            break;
            case 7:
            v319 = (v318+1);
            length_0 = length_2;
            result_0 = result_3;
            it_0 = it_2;
            i_0 = v319;
            block = 1;
            break;
            case 4:
            throw(evalue_4);
            case 5:
            return ( v298 );
        }
    }
}

function exceptions_StandardError () {
}

exceptions_StandardError.prototype.toString = function (){
    return ( '<exceptions.StandardError object>' );
}

inherits(exceptions_StandardError,exceptions_Exception);
function ll_dict_getitem__Dict_String__String__String (d_1,key_4) {
    var v256,v257,v258,v259,v260,v261,v262,etype_2,evalue_2,key_5,v263,v264,v265;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v258 = (d_1[key_4]!=undefined);
            if (v258 == false)
            {
                block = 1;
                break;
            }
            key_5 = key_4;
            v263 = d_1;
            block = 3;
            break;
            case 1:
            v260 = __consts_0.exceptions_KeyError;
            v261 = v260.meta;
            etype_2 = v261;
            evalue_2 = v260;
            block = 2;
            break;
            case 3:
            v265 = v263[key_5];
            v256 = v265;
            block = 4;
            break;
            case 2:
            throw(evalue_2);
            case 4:
            return ( v256 );
        }
    }
}

function ll_newdict__Dict_String__List_String__LlT () {
    var v354,v355;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v355 = new Object();
            v354 = v355;
            block = 1;
            break;
            case 1:
            return ( v354 );
        }
    }
}

function exceptions_LookupError () {
}

exceptions_LookupError.prototype.toString = function (){
    return ( '<exceptions.LookupError object>' );
}

inherits(exceptions_LookupError,exceptions_StandardError);
function exceptions_KeyError () {
}

exceptions_KeyError.prototype.toString = function (){
    return ( '<exceptions.KeyError object>' );
}

inherits(exceptions_KeyError,exceptions_LookupError);
function create_elem (s_0) {
    var v219,v220,v221;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v220 = __consts_0.Document;
            v221 = v220.createElement(s_0);
            v219 = v221;
            block = 1;
            break;
            case 1:
            return ( v219 );
        }
    }
}

function ll_dict_getitem__Dict_String__List_String___String (d_0,key_2) {
    var v222,v223,v224,v225,v226,v227,v228,etype_0,evalue_0,key_3,v229,v230,v231;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v224 = (d_0[key_2]!=undefined);
            if (v224 == false)
            {
                block = 1;
                break;
            }
            key_3 = key_2;
            v229 = d_0;
            block = 3;
            break;
            case 1:
            v226 = __consts_0.exceptions_KeyError;
            v227 = v226.meta;
            etype_0 = v227;
            evalue_0 = v226;
            block = 2;
            break;
            case 3:
            v231 = v229[key_3];
            v222 = v231;
            block = 4;
            break;
            case 2:
            throw(evalue_0);
            case 4:
            return ( v222 );
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

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed (l_1,index_0) {
    var v202,v203,l_2,index_1,v205,v206,v207,index_2,v209,v210,v211;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v203 = (index_0>=0);
            l_2 = l_1;
            index_1 = index_0;
            block = 1;
            break;
            case 1:
            v206 = l_2.length;
            v207 = (index_1<v206);
            index_2 = index_1;
            v209 = l_2;
            block = 2;
            break;
            case 2:
            v211 = v209[index_2];
            v202 = v211;
            block = 3;
            break;
            case 3:
            return ( v202 );
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
            v66 = v65.getElementById(__consts_0.const_str__12);
            v67 = v66.style;
            v67.visibility = __consts_0.const_str__20;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_listnext__Record_index__Signed__iterable_0 (iter_0) {
    var v236,v237,v238,v239,v240,v241,v242,iter_1,l_4,index_3,v243,v245,v246,v247,v248,v249,etype_1,evalue_1;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v237 = iter_0.iterable;
            v238 = iter_0.index;
            v240 = v237.length;
            v241 = (v238>=v240);
            iter_1 = iter_0;
            l_4 = v237;
            index_3 = v238;
            if (v241 == false)
            {
                block = 1;
                break;
            }
            block = 3;
            break;
            case 1:
            v243 = (index_3+1);
            iter_1.index = v243;
            v246 = l_4[index_3];
            v236 = v246;
            block = 2;
            break;
            case 3:
            v247 = __consts_0.exceptions_StopIteration;
            v248 = v247.meta;
            etype_1 = v248;
            evalue_1 = v247;
            block = 4;
            break;
            case 4:
            throw(evalue_1);
            case 2:
            return ( v236 );
        }
    }
}

function update_rsync () {
    var v321,v322,v323,v324,v325,v326,v327,v328,elem_7,v329,v330,v331,v332,v333,v335,v336,v337,elem_8,v338,v339,v341,v344,v345,v346,elem_9,text_0,v350,v351,v352;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v321 = __consts_0.py____test_rsession_webjs_Globals.ofinished;
            if (v321 == false)
            {
                block = 1;
                break;
            }
            block = 4;
            break;
            case 1:
            v323 = __consts_0.Document;
            v324 = v323.getElementById(__consts_0.const_str__37);
            v325 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v327 = (v325==1);
            elem_7 = v324;
            if (v327 == false)
            {
                block = 2;
                break;
            }
            v350 = v324;
            block = 6;
            break;
            case 2:
            v329 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v330 = ll_char_mul__Char_Signed ( '.',v329 );
            v331 = ll_strconcat__String_String ( __consts_0.const_str__38,v330 );
            v332 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v333 = (v332+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v333;
            v335 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v336 = (v335>5);
            elem_8 = elem_7;
            v338 = v331;
            if (v336 == false)
            {
                block = 3;
                break;
            }
            elem_9 = elem_7;
            text_0 = v331;
            block = 5;
            break;
            case 3:
            v339 = new StringBuilder();
            v339.ll_append(__consts_0.const_str__39);
            v341 = ll_str__StringR_StringConst_String ( v338 );
            v339.ll_append(v341);
            v339.ll_append(__consts_0.const_str__40);
            v344 = v339.ll_build();
            v345 = elem_8.childNodes;
            v346 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v345,0 );
            v346.nodeValue = v344;
            setTimeout ( 'update_rsync()',1000 );
            block = 4;
            break;
            case 5:
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            elem_8 = elem_9;
            v338 = text_0;
            block = 3;
            break;
            case 6:
            v351 = v350.childNodes;
            v352 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v351,0 );
            v352.nodeValue = __consts_0.const_str__37;
            block = 4;
            break;
            case 4:
            return ( undefined );
        }
    }
}

function ll_newlist__List_String_LlT_Signed (length_3) {
    var v366,v367,v368;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v367 = new Array();
            v367.length = length_3;
            v366 = v367;
            block = 1;
            break;
            case 1:
            return ( v366 );
        }
    }
}

function ll_len__List_ExternalType_Element__ (l_0) {
    var v196,v197,v198;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v198 = l_0.length;
            v196 = v198;
            block = 1;
            break;
            case 1:
            return ( v196 );
        }
    }
}

function exceptions_AssertionError () {
}

exceptions_AssertionError.prototype.toString = function (){
    return ( '<exceptions.AssertionError object>' );
}

inherits(exceptions_AssertionError,exceptions_StandardError);
function py____magic_assertion_AssertionError () {
}

py____magic_assertion_AssertionError.prototype.toString = function (){
    return ( '<py.__.magic.assertion.AssertionError object>' );
}

inherits(py____magic_assertion_AssertionError,exceptions_AssertionError);
function ll_streq__String_String (s1_0,s2_0) {
    var v356,v357,v358,v359,s2_1,v360,v361,v362,v363,v364,v365;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v357 = !!s1_0;
            v358 = !v357;
            s2_1 = s2_0;
            v360 = s1_0;
            if (v358 == false)
            {
                block = 1;
                break;
            }
            v363 = s2_0;
            block = 3;
            break;
            case 1:
            v362 = (v360==s2_1);
            v356 = v362;
            block = 2;
            break;
            case 3:
            v364 = !!v363;
            v365 = !v364;
            v356 = v365;
            block = 2;
            break;
            case 2:
            return ( v356 );
        }
    }
}

function ll_dict_getitem__Dict_String__Record_item2__Str_String (d_2,key_6) {
    var v287,v288,v289,v290,v291,v292,v293,etype_3,evalue_3,key_7,v294,v295,v296;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v289 = (d_2[key_6]!=undefined);
            if (v289 == false)
            {
                block = 1;
                break;
            }
            key_7 = key_6;
            v294 = d_2;
            block = 3;
            break;
            case 1:
            v291 = __consts_0.exceptions_KeyError;
            v292 = v291.meta;
            etype_3 = v292;
            evalue_3 = v291;
            block = 2;
            break;
            case 3:
            v296 = v294[key_7];
            v287 = v296;
            block = 4;
            break;
            case 2:
            throw(evalue_3);
            case 4:
            return ( v287 );
        }
    }
}

function set_msgbox (item_name_2,data_3) {
    var v267,item_name_3,data_4,msgbox_0,v268,v269,v270,item_name_4,data_5,msgbox_1,v271,v272,v273,v274,v275,v277,v279,v280,item_name_5,data_6,msgbox_2,v283,v284,v285;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v267 = get_elem ( __consts_0.const_str__33 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v267;
            block = 1;
            break;
            case 1:
            v268 = msgbox_0.childNodes;
            v269 = ll_len__List_ExternalType_Element__ ( v268 );
            v270 = !!v269;
            item_name_4 = item_name_3;
            data_5 = data_4;
            msgbox_1 = msgbox_0;
            if (v270 == false)
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
            v271 = create_elem ( __consts_0.const_str__41 );
            v272 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__25 );
            v273 = ll_strconcat__String_String ( v272,data_5 );
            v274 = create_text_elem ( v273 );
            v271.appendChild(v274);
            msgbox_1.appendChild(v271);
            v279 = __consts_0.Window.location;
            v279.assign(__consts_0.const_str__43);
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 4:
            v284 = msgbox_2.childNodes;
            v285 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v284,0 );
            msgbox_2.removeChild(v285);
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

function key_pressed (key_1) {
    var v181,v182,v183,v184,v185,v186,v187,v188,v189,v192,v193;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v181 = key_1.charCode;
            v182 = (v181==115);
            if (v182 == false)
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
            v188 = v185;
            if (v186 == false)
            {
                block = 3;
                break;
            }
            v192 = v185;
            block = 4;
            break;
            case 3:
            v188.setAttribute(__consts_0.const_str__5,__consts_0.const_str__44);
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 1;
            break;
            case 4:
            v192.removeAttribute(__consts_0.const_str__5);
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function create_text_elem (txt_0) {
    var v199,v200,v201;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v200 = __consts_0.Document;
            v201 = v200.createTextNode(txt_0);
            v199 = v201;
            block = 1;
            break;
            case 1:
            return ( v199 );
        }
    }
}

function get_elem (el_0) {
    var v414,v415,v416;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v415 = __consts_0.Document;
            v416 = v415.getElementById(el_0);
            v414 = v416;
            block = 1;
            break;
            case 1:
            return ( v414 );
        }
    }
}

function comeback (msglist_0) {
    var v371,v372,v373,msglist_1,v374,v375,v376,v377,msglist_2,v378,v379,last_exc_value_3,msglist_3,v380,v381,v382,v383,msglist_4,v384,v387,v388,v389,last_exc_value_4,v390,v391,v392,v393,v394,v395,v396;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v371 = ll_len__List_Dict_String__String__ ( msglist_0 );
            v372 = (v371==0);
            msglist_1 = msglist_0;
            if (v372 == false)
            {
                block = 1;
                break;
            }
            block = 4;
            break;
            case 1:
            v374 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v375 = 0;
            v376 = ll_listslice_startonly__List_Dict_String__String__LlT_List_Dict_String__String___Signed ( v374,v375 );
            v377 = ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ ( v376 );
            msglist_2 = msglist_1;
            v378 = v377;
            block = 2;
            break;
            case 2:
            try {
                v379 = ll_listnext__Record_index__Signed__iterable ( v378 );
                msglist_3 = msglist_2;
                v380 = v378;
                v381 = v379;
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
            v382 = process ( v381 );
            if (v382 == false)
            {
                block = 4;
                break;
            }
            msglist_2 = msglist_3;
            v378 = v380;
            block = 2;
            break;
            case 5:
            v384 = new Array();
            v384.length = 0;
            __consts_0.py____test_rsession_webjs_Globals.opending = v384;
            v387 = ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ ( msglist_4 );
            v388 = v387;
            block = 6;
            break;
            case 6:
            try {
                v389 = ll_listnext__Record_index__Signed__iterable ( v388 );
                v390 = v388;
                v391 = v389;
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
            v392 = process ( v391 );
            if (v392 == false)
            {
                block = 4;
                break;
            }
            v388 = v390;
            block = 6;
            break;
            case 8:
            v394 = __consts_0.ExportedMethods;
            v395 = __consts_0.py____test_rsession_webjs_Globals.osessid;
            v396 = v394.show_all_statuses(v395,comeback);
            block = 4;
            break;
            case 4:
            return ( undefined );
        }
    }
}

function ll_char_mul__Char_Signed (ch_0,times_0) {
    var v397,v398,v399,ch_1,times_1,v400,v401,ch_2,times_2,buf_0,i_2,v403,v404,v405,v406,v407,ch_3,times_3,buf_1,i_3,v408,v410;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v398 = (times_0<0);
            ch_1 = ch_0;
            times_1 = times_0;
            if (v398 == false)
            {
                block = 1;
                break;
            }
            ch_1 = ch_0;
            times_1 = 0;
            block = 1;
            break;
            case 1:
            v400 = new StringBuilder();
            v400.ll_allocate(times_1);
            ch_2 = ch_1;
            times_2 = times_1;
            buf_0 = v400;
            i_2 = 0;
            block = 2;
            break;
            case 2:
            v403 = (i_2<times_2);
            v405 = buf_0;
            if (v403 == false)
            {
                block = 3;
                break;
            }
            ch_3 = ch_2;
            times_3 = times_2;
            buf_1 = buf_0;
            i_3 = i_2;
            block = 5;
            break;
            case 3:
            v407 = v405.ll_build();
            v397 = v407;
            block = 4;
            break;
            case 5:
            buf_1.ll_append_char(ch_3);
            v410 = (i_3+1);
            ch_2 = ch_3;
            times_2 = times_3;
            buf_0 = buf_1;
            i_2 = v410;
            block = 2;
            break;
            case 4:
            return ( v397 );
        }
    }
}

function ll_listslice_startonly__List_Dict_String__String__LlT_List_Dict_String__String___Signed (l1_0,start_0) {
    var v420,v421,v422,v423,v425,v427,v429,l1_1,len1_0,l_6,j_0,i_4,v430,v431,l1_2,len1_1,l_7,j_1,i_5,v432,v433,v434,v436,v437;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v422 = l1_0.length;
            v423 = (start_0>=0);
            v425 = (start_0<=v422);
            v427 = (v422-start_0);
            undefined;
            v429 = ll_newlist__List_Dict_String__String__LlT_Signed ( v427 );
            l1_1 = l1_0;
            len1_0 = v422;
            l_6 = v429;
            j_0 = 0;
            i_4 = start_0;
            block = 1;
            break;
            case 1:
            v430 = (i_4<len1_0);
            v420 = l_6;
            if (v430 == false)
            {
                block = 2;
                break;
            }
            l1_2 = l1_1;
            len1_1 = len1_0;
            l_7 = l_6;
            j_1 = j_0;
            i_5 = i_4;
            block = 3;
            break;
            case 3:
            v434 = l1_2[i_5];
            l_7[j_1]=v434;
            v436 = (i_5+1);
            v437 = (j_1+1);
            l1_1 = l1_2;
            len1_0 = len1_1;
            l_6 = l_7;
            j_0 = v437;
            i_4 = v436;
            block = 1;
            break;
            case 2:
            return ( v420 );
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed (length_4) {
    var v665,v666;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v666 = ll_newlist__List_Dict_String__String__LlT_Signed_0 ( length_4 );
            v665 = v666;
            block = 1;
            break;
            case 1:
            return ( v665 );
        }
    }
}

function ll_strconcat__String_String (obj_0,arg0_0) {
    var v411,v412,v413;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v413 = (obj_0+arg0_0);
            v411 = v413;
            block = 1;
            break;
            case 1:
            return ( v411 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_Dict_String__String__ (lst_1) {
    var v438,v439;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v439 = new Object();
            v439.iterable = lst_1;
            v439.index = 0;
            v438 = v439;
            block = 1;
            break;
            case 1:
            return ( v438 );
        }
    }
}

function ll_listnext__Record_index__Signed__iterable (iter_2) {
    var v442,v443,v444,v445,v446,v447,v448,iter_3,l_8,index_4,v449,v451,v452,v453,v454,v455,etype_5,evalue_5;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v443 = iter_2.iterable;
            v444 = iter_2.index;
            v446 = v443.length;
            v447 = (v444>=v446);
            iter_3 = iter_2;
            l_8 = v443;
            index_4 = v444;
            if (v447 == false)
            {
                block = 1;
                break;
            }
            block = 3;
            break;
            case 1:
            v449 = (index_4+1);
            iter_3.index = v449;
            v452 = l_8[index_4];
            v442 = v452;
            block = 2;
            break;
            case 3:
            v453 = __consts_0.exceptions_StopIteration;
            v454 = v453.meta;
            etype_5 = v454;
            evalue_5 = v453;
            block = 4;
            break;
            case 4:
            throw(evalue_5);
            case 2:
            return ( v442 );
        }
    }
}

function process (msg_0) {
    var v456,v457,v458,v459,msg_1,v460,v461,v462,v463,v464,v465,v466,msg_2,v467,v468,v469,msg_3,v470,v471,v472,msg_4,v473,v474,v475,msg_5,v476,v477,v478,msg_6,v479,v480,v481,msg_7,v482,v483,v484,msg_8,v485,v486,v487,msg_9,v488,v489,v490,v491,v492,v493,v494,v495,v496,v497,v498,msg_10,v503,v504,v505,msg_11,v506,v507,msg_12,module_part_0,v509,v510,v511,v512,v514,v515,v517,v520,v521,v522,v524,v526,msg_13,v528,v529,v530,msg_14,v531,v532,msg_15,module_part_1,v534,v535,v536,v537,v538,v539,v541,v542,v544,v547,v549,v550,v552,v554,v556,v558,v559,v560,msg_16,v561,v562,v563,v564,v568,v569,v570,v571,v573,v576,v579,v582,v584,v586,v588,v590,v592,v595,v596,v597,v598,v599,msg_17,v601,v602,v603,msg_18,v604,v605,v607,v608,msg_19,v610,v611,v612,v613,v615,v616,v617,v618,v620,v621,v622,v625,v626,v627,msg_20,v629,v630,v631,v632,v633,v634,v635,v636,v638,v639,v640,v641,v642,v643,v644,v645,v648,v649,v650,v651,v654,v657,v658,v659,main_t_0,v661,v662,v663;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v457 = get_dict_len ( msg_0 );
            v458 = (v457==0);
            msg_1 = msg_0;
            if (v458 == false)
            {
                block = 1;
                break;
            }
            v456 = false;
            block = 12;
            break;
            case 1:
            v460 = __consts_0.Document;
            v461 = v460.getElementById(__consts_0.const_str__45);
            v462 = __consts_0.Document;
            v463 = v462.getElementById(__consts_0.const_str__46);
            v464 = ll_dict_getitem__Dict_String__String__String ( msg_1,__consts_0.const_str__47 );
            v465 = ll_streq__String_String ( v464,__consts_0.const_str__48 );
            msg_2 = msg_1;
            if (v465 == false)
            {
                block = 2;
                break;
            }
            main_t_0 = v463;
            v661 = msg_1;
            block = 29;
            break;
            case 2:
            v467 = ll_dict_getitem__Dict_String__String__String ( msg_2,__consts_0.const_str__47 );
            v468 = ll_streq__String_String ( v467,__consts_0.const_str__49 );
            msg_3 = msg_2;
            if (v468 == false)
            {
                block = 3;
                break;
            }
            msg_20 = msg_2;
            block = 28;
            break;
            case 3:
            v470 = ll_dict_getitem__Dict_String__String__String ( msg_3,__consts_0.const_str__47 );
            v471 = ll_streq__String_String ( v470,__consts_0.const_str__50 );
            msg_4 = msg_3;
            if (v471 == false)
            {
                block = 4;
                break;
            }
            msg_19 = msg_3;
            block = 27;
            break;
            case 4:
            v473 = ll_dict_getitem__Dict_String__String__String ( msg_4,__consts_0.const_str__47 );
            v474 = ll_streq__String_String ( v473,__consts_0.const_str__51 );
            msg_5 = msg_4;
            if (v474 == false)
            {
                block = 5;
                break;
            }
            msg_17 = msg_4;
            block = 24;
            break;
            case 5:
            v476 = ll_dict_getitem__Dict_String__String__String ( msg_5,__consts_0.const_str__47 );
            v477 = ll_streq__String_String ( v476,__consts_0.const_str__52 );
            msg_6 = msg_5;
            if (v477 == false)
            {
                block = 6;
                break;
            }
            msg_16 = msg_5;
            block = 23;
            break;
            case 6:
            v479 = ll_dict_getitem__Dict_String__String__String ( msg_6,__consts_0.const_str__47 );
            v480 = ll_streq__String_String ( v479,__consts_0.const_str__53 );
            msg_7 = msg_6;
            if (v480 == false)
            {
                block = 7;
                break;
            }
            msg_13 = msg_6;
            block = 20;
            break;
            case 7:
            v482 = ll_dict_getitem__Dict_String__String__String ( msg_7,__consts_0.const_str__47 );
            v483 = ll_streq__String_String ( v482,__consts_0.const_str__54 );
            msg_8 = msg_7;
            if (v483 == false)
            {
                block = 8;
                break;
            }
            msg_10 = msg_7;
            block = 17;
            break;
            case 8:
            v485 = ll_dict_getitem__Dict_String__String__String ( msg_8,__consts_0.const_str__47 );
            v486 = ll_streq__String_String ( v485,__consts_0.const_str__55 );
            msg_9 = msg_8;
            if (v486 == false)
            {
                block = 9;
                break;
            }
            block = 16;
            break;
            case 9:
            v488 = ll_dict_getitem__Dict_String__String__String ( msg_9,__consts_0.const_str__47 );
            v489 = ll_streq__String_String ( v488,__consts_0.const_str__56 );
            v491 = msg_9;
            if (v489 == false)
            {
                block = 10;
                break;
            }
            block = 15;
            break;
            case 10:
            v492 = ll_dict_getitem__Dict_String__String__String ( v491,__consts_0.const_str__47 );
            v493 = ll_streq__String_String ( v492,__consts_0.const_str__57 );
            if (v493 == false)
            {
                block = 11;
                break;
            }
            block = 14;
            break;
            case 11:
            v495 = __consts_0.py____test_rsession_webjs_Globals.odata_empty;
            v456 = true;
            if (v495 == false)
            {
                block = 12;
                break;
            }
            block = 13;
            break;
            case 13:
            v497 = __consts_0.Document;
            v498 = v497.getElementById(__consts_0.const_str__33);
            scroll_down_if_needed ( v498 );
            v456 = true;
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
            v503 = ll_dict_getitem__Dict_String__String__String ( msg_10,__consts_0.const_str__58 );
            v504 = get_elem ( v503 );
            v505 = !!v504;
            msg_11 = msg_10;
            if (v505 == false)
            {
                block = 18;
                break;
            }
            msg_12 = msg_10;
            module_part_0 = v504;
            block = 19;
            break;
            case 18:
            v506 = __consts_0.py____test_rsession_webjs_Globals.opending;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v506,msg_11 );
            v456 = true;
            block = 12;
            break;
            case 19:
            v509 = create_elem ( __consts_0.const_str__17 );
            v510 = create_elem ( __consts_0.const_str__18 );
            v511 = ll_dict_getitem__Dict_String__String__String ( msg_12,__consts_0.const_str__59 );
            v512 = new Object();
            v512.item0 = v511;
            v514 = v512.item0;
            v515 = new StringBuilder();
            v515.ll_append(__consts_0.const_str__60);
            v517 = ll_str__StringR_StringConst_String ( v514 );
            v515.ll_append(v517);
            v515.ll_append(__consts_0.const_str__61);
            v520 = v515.ll_build();
            v521 = create_text_elem ( v520 );
            v510.appendChild(v521);
            v509.appendChild(v510);
            module_part_0.appendChild(v509);
            block = 11;
            break;
            case 20:
            v528 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__58 );
            v529 = get_elem ( v528 );
            v530 = !!v529;
            msg_14 = msg_13;
            if (v530 == false)
            {
                block = 21;
                break;
            }
            msg_15 = msg_13;
            module_part_1 = v529;
            block = 22;
            break;
            case 21:
            v531 = __consts_0.py____test_rsession_webjs_Globals.opending;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v531,msg_14 );
            v456 = true;
            block = 12;
            break;
            case 22:
            v534 = create_elem ( __consts_0.const_str__17 );
            v535 = create_elem ( __consts_0.const_str__18 );
            v536 = create_elem ( __consts_0.const_str__62 );
            v538 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__58 );
            v539 = new Object();
            v539.item0 = v538;
            v541 = v539.item0;
            v542 = new StringBuilder();
            v542.ll_append(__consts_0.const_str__63);
            v544 = ll_str__StringR_StringConst_String ( v541 );
            v542.ll_append(v544);
            v542.ll_append(__consts_0.const_str__29);
            v547 = v542.ll_build();
            v536.setAttribute(__consts_0.const_str__64,v547);
            v549 = create_text_elem ( __consts_0.const_str__65 );
            v536.appendChild(v549);
            v535.appendChild(v536);
            v534.appendChild(v535);
            module_part_1.appendChild(v534);
            v558 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__58 );
            v559 = __consts_0.ExportedMethods;
            v560 = v559.show_fail(v558,fail_come_back);
            block = 11;
            break;
            case 23:
            v561 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__66 );
            v562 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__67 );
            v563 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__68 );
            v564 = new Object();
            v564.item0 = v561;
            v564.item1 = v562;
            v564.item2 = v563;
            v568 = v564.item0;
            v569 = v564.item1;
            v570 = v564.item2;
            v571 = new StringBuilder();
            v571.ll_append(__consts_0.const_str__69);
            v573 = ll_str__StringR_StringConst_String ( v568 );
            v571.ll_append(v573);
            v571.ll_append(__consts_0.const_str__70);
            v576 = ll_str__StringR_StringConst_String ( v569 );
            v571.ll_append(v576);
            v571.ll_append(__consts_0.const_str__71);
            v579 = ll_str__StringR_StringConst_String ( v570 );
            v571.ll_append(v579);
            v571.ll_append(__consts_0.const_str__72);
            v582 = v571.ll_build();
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            v584 = new StringBuilder();
            v584.ll_append(__consts_0.const_str__73);
            v586 = ll_str__StringR_StringConst_String ( v582 );
            v584.ll_append(v586);
            v588 = v584.ll_build();
            __consts_0.Document.title = v588;
            v590 = new StringBuilder();
            v590.ll_append(__consts_0.const_str__39);
            v592 = ll_str__StringR_StringConst_String ( v582 );
            v590.ll_append(v592);
            v590.ll_append(__consts_0.const_str__40);
            v595 = v590.ll_build();
            v596 = __consts_0.Document;
            v597 = v596.getElementById(__consts_0.const_str__37);
            v598 = v597.childNodes;
            v599 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v598,0 );
            v599.nodeValue = v595;
            block = 11;
            break;
            case 24:
            v601 = ll_dict_getitem__Dict_String__String__String ( msg_17,__consts_0.const_str__74 );
            v602 = get_elem ( v601 );
            v603 = !!v602;
            msg_18 = msg_17;
            if (v603 == false)
            {
                block = 25;
                break;
            }
            v607 = msg_17;
            v608 = v602;
            block = 26;
            break;
            case 25:
            v604 = __consts_0.py____test_rsession_webjs_Globals.opending;
            ll_append__List_Dict_String__String___Dict_String__String_ ( v604,msg_18 );
            v456 = true;
            block = 12;
            break;
            case 26:
            add_received_item_outcome ( v607,v608 );
            block = 11;
            break;
            case 27:
            v610 = __consts_0.Document;
            v611 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__75 );
            v612 = v610.getElementById(v611);
            v613 = v612.style;
            v613.background = __consts_0.const_str__76;
            v615 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v616 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__75 );
            v617 = ll_dict_getitem__Dict_String__String__String ( v615,v616 );
            v618 = new Object();
            v618.item0 = v617;
            v620 = v618.item0;
            v621 = new StringBuilder();
            v622 = ll_str__StringR_StringConst_String ( v620 );
            v621.ll_append(v622);
            v621.ll_append(__consts_0.const_str__77);
            v625 = v621.ll_build();
            v626 = v612.childNodes;
            v627 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v626,0 );
            v627.nodeValue = v625;
            block = 11;
            break;
            case 28:
            v629 = __consts_0.Document;
            v630 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v631 = v629.getElementById(v630);
            v632 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v633 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v634 = ll_dict_getitem__Dict_String__List_String___String ( v632,v633 );
            v636 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__58 );
            ll_prepend__List_String__String ( v634,v636 );
            v638 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v639 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v640 = ll_dict_getitem__Dict_String__List_String___String ( v638,v639 );
            v641 = ll_len__List_String_ ( v640 );
            v642 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v643 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__75 );
            v644 = ll_dict_getitem__Dict_String__String__String ( v642,v643 );
            v645 = new Object();
            v645.item0 = v644;
            v645.item1 = v641;
            v648 = v645.item0;
            v649 = v645.item1;
            v650 = new StringBuilder();
            v651 = ll_str__StringR_StringConst_String ( v648 );
            v650.ll_append(v651);
            v650.ll_append(__consts_0.const_str__78);
            v654 = ll_int_str__IntegerR_SignedConst_Signed ( v649 );
            v650.ll_append(v654);
            v650.ll_append(__consts_0.const_str__40);
            v657 = v650.ll_build();
            v658 = v631.childNodes;
            v659 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v658,0 );
            v659.nodeValue = v657;
            block = 11;
            break;
            case 29:
            v662 = make_module_box ( v661 );
            main_t_0.appendChild(v662);
            block = 11;
            break;
            case 12:
            return ( v456 );
        }
    }
}

function fail_come_back (msg_21) {
    var v703,v704,v705,v706,v710;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v703 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__79 );
            v704 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__80 );
            v705 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__81 );
            v706 = new Object();
            v706.item0 = v703;
            v706.item1 = v704;
            v706.item2 = v705;
            v710 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__82 );
            __consts_0.const_tuple__21[v710]=v706;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_len__List_Dict_String__String__ (l_5) {
    var v417,v418,v419;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v419 = l_5.length;
            v417 = v419;
            block = 1;
            break;
            case 1:
            return ( v417 );
        }
    }
}

function ll_int_str__IntegerR_SignedConst_Signed (i_6) {
    var v880,v881;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v881 = ll_int2dec__Signed ( i_6 );
            v880 = v881;
            block = 1;
            break;
            case 1:
            return ( v880 );
        }
    }
}

function add_received_item_outcome (msg_22,module_part_2) {
    var v713,v714,v715,msg_23,module_part_3,v716,v717,v718,v719,v721,v722,v724,v727,v729,v731,v732,v733,v734,msg_24,module_part_4,td_0,item_name_6,v735,v736,v737,v738,msg_25,module_part_5,td_1,item_name_7,v739,v740,v741,v742,v744,v745,v747,v750,v752,v753,v755,v757,v759,v760,msg_26,module_part_6,td_2,v761,v762,v763,v764,module_part_7,td_3,v765,v766,v767,v768,v770,v771,v772,v773,v774,v775,v779,v780,v781,v782,v783,v786,v789,v792,v793,v794,v796,v797,v798,msg_27,module_part_8,td_4,v800,v801,msg_28,module_part_9,td_5,item_name_8,v803,v804,v805,v806,msg_29,module_part_10,td_6,item_name_9,v807,v808,v809,v810,v811,v812,v814,v815,v817,v820,v822,v823,v825,msg_30,module_part_11,td_7,v827,v828,msg_31,module_part_12,v830,v831,v832,v833,v834,v835,v836,v837,v838,v839,v840,v841,v842,v843,v844,v845,v848,v849,v850,v851,v854,v857,v858,v859;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v713 = ll_dict_getitem__Dict_String__String__String ( msg_22,__consts_0.const_str__75 );
            v714 = ll_strlen__String ( v713 );
            v715 = !!v714;
            msg_23 = msg_22;
            module_part_3 = module_part_2;
            if (v715 == false)
            {
                block = 1;
                break;
            }
            msg_31 = msg_22;
            module_part_12 = module_part_2;
            block = 11;
            break;
            case 1:
            v716 = create_elem ( __consts_0.const_str__18 );
            v718 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__58 );
            v719 = new Object();
            v719.item0 = v718;
            v721 = v719.item0;
            v722 = new StringBuilder();
            v722.ll_append(__consts_0.const_str__83);
            v724 = ll_str__StringR_StringConst_String ( v721 );
            v722.ll_append(v724);
            v722.ll_append(__consts_0.const_str__29);
            v727 = v722.ll_build();
            v716.setAttribute(__consts_0.const_str__30,v727);
            v716.setAttribute(__consts_0.const_str__31,__consts_0.const_str__84);
            v731 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__58 );
            v732 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__85 );
            v733 = ll_streq__String_String ( v732,__consts_0.const_str__6 );
            msg_24 = msg_23;
            module_part_4 = module_part_3;
            td_0 = v716;
            item_name_6 = v731;
            if (v733 == false)
            {
                block = 2;
                break;
            }
            msg_30 = msg_23;
            module_part_11 = module_part_3;
            td_7 = v716;
            block = 10;
            break;
            case 2:
            v735 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__86 );
            v736 = ll_streq__String_String ( v735,__consts_0.const_str__87 );
            v737 = !v736;
            msg_25 = msg_24;
            module_part_5 = module_part_4;
            td_1 = td_0;
            item_name_7 = item_name_6;
            if (v737 == false)
            {
                block = 3;
                break;
            }
            msg_28 = msg_24;
            module_part_9 = module_part_4;
            td_5 = td_0;
            item_name_8 = item_name_6;
            block = 8;
            break;
            case 3:
            v739 = create_elem ( __consts_0.const_str__62 );
            v741 = ll_dict_getitem__Dict_String__String__String ( msg_25,__consts_0.const_str__58 );
            v742 = new Object();
            v742.item0 = v741;
            v744 = v742.item0;
            v745 = new StringBuilder();
            v745.ll_append(__consts_0.const_str__63);
            v747 = ll_str__StringR_StringConst_String ( v744 );
            v745.ll_append(v747);
            v745.ll_append(__consts_0.const_str__29);
            v750 = v745.ll_build();
            v739.setAttribute(__consts_0.const_str__64,v750);
            v752 = create_text_elem ( __consts_0.const_str__88 );
            v739.setAttribute(__consts_0.const_str__89,__consts_0.const_str__90);
            v739.appendChild(v752);
            td_1.appendChild(v739);
            v759 = __consts_0.ExportedMethods;
            v760 = v759.show_fail(item_name_7,fail_come_back);
            msg_26 = msg_25;
            module_part_6 = module_part_5;
            td_2 = td_1;
            block = 4;
            break;
            case 4:
            v761 = ll_dict_getitem__Dict_String__String__String ( msg_26,__consts_0.const_str__74 );
            v762 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__91,v761 );
            v763 = (v762==0);
            module_part_7 = module_part_6;
            td_3 = td_2;
            v765 = msg_26;
            if (v763 == false)
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
            v766 = ll_dict_getitem__Dict_String__String__String ( v765,__consts_0.const_str__74 );
            v767 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__91,v766 );
            v768 = (v767+1);
            __consts_0.const_tuple__91[v766]=v768;
            v770 = ll_strconcat__String_String ( __consts_0.const_str__92,v766 );
            v771 = get_elem ( v770 );
            v772 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__93,v766 );
            v773 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__91,v766 );
            v774 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__94,v766 );
            v775 = new Object();
            v775.item0 = v772;
            v775.item1 = v773;
            v775.item2 = v774;
            v779 = v775.item0;
            v780 = v775.item1;
            v781 = v775.item2;
            v782 = new StringBuilder();
            v783 = ll_str__StringR_StringConst_String ( v779 );
            v782.ll_append(v783);
            v782.ll_append(__consts_0.const_str__78);
            v786 = convertToString ( v780 );
            v782.ll_append(v786);
            v782.ll_append(__consts_0.const_str__95);
            v789 = convertToString ( v781 );
            v782.ll_append(v789);
            v782.ll_append(__consts_0.const_str__40);
            v792 = v782.ll_build();
            v793 = v771.childNodes;
            v794 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v793,0 );
            v794.nodeValue = v792;
            v796 = module_part_7.childNodes;
            v797 = ll_getitem__dum_nocheckConst_List_ExternalType_Element___Signed ( v796,-1 );
            v797.appendChild(td_3);
            block = 6;
            break;
            case 7:
            v800 = create_elem ( __consts_0.const_str__17 );
            module_part_8.appendChild(v800);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v765 = msg_27;
            block = 5;
            break;
            case 8:
            v803 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__86 );
            v804 = ll_streq__String_String ( v803,__consts_0.const_str__96 );
            v805 = !v804;
            msg_25 = msg_28;
            module_part_5 = module_part_9;
            td_1 = td_5;
            item_name_7 = item_name_8;
            if (v805 == false)
            {
                block = 3;
                break;
            }
            msg_29 = msg_28;
            module_part_10 = module_part_9;
            td_6 = td_5;
            item_name_9 = item_name_8;
            block = 9;
            break;
            case 9:
            v807 = __consts_0.ExportedMethods;
            v808 = v807.show_skip(item_name_9,skip_come_back);
            v809 = create_elem ( __consts_0.const_str__62 );
            v811 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__58 );
            v812 = new Object();
            v812.item0 = v811;
            v814 = v812.item0;
            v815 = new StringBuilder();
            v815.ll_append(__consts_0.const_str__97);
            v817 = ll_str__StringR_StringConst_String ( v814 );
            v815.ll_append(v817);
            v815.ll_append(__consts_0.const_str__29);
            v820 = v815.ll_build();
            v809.setAttribute(__consts_0.const_str__64,v820);
            v822 = create_text_elem ( __consts_0.const_str__98 );
            v809.appendChild(v822);
            td_6.appendChild(v809);
            msg_26 = msg_29;
            module_part_6 = module_part_10;
            td_2 = td_6;
            block = 4;
            break;
            case 10:
            v827 = create_text_elem ( __consts_0.const_str__99 );
            td_7.appendChild(v827);
            msg_26 = msg_30;
            module_part_6 = module_part_11;
            td_2 = td_7;
            block = 4;
            break;
            case 11:
            v830 = __consts_0.Document;
            v831 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v832 = v830.getElementById(v831);
            v833 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v834 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v835 = ll_dict_getitem__Dict_String__List_String___String ( v833,v834 );
            v837 = ll_pop_default__dum_nocheckConst_List_String_ ( v835 );
            v838 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v839 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v840 = ll_dict_getitem__Dict_String__List_String___String ( v838,v839 );
            v841 = ll_len__List_String_ ( v840 );
            v842 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v843 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v844 = ll_dict_getitem__Dict_String__String__String ( v842,v843 );
            v845 = new Object();
            v845.item0 = v844;
            v845.item1 = v841;
            v848 = v845.item0;
            v849 = v845.item1;
            v850 = new StringBuilder();
            v851 = ll_str__StringR_StringConst_String ( v848 );
            v850.ll_append(v851);
            v850.ll_append(__consts_0.const_str__78);
            v854 = ll_int_str__IntegerR_SignedConst_Signed ( v849 );
            v850.ll_append(v854);
            v850.ll_append(__consts_0.const_str__40);
            v857 = v850.ll_build();
            v858 = v832.childNodes;
            v859 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v858,0 );
            v859.nodeValue = v857;
            msg_23 = msg_31;
            module_part_3 = module_part_12;
            block = 1;
            break;
            case 6:
            return ( undefined );
        }
    }
}

function make_module_box (msg_32) {
    var v882,v883,v884,v885,v887,v888,v889,v890,v893,v894,v895,v896,v899,v902,v903,v905,v906,v907,v909,v910,v912,v913,v915,v916,v917,v919,v920,v922,v925,v927,v929,v930,v932,v933,v935,v936,v938,v940;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v883 = create_elem ( __consts_0.const_str__17 );
            v884 = create_elem ( __consts_0.const_str__18 );
            v883.appendChild(v884);
            v888 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__100 );
            v889 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__101 );
            v890 = new Object();
            v890.item0 = v888;
            v890.item1 = v889;
            v893 = v890.item0;
            v894 = v890.item1;
            v895 = new StringBuilder();
            v896 = ll_str__StringR_StringConst_String ( v893 );
            v895.ll_append(v896);
            v895.ll_append(__consts_0.const_str__102);
            v899 = ll_str__StringR_StringConst_String ( v894 );
            v895.ll_append(v899);
            v895.ll_append(__consts_0.const_str__40);
            v902 = v895.ll_build();
            v903 = create_text_elem ( v902 );
            v884.appendChild(v903);
            v905 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__101 );
            v906 = ll_int__String_Signed ( v905,10 );
            v907 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__94[v907]=v906;
            v909 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__100 );
            v910 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__93[v910]=v909;
            v912 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v913 = ll_strconcat__String_String ( __consts_0.const_str__92,v912 );
            v884.id = v913;
            v916 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v917 = new Object();
            v917.item0 = v916;
            v919 = v917.item0;
            v920 = new StringBuilder();
            v920.ll_append(__consts_0.const_str__83);
            v922 = ll_str__StringR_StringConst_String ( v919 );
            v920.ll_append(v922);
            v920.ll_append(__consts_0.const_str__29);
            v925 = v920.ll_build();
            v884.setAttribute(__consts_0.const_str__30,v925);
            v884.setAttribute(__consts_0.const_str__31,__consts_0.const_str__84);
            v929 = create_elem ( __consts_0.const_str__18 );
            v883.appendChild(v929);
            v932 = create_elem ( __consts_0.const_str__103 );
            v929.appendChild(v932);
            v935 = create_elem ( __consts_0.const_str__16 );
            v936 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v935.id = v936;
            v932.appendChild(v935);
            v940 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__91[v940]=0;
            v882 = v883;
            block = 1;
            break;
            case 1:
            return ( v882 );
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed_0 (length_5) {
    var v667,v668,v669;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v668 = new Array();
            v668.length = length_5;
            v667 = v668;
            block = 1;
            break;
            case 1:
            return ( v667 );
        }
    }
}

function ll_pop_default__dum_nocheckConst_List_String_ (l_17) {
    var v975,v976,v977,l_18,length_8,v978,v980,v981,v982,newlength_0,res_0,v984,v985;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v977 = l_17.length;
            l_18 = l_17;
            length_8 = v977;
            block = 1;
            break;
            case 1:
            v978 = (length_8>0);
            v980 = (length_8-1);
            v982 = l_18[v980];
            ll_null_item__List_String_ ( l_18 );
            newlength_0 = v980;
            res_0 = v982;
            v984 = l_18;
            block = 2;
            break;
            case 2:
            v984.length = newlength_0;
            v975 = res_0;
            block = 3;
            break;
            case 3:
            return ( v975 );
        }
    }
}

function ll_len__List_String_ (l_13) {
    var v877,v878,v879;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v879 = l_13.length;
            v877 = v879;
            block = 1;
            break;
            case 1:
            return ( v877 );
        }
    }
}

function show_interrupt () {
    var v689,v690,v691,v692;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__104;
            v689 = __consts_0.Document;
            v690 = v689.getElementById(__consts_0.const_str__37);
            v691 = v690.childNodes;
            v692 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v691,0 );
            v692.nodeValue = __consts_0.const_str__105;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function show_crash () {
    var v681,v682,v683,v684;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__106;
            v681 = __consts_0.Document;
            v682 = v681.getElementById(__consts_0.const_str__37);
            v683 = v682.childNodes;
            v684 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType_Element___Signed ( v683,0 );
            v684.nodeValue = __consts_0.const_str__107;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_append__List_Dict_String__String___Dict_String__String_ (l_9,newitem_0) {
    var v695,v696,v697,v698,v700;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v696 = l_9.length;
            v698 = (v696+1);
            l_9.length = v698;
            l_9[v696]=newitem_0;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_prepend__List_String__String (l_10,newitem_1) {
    var v862,v863,v864,v865,l_11,newitem_2,dst_0,v867,v868,newitem_3,v869,v870,l_12,newitem_4,dst_1,v872,v873,v874,v875;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v863 = l_10.length;
            v865 = (v863+1);
            l_10.length = v865;
            l_11 = l_10;
            newitem_2 = newitem_1;
            dst_0 = v863;
            block = 1;
            break;
            case 1:
            v867 = (dst_0>0);
            newitem_3 = newitem_2;
            v869 = l_11;
            if (v867 == false)
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
            v869[0]=newitem_3;
            block = 3;
            break;
            case 4:
            v872 = (dst_1-1);
            v875 = l_12[v872];
            l_12[dst_1]=v875;
            l_11 = l_12;
            newitem_2 = newitem_4;
            dst_0 = v872;
            block = 1;
            break;
            case 3:
            return ( undefined );
        }
    }
}

function scroll_down_if_needed (mbox_2) {
    var v672,v673,v674,v675,v676;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v672 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            if (v672 == false)
            {
                block = 1;
                break;
            }
            v674 = mbox_2;
            block = 2;
            break;
            case 2:
            v675 = v674.parentNode;
            v675.scrollIntoView();
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

function ll_int2dec__Signed (i_7) {
    var v942,v943;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v943 = convertToString ( i_7 );
            v942 = v943;
            block = 1;
            break;
            case 1:
            return ( v942 );
        }
    }
}

function skip_come_back (msg_33) {
    var v972,v973;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v972 = ll_dict_getitem__Dict_String__String__String ( msg_33,__consts_0.const_str__59 );
            v973 = ll_dict_getitem__Dict_String__String__String ( msg_33,__consts_0.const_str__82 );
            __consts_0.const_tuple__19[v973]=v972;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_strlen__String (obj_1) {
    var v944,v945,v946;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v946 = obj_1.length;
            v944 = v946;
            block = 1;
            break;
            case 1:
            return ( v944 );
        }
    }
}

function ll_getitem__dum_nocheckConst_List_ExternalType_Element___Signed (l_14,index_5) {
    var v957,v958,v959,v960,v961,l_15,index_6,length_6,v962,v964,index_7,v966,v967,v968,l_16,length_7,v969,v970;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v959 = l_14.length;
            v960 = (index_5<0);
            l_15 = l_14;
            index_6 = index_5;
            length_6 = v959;
            if (v960 == false)
            {
                block = 1;
                break;
            }
            l_16 = l_14;
            length_7 = v959;
            v969 = index_5;
            block = 4;
            break;
            case 1:
            v962 = (index_6>=0);
            v964 = (index_6<length_6);
            index_7 = index_6;
            v966 = l_15;
            block = 2;
            break;
            case 2:
            v968 = v966[index_7];
            v957 = v968;
            block = 3;
            break;
            case 4:
            v970 = (v969+length_7);
            l_15 = l_16;
            index_6 = v970;
            length_6 = length_7;
            block = 1;
            break;
            case 3:
            return ( v957 );
        }
    }
}

function ll_int__String_Signed (s_2,base_0) {
    var v987,v988,v989,v990,v991,v992,etype_7,evalue_7,s_3,base_1,v993,s_4,base_2,v994,v995,s_5,base_3,v996,v997,s_6,base_4,strlen_0,i_8,v998,v999,s_7,base_5,strlen_1,i_9,v1000,v1001,v1002,v1003,v1004,s_8,base_6,strlen_2,i_10,v1005,v1006,v1007,v1008,s_9,base_7,strlen_3,i_11,v1009,v1010,v1011,v1012,s_10,base_8,strlen_4,i_12,sign_0,v1013,v1014,s_11,base_9,strlen_5,i_13,sign_1,val_0,oldpos_0,v1015,v1016,s_12,strlen_6,i_14,sign_2,val_1,v1017,v1018,v1019,s_13,strlen_7,i_15,sign_3,val_2,v1020,v1021,sign_4,val_3,v1022,v1023,v1024,v1025,v1026,v1027,v1028,v1029,v1030,v1031,s_14,strlen_8,i_16,sign_5,val_4,v1032,v1033,v1034,v1035,s_15,strlen_9,sign_6,val_5,v1036,v1037,v1038,v1039,v1040,s_16,base_10,strlen_10,i_17,sign_7,val_6,oldpos_1,v1041,v1042,v1043,v1044,v1045,s_17,base_11,strlen_11,i_18,sign_8,val_7,oldpos_2,c_0,v1046,v1047,s_18,base_12,strlen_12,i_19,sign_9,val_8,oldpos_3,c_1,v1048,v1049,s_19,base_13,strlen_13,i_20,sign_10,val_9,oldpos_4,c_2,v1050,s_20,base_14,strlen_14,i_21,sign_11,val_10,oldpos_5,c_3,v1051,v1052,s_21,base_15,strlen_15,i_22,sign_12,val_11,oldpos_6,v1053,v1054,s_22,base_16,strlen_16,i_23,sign_13,val_12,oldpos_7,digit_0,v1055,v1056,s_23,base_17,strlen_17,i_24,sign_14,oldpos_8,digit_1,v1057,v1058,v1059,v1060,s_24,base_18,strlen_18,i_25,sign_15,val_13,oldpos_9,c_4,v1061,s_25,base_19,strlen_19,i_26,sign_16,val_14,oldpos_10,c_5,v1062,v1063,s_26,base_20,strlen_20,i_27,sign_17,val_15,oldpos_11,v1064,v1065,v1066,s_27,base_21,strlen_21,i_28,sign_18,val_16,oldpos_12,c_6,v1067,s_28,base_22,strlen_22,i_29,sign_19,val_17,oldpos_13,c_7,v1068,v1069,s_29,base_23,strlen_23,i_30,sign_20,val_18,oldpos_14,v1070,v1071,v1072,s_30,base_24,strlen_24,i_31,sign_21,v1073,v1074,v1075,v1076,s_31,base_25,strlen_25,sign_22,v1077,v1078,s_32,base_26,strlen_26,v1079,v1080,s_33,base_27,strlen_27,v1081,v1082,s_34,base_28,strlen_28,i_32,v1083,v1084,v1085,v1086,s_35,base_29,strlen_29,v1087,v1088;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v988 = (2<=base_0);
            if (v988 == false)
            {
                block = 1;
                break;
            }
            s_3 = s_2;
            base_1 = base_0;
            block = 3;
            break;
            case 1:
            v990 = __consts_0.exceptions_ValueError;
            v991 = v990.meta;
            etype_7 = v991;
            evalue_7 = v990;
            block = 2;
            break;
            case 3:
            v993 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v994 = v993;
            block = 4;
            break;
            case 4:
            if (v994 == false)
            {
                block = 1;
                break;
            }
            s_5 = s_4;
            base_3 = base_2;
            block = 5;
            break;
            case 5:
            v997 = s_5.length;
            s_6 = s_5;
            base_4 = base_3;
            strlen_0 = v997;
            i_8 = 0;
            block = 6;
            break;
            case 6:
            v998 = (i_8<strlen_0);
            s_7 = s_6;
            base_5 = base_4;
            strlen_1 = strlen_0;
            i_9 = i_8;
            if (v998 == false)
            {
                block = 7;
                break;
            }
            s_34 = s_6;
            base_28 = base_4;
            strlen_28 = strlen_0;
            i_32 = i_8;
            block = 40;
            break;
            case 7:
            v1000 = (i_9<strlen_1);
            if (v1000 == false)
            {
                block = 8;
                break;
            }
            s_8 = s_7;
            base_6 = base_5;
            strlen_2 = strlen_1;
            i_10 = i_9;
            block = 9;
            break;
            case 8:
            v1002 = __consts_0.exceptions_ValueError;
            v1003 = v1002.meta;
            etype_7 = v1003;
            evalue_7 = v1002;
            block = 2;
            break;
            case 9:
            v1006 = s_8.charAt(i_10);
            v1007 = (v1006=='-');
            s_9 = s_8;
            base_7 = base_6;
            strlen_3 = strlen_2;
            i_11 = i_10;
            if (v1007 == false)
            {
                block = 10;
                break;
            }
            s_33 = s_8;
            base_27 = base_6;
            strlen_27 = strlen_2;
            v1081 = i_10;
            block = 39;
            break;
            case 10:
            v1010 = s_9.charAt(i_11);
            v1011 = (v1010=='+');
            s_10 = s_9;
            base_8 = base_7;
            strlen_4 = strlen_3;
            i_12 = i_11;
            sign_0 = 1;
            if (v1011 == false)
            {
                block = 11;
                break;
            }
            s_32 = s_9;
            base_26 = base_7;
            strlen_26 = strlen_3;
            v1079 = i_11;
            block = 38;
            break;
            case 11:
            v1013 = (i_12<strlen_4);
            s_11 = s_10;
            base_9 = base_8;
            strlen_5 = strlen_4;
            i_13 = i_12;
            sign_1 = sign_0;
            val_0 = 0;
            oldpos_0 = i_12;
            if (v1013 == false)
            {
                block = 12;
                break;
            }
            s_30 = s_10;
            base_24 = base_8;
            strlen_24 = strlen_4;
            i_31 = i_12;
            sign_21 = sign_0;
            block = 36;
            break;
            case 12:
            v1015 = (i_13<strlen_5);
            s_12 = s_11;
            strlen_6 = strlen_5;
            i_14 = i_13;
            sign_2 = sign_1;
            val_1 = val_0;
            v1017 = oldpos_0;
            if (v1015 == false)
            {
                block = 13;
                break;
            }
            s_16 = s_11;
            base_10 = base_9;
            strlen_10 = strlen_5;
            i_17 = i_13;
            sign_7 = sign_1;
            val_6 = val_0;
            oldpos_1 = oldpos_0;
            block = 22;
            break;
            case 13:
            v1018 = (i_14==v1017);
            s_13 = s_12;
            strlen_7 = strlen_6;
            i_15 = i_14;
            sign_3 = sign_2;
            val_2 = val_1;
            if (v1018 == false)
            {
                block = 14;
                break;
            }
            block = 21;
            break;
            case 14:
            v1020 = (i_15<strlen_7);
            sign_4 = sign_3;
            val_3 = val_2;
            v1022 = i_15;
            v1023 = strlen_7;
            if (v1020 == false)
            {
                block = 15;
                break;
            }
            s_14 = s_13;
            strlen_8 = strlen_7;
            i_16 = i_15;
            sign_5 = sign_3;
            val_4 = val_2;
            block = 19;
            break;
            case 15:
            v1024 = (v1022==v1023);
            if (v1024 == false)
            {
                block = 16;
                break;
            }
            v1029 = sign_4;
            v1030 = val_3;
            block = 17;
            break;
            case 16:
            v1026 = __consts_0.exceptions_ValueError;
            v1027 = v1026.meta;
            etype_7 = v1027;
            evalue_7 = v1026;
            block = 2;
            break;
            case 17:
            v1031 = (v1029*v1030);
            v987 = v1031;
            block = 18;
            break;
            case 19:
            v1033 = s_14.charAt(i_16);
            v1034 = (v1033==' ');
            sign_4 = sign_5;
            val_3 = val_4;
            v1022 = i_16;
            v1023 = strlen_8;
            if (v1034 == false)
            {
                block = 15;
                break;
            }
            s_15 = s_14;
            strlen_9 = strlen_8;
            sign_6 = sign_5;
            val_5 = val_4;
            v1036 = i_16;
            block = 20;
            break;
            case 20:
            v1037 = (v1036+1);
            s_13 = s_15;
            strlen_7 = strlen_9;
            i_15 = v1037;
            sign_3 = sign_6;
            val_2 = val_5;
            block = 14;
            break;
            case 21:
            v1038 = __consts_0.exceptions_ValueError;
            v1039 = v1038.meta;
            etype_7 = v1039;
            evalue_7 = v1038;
            block = 2;
            break;
            case 22:
            v1042 = s_16.charAt(i_17);
            v1043 = v1042.charCodeAt(0);
            v1044 = (97<=v1043);
            s_17 = s_16;
            base_11 = base_10;
            strlen_11 = strlen_10;
            i_18 = i_17;
            sign_8 = sign_7;
            val_7 = val_6;
            oldpos_2 = oldpos_1;
            c_0 = v1043;
            if (v1044 == false)
            {
                block = 23;
                break;
            }
            s_27 = s_16;
            base_21 = base_10;
            strlen_21 = strlen_10;
            i_28 = i_17;
            sign_18 = sign_7;
            val_16 = val_6;
            oldpos_12 = oldpos_1;
            c_6 = v1043;
            block = 33;
            break;
            case 23:
            v1046 = (65<=c_0);
            s_18 = s_17;
            base_12 = base_11;
            strlen_12 = strlen_11;
            i_19 = i_18;
            sign_9 = sign_8;
            val_8 = val_7;
            oldpos_3 = oldpos_2;
            c_1 = c_0;
            if (v1046 == false)
            {
                block = 24;
                break;
            }
            s_24 = s_17;
            base_18 = base_11;
            strlen_18 = strlen_11;
            i_25 = i_18;
            sign_15 = sign_8;
            val_13 = val_7;
            oldpos_9 = oldpos_2;
            c_4 = c_0;
            block = 30;
            break;
            case 24:
            v1048 = (48<=c_1);
            s_12 = s_18;
            strlen_6 = strlen_12;
            i_14 = i_19;
            sign_2 = sign_9;
            val_1 = val_8;
            v1017 = oldpos_3;
            if (v1048 == false)
            {
                block = 13;
                break;
            }
            s_19 = s_18;
            base_13 = base_12;
            strlen_13 = strlen_12;
            i_20 = i_19;
            sign_10 = sign_9;
            val_9 = val_8;
            oldpos_4 = oldpos_3;
            c_2 = c_1;
            block = 25;
            break;
            case 25:
            v1050 = (c_2<=57);
            s_20 = s_19;
            base_14 = base_13;
            strlen_14 = strlen_13;
            i_21 = i_20;
            sign_11 = sign_10;
            val_10 = val_9;
            oldpos_5 = oldpos_4;
            c_3 = c_2;
            v1051 = v1050;
            block = 26;
            break;
            case 26:
            s_12 = s_20;
            strlen_6 = strlen_14;
            i_14 = i_21;
            sign_2 = sign_11;
            val_1 = val_10;
            v1017 = oldpos_5;
            if (v1051 == false)
            {
                block = 13;
                break;
            }
            s_21 = s_20;
            base_15 = base_14;
            strlen_15 = strlen_14;
            i_22 = i_21;
            sign_12 = sign_11;
            val_11 = val_10;
            oldpos_6 = oldpos_5;
            v1053 = c_3;
            block = 27;
            break;
            case 27:
            v1054 = (v1053-48);
            s_22 = s_21;
            base_16 = base_15;
            strlen_16 = strlen_15;
            i_23 = i_22;
            sign_13 = sign_12;
            val_12 = val_11;
            oldpos_7 = oldpos_6;
            digit_0 = v1054;
            block = 28;
            break;
            case 28:
            v1055 = (digit_0>=base_16);
            s_23 = s_22;
            base_17 = base_16;
            strlen_17 = strlen_16;
            i_24 = i_23;
            sign_14 = sign_13;
            oldpos_8 = oldpos_7;
            digit_1 = digit_0;
            v1057 = val_12;
            if (v1055 == false)
            {
                block = 29;
                break;
            }
            s_12 = s_22;
            strlen_6 = strlen_16;
            i_14 = i_23;
            sign_2 = sign_13;
            val_1 = val_12;
            v1017 = oldpos_7;
            block = 13;
            break;
            case 29:
            v1058 = (v1057*base_17);
            v1059 = (v1058+digit_1);
            v1060 = (i_24+1);
            s_11 = s_23;
            base_9 = base_17;
            strlen_5 = strlen_17;
            i_13 = v1060;
            sign_1 = sign_14;
            val_0 = v1059;
            oldpos_0 = oldpos_8;
            block = 12;
            break;
            case 30:
            v1061 = (c_4<=90);
            s_25 = s_24;
            base_19 = base_18;
            strlen_19 = strlen_18;
            i_26 = i_25;
            sign_16 = sign_15;
            val_14 = val_13;
            oldpos_10 = oldpos_9;
            c_5 = c_4;
            v1062 = v1061;
            block = 31;
            break;
            case 31:
            s_18 = s_25;
            base_12 = base_19;
            strlen_12 = strlen_19;
            i_19 = i_26;
            sign_9 = sign_16;
            val_8 = val_14;
            oldpos_3 = oldpos_10;
            c_1 = c_5;
            if (v1062 == false)
            {
                block = 24;
                break;
            }
            s_26 = s_25;
            base_20 = base_19;
            strlen_20 = strlen_19;
            i_27 = i_26;
            sign_17 = sign_16;
            val_15 = val_14;
            oldpos_11 = oldpos_10;
            v1064 = c_5;
            block = 32;
            break;
            case 32:
            v1065 = (v1064-65);
            v1066 = (v1065+10);
            s_22 = s_26;
            base_16 = base_20;
            strlen_16 = strlen_20;
            i_23 = i_27;
            sign_13 = sign_17;
            val_12 = val_15;
            oldpos_7 = oldpos_11;
            digit_0 = v1066;
            block = 28;
            break;
            case 33:
            v1067 = (c_6<=122);
            s_28 = s_27;
            base_22 = base_21;
            strlen_22 = strlen_21;
            i_29 = i_28;
            sign_19 = sign_18;
            val_17 = val_16;
            oldpos_13 = oldpos_12;
            c_7 = c_6;
            v1068 = v1067;
            block = 34;
            break;
            case 34:
            s_17 = s_28;
            base_11 = base_22;
            strlen_11 = strlen_22;
            i_18 = i_29;
            sign_8 = sign_19;
            val_7 = val_17;
            oldpos_2 = oldpos_13;
            c_0 = c_7;
            if (v1068 == false)
            {
                block = 23;
                break;
            }
            s_29 = s_28;
            base_23 = base_22;
            strlen_23 = strlen_22;
            i_30 = i_29;
            sign_20 = sign_19;
            val_18 = val_17;
            oldpos_14 = oldpos_13;
            v1070 = c_7;
            block = 35;
            break;
            case 35:
            v1071 = (v1070-97);
            v1072 = (v1071+10);
            s_22 = s_29;
            base_16 = base_23;
            strlen_16 = strlen_23;
            i_23 = i_30;
            sign_13 = sign_20;
            val_12 = val_18;
            oldpos_7 = oldpos_14;
            digit_0 = v1072;
            block = 28;
            break;
            case 36:
            v1074 = s_30.charAt(i_31);
            v1075 = (v1074==' ');
            s_11 = s_30;
            base_9 = base_24;
            strlen_5 = strlen_24;
            i_13 = i_31;
            sign_1 = sign_21;
            val_0 = 0;
            oldpos_0 = i_31;
            if (v1075 == false)
            {
                block = 12;
                break;
            }
            s_31 = s_30;
            base_25 = base_24;
            strlen_25 = strlen_24;
            sign_22 = sign_21;
            v1077 = i_31;
            block = 37;
            break;
            case 37:
            v1078 = (v1077+1);
            s_10 = s_31;
            base_8 = base_25;
            strlen_4 = strlen_25;
            i_12 = v1078;
            sign_0 = sign_22;
            block = 11;
            break;
            case 38:
            v1080 = (v1079+1);
            s_10 = s_32;
            base_8 = base_26;
            strlen_4 = strlen_26;
            i_12 = v1080;
            sign_0 = 1;
            block = 11;
            break;
            case 39:
            v1082 = (v1081+1);
            s_10 = s_33;
            base_8 = base_27;
            strlen_4 = strlen_27;
            i_12 = v1082;
            sign_0 = -1;
            block = 11;
            break;
            case 40:
            v1084 = s_34.charAt(i_32);
            v1085 = (v1084==' ');
            s_7 = s_34;
            base_5 = base_28;
            strlen_1 = strlen_28;
            i_9 = i_32;
            if (v1085 == false)
            {
                block = 7;
                break;
            }
            s_35 = s_34;
            base_29 = base_28;
            strlen_29 = strlen_28;
            v1087 = i_32;
            block = 41;
            break;
            case 41:
            v1088 = (v1087+1);
            s_6 = s_35;
            base_4 = base_29;
            strlen_0 = strlen_29;
            i_8 = v1088;
            block = 6;
            break;
            case 2:
            throw(evalue_7);
            case 18:
            return ( v987 );
        }
    }
}

function ll_dict_getitem__Dict_String__Signed__String (d_4,key_8) {
    var v947,v948,v949,v950,v951,v952,v953,etype_6,evalue_6,key_9,v954,v955,v956;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v949 = (d_4[key_8]!=undefined);
            if (v949 == false)
            {
                block = 1;
                break;
            }
            key_9 = key_8;
            v954 = d_4;
            block = 3;
            break;
            case 1:
            v951 = __consts_0.exceptions_KeyError;
            v952 = v951.meta;
            etype_6 = v952;
            evalue_6 = v951;
            block = 2;
            break;
            case 3:
            v956 = v954[key_9];
            v947 = v956;
            block = 4;
            break;
            case 2:
            throw(evalue_6);
            case 4:
            return ( v947 );
        }
    }
}

function exceptions_ValueError () {
}

exceptions_ValueError.prototype.toString = function (){
    return ( '<exceptions.ValueError object>' );
}

inherits(exceptions_ValueError,exceptions_StandardError);
function Object_meta () {
    this.class_ = __consts_0.None;
}

Object_meta.prototype.toString = function (){
    return ( '<Object_meta object>' );
}

function exceptions_Exception_meta () {
}

exceptions_Exception_meta.prototype.toString = function (){
    return ( '<exceptions.Exception_meta object>' );
}

inherits(exceptions_Exception_meta,Object_meta);
function exceptions_StandardError_meta () {
}

exceptions_StandardError_meta.prototype.toString = function (){
    return ( '<exceptions.StandardError_meta object>' );
}

inherits(exceptions_StandardError_meta,exceptions_Exception_meta);
function exceptions_AssertionError_meta () {
}

exceptions_AssertionError_meta.prototype.toString = function (){
    return ( '<exceptions.AssertionError_meta object>' );
}

inherits(exceptions_AssertionError_meta,exceptions_StandardError_meta);
function py____magic_assertion_AssertionError_meta () {
}

py____magic_assertion_AssertionError_meta.prototype.toString = function (){
    return ( '<py.__.magic.assertion.AssertionError_meta object>' );
}

inherits(py____magic_assertion_AssertionError_meta,exceptions_AssertionError_meta);
function exceptions_LookupError_meta () {
}

exceptions_LookupError_meta.prototype.toString = function (){
    return ( '<exceptions.LookupError_meta object>' );
}

inherits(exceptions_LookupError_meta,exceptions_StandardError_meta);
function exceptions_KeyError_meta () {
}

exceptions_KeyError_meta.prototype.toString = function (){
    return ( '<exceptions.KeyError_meta object>' );
}

inherits(exceptions_KeyError_meta,exceptions_LookupError_meta);
function exceptions_StopIteration_meta () {
}

exceptions_StopIteration_meta.prototype.toString = function (){
    return ( '<exceptions.StopIteration_meta object>' );
}

inherits(exceptions_StopIteration_meta,exceptions_Exception_meta);
function exceptions_ValueError_meta () {
}

exceptions_ValueError_meta.prototype.toString = function (){
    return ( '<exceptions.ValueError_meta object>' );
}

inherits(exceptions_ValueError_meta,exceptions_StandardError_meta);
function py____test_rsession_webjs_Options_meta () {
}

py____test_rsession_webjs_Options_meta.prototype.toString = function (){
    return ( '<py.__.test.rsession.webjs.Options_meta object>' );
}

inherits(py____test_rsession_webjs_Options_meta,Object_meta);
function py____test_rsession_webjs_Globals_meta () {
}

py____test_rsession_webjs_Globals_meta.prototype.toString = function (){
    return ( '<py.__.test.rsession.webjs.Globals_meta object>' );
}

inherits(py____test_rsession_webjs_Globals_meta,Object_meta);
__consts_0 = {};
__consts_0.const_str__71 = ' failures, ';
__consts_0.const_str__28 = "show_host('";
__consts_0.const_str__70 = ' run, ';
__consts_0.const_tuple__91 = {};
__consts_0.const_str__62 = 'a';
__consts_0.const_str__89 = 'class';
__consts_0.const_str__40 = ']';
__consts_0.exceptions_KeyError__114 = exceptions_KeyError;
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.const_str__51 = 'ReceivedItemOutcome';
__consts_0.const_str__83 = "show_info('";
__consts_0.const_tuple__93 = {};
__consts_0.const_str__60 = '- skipped (';
__consts_0.const_str__32 = 'hide_host()';
__consts_0.const_str__84 = 'hide_info()';
__consts_0.const_str__43 = '#message';
__consts_0.py____test_rsession_webjs_Globals__121 = py____test_rsession_webjs_Globals;
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__16 = 'tbody';
__consts_0.const_tuple__94 = {};
__consts_0.const_str__61 = ')';
__consts_0.const_str__46 = 'main_table';
__consts_0.const_str__105 = 'Tests [interrupted]';
__consts_0.const_str__29 = "')";
__consts_0.const_str__55 = 'RsyncFinished';
__consts_0.Window = window;
__consts_0.const_str__92 = '_txt_';
__consts_0.py____magic_assertion_AssertionError__116 = py____magic_assertion_AssertionError;
__consts_0.exceptions_ValueError__110 = exceptions_ValueError;
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.const_str__80 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_list = undefined;
__consts_0.const_str__90 = 'error';
__consts_0.exceptions_StopIteration__112 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_str__69 = 'FINISHED ';
__consts_0.const_str__38 = 'Rsyncing';
__consts_0.const_str__12 = 'info';
__consts_0.const_str__18 = 'td';
__consts_0.const_str__44 = 'true';
__consts_0.const_tuple = undefined;
__consts_0.const_str__88 = 'F';
__consts_0.const_str__31 = 'onmouseout';
__consts_0.const_str__47 = 'type';
__consts_0.const_str__101 = 'length';
__consts_0.const_str__85 = 'passed';
__consts_0.const_str__99 = '.';
__consts_0.const_str__53 = 'FailedTryiter';
__consts_0.const_str__27 = '#ff0000';
__consts_0.const_str__5 = 'checked';
__consts_0.const_str__33 = 'messagebox';
__consts_0.const_str__58 = 'fullitemname';
__consts_0.const_str__103 = 'table';
__consts_0.const_str__64 = 'href';
__consts_0.const_str__68 = 'skips';
__consts_0.const_str__57 = 'CrashedExecution';
__consts_0.const_str__25 = '\n';
__consts_0.const_str__17 = 'tr';
__consts_0.const_str__41 = 'pre';
__consts_0.const_str__104 = 'Py.test [interrupted]';
__consts_0.const_str__23 = '\n======== Stdout: ========\n';
__consts_0.const_str__76 = '#00ff00';
__consts_0.const_str__14 = 'beige';
__consts_0.const_str__98 = 's';
__consts_0.const_str__59 = 'reason';
__consts_0.const_tuple__21 = {};
__consts_0.const_str__79 = 'traceback';
__consts_0.const_str__45 = 'testmain';
__consts_0.const_str__97 = "javascript:show_skip('";
__consts_0.const_str__78 = '[';
__consts_0.const_str__107 = 'Tests [crashed]';
__consts_0.const_tuple__11 = undefined;
__consts_0.const_str__63 = "javascript:show_traceback('";
__consts_0.const_str__37 = 'Tests';
__consts_0.const_list__120 = [];
__consts_0.const_str__8 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.py____test_rsession_webjs_Options__118 = py____test_rsession_webjs_Options;
__consts_0.py____test_rsession_webjs_Options_meta = new py____test_rsession_webjs_Options_meta();
__consts_0.py____test_rsession_webjs_Options = new py____test_rsession_webjs_Options();
__consts_0.const_str__66 = 'run';
__consts_0.const_str__54 = 'SkippedTryiter';
__consts_0.const_str__87 = 'None';
__consts_0.const_str__6 = 'True';
__consts_0.const_str__95 = '/';
__consts_0.const_str__75 = 'hostkey';
__consts_0.const_str__67 = 'fails';
__consts_0.const_str__48 = 'ItemStart';
__consts_0.const_str__100 = 'itemname';
__consts_0.const_str__52 = 'TestFinished';
__consts_0.const_str__15 = 'jobs';
__consts_0.const_str__24 = '\n========== Stderr: ==========\n';
__consts_0.const_str__72 = ' skipped';
__consts_0.const_str__81 = 'stderr';
__consts_0.const_str__73 = 'Py.test ';
__consts_0.const_str__13 = 'visible';
__consts_0.const_str__96 = 'False';
__consts_0.const_str__50 = 'HostRSyncRootReady';
__consts_0.const_str__30 = 'onmouseover';
__consts_0.const_str__65 = '- FAILED TO LOAD MODULE';
__consts_0.const_str__102 = '[0/';
__consts_0.const_tuple__19 = {};
__consts_0.py____magic_assertion_AssertionError_meta = new py____magic_assertion_AssertionError_meta();
__consts_0.const_str__49 = 'SendItem';
__consts_0.const_str__74 = 'fullmodulename';
__consts_0.const_str__86 = 'skipped';
__consts_0.const_str__26 = 'hostsbody';
__consts_0.const_str__77 = '[0]';
__consts_0.const_str__20 = 'hidden';
__consts_0.const_str__22 = '====== Traceback: =========\n';
__consts_0.py____magic_assertion_AssertionError = new py____magic_assertion_AssertionError();
__consts_0.const_str__82 = 'item_name';
__consts_0.const_str__39 = 'Tests [';
__consts_0.Document = document;
__consts_0.const_str__106 = 'Py.test [crashed]';
__consts_0.const_str__56 = 'InterruptedExecution';
__consts_0.const_str__4 = 'opt_scroll';
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__114;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__121;
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__110;
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__112;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__8;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__8;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ofinished = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__120;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__11;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
__consts_0.py____test_rsession_webjs_Options_meta.class_ = __consts_0.py____test_rsession_webjs_Options__118;
__consts_0.py____test_rsession_webjs_Options.meta = __consts_0.py____test_rsession_webjs_Options_meta;
__consts_0.py____test_rsession_webjs_Options.oscroll = true;
__consts_0.py____magic_assertion_AssertionError_meta.class_ = __consts_0.py____magic_assertion_AssertionError__116;
__consts_0.py____magic_assertion_AssertionError.meta = __consts_0.py____magic_assertion_AssertionError_meta;
