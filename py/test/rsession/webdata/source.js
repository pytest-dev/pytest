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
            v33.ll_append(__consts_0.const_str__2);
            v35 = ll_str__StringR_StringConst_String ( v30 );
            v33.ll_append(v35);
            v33.ll_append(__consts_0.const_str__3);
            v38 = ll_str__StringR_StringConst_String ( v31 );
            v33.ll_append(v38);
            v33.ll_append(__consts_0.const_str__4);
            v41 = ll_str__StringR_StringConst_String ( v32 );
            v33.ll_append(v41);
            v33.ll_append(__consts_0.const_str__5);
            v44 = v33.ll_build();
            set_msgbox ( item_name_1,v44 );
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
            v102 = v101.getElementById(__consts_0.const_str__7);
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
            v107.visibility = __consts_0.const_str__8;
            __consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__10;
            block = 3;
            break;
            case 4:
            v111 = elem_6.childNodes;
            v112 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v111,0 );
            elem_6.removeChild(v112);
            elem_5 = elem_6;
            block = 1;
            break;
            case 3:
            return ( undefined );
        }
    }
}

function ll_str__StringR_StringConst_String (s_0) {
    var v138;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v138 = s_0;
            block = 1;
            break;
            case 1:
            return ( v138 );
        }
    }
}

function show_skip (item_name_0) {
    var v26;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v26 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__11,item_name_0 );
            set_msgbox ( item_name_0,v26 );
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_dict_getitem__Dict_String__Record_item2__Str_String (d_0,key_0) {
    var v128,v129,v130,v131,v132,v133,v134,etype_0,evalue_0,key_1,v135,v136,v137;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v130 = (d_0[key_0]!=undefined);
            if (v130 == false)
            {
                block = 1;
                break;
            }
            key_1 = key_0;
            v135 = d_0;
            block = 3;
            break;
            case 1:
            v132 = __consts_0.exceptions_KeyError;
            v133 = v132.meta;
            etype_0 = v133;
            evalue_0 = v132;
            block = 2;
            break;
            case 3:
            v137 = v135[key_1];
            v128 = v137;
            block = 4;
            break;
            case 2:
            throw(evalue_0);
            case 4:
            return ( v128 );
        }
    }
}

function exceptions_Exception () {
}

exceptions_Exception.prototype.toString = function (){
    return ( '<exceptions.Exception object>' );
}

inherits(exceptions_Exception,Object);
function exceptions_StandardError () {
}

exceptions_StandardError.prototype.toString = function (){
    return ( '<exceptions.StandardError object>' );
}

inherits(exceptions_StandardError,exceptions_Exception);
function show_info (data_0) {
    var v47,v48,v49,data_1,info_0,v51,v52,v53,info_1,v54,v55,v56,v58,data_2,info_2,v60,v61,v62;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v47 = __consts_0.Document;
            v48 = v47.getElementById(__consts_0.const_str__13);
            v49 = v48.style;
            v49.visibility = __consts_0.const_str__14;
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
            info_1.appendChild(v55);
            v58 = info_1.style;
            v58.backgroundColor = __consts_0.const_str__15;
            block = 3;
            break;
            case 4:
            v61 = info_2.childNodes;
            v62 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v61,0 );
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

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed (l_1,index_0) {
    var v163,v164,l_2,index_1,v166,v167,v168,index_2,v170,v171,v172;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v164 = (index_0>=0);
            l_2 = l_1;
            index_1 = index_0;
            block = 1;
            break;
            case 1:
            v167 = l_2.length;
            v168 = (index_1<v167);
            index_2 = index_1;
            v170 = l_2;
            block = 2;
            break;
            case 2:
            v172 = v170[index_2];
            v163 = v172;
            block = 3;
            break;
            case 3:
            return ( v163 );
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

function hide_info () {
    var v65,v66,v67;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v65 = __consts_0.Document;
            v66 = v65.getElementById(__consts_0.const_str__13);
            v67 = v66.style;
            v67.visibility = __consts_0.const_str__8;
            block = 1;
            break;
            case 1:
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
            v71 = v70.getElementById(__consts_0.const_str__7);
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
            v81 = create_elem ( __consts_0.const_str__18 );
            v82 = create_elem ( __consts_0.const_str__19 );
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
            v92.visibility = __consts_0.const_str__14;
            __consts_0.py____test_rsession_webjs_Globals.ohost = host_name_4;
            setTimeout ( 'reshow_host()',100 );
            block = 5;
            break;
            case 6:
            v97 = elem_4.childNodes;
            v98 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v97,0 );
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

function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions.StopIteration object>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
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
            v22 = v21.getElementById(__consts_0.const_str__21);
            v22.setAttribute(__consts_0.const_str__22,__consts_0.const_str__23);
            block = 1;
            break;
            case 1:
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
function exceptions_LookupError () {
}

exceptions_LookupError.prototype.toString = function (){
    return ( '<exceptions.LookupError object>' );
}

inherits(exceptions_LookupError,exceptions_StandardError);
function reshow_host () {
    var v225,v226,v227,v228;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v225 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v226 = ll_streq__String_String ( v225,__consts_0.const_str__10 );
            if (v226 == false)
            {
                block = 1;
                break;
            }
            block = 2;
            break;
            case 1:
            v228 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v228 );
            block = 2;
            break;
            case 2:
            return ( undefined );
        }
    }
}

function ll_len__List_ExternalType_ (l_0) {
    var v160,v161,v162;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v162 = l_0.length;
            v160 = v162;
            block = 1;
            break;
            case 1:
            return ( v160 );
        }
    }
}

function ll_list_is_true__List_ExternalType_ (l_3) {
    var v186,v187,v188,v189,v190,v191,v192;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v187 = !!l_3;
            v186 = v187;
            if (v187 == false)
            {
                block = 1;
                break;
            }
            v189 = l_3;
            block = 2;
            break;
            case 2:
            v191 = v189.length;
            v192 = (v191!=0);
            v186 = v192;
            block = 1;
            break;
            case 1:
            return ( v186 );
        }
    }
}

function ll_dict_getitem__Dict_String__String__String (d_1,key_2) {
    var v173,v174,v175,v176,v177,v178,v179,etype_1,evalue_1,key_3,v180,v181,v182;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v175 = (d_1[key_2]!=undefined);
            if (v175 == false)
            {
                block = 1;
                break;
            }
            key_3 = key_2;
            v180 = d_1;
            block = 3;
            break;
            case 1:
            v177 = __consts_0.exceptions_KeyError;
            v178 = v177.meta;
            etype_1 = v178;
            evalue_1 = v177;
            block = 2;
            break;
            case 3:
            v182 = v180[key_3];
            v173 = v182;
            block = 4;
            break;
            case 2:
            throw(evalue_1);
            case 4:
            return ( v173 );
        }
    }
}

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__10;
    this.ohost = __consts_0.const_str__10;
    this.orsync_dots = 0;
    this.ofinished = false;
    this.ohost_dict = __consts_0.const_tuple__24;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__26;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py.__.test.rsession.webjs.Globals object>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
function ll_listiter__Record_index__Signed__iterable_List_String_ (lst_0) {
    var v206,v207;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v207 = new Object();
            v207.iterable = lst_0;
            v207.index = 0;
            v206 = v207;
            block = 1;
            break;
            case 1:
            return ( v206 );
        }
    }
}

function ll_dict_getitem__Dict_String__List_String___String (d_2,key_4) {
    var v196,v197,v198,v199,v200,v201,v202,etype_2,evalue_2,key_5,v203,v204,v205;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v198 = (d_2[key_4]!=undefined);
            if (v198 == false)
            {
                block = 1;
                break;
            }
            key_5 = key_4;
            v203 = d_2;
            block = 3;
            break;
            case 1:
            v200 = __consts_0.exceptions_KeyError;
            v201 = v200.meta;
            etype_2 = v201;
            evalue_2 = v200;
            block = 2;
            break;
            case 3:
            v205 = v203[key_5];
            v196 = v205;
            block = 4;
            break;
            case 2:
            throw(evalue_2);
            case 4:
            return ( v196 );
        }
    }
}

function exceptions_KeyError () {
}

exceptions_KeyError.prototype.toString = function (){
    return ( '<exceptions.KeyError object>' );
}

inherits(exceptions_KeyError,exceptions_LookupError);
function ll_listnext__Record_index__Signed__iterable_0 (iter_0) {
    var v210,v211,v212,v213,v214,v215,v216,iter_1,l_4,index_3,v217,v219,v220,v221,v222,v223,etype_3,evalue_3;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v211 = iter_0.iterable;
            v212 = iter_0.index;
            v214 = v211.length;
            v215 = (v212>=v214);
            iter_1 = iter_0;
            l_4 = v211;
            index_3 = v212;
            if (v215 == false)
            {
                block = 1;
                break;
            }
            block = 3;
            break;
            case 1:
            v217 = (index_3+1);
            iter_1.index = v217;
            v220 = l_4[index_3];
            v210 = v220;
            block = 2;
            break;
            case 3:
            v221 = __consts_0.exceptions_StopIteration;
            v222 = v221.meta;
            etype_3 = v222;
            evalue_3 = v221;
            block = 4;
            break;
            case 4:
            throw(evalue_3);
            case 2:
            return ( v210 );
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
            v116 = v115.getElementById(__consts_0.const_str__28);
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
            v120 = mbox_1.childNodes;
            v121 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v120,0 );
            mbox_1.removeChild(v121);
            mbox_0 = mbox_1;
            block = 1;
            break;
            case 2:
            return ( undefined );
        }
    }
}

function set_msgbox (item_name_2,data_3) {
    var v140,item_name_3,data_4,msgbox_0,v141,v142,v143,item_name_4,data_5,msgbox_1,v144,v145,v146,v147,v148,v150,v152,v153,item_name_5,data_6,msgbox_2,v156,v157,v158;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v140 = get_elem ( __consts_0.const_str__28 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v140;
            block = 1;
            break;
            case 1:
            v141 = msgbox_0.childNodes;
            v142 = ll_len__List_ExternalType_ ( v141 );
            v143 = !!v142;
            item_name_4 = item_name_3;
            data_5 = data_4;
            msgbox_1 = msgbox_0;
            if (v143 == false)
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
            v144 = create_elem ( __consts_0.const_str__29 );
            v145 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__5 );
            v146 = ll_strconcat__String_String ( v145,data_5 );
            v147 = create_text_elem ( v146 );
            v144.appendChild(v147);
            msgbox_1.appendChild(v144);
            v152 = __consts_0.Window.location;
            v152.assign(__consts_0.const_str__31);
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 4:
            v157 = msgbox_2.childNodes;
            v158 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v157,0 );
            msgbox_2.removeChild(v158);
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

function host_init (host_dict_0) {
    var v231,v232,v233,v234,v235,host_dict_1,tbody_3,v236,v237,last_exc_value_1,host_dict_2,tbody_4,host_0,v238,v239,v240,v242,v243,v245,v246,v247,v250,v252,v253,v255,v258,v260,host_dict_3,v266,v268,v269,v270,v271,v272,last_exc_value_2,key_6,v273,v274,v276;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v231 = __consts_0.Document;
            v232 = v231.getElementById(__consts_0.const_str__32);
            v234 = ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst ( host_dict_0 );
            v235 = ll_listiter__Record_index__Signed__iterable_List_String_ ( v234 );
            host_dict_1 = host_dict_0;
            tbody_3 = v232;
            v236 = v235;
            block = 1;
            break;
            case 1:
            try {
                v237 = ll_listnext__Record_index__Signed__iterable_0 ( v236 );
                host_dict_2 = host_dict_1;
                tbody_4 = tbody_3;
                host_0 = v237;
                v238 = v236;
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
            v239 = create_elem ( __consts_0.const_str__18 );
            tbody_4.appendChild(v239);
            v242 = create_elem ( __consts_0.const_str__19 );
            v243 = v242.style;
            v243.background = __consts_0.const_str__33;
            v245 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v246 = create_text_elem ( v245 );
            v242.appendChild(v246);
            v242.id = host_0;
            v239.appendChild(v242);
            v253 = new StringBuilder();
            v253.ll_append(__consts_0.const_str__34);
            v255 = ll_str__StringR_StringConst_String ( host_0 );
            v253.ll_append(v255);
            v253.ll_append(__consts_0.const_str__35);
            v258 = v253.ll_build();
            v242.setAttribute(__consts_0.const_str__36,v258);
            v242.setAttribute(__consts_0.const_str__37,__consts_0.const_str__38);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
            setTimeout ( 'update_rsync()',1000 );
            host_dict_1 = host_dict_2;
            tbody_3 = tbody_4;
            v236 = v238;
            block = 1;
            break;
            case 3:
            __consts_0.py____test_rsession_webjs_Globals.ohost_dict = host_dict_3;
            v266 = ll_newdict__Dict_String__List_String__LlT (  );
            __consts_0.py____test_rsession_webjs_Globals.ohost_pending = v266;
            v269 = ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst ( host_dict_3 );
            v270 = ll_listiter__Record_index__Signed__iterable_List_String_ ( v269 );
            v271 = v270;
            block = 4;
            break;
            case 4:
            try {
                v272 = ll_listnext__Record_index__Signed__iterable_0 ( v271 );
                key_6 = v272;
                v273 = v271;
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
            v274 = new Array();
            v274.length = 0;
            v276 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v276[key_6]=v274;
            v271 = v273;
            block = 4;
            break;
            case 6:
            return ( undefined );
        }
    }
}

function create_elem (s_1) {
    var v193,v194,v195;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v194 = __consts_0.Document;
            v195 = v194.createElement(s_1);
            v193 = v195;
            block = 1;
            break;
            case 1:
            return ( v193 );
        }
    }
}

function create_text_elem (txt_0) {
    var v183,v184,v185;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v184 = __consts_0.Document;
            v185 = v184.createTextNode(txt_0);
            v183 = v185;
            block = 1;
            break;
            case 1:
            return ( v183 );
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

function key_pressed (key_7) {
    var v283,v284,v285,v286,v287,v288,v289,v290,v291,v294,v295;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v283 = key_7.charCode;
            v284 = (v283==115);
            if (v284 == false)
            {
                block = 1;
                break;
            }
            block = 2;
            break;
            case 2:
            v286 = __consts_0.Document;
            v287 = v286.getElementById(__consts_0.const_str__21);
            v288 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v290 = v287;
            if (v288 == false)
            {
                block = 3;
                break;
            }
            v294 = v287;
            block = 4;
            break;
            case 3:
            v290.setAttribute(__consts_0.const_str__22,__consts_0.const_str__39);
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 1;
            break;
            case 4:
            v294.removeAttribute(__consts_0.const_str__22);
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function sessid_comeback (id_0) {
    var v280,v281;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.osessid = id_0;
            v280 = __consts_0.ExportedMethods;
            v281 = v280.show_all_statuses(id_0,comeback);
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_streq__String_String (s1_0,s2_0) {
    var v298,v299,v300,v301,s2_1,v302,v303,v304,v305,v306,v307;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v299 = !!s1_0;
            v300 = !v299;
            s2_1 = s2_0;
            v302 = s1_0;
            if (v300 == false)
            {
                block = 1;
                break;
            }
            v305 = s2_0;
            block = 3;
            break;
            case 1:
            v304 = (v302==s2_1);
            v298 = v304;
            block = 2;
            break;
            case 3:
            v306 = !!v305;
            v307 = !v306;
            v298 = v307;
            block = 2;
            break;
            case 2:
            return ( v298 );
        }
    }
}

function get_elem (el_0) {
    var v308,v309,v310;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v309 = __consts_0.Document;
            v310 = v309.getElementById(el_0);
            v308 = v310;
            block = 1;
            break;
            case 1:
            return ( v308 );
        }
    }
}

function ll_dict_kvi__Dict_String__String__List_String_LlT_dum_keysConst (d_3) {
    var v314,v315,v316,v317,v318,v319,length_0,result_0,it_0,i_0,v320,v321,v322,result_1,v323,v324,v325,v326,v327,v328,v329,etype_4,evalue_4,length_1,result_2,it_1,i_1,v330,v331,v332,length_2,result_3,it_2,v334,v335;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v316 = get_dict_len ( d_3 );
            v317 = ll_newlist__List_String_LlT_Signed ( v316 );
            v319 = dict_items_iterator ( d_3 );
            length_0 = v316;
            result_0 = v317;
            it_0 = v319;
            i_0 = 0;
            block = 1;
            break;
            case 1:
            v321 = it_0.ll_go_next();
            result_1 = result_0;
            v323 = i_0;
            v324 = length_0;
            if (v321 == false)
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
            v325 = (v323==v324);
            if (v325 == false)
            {
                block = 3;
                break;
            }
            v314 = result_1;
            block = 5;
            break;
            case 3:
            v327 = __consts_0.exceptions_AssertionError;
            v328 = v327.meta;
            etype_4 = v328;
            evalue_4 = v327;
            block = 4;
            break;
            case 6:
            v332 = it_1.ll_current_key();
            result_2[i_1]=v332;
            length_2 = length_1;
            result_3 = result_2;
            it_2 = it_1;
            v334 = i_1;
            block = 7;
            break;
            case 7:
            v335 = (v334+1);
            length_0 = length_2;
            result_0 = result_3;
            it_0 = it_2;
            i_0 = v335;
            block = 1;
            break;
            case 4:
            throw(evalue_4);
            case 5:
            return ( v314 );
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
            v400.length = length_3;
            v399 = v400;
            block = 1;
            break;
            case 1:
            return ( v399 );
        }
    }
}

function update_rsync () {
    var v337,v338,v339,v340,v341,v342,v343,v344,elem_7,v345,v346,v347,v348,v349,v351,v352,v353,elem_8,v354,v355,v357,v360,v361,v362,elem_9,text_0,v366,v367,v368;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v337 = __consts_0.py____test_rsession_webjs_Globals.ofinished;
            if (v337 == false)
            {
                block = 1;
                break;
            }
            block = 4;
            break;
            case 1:
            v339 = __consts_0.Document;
            v340 = v339.getElementById(__consts_0.const_str__41);
            v341 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v343 = (v341==1);
            elem_7 = v340;
            if (v343 == false)
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
            v347 = ll_strconcat__String_String ( __consts_0.const_str__42,v346 );
            v348 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v349 = (v348+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v349;
            v351 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v352 = (v351>5);
            elem_8 = elem_7;
            v354 = v347;
            if (v352 == false)
            {
                block = 3;
                break;
            }
            elem_9 = elem_7;
            text_0 = v347;
            block = 5;
            break;
            case 3:
            v355 = new StringBuilder();
            v355.ll_append(__consts_0.const_str__43);
            v357 = ll_str__StringR_StringConst_String ( v354 );
            v355.ll_append(v357);
            v355.ll_append(__consts_0.const_str__44);
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
            v368.nodeValue = __consts_0.const_str__41;
            block = 4;
            break;
            case 4:
            return ( undefined );
        }
    }
}

function ll_strconcat__String_String (obj_0,arg0_0) {
    var v311,v312,v313;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v313 = (obj_0+arg0_0);
            v311 = v313;
            block = 1;
            break;
            case 1:
            return ( v311 );
        }
    }
}

function ll_char_mul__Char_Signed (ch_0,times_0) {
    var v403,v404,v405,ch_1,times_1,v406,v407,ch_2,times_2,buf_0,i_2,v409,v410,v411,v412,v413,ch_3,times_3,buf_1,i_3,v414,v416;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v404 = (times_0<0);
            ch_1 = ch_0;
            times_1 = times_0;
            if (v404 == false)
            {
                block = 1;
                break;
            }
            ch_1 = ch_0;
            times_1 = 0;
            block = 1;
            break;
            case 1:
            v406 = new StringBuilder();
            v406.ll_allocate(times_1);
            ch_2 = ch_1;
            times_2 = times_1;
            buf_0 = v406;
            i_2 = 0;
            block = 2;
            break;
            case 2:
            v409 = (i_2<times_2);
            v411 = buf_0;
            if (v409 == false)
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
            v413 = v411.ll_build();
            v403 = v413;
            block = 4;
            break;
            case 5:
            buf_1.ll_append_char(ch_3);
            v416 = (i_3+1);
            ch_2 = ch_3;
            times_2 = times_3;
            buf_0 = buf_1;
            i_2 = v416;
            block = 2;
            break;
            case 4:
            return ( v403 );
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
            msglist_1 = msglist_0;
            if (v374 == false)
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
            if (v384 == false)
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
            if (v394 == false)
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

function exceptions_AssertionError () {
}

exceptions_AssertionError.prototype.toString = function (){
    return ( '<exceptions.AssertionError object>' );
}

inherits(exceptions_AssertionError,exceptions_StandardError);
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
            v498 = v497.getElementById(__consts_0.const_str__28);
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
            v509 = create_elem ( __consts_0.const_str__18 );
            v510 = create_elem ( __consts_0.const_str__19 );
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
            v534 = create_elem ( __consts_0.const_str__18 );
            v535 = create_elem ( __consts_0.const_str__19 );
            v536 = create_elem ( __consts_0.const_str__62 );
            v538 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__58 );
            v539 = new Object();
            v539.item0 = v538;
            v541 = v539.item0;
            v542 = new StringBuilder();
            v542.ll_append(__consts_0.const_str__63);
            v544 = ll_str__StringR_StringConst_String ( v541 );
            v542.ll_append(v544);
            v542.ll_append(__consts_0.const_str__35);
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
            v590.ll_append(__consts_0.const_str__43);
            v592 = ll_str__StringR_StringConst_String ( v582 );
            v590.ll_append(v592);
            v590.ll_append(__consts_0.const_str__44);
            v595 = v590.ll_build();
            v596 = __consts_0.Document;
            v597 = v596.getElementById(__consts_0.const_str__41);
            v598 = v597.childNodes;
            v599 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v598,0 );
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
            v627 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v626,0 );
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
            v650.ll_append(__consts_0.const_str__44);
            v657 = v650.ll_build();
            v658 = v631.childNodes;
            v659 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v658,0 );
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

function make_module_box (msg_32) {
    var v876,v877,v878,v879,v881,v882,v883,v884,v887,v888,v889,v890,v893,v896,v897,v899,v900,v901,v903,v904,v906,v907,v909,v910,v911,v913,v914,v916,v919,v921,v923,v924,v926,v927,v929,v930,v932,v934;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v877 = create_elem ( __consts_0.const_str__18 );
            v878 = create_elem ( __consts_0.const_str__19 );
            v877.appendChild(v878);
            v882 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__79 );
            v883 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__80 );
            v884 = new Object();
            v884.item0 = v882;
            v884.item1 = v883;
            v887 = v884.item0;
            v888 = v884.item1;
            v889 = new StringBuilder();
            v890 = ll_str__StringR_StringConst_String ( v887 );
            v889.ll_append(v890);
            v889.ll_append(__consts_0.const_str__81);
            v893 = ll_str__StringR_StringConst_String ( v888 );
            v889.ll_append(v893);
            v889.ll_append(__consts_0.const_str__44);
            v896 = v889.ll_build();
            v897 = create_text_elem ( v896 );
            v878.appendChild(v897);
            v899 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__80 );
            v900 = ll_int__String_Signed ( v899,10 );
            v901 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__82[v901]=v900;
            v903 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__79 );
            v904 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__83[v904]=v903;
            v906 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v907 = ll_strconcat__String_String ( __consts_0.const_str__84,v906 );
            v878.id = v907;
            v910 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v911 = new Object();
            v911.item0 = v910;
            v913 = v911.item0;
            v914 = new StringBuilder();
            v914.ll_append(__consts_0.const_str__85);
            v916 = ll_str__StringR_StringConst_String ( v913 );
            v914.ll_append(v916);
            v914.ll_append(__consts_0.const_str__35);
            v919 = v914.ll_build();
            v878.setAttribute(__consts_0.const_str__36,v919);
            v878.setAttribute(__consts_0.const_str__37,__consts_0.const_str__86);
            v923 = create_elem ( __consts_0.const_str__19 );
            v877.appendChild(v923);
            v926 = create_elem ( __consts_0.const_str__87 );
            v923.appendChild(v926);
            v929 = create_elem ( __consts_0.const_str__17 );
            v930 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            v929.id = v930;
            v926.appendChild(v929);
            v934 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__58 );
            __consts_0.const_tuple__88[v934]=0;
            v876 = v877;
            block = 1;
            break;
            case 1:
            return ( v876 );
        }
    }
}

function add_received_item_outcome (msg_22,module_part_2) {
    var v707,v708,v709,msg_23,module_part_3,v710,v711,v712,v713,v715,v716,v718,v721,v723,v725,v726,v727,v728,msg_24,module_part_4,td_0,item_name_6,v729,v730,v731,v732,msg_25,module_part_5,td_1,item_name_7,v733,v734,v735,v736,v738,v739,v741,v744,v746,v747,v749,v751,v753,v754,msg_26,module_part_6,td_2,v755,v756,v757,v758,module_part_7,td_3,v759,v760,v761,v762,v764,v765,v766,v767,v768,v769,v773,v774,v775,v776,v777,v780,v783,v786,v787,v788,v790,v791,v792,msg_27,module_part_8,td_4,v794,v795,msg_28,module_part_9,td_5,item_name_8,v797,v798,v799,v800,msg_29,module_part_10,td_6,item_name_9,v801,v802,v803,v804,v805,v806,v808,v809,v811,v814,v816,v817,v819,msg_30,module_part_11,td_7,v821,v822,msg_31,module_part_12,v824,v825,v826,v827,v828,v829,v830,v831,v832,v833,v834,v835,v836,v837,v838,v839,v842,v843,v844,v845,v848,v851,v852,v853;
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
            v712 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__58 );
            v713 = new Object();
            v713.item0 = v712;
            v715 = v713.item0;
            v716 = new StringBuilder();
            v716.ll_append(__consts_0.const_str__85);
            v718 = ll_str__StringR_StringConst_String ( v715 );
            v716.ll_append(v718);
            v716.ll_append(__consts_0.const_str__35);
            v721 = v716.ll_build();
            v710.setAttribute(__consts_0.const_str__36,v721);
            v710.setAttribute(__consts_0.const_str__37,__consts_0.const_str__86);
            v725 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__58 );
            v726 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__89 );
            v727 = ll_streq__String_String ( v726,__consts_0.const_str__23 );
            msg_24 = msg_23;
            module_part_4 = module_part_3;
            td_0 = v710;
            item_name_6 = v725;
            if (v727 == false)
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
            v729 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__90 );
            v730 = ll_streq__String_String ( v729,__consts_0.const_str__91 );
            v731 = !v730;
            msg_25 = msg_24;
            module_part_5 = module_part_4;
            td_1 = td_0;
            item_name_7 = item_name_6;
            if (v731 == false)
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
            v733 = create_elem ( __consts_0.const_str__62 );
            v735 = ll_dict_getitem__Dict_String__String__String ( msg_25,__consts_0.const_str__58 );
            v736 = new Object();
            v736.item0 = v735;
            v738 = v736.item0;
            v739 = new StringBuilder();
            v739.ll_append(__consts_0.const_str__63);
            v741 = ll_str__StringR_StringConst_String ( v738 );
            v739.ll_append(v741);
            v739.ll_append(__consts_0.const_str__35);
            v744 = v739.ll_build();
            v733.setAttribute(__consts_0.const_str__64,v744);
            v746 = create_text_elem ( __consts_0.const_str__92 );
            v733.setAttribute(__consts_0.const_str__93,__consts_0.const_str__94);
            v733.appendChild(v746);
            td_1.appendChild(v733);
            v753 = __consts_0.ExportedMethods;
            v754 = v753.show_fail(item_name_7,fail_come_back);
            msg_26 = msg_25;
            module_part_6 = module_part_5;
            td_2 = td_1;
            block = 4;
            break;
            case 4:
            v755 = ll_dict_getitem__Dict_String__String__String ( msg_26,__consts_0.const_str__74 );
            v756 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__88,v755 );
            v757 = (v756==0);
            module_part_7 = module_part_6;
            td_3 = td_2;
            v759 = msg_26;
            if (v757 == false)
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
            v760 = ll_dict_getitem__Dict_String__String__String ( v759,__consts_0.const_str__74 );
            v761 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__88,v760 );
            v762 = (v761+1);
            __consts_0.const_tuple__88[v760]=v762;
            v764 = ll_strconcat__String_String ( __consts_0.const_str__84,v760 );
            v765 = get_elem ( v764 );
            v766 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__83,v760 );
            v767 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__88,v760 );
            v768 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__82,v760 );
            v769 = new Object();
            v769.item0 = v766;
            v769.item1 = v767;
            v769.item2 = v768;
            v773 = v769.item0;
            v774 = v769.item1;
            v775 = v769.item2;
            v776 = new StringBuilder();
            v777 = ll_str__StringR_StringConst_String ( v773 );
            v776.ll_append(v777);
            v776.ll_append(__consts_0.const_str__78);
            v780 = convertToString ( v774 );
            v776.ll_append(v780);
            v776.ll_append(__consts_0.const_str__95);
            v783 = convertToString ( v775 );
            v776.ll_append(v783);
            v776.ll_append(__consts_0.const_str__44);
            v786 = v776.ll_build();
            v787 = v765.childNodes;
            v788 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v787,0 );
            v788.nodeValue = v786;
            v790 = module_part_7.childNodes;
            v791 = ll_getitem__dum_nocheckConst_List_ExternalType__Signed ( v790,-1 );
            v791.appendChild(td_3);
            block = 6;
            break;
            case 7:
            v794 = create_elem ( __consts_0.const_str__18 );
            module_part_8.appendChild(v794);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v759 = msg_27;
            block = 5;
            break;
            case 8:
            v797 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__90 );
            v798 = ll_streq__String_String ( v797,__consts_0.const_str__96 );
            v799 = !v798;
            msg_25 = msg_28;
            module_part_5 = module_part_9;
            td_1 = td_5;
            item_name_7 = item_name_8;
            if (v799 == false)
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
            v801 = __consts_0.ExportedMethods;
            v802 = v801.show_skip(item_name_9,skip_come_back);
            v803 = create_elem ( __consts_0.const_str__62 );
            v805 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__58 );
            v806 = new Object();
            v806.item0 = v805;
            v808 = v806.item0;
            v809 = new StringBuilder();
            v809.ll_append(__consts_0.const_str__97);
            v811 = ll_str__StringR_StringConst_String ( v808 );
            v809.ll_append(v811);
            v809.ll_append(__consts_0.const_str__35);
            v814 = v809.ll_build();
            v803.setAttribute(__consts_0.const_str__64,v814);
            v816 = create_text_elem ( __consts_0.const_str__98 );
            v803.appendChild(v816);
            td_6.appendChild(v803);
            msg_26 = msg_29;
            module_part_6 = module_part_10;
            td_2 = td_6;
            block = 4;
            break;
            case 10:
            v821 = create_text_elem ( __consts_0.const_str__99 );
            td_7.appendChild(v821);
            msg_26 = msg_30;
            module_part_6 = module_part_11;
            td_2 = td_7;
            block = 4;
            break;
            case 11:
            v824 = __consts_0.Document;
            v825 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v826 = v824.getElementById(v825);
            v827 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v828 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v829 = ll_dict_getitem__Dict_String__List_String___String ( v827,v828 );
            v831 = ll_pop_default__dum_nocheckConst_List_String_ ( v829 );
            v832 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v833 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v834 = ll_dict_getitem__Dict_String__List_String___String ( v832,v833 );
            v835 = ll_len__List_String_ ( v834 );
            v836 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v837 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__75 );
            v838 = ll_dict_getitem__Dict_String__String__String ( v836,v837 );
            v839 = new Object();
            v839.item0 = v838;
            v839.item1 = v835;
            v842 = v839.item0;
            v843 = v839.item1;
            v844 = new StringBuilder();
            v845 = ll_str__StringR_StringConst_String ( v842 );
            v844.ll_append(v845);
            v844.ll_append(__consts_0.const_str__78);
            v848 = ll_int_str__IntegerR_SignedConst_Signed ( v843 );
            v844.ll_append(v848);
            v844.ll_append(__consts_0.const_str__44);
            v851 = v844.ll_build();
            v852 = v826.childNodes;
            v853 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v852,0 );
            v853.nodeValue = v851;
            msg_23 = msg_31;
            module_part_3 = module_part_12;
            block = 1;
            break;
            case 6:
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
            if (v666 == false)
            {
                block = 1;
                break;
            }
            v668 = mbox_2;
            block = 2;
            break;
            case 2:
            v669 = v668.parentNode;
            v669.scrollIntoView();
            block = 1;
            break;
            case 1:
            return ( undefined );
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
            __consts_0.Document.title = __consts_0.const_str__100;
            v675 = __consts_0.Document;
            v676 = v675.getElementById(__consts_0.const_str__41);
            v677 = v676.childNodes;
            v678 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v677,0 );
            v678.nodeValue = __consts_0.const_str__101;
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
            v690 = l_9.length;
            v692 = (v690+1);
            l_9.length = v692;
            l_9[v690]=newitem_0;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_prepend__List_String__String (l_10,newitem_1) {
    var v856,v857,v858,v859,l_11,newitem_2,dst_0,v861,v862,newitem_3,v863,v864,l_12,newitem_4,dst_1,v866,v867,v868,v869;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v857 = l_10.length;
            v859 = (v857+1);
            l_10.length = v859;
            l_11 = l_10;
            newitem_2 = newitem_1;
            dst_0 = v857;
            block = 1;
            break;
            case 1:
            v861 = (dst_0>0);
            newitem_3 = newitem_2;
            v863 = l_11;
            if (v861 == false)
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
            v863[0]=newitem_3;
            block = 3;
            break;
            case 4:
            v866 = (dst_1-1);
            v869 = l_12[v866];
            l_12[dst_1]=v869;
            l_11 = l_12;
            newitem_2 = newitem_4;
            dst_0 = v866;
            block = 1;
            break;
            case 3:
            return ( undefined );
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

function ll_pop_default__dum_nocheckConst_List_String_ (l_17) {
    var v1055,v1056,v1057,l_18,length_6,v1058,v1060,v1061,v1062,newlength_0,res_0,v1064,v1065;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1057 = l_17.length;
            l_18 = l_17;
            length_6 = v1057;
            block = 1;
            break;
            case 1:
            v1058 = (length_6>0);
            v1060 = (length_6-1);
            v1062 = l_18[v1060];
            ll_null_item__List_String_ ( l_18 );
            newlength_0 = v1060;
            res_0 = v1062;
            v1064 = l_18;
            block = 2;
            break;
            case 2:
            v1064.length = newlength_0;
            v1055 = res_0;
            block = 3;
            break;
            case 3:
            return ( v1055 );
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

function skip_come_back (msg_33) {
    var v1052,v1053;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1052 = ll_dict_getitem__Dict_String__String__String ( msg_33,__consts_0.const_str__59 );
            v1053 = ll_dict_getitem__Dict_String__String__String ( msg_33,__consts_0.const_str__102 );
            __consts_0.const_tuple__11[v1053]=v1052;
            block = 1;
            break;
            case 1:
            return ( undefined );
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

function ll_int__String_Signed (s_2,base_0) {
    var v936,v937,v938,v939,v940,v941,etype_6,evalue_6,s_3,base_1,v942,s_4,base_2,v943,v944,s_5,base_3,v945,v946,s_6,base_4,strlen_0,i_7,v947,v948,s_7,base_5,strlen_1,i_8,v949,v950,v951,v952,v953,s_8,base_6,strlen_2,i_9,v954,v955,v956,v957,s_9,base_7,strlen_3,i_10,v958,v959,v960,v961,s_10,base_8,strlen_4,i_11,sign_0,val_0,v962,v963,s_11,strlen_5,i_12,sign_1,val_1,v964,v965,sign_2,val_2,v966,v967,v968,v969,v970,v971,v972,v973,v974,v975,s_12,strlen_6,i_13,sign_3,val_3,v976,v977,v978,v979,s_13,strlen_7,sign_4,val_4,v980,v981,s_14,base_9,strlen_8,i_14,sign_5,val_5,v982,v983,v984,v985,v986,s_15,base_10,strlen_9,i_15,sign_6,val_6,c_0,v987,v988,s_16,base_11,strlen_10,i_16,sign_7,val_7,c_1,v989,v990,s_17,base_12,strlen_11,i_17,sign_8,val_8,c_2,v991,s_18,base_13,strlen_12,i_18,sign_9,val_9,c_3,v992,v993,s_19,base_14,strlen_13,i_19,sign_10,val_10,v994,v995,s_20,base_15,strlen_14,i_20,sign_11,val_11,digit_0,v996,v997,s_21,base_16,strlen_15,i_21,sign_12,digit_1,v998,v999,v1000,v1001,s_22,base_17,strlen_16,i_22,sign_13,val_12,c_4,v1002,s_23,base_18,strlen_17,i_23,sign_14,val_13,c_5,v1003,v1004,s_24,base_19,strlen_18,i_24,sign_15,val_14,v1005,v1006,v1007,s_25,base_20,strlen_19,i_25,sign_16,val_15,c_6,v1008,s_26,base_21,strlen_20,i_26,sign_17,val_16,c_7,v1009,v1010,s_27,base_22,strlen_21,i_27,sign_18,val_17,v1011,v1012,v1013,s_28,base_23,strlen_22,v1014,v1015,s_29,base_24,strlen_23,v1016,v1017,s_30,base_25,strlen_24,i_28,v1018,v1019,v1020,v1021,s_31,base_26,strlen_25,v1022,v1023;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v937 = (2<=base_0);
            if (v937 == false)
            {
                block = 1;
                break;
            }
            s_3 = s_2;
            base_1 = base_0;
            block = 3;
            break;
            case 1:
            v939 = __consts_0.exceptions_ValueError;
            v940 = v939.meta;
            etype_6 = v940;
            evalue_6 = v939;
            block = 2;
            break;
            case 3:
            v942 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v943 = v942;
            block = 4;
            break;
            case 4:
            if (v943 == false)
            {
                block = 1;
                break;
            }
            s_5 = s_4;
            base_3 = base_2;
            block = 5;
            break;
            case 5:
            v946 = s_5.length;
            s_6 = s_5;
            base_4 = base_3;
            strlen_0 = v946;
            i_7 = 0;
            block = 6;
            break;
            case 6:
            v947 = (i_7<strlen_0);
            s_7 = s_6;
            base_5 = base_4;
            strlen_1 = strlen_0;
            i_8 = i_7;
            if (v947 == false)
            {
                block = 7;
                break;
            }
            s_30 = s_6;
            base_25 = base_4;
            strlen_24 = strlen_0;
            i_28 = i_7;
            block = 35;
            break;
            case 7:
            v949 = (i_8<strlen_1);
            if (v949 == false)
            {
                block = 8;
                break;
            }
            s_8 = s_7;
            base_6 = base_5;
            strlen_2 = strlen_1;
            i_9 = i_8;
            block = 9;
            break;
            case 8:
            v951 = __consts_0.exceptions_ValueError;
            v952 = v951.meta;
            etype_6 = v952;
            evalue_6 = v951;
            block = 2;
            break;
            case 9:
            v955 = s_8.charAt(i_9);
            v956 = (v955=='-');
            s_9 = s_8;
            base_7 = base_6;
            strlen_3 = strlen_2;
            i_10 = i_9;
            if (v956 == false)
            {
                block = 10;
                break;
            }
            s_29 = s_8;
            base_24 = base_6;
            strlen_23 = strlen_2;
            v1016 = i_9;
            block = 34;
            break;
            case 10:
            v959 = s_9.charAt(i_10);
            v960 = (v959=='+');
            s_10 = s_9;
            base_8 = base_7;
            strlen_4 = strlen_3;
            i_11 = i_10;
            sign_0 = 1;
            val_0 = 0;
            if (v960 == false)
            {
                block = 11;
                break;
            }
            s_28 = s_9;
            base_23 = base_7;
            strlen_22 = strlen_3;
            v1014 = i_10;
            block = 33;
            break;
            case 11:
            v962 = (i_11<strlen_4);
            s_11 = s_10;
            strlen_5 = strlen_4;
            i_12 = i_11;
            sign_1 = sign_0;
            val_1 = val_0;
            if (v962 == false)
            {
                block = 12;
                break;
            }
            s_14 = s_10;
            base_9 = base_8;
            strlen_8 = strlen_4;
            i_14 = i_11;
            sign_5 = sign_0;
            val_5 = val_0;
            block = 19;
            break;
            case 12:
            v964 = (i_12<strlen_5);
            sign_2 = sign_1;
            val_2 = val_1;
            v966 = i_12;
            v967 = strlen_5;
            if (v964 == false)
            {
                block = 13;
                break;
            }
            s_12 = s_11;
            strlen_6 = strlen_5;
            i_13 = i_12;
            sign_3 = sign_1;
            val_3 = val_1;
            block = 17;
            break;
            case 13:
            v968 = (v966==v967);
            if (v968 == false)
            {
                block = 14;
                break;
            }
            v973 = sign_2;
            v974 = val_2;
            block = 15;
            break;
            case 14:
            v970 = __consts_0.exceptions_ValueError;
            v971 = v970.meta;
            etype_6 = v971;
            evalue_6 = v970;
            block = 2;
            break;
            case 15:
            v975 = (v973*v974);
            v936 = v975;
            block = 16;
            break;
            case 17:
            v977 = s_12.charAt(i_13);
            v978 = (v977==' ');
            sign_2 = sign_3;
            val_2 = val_3;
            v966 = i_13;
            v967 = strlen_6;
            if (v978 == false)
            {
                block = 13;
                break;
            }
            s_13 = s_12;
            strlen_7 = strlen_6;
            sign_4 = sign_3;
            val_4 = val_3;
            v980 = i_13;
            block = 18;
            break;
            case 18:
            v981 = (v980+1);
            s_11 = s_13;
            strlen_5 = strlen_7;
            i_12 = v981;
            sign_1 = sign_4;
            val_1 = val_4;
            block = 12;
            break;
            case 19:
            v983 = s_14.charAt(i_14);
            v984 = v983.charCodeAt(0);
            v985 = (97<=v984);
            s_15 = s_14;
            base_10 = base_9;
            strlen_9 = strlen_8;
            i_15 = i_14;
            sign_6 = sign_5;
            val_6 = val_5;
            c_0 = v984;
            if (v985 == false)
            {
                block = 20;
                break;
            }
            s_25 = s_14;
            base_20 = base_9;
            strlen_19 = strlen_8;
            i_25 = i_14;
            sign_16 = sign_5;
            val_15 = val_5;
            c_6 = v984;
            block = 30;
            break;
            case 20:
            v987 = (65<=c_0);
            s_16 = s_15;
            base_11 = base_10;
            strlen_10 = strlen_9;
            i_16 = i_15;
            sign_7 = sign_6;
            val_7 = val_6;
            c_1 = c_0;
            if (v987 == false)
            {
                block = 21;
                break;
            }
            s_22 = s_15;
            base_17 = base_10;
            strlen_16 = strlen_9;
            i_22 = i_15;
            sign_13 = sign_6;
            val_12 = val_6;
            c_4 = c_0;
            block = 27;
            break;
            case 21:
            v989 = (48<=c_1);
            s_11 = s_16;
            strlen_5 = strlen_10;
            i_12 = i_16;
            sign_1 = sign_7;
            val_1 = val_7;
            if (v989 == false)
            {
                block = 12;
                break;
            }
            s_17 = s_16;
            base_12 = base_11;
            strlen_11 = strlen_10;
            i_17 = i_16;
            sign_8 = sign_7;
            val_8 = val_7;
            c_2 = c_1;
            block = 22;
            break;
            case 22:
            v991 = (c_2<=57);
            s_18 = s_17;
            base_13 = base_12;
            strlen_12 = strlen_11;
            i_18 = i_17;
            sign_9 = sign_8;
            val_9 = val_8;
            c_3 = c_2;
            v992 = v991;
            block = 23;
            break;
            case 23:
            s_11 = s_18;
            strlen_5 = strlen_12;
            i_12 = i_18;
            sign_1 = sign_9;
            val_1 = val_9;
            if (v992 == false)
            {
                block = 12;
                break;
            }
            s_19 = s_18;
            base_14 = base_13;
            strlen_13 = strlen_12;
            i_19 = i_18;
            sign_10 = sign_9;
            val_10 = val_9;
            v994 = c_3;
            block = 24;
            break;
            case 24:
            v995 = (v994-48);
            s_20 = s_19;
            base_15 = base_14;
            strlen_14 = strlen_13;
            i_20 = i_19;
            sign_11 = sign_10;
            val_11 = val_10;
            digit_0 = v995;
            block = 25;
            break;
            case 25:
            v996 = (digit_0>=base_15);
            s_21 = s_20;
            base_16 = base_15;
            strlen_15 = strlen_14;
            i_21 = i_20;
            sign_12 = sign_11;
            digit_1 = digit_0;
            v998 = val_11;
            if (v996 == false)
            {
                block = 26;
                break;
            }
            s_11 = s_20;
            strlen_5 = strlen_14;
            i_12 = i_20;
            sign_1 = sign_11;
            val_1 = val_11;
            block = 12;
            break;
            case 26:
            v999 = (v998*base_16);
            v1000 = (v999+digit_1);
            v1001 = (i_21+1);
            s_10 = s_21;
            base_8 = base_16;
            strlen_4 = strlen_15;
            i_11 = v1001;
            sign_0 = sign_12;
            val_0 = v1000;
            block = 11;
            break;
            case 27:
            v1002 = (c_4<=90);
            s_23 = s_22;
            base_18 = base_17;
            strlen_17 = strlen_16;
            i_23 = i_22;
            sign_14 = sign_13;
            val_13 = val_12;
            c_5 = c_4;
            v1003 = v1002;
            block = 28;
            break;
            case 28:
            s_16 = s_23;
            base_11 = base_18;
            strlen_10 = strlen_17;
            i_16 = i_23;
            sign_7 = sign_14;
            val_7 = val_13;
            c_1 = c_5;
            if (v1003 == false)
            {
                block = 21;
                break;
            }
            s_24 = s_23;
            base_19 = base_18;
            strlen_18 = strlen_17;
            i_24 = i_23;
            sign_15 = sign_14;
            val_14 = val_13;
            v1005 = c_5;
            block = 29;
            break;
            case 29:
            v1006 = (v1005-65);
            v1007 = (v1006+10);
            s_20 = s_24;
            base_15 = base_19;
            strlen_14 = strlen_18;
            i_20 = i_24;
            sign_11 = sign_15;
            val_11 = val_14;
            digit_0 = v1007;
            block = 25;
            break;
            case 30:
            v1008 = (c_6<=122);
            s_26 = s_25;
            base_21 = base_20;
            strlen_20 = strlen_19;
            i_26 = i_25;
            sign_17 = sign_16;
            val_16 = val_15;
            c_7 = c_6;
            v1009 = v1008;
            block = 31;
            break;
            case 31:
            s_15 = s_26;
            base_10 = base_21;
            strlen_9 = strlen_20;
            i_15 = i_26;
            sign_6 = sign_17;
            val_6 = val_16;
            c_0 = c_7;
            if (v1009 == false)
            {
                block = 20;
                break;
            }
            s_27 = s_26;
            base_22 = base_21;
            strlen_21 = strlen_20;
            i_27 = i_26;
            sign_18 = sign_17;
            val_17 = val_16;
            v1011 = c_7;
            block = 32;
            break;
            case 32:
            v1012 = (v1011-97);
            v1013 = (v1012+10);
            s_20 = s_27;
            base_15 = base_22;
            strlen_14 = strlen_21;
            i_20 = i_27;
            sign_11 = sign_18;
            val_11 = val_17;
            digit_0 = v1013;
            block = 25;
            break;
            case 33:
            v1015 = (v1014+1);
            s_10 = s_28;
            base_8 = base_23;
            strlen_4 = strlen_22;
            i_11 = v1015;
            sign_0 = 1;
            val_0 = 0;
            block = 11;
            break;
            case 34:
            v1017 = (v1016+1);
            s_10 = s_29;
            base_8 = base_24;
            strlen_4 = strlen_23;
            i_11 = v1017;
            sign_0 = -1;
            val_0 = 0;
            block = 11;
            break;
            case 35:
            v1019 = s_30.charAt(i_28);
            v1020 = (v1019==' ');
            s_7 = s_30;
            base_5 = base_25;
            strlen_1 = strlen_24;
            i_8 = i_28;
            if (v1020 == false)
            {
                block = 7;
                break;
            }
            s_31 = s_30;
            base_26 = base_25;
            strlen_25 = strlen_24;
            v1022 = i_28;
            block = 36;
            break;
            case 36:
            v1023 = (v1022+1);
            s_6 = s_31;
            base_4 = base_26;
            strlen_0 = strlen_25;
            i_7 = v1023;
            block = 6;
            break;
            case 2:
            throw(evalue_6);
            case 16:
            return ( v936 );
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

function ll_strlen__String (obj_1) {
    var v1024,v1025,v1026;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1026 = obj_1.length;
            v1024 = v1026;
            block = 1;
            break;
            case 1:
            return ( v1024 );
        }
    }
}

function ll_int_str__IntegerR_SignedConst_Signed (i_6) {
    var v874,v875;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v875 = ll_int2dec__Signed ( i_6 );
            v874 = v875;
            block = 1;
            break;
            case 1:
            return ( v874 );
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
            __consts_0.Document.title = __consts_0.const_str__104;
            v683 = __consts_0.Document;
            v684 = v683.getElementById(__consts_0.const_str__41);
            v685 = v684.childNodes;
            v686 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalType__Signed ( v685,0 );
            v686.nodeValue = __consts_0.const_str__105;
            block = 1;
            break;
            case 1:
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
            v697 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__106 );
            v698 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__107 );
            v699 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__108 );
            v700 = new Object();
            v700.item0 = v697;
            v700.item1 = v698;
            v700.item2 = v699;
            v704 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__102 );
            __consts_0.const_tuple[v704]=v700;
            block = 1;
            break;
            case 1:
            return ( undefined );
        }
    }
}

function ll_dict_getitem__Dict_String__Signed__String (d_4,key_8) {
    var v1027,v1028,v1029,v1030,v1031,v1032,v1033,etype_7,evalue_7,key_9,v1034,v1035,v1036;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1029 = (d_4[key_8]!=undefined);
            if (v1029 == false)
            {
                block = 1;
                break;
            }
            key_9 = key_8;
            v1034 = d_4;
            block = 3;
            break;
            case 1:
            v1031 = __consts_0.exceptions_KeyError;
            v1032 = v1031.meta;
            etype_7 = v1032;
            evalue_7 = v1031;
            block = 2;
            break;
            case 3:
            v1036 = v1034[key_9];
            v1027 = v1036;
            block = 4;
            break;
            case 2:
            throw(evalue_7);
            case 4:
            return ( v1027 );
        }
    }
}

function ll_int2dec__Signed (i_29) {
    var v1069,v1070;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1070 = convertToString ( i_29 );
            v1069 = v1070;
            block = 1;
            break;
            case 1:
            return ( v1069 );
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

function exceptions_ValueError () {
}

exceptions_ValueError.prototype.toString = function (){
    return ( '<exceptions.ValueError object>' );
}

inherits(exceptions_ValueError,exceptions_StandardError);
function ll_len__List_String_ (l_13) {
    var v871,v872,v873;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v873 = l_13.length;
            v871 = v873;
            block = 1;
            break;
            case 1:
            return ( v871 );
        }
    }
}

function ll_getitem__dum_nocheckConst_List_ExternalType__Signed (l_14,index_5) {
    var v1037,v1038,v1039,v1040,v1041,l_15,index_6,length_4,v1042,v1044,index_7,v1046,v1047,v1048,l_16,length_5,v1049,v1050;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1039 = l_14.length;
            v1040 = (index_5<0);
            l_15 = l_14;
            index_6 = index_5;
            length_4 = v1039;
            if (v1040 == false)
            {
                block = 1;
                break;
            }
            l_16 = l_14;
            length_5 = v1039;
            v1049 = index_5;
            block = 4;
            break;
            case 1:
            v1042 = (index_6>=0);
            v1044 = (index_6<length_4);
            index_7 = index_6;
            v1046 = l_15;
            block = 2;
            break;
            case 2:
            v1048 = v1046[index_7];
            v1037 = v1048;
            block = 3;
            break;
            case 4:
            v1050 = (v1049+length_5);
            l_15 = l_16;
            index_6 = v1050;
            length_4 = length_5;
            block = 1;
            break;
            case 3:
            return ( v1037 );
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed (length_7) {
    var v1071,v1072;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1072 = ll_newlist__List_Dict_String__String__LlT_Signed_0 ( length_7 );
            v1071 = v1072;
            block = 1;
            break;
            case 1:
            return ( v1071 );
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed_0 (length_8) {
    var v1073,v1074,v1075;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1074 = new Array();
            v1074.length = length_8;
            v1073 = v1074;
            block = 1;
            break;
            case 1:
            return ( v1073 );
        }
    }
}

function Object_meta () {
    this.class_ = __consts_0.None;
}

Object_meta.prototype.toString = function (){
    return ( '<Object_meta object>' );
}

function py____test_rsession_webjs_Globals_meta () {
}

py____test_rsession_webjs_Globals_meta.prototype.toString = function (){
    return ( '<py.__.test.rsession.webjs.Globals_meta object>' );
}

inherits(py____test_rsession_webjs_Globals_meta,Object_meta);
function py____test_rsession_webjs_Options_meta () {
}

py____test_rsession_webjs_Options_meta.prototype.toString = function (){
    return ( '<py.__.test.rsession.webjs.Options_meta object>' );
}

inherits(py____test_rsession_webjs_Options_meta,Object_meta);
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
function exceptions_LookupError_meta () {
}

exceptions_LookupError_meta.prototype.toString = function (){
    return ( '<exceptions.LookupError_meta object>' );
}

inherits(exceptions_LookupError_meta,exceptions_StandardError_meta);
function exceptions_ValueError_meta () {
}

exceptions_ValueError_meta.prototype.toString = function (){
    return ( '<exceptions.ValueError_meta object>' );
}

inherits(exceptions_ValueError_meta,exceptions_StandardError_meta);
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
function exceptions_AssertionError_meta () {
}

exceptions_AssertionError_meta.prototype.toString = function (){
    return ( '<exceptions.AssertionError_meta object>' );
}

inherits(exceptions_AssertionError_meta,exceptions_StandardError_meta);
__consts_0 = {};
__consts_0.const_str__71 = ' failures, ';
__consts_0.const_str__34 = "show_host('";
__consts_0.const_str__84 = '_txt_';
__consts_0.const_list__120 = [];
__consts_0.const_str__62 = 'a';
__consts_0.const_str__93 = 'class';
__consts_0.const_str__44 = ']';
__consts_0.const_str__51 = 'ReceivedItemOutcome';
__consts_0.const_str__85 = "show_info('";
__consts_0.exceptions_ValueError__110 = exceptions_ValueError;
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.const_str__60 = '- skipped (';
__consts_0.const_str__38 = 'hide_host()';
__consts_0.const_str__86 = 'hide_info()';
__consts_0.const_str__31 = '#message';
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__17 = 'tbody';
__consts_0.const_tuple__83 = {};
__consts_0.const_str__61 = ')';
__consts_0.const_str__46 = 'main_table';
__consts_0.const_str__105 = 'Tests [interrupted]';
__consts_0.exceptions_KeyError__118 = exceptions_KeyError;
__consts_0.const_str__35 = "')";
__consts_0.const_str__55 = 'RsyncFinished';
__consts_0.Window = window;
__consts_0.const_str__70 = ' run, ';
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.py____test_rsession_webjs_Globals__121 = py____test_rsession_webjs_Globals;
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.const_str__107 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_str__94 = 'error';
__consts_0.const_tuple__24 = undefined;
__consts_0.const_str__72 = ' skipped';
__consts_0.const_str__69 = 'FINISHED ';
__consts_0.const_str__42 = 'Rsyncing';
__consts_0.const_str__13 = 'info';
__consts_0.const_str__19 = 'td';
__consts_0.const_str__39 = 'true';
__consts_0.const_tuple__26 = undefined;
__consts_0.const_str__10 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.py____test_rsession_webjs_Options__116 = py____test_rsession_webjs_Options;
__consts_0.py____test_rsession_webjs_Options_meta = new py____test_rsession_webjs_Options_meta();
__consts_0.py____test_rsession_webjs_Options = new py____test_rsession_webjs_Options();
__consts_0.const_str__92 = 'F';
__consts_0.const_str__37 = 'onmouseout';
__consts_0.const_str__47 = 'type';
__consts_0.const_str__89 = 'passed';
__consts_0.const_str__99 = '.';
__consts_0.const_str__53 = 'FailedTryiter';
__consts_0.const_tuple__11 = {};
__consts_0.const_str__33 = '#ff0000';
__consts_0.const_str__22 = 'checked';
__consts_0.const_str__28 = 'messagebox';
__consts_0.const_str__58 = 'fullitemname';
__consts_0.const_str__87 = 'table';
__consts_0.const_str__64 = 'href';
__consts_0.const_str__68 = 'skips';
__consts_0.const_str__57 = 'CrashedExecution';
__consts_0.const_str__5 = '\n';
__consts_0.const_tuple = {};
__consts_0.const_str__29 = 'pre';
__consts_0.const_str__104 = 'Py.test [interrupted]';
__consts_0.const_str__3 = '\n======== Stdout: ========\n';
__consts_0.const_str__76 = '#00ff00';
__consts_0.const_str__15 = 'beige';
__consts_0.const_str__80 = 'length';
__consts_0.exceptions_AssertionError__112 = exceptions_AssertionError;
__consts_0.exceptions_AssertionError_meta = new exceptions_AssertionError_meta();
__consts_0.exceptions_AssertionError = new exceptions_AssertionError();
__consts_0.const_str__106 = 'traceback';
__consts_0.const_str__45 = 'testmain';
__consts_0.const_str__97 = "javascript:show_skip('";
__consts_0.const_str__78 = '[';
__consts_0.const_str__101 = 'Tests [crashed]';
__consts_0.exceptions_StopIteration__114 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.const_str__43 = 'Tests [';
__consts_0.const_str__59 = 'reason';
__consts_0.const_str__63 = "javascript:show_traceback('";
__consts_0.const_str__41 = 'Tests';
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_str__98 = 's';
__consts_0.const_str__66 = 'run';
__consts_0.const_str__54 = 'SkippedTryiter';
__consts_0.const_str__91 = 'None';
__consts_0.const_str__23 = 'True';
__consts_0.const_str__95 = '/';
__consts_0.const_tuple__88 = {};
__consts_0.const_str__75 = 'hostkey';
__consts_0.const_str__67 = 'fails';
__consts_0.const_str__48 = 'ItemStart';
__consts_0.const_str__79 = 'itemname';
__consts_0.const_str__52 = 'TestFinished';
__consts_0.const_str__7 = 'jobs';
__consts_0.const_str__4 = '\n========== Stderr: ==========\n';
__consts_0.const_tuple__82 = {};
__consts_0.const_str__108 = 'stderr';
__consts_0.const_str__73 = 'Py.test ';
__consts_0.const_str__14 = 'visible';
__consts_0.const_str__96 = 'False';
__consts_0.const_str__50 = 'HostRSyncRootReady';
__consts_0.const_str__36 = 'onmouseover';
__consts_0.const_str__65 = '- FAILED TO LOAD MODULE';
__consts_0.const_str__81 = '[0/';
__consts_0.const_str__49 = 'SendItem';
__consts_0.const_str__74 = 'fullmodulename';
__consts_0.const_str__90 = 'skipped';
__consts_0.const_str__32 = 'hostsbody';
__consts_0.const_str__77 = '[0]';
__consts_0.const_str__8 = 'hidden';
__consts_0.const_str__2 = '====== Traceback: =========\n';
__consts_0.const_str__18 = 'tr';
__consts_0.const_str__102 = 'item_name';
__consts_0.const_list = undefined;
__consts_0.Document = document;
__consts_0.const_str__100 = 'Py.test [crashed]';
__consts_0.const_str__56 = 'InterruptedExecution';
__consts_0.const_str__21 = 'opt_scroll';
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__110;
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__118;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__121;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__10;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__10;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ofinished = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple__24;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__120;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__26;
__consts_0.py____test_rsession_webjs_Options_meta.class_ = __consts_0.py____test_rsession_webjs_Options__116;
__consts_0.py____test_rsession_webjs_Options.meta = __consts_0.py____test_rsession_webjs_Options_meta;
__consts_0.py____test_rsession_webjs_Options.oscroll = true;
__consts_0.exceptions_AssertionError_meta.class_ = __consts_0.exceptions_AssertionError__112;
__consts_0.exceptions_AssertionError.meta = __consts_0.exceptions_AssertionError_meta;
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__114;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
