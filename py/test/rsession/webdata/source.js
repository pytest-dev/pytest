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
    if (s1.length<s2.length) {
        return(false);
    }
    for (i = 0; i < s2.length; ++i){
        if (s1[i]!=s2[i]) {
            return(false);
        }
    }
    return(true);
}

function endswith(s1, s2) {
    if (s2.length>s1.length) {
        return(false);
    }
    for (i = s1.length-s2.length; i<s1.length; ++i) {
        if (s1[i]!=s2[i-s1.length+s2.length]) {
            return(false);
        }
    }
    return(true);
}

function splitchr(s, ch) {
    var i, lst;
    lst = [];
    next = "";
    for (i = 0; i<s.length; ++i) {
        if (s[i] == ch) {
            lst.length += 1;
            lst[lst.length-1] = next;
            next = "";
        } else {
            next += s[i];
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
    this.l += s;
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
            str += i + "=" + data[i].toString();
        }
    }
    //logDebug('show_all_statuses'+str);
    x.open("GET", 'show_all_statuses' + str, true);
    //x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
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
            str += i + "=" + data[i].toString();
        }
    }
    //logDebug('show_skip'+str);
    x.open("GET", 'show_skip' + str, true);
    //x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
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
            str += i + "=" + data[i].toString();
        }
    }
    //logDebug('show_sessid'+str);
    x.open("GET", 'show_sessid' + str, true);
    //x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
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
            str += i + "=" + data[i].toString();
        }
    }
    //logDebug('show_hosts'+str);
    x.open("GET", 'show_hosts' + str, true);
    //x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
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
            str += i + "=" + data[i].toString();
        }
    }
    //logDebug('show_fail'+str);
    x.open("GET", 'show_fail' + str, true);
    //x.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    x.onreadystatechange = function () { callback_4(x, callback) };
    //x.setRequestHeader("Connection", "close");
    //x.send(data);
    x.send(null);
}
function some_strange_function_which_will_never_be_called () {
    var v0,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13;
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
            return ( v0 );
        }
    }
}

function show_info (data_0) {
    var v46,v47,v48,v49,v50,data_1,info_0,v51,v52,v53,info_1,v54,v55,v56,v57,v58,v59,data_2,info_2,v60,v61,v62,v63;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v47 = __consts_0.Document;
            v48 = v47.getElementById(__consts_0.const_str__2);
            v49 = v48.style;
            v49.visibility = __consts_0.const_str__3;
            data_1 = data_0;
            info_0 = v48;
            block = 1;
            break;
            case 1:
            v51 = info_0.childNodes;
            v52 = ll_len__List_ExternalType_ ( v51 );
            v53 = !!v52;
            if (v53 == true)
            {
                data_2 = data_1;
                info_2 = info_0;
                block = 4;
                break;
            }
            else{
                info_1 = info_0;
                v54 = data_1;
                block = 2;
                break;
            }
            case 2:
            v55 = create_text_elem ( v54 );
            v56 = info_1;
            v56.appendChild(v55);
            v58 = info_1.style;
            v58.backgroundColor = __consts_0.const_str__4;
            block = 3;
            break;
            case 3:
            return ( v46 );
            case 4:
            v60 = info_2;
            v61 = info_2.childNodes;
            v62 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v61,0 );
            v60.removeChild(v62);
            data_1 = data_2;
            info_0 = info_2;
            block = 1;
            break;
        }
    }
}

function show_traceback (item_name_1) {
    var v28,v29,v30,v31,v32,v33,v34,v35,v36,v37,v38,v39,v40,v41,v42,v43,v44,v45;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v29 = ll_dict_getitem__Dict_String__Record_item2__Str_St ( __consts_0.const_tuple,item_name_1 );
            v30 = v29.item0;
            v31 = v29.item1;
            v32 = v29.item2;
            v33 = new StringBuilder();
            v33.ll_append(__consts_0.const_str__6);
            v35 = ll_str__StringR_StringConst_String ( undefined,v30 );
            v33.ll_append(v35);
            v33.ll_append(__consts_0.const_str__7);
            v38 = ll_str__StringR_StringConst_String ( undefined,v31 );
            v33.ll_append(v38);
            v33.ll_append(__consts_0.const_str__8);
            v41 = ll_str__StringR_StringConst_String ( undefined,v32 );
            v33.ll_append(v41);
            v33.ll_append(__consts_0.const_str__9);
            v44 = v33.ll_build();
            set_msgbox ( item_name_1,v44 );
            block = 1;
            break;
            case 1:
            return ( v28 );
        }
    }
}

function hide_info () {
    var v64,v65,v66,v67,v68;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v65 = __consts_0.Document;
            v66 = v65.getElementById(__consts_0.const_str__2);
            v67 = v66.style;
            v67.visibility = __consts_0.const_str__10;
            block = 1;
            break;
            case 1:
            return ( v64 );
        }
    }
}

function create_text_elem (txt_0) {
    var v131,v132,v133;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v132 = __consts_0.Document;
            v133 = v132.createTextNode(txt_0);
            v131 = v133;
            block = 1;
            break;
            case 1:
            return ( v131 );
        }
    }
}

function show_host (host_name_0) {
    var v69,v70,v71,v72,v73,host_name_1,elem_0,v74,v75,v76,v77,host_name_2,tbody_0,elem_1,v78,v79,last_exc_value_0,host_name_3,tbody_1,elem_2,item_0,v80,v81,v82,v83,v84,v85,v86,v87,v88,v89,host_name_4,tbody_2,elem_3,v90,v91,v92,v93,v94,v95,host_name_5,elem_4,v96,v97,v98,v99;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v70 = __consts_0.Document;
            v71 = v70.getElementById(__consts_0.const_str__11);
            v72 = v71.childNodes;
            v73 = ll_list_is_true__List_ExternalType_ ( v72 );
            if (v73 == true)
            {
                host_name_5 = host_name_0;
                elem_4 = v71;
                block = 6;
                break;
            }
            else{
                host_name_1 = host_name_0;
                elem_0 = v71;
                block = 1;
                break;
            }
            case 1:
            v74 = create_elem ( __consts_0.const_str__12 );
            v75 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v76 = ll_dict_getitem__Dict_String__List_String___String ( v75,host_name_1 );
            v77 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v76 );
            host_name_2 = host_name_1;
            tbody_0 = v74;
            elem_1 = elem_0;
            v78 = v77;
            block = 2;
            break;
            case 2:
            try {
                v79 = ll_listnext__Record_index__Signed__iterable ( v78 );
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
            v81 = create_elem ( __consts_0.const_str__14 );
            v82 = create_elem ( __consts_0.const_str__15 );
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
            v92.visibility = __consts_0.const_str__3;
            __consts_0.py____test_rsession_webjs_Globals.ohost = host_name_4;
            setTimeout ( 'reshow_host()',100 );
            block = 5;
            break;
            case 5:
            return ( v69 );
            case 6:
            v96 = elem_4;
            v97 = elem_4.childNodes;
            v98 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v97,0 );
            v96.removeChild(v98);
            host_name_1 = host_name_5;
            elem_0 = elem_4;
            block = 1;
            break;
        }
    }
}

function reshow_host () {
    var v212,v213,v214,v215,v216,v217;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v213 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v214 = ll_streq__String_String ( v213,__consts_0.const_str__16 );
            v215 = v214;
            if (v215 == true)
            {
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v216 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v216 );
            block = 2;
            break;
            case 2:
            return ( v212 );
        }
    }
}

function ll_dict_getitem__Dict_String__List_String___String (d_1,key_2) {
    var v184,v185,v186,v187,v188,v189,v190,etype_1,evalue_1,key_3,v191,v192,v193;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v185 = d_1;
            v186 = (v185[key_2]!=undefined);
            v187 = v186;
            if (v187 == true)
            {
                key_3 = key_2;
                v191 = d_1;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v188 = __consts_0.exceptions_KeyError;
            v189 = v188.meta;
            v190 = v188;
            etype_1 = v189;
            evalue_1 = v190;
            block = 2;
            break;
            case 2:
            throw(evalue_1);
            case 3:
            v192 = v191;
            v193 = v192[key_3];
            v184 = v193;
            block = 4;
            break;
            case 4:
            return ( v184 );
        }
    }
}

function ll_str__StringR_StringConst_String (self_0,s_0) {
    var v154;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v154 = s_0;
            block = 1;
            break;
            case 1:
            return ( v154 );
        }
    }
}

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalT (func_0,l_1,index_0) {
    var v134,v135,v136,l_2,index_1,v137,v138,v139,v140,index_2,v141,v142,v143;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v135 = (index_0>=0);
            undefined;
            l_2 = l_1;
            index_1 = index_0;
            block = 1;
            break;
            case 1:
            v137 = l_2;
            v138 = v137.length;
            v139 = (index_1<v138);
            undefined;
            index_2 = index_1;
            v141 = l_2;
            block = 2;
            break;
            case 2:
            v142 = v141;
            v143 = v142[index_2];
            v134 = v143;
            block = 3;
            break;
            case 3:
            return ( v134 );
        }
    }
}

function main () {
    var v14,v15,v16,v17,v18,v19,v20,v21,v22,v23,v24;
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
            v22 = v21.getElementById(__consts_0.const_str__19);
            v23 = v22;
            v23.setAttribute(__consts_0.const_str__20,__consts_0.const_str__21);
            block = 1;
            break;
            case 1:
            return ( v14 );
        }
    }
}

function key_pressed (key_5) {
    var v280,v281,v282,v283,v284,v285,v286,v287,v288,v289,v290,v291,v292,v293,v294,v295;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v281 = key_5.charCode;
            v282 = (v281==115);
            v283 = v282;
            if (v283 == true)
            {
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            return ( v280 );
            case 2:
            v284 = __consts_0.Document;
            v285 = v284.getElementById(__consts_0.const_str__19);
            v286 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v287 = v286;
            if (v287 == true)
            {
                v292 = v285;
                block = 4;
                break;
            }
            else{
                v288 = v285;
                block = 3;
                break;
            }
            case 3:
            v289 = v288;
            v289.setAttribute(__consts_0.const_str__20,__consts_0.const_str__23);
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 1;
            break;
            case 4:
            v293 = v292;
            v293.removeAttribute(__consts_0.const_str__20);
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 1;
            break;
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
function ll_list_is_true__List_ExternalType_ (l_3) {
    var v174,v175,v176,v177,v178,v179,v180;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v175 = !!l_3;
            v176 = v175;
            if (v176 == true)
            {
                v177 = l_3;
                block = 2;
                break;
            }
            else{
                v174 = v175;
                block = 1;
                break;
            }
            case 1:
            return ( v174 );
            case 2:
            v178 = v177;
            v179 = v178.length;
            v180 = (v179!=0);
            v174 = v180;
            block = 1;
            break;
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

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__16;
    this.ohost = __consts_0.const_str__16;
    this.orsync_dots = 0;
    this.ofinished = false;
    this.ohost_dict = __consts_0.const_tuple__24;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__26;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals instance>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
function set_msgbox (item_name_2,data_3) {
    var v155,v156,item_name_3,data_4,msgbox_0,v157,v158,v159,item_name_4,data_5,msgbox_1,v160,v161,v162,v163,v164,v165,v166,v167,v168,v169,item_name_5,data_6,msgbox_2,v170,v171,v172,v173;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v156 = get_elem ( __consts_0.const_str__27 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v156;
            block = 1;
            break;
            case 1:
            v157 = msgbox_0.childNodes;
            v158 = ll_len__List_ExternalType_ ( v157 );
            v159 = !!v158;
            if (v159 == true)
            {
                item_name_5 = item_name_3;
                data_6 = data_4;
                msgbox_2 = msgbox_0;
                block = 4;
                break;
            }
            else{
                item_name_4 = item_name_3;
                data_5 = data_4;
                msgbox_1 = msgbox_0;
                block = 2;
                break;
            }
            case 2:
            v160 = create_elem ( __consts_0.const_str__28 );
            v161 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__9 );
            v162 = ll_strconcat__String_String ( v161,data_5 );
            v163 = create_text_elem ( v162 );
            v164 = v160;
            v164.appendChild(v163);
            v166 = msgbox_1;
            v166.appendChild(v160);
            __consts_0.Document.location = __consts_0.const_str__29;
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 3:
            return ( v155 );
            case 4:
            v170 = msgbox_2;
            v171 = msgbox_2.childNodes;
            v172 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v171,0 );
            v170.removeChild(v172);
            item_name_3 = item_name_5;
            data_4 = data_6;
            msgbox_0 = msgbox_2;
            block = 1;
            break;
        }
    }
}

function ll_dict_getitem__Dict_String__Record_item2__Str_St (d_0,key_0) {
    var v144,v145,v146,v147,v148,v149,v150,etype_0,evalue_0,key_1,v151,v152,v153;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v145 = d_0;
            v146 = (v145[key_0]!=undefined);
            v147 = v146;
            if (v147 == true)
            {
                key_1 = key_0;
                v151 = d_0;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v148 = __consts_0.exceptions_KeyError;
            v149 = v148.meta;
            v150 = v148;
            etype_0 = v149;
            evalue_0 = v150;
            block = 2;
            break;
            case 2:
            throw(evalue_0);
            case 3:
            v152 = v151;
            v153 = v152[key_1];
            v144 = v153;
            block = 4;
            break;
            case 4:
            return ( v144 );
        }
    }
}

function ll_listnext__Record_index__Signed__iterable (iter_0) {
    var v198,v199,v200,v201,v202,v203,v204,iter_1,index_3,l_4,v205,v206,v207,v208,v209,v210,v211,etype_2,evalue_2;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v199 = iter_0.iterable;
            v200 = iter_0.index;
            v201 = v199;
            v202 = v201.length;
            v203 = (v200>=v202);
            v204 = v203;
            if (v204 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_1 = iter_0;
                index_3 = v200;
                l_4 = v199;
                block = 1;
                break;
            }
            case 1:
            v205 = (index_3+1);
            iter_1.index = v205;
            v207 = l_4;
            v208 = v207[index_3];
            v198 = v208;
            block = 2;
            break;
            case 2:
            return ( v198 );
            case 3:
            v209 = __consts_0.exceptions_StopIteration;
            v210 = v209.meta;
            v211 = v209;
            etype_2 = v210;
            evalue_2 = v211;
            block = 4;
            break;
            case 4:
            throw(evalue_2);
        }
    }
}

function show_skip (item_name_0) {
    var v25,v26,v27;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v26 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__31,item_name_0 );
            set_msgbox ( item_name_0,v26 );
            block = 1;
            break;
            case 1:
            return ( v25 );
        }
    }
}

function create_elem (s_1) {
    var v181,v182,v183;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v182 = __consts_0.Document;
            v183 = v182.createElement(s_1);
            v181 = v183;
            block = 1;
            break;
            case 1:
            return ( v181 );
        }
    }
}

function opt_scroll () {
    var v123,v124,v125,v126,v127;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v124 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v125 = v124;
            if (v125 == true)
            {
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 2;
            break;
            case 2:
            return ( v123 );
            case 3:
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 2;
            break;
        }
    }
}

function hide_messagebox () {
    var v114,v115,v116,mbox_0,v117,v118,mbox_1,v119,v120,v121,v122;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v115 = __consts_0.Document;
            v116 = v115.getElementById(__consts_0.const_str__27);
            mbox_0 = v116;
            block = 1;
            break;
            case 1:
            v117 = mbox_0.childNodes;
            v118 = ll_list_is_true__List_ExternalType_ ( v117 );
            if (v118 == true)
            {
                mbox_1 = mbox_0;
                block = 3;
                break;
            }
            else{
                block = 2;
                break;
            }
            case 2:
            return ( v114 );
            case 3:
            v119 = mbox_1;
            v120 = mbox_1.childNodes;
            v121 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v120,0 );
            v119.removeChild(v121);
            mbox_0 = mbox_1;
            block = 1;
            break;
        }
    }
}

function exceptions_KeyError () {
}

exceptions_KeyError.prototype.toString = function (){
    return ( '<exceptions_KeyError instance>' );
}

inherits(exceptions_KeyError,exceptions_LookupError);
function hide_host () {
    var v100,v101,v102,elem_5,v103,v104,v105,v106,v107,v108,v109,elem_6,v110,v111,v112,v113;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v101 = __consts_0.Document;
            v102 = v101.getElementById(__consts_0.const_str__11);
            elem_5 = v102;
            block = 1;
            break;
            case 1:
            v103 = elem_5.childNodes;
            v104 = ll_len__List_ExternalType_ ( v103 );
            v105 = !!v104;
            if (v105 == true)
            {
                elem_6 = elem_5;
                block = 4;
                break;
            }
            else{
                v106 = elem_5;
                block = 2;
                break;
            }
            case 2:
            v107 = v106.style;
            v107.visibility = __consts_0.const_str__10;
            __consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__16;
            block = 3;
            break;
            case 3:
            return ( v100 );
            case 4:
            v110 = elem_6;
            v111 = elem_6.childNodes;
            v112 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v111,0 );
            v110.removeChild(v112);
            elem_5 = elem_6;
            block = 1;
            break;
        }
    }
}

function get_elem (el_0) {
    var v296,v297,v298;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v297 = __consts_0.Document;
            v298 = v297.getElementById(el_0);
            v296 = v298;
            block = 1;
            break;
            case 1:
            return ( v296 );
        }
    }
}

function ll_streq__String_String (s1_0,s2_0) {
    var v218,v219,v220,v221,s2_1,v222,v223,v224,v225,v226,v227;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v219 = !!s1_0;
            v220 = !v219;
            v221 = v220;
            if (v221 == true)
            {
                v225 = s2_0;
                block = 3;
                break;
            }
            else{
                s2_1 = s2_0;
                v222 = s1_0;
                block = 1;
                break;
            }
            case 1:
            v223 = v222;
            v224 = (v223==s2_1);
            v218 = v224;
            block = 2;
            break;
            case 2:
            return ( v218 );
            case 3:
            v226 = !!v225;
            v227 = !v226;
            v218 = v227;
            block = 2;
            break;
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_S (ITER_0,lst_0) {
    var v194,v195,v196,v197;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v195 = new Object();
            v195.iterable = lst_0;
            v195.index = 0;
            v194 = v195;
            block = 1;
            break;
            case 1:
            return ( v194 );
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
function sessid_comeback (id_0) {
    var v276,v277,v278,v279;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.osessid = id_0;
            v278 = __consts_0.ExportedMethods;
            v279 = v278.show_all_statuses(id_0,comeback);
            block = 1;
            break;
            case 1:
            return ( v276 );
        }
    }
}

function host_init (host_dict_0) {
    var v228,v229,v230,v231,v232,v233,host_dict_1,tbody_3,v234,v235,last_exc_value_1,host_dict_2,tbody_4,host_0,v236,v237,v238,v239,v240,v241,v242,v243,v244,v245,v246,v247,v248,v249,v250,v251,v252,v253,v254,v255,v256,v257,v258,v259,v260,v261,v262,host_dict_3,v263,v264,v265,v266,v267,v268,v269,v270,last_exc_value_2,key_4,v271,v272,v273,v274,v275;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v229 = __consts_0.Document;
            v230 = v229.getElementById(__consts_0.const_str__32);
            v231 = host_dict_0;
            v232 = ll_dict_kvi__Dict_String__String__List_String_LlT_ ( v231,undefined,undefined );
            v233 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v232 );
            host_dict_1 = host_dict_0;
            tbody_3 = v230;
            v234 = v233;
            block = 1;
            break;
            case 1:
            try {
                v235 = ll_listnext__Record_index__Signed__iterable ( v234 );
                host_dict_2 = host_dict_1;
                tbody_4 = tbody_3;
                host_0 = v235;
                v236 = v234;
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
            v237 = create_elem ( __consts_0.const_str__14 );
            v238 = tbody_4;
            v238.appendChild(v237);
            v240 = create_elem ( __consts_0.const_str__15 );
            v241 = v240.style;
            v241.background = __consts_0.const_str__33;
            v243 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v244 = create_text_elem ( v243 );
            v245 = v240;
            v245.appendChild(v244);
            v240.id = host_0;
            v248 = v237;
            v248.appendChild(v240);
            v250 = v240;
            v251 = new StringBuilder();
            v251.ll_append(__consts_0.const_str__34);
            v253 = ll_str__StringR_StringConst_String ( undefined,host_0 );
            v251.ll_append(v253);
            v251.ll_append(__consts_0.const_str__35);
            v256 = v251.ll_build();
            v250.setAttribute(__consts_0.const_str__36,v256);
            v258 = v240;
            v258.setAttribute(__consts_0.const_str__37,__consts_0.const_str__38);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
            setTimeout ( 'update_rsync()',1000 );
            host_dict_1 = host_dict_2;
            tbody_3 = tbody_4;
            v234 = v236;
            block = 1;
            break;
            case 3:
            __consts_0.py____test_rsession_webjs_Globals.ohost_dict = host_dict_3;
            v264 = ll_newdict__Dict_String__List_String__LlT ( undefined );
            __consts_0.py____test_rsession_webjs_Globals.ohost_pending = v264;
            v266 = host_dict_3;
            v267 = ll_dict_kvi__Dict_String__String__List_String_LlT_ ( v266,undefined,undefined );
            v268 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v267 );
            v269 = v268;
            block = 4;
            break;
            case 4:
            try {
                v270 = ll_listnext__Record_index__Signed__iterable ( v269 );
                key_4 = v270;
                v271 = v269;
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
            v272 = new Array();
            v272.length = 0;
            v274 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v274[key_4]=v272;
            v269 = v271;
            block = 4;
            break;
            case 6:
            return ( v228 );
        }
    }
}

function ll_dict_getitem__Dict_String__String__String (d_2,key_6) {
    var v302,v303,v304,v305,v306,v307,v308,etype_3,evalue_3,key_7,v309,v310,v311;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v303 = d_2;
            v304 = (v303[key_6]!=undefined);
            v305 = v304;
            if (v305 == true)
            {
                key_7 = key_6;
                v309 = d_2;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v306 = __consts_0.exceptions_KeyError;
            v307 = v306.meta;
            v308 = v306;
            etype_3 = v307;
            evalue_3 = v308;
            block = 2;
            break;
            case 2:
            throw(evalue_3);
            case 3:
            v310 = v309;
            v311 = v310[key_7];
            v302 = v311;
            block = 4;
            break;
            case 4:
            return ( v302 );
        }
    }
}

function comeback (msglist_0) {
    var v312,v313,v314,v315,msglist_1,v316,v317,v318,v319,msglist_2,v320,v321,last_exc_value_3,msglist_3,v322,v323,v324,v325,msglist_4,v326,v327,v328,v329,v330,v331,last_exc_value_4,v332,v333,v334,v335,v336,v337,v338;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v313 = ll_len__List_Dict_String__String__ ( msglist_0 );
            v314 = (v313==0);
            v315 = v314;
            if (v315 == true)
            {
                block = 4;
                break;
            }
            else{
                msglist_1 = msglist_0;
                block = 1;
                break;
            }
            case 1:
            v316 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v317 = 0;
            v318 = ll_listslice_startonly__List_Dict_String__String__ ( undefined,v316,v317 );
            v319 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,v318 );
            msglist_2 = msglist_1;
            v320 = v319;
            block = 2;
            break;
            case 2:
            try {
                v321 = ll_listnext__Record_index__Signed__iterable_0 ( v320 );
                msglist_3 = msglist_2;
                v322 = v320;
                v323 = v321;
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
            v324 = process ( v323 );
            v325 = v324;
            if (v325 == true)
            {
                msglist_2 = msglist_3;
                v320 = v322;
                block = 2;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 4:
            return ( v312 );
            case 5:
            v326 = new Array();
            v326.length = 0;
            __consts_0.py____test_rsession_webjs_Globals.opending = v326;
            v329 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,msglist_4 );
            v330 = v329;
            block = 6;
            break;
            case 6:
            try {
                v331 = ll_listnext__Record_index__Signed__iterable_0 ( v330 );
                v332 = v330;
                v333 = v331;
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
            v334 = process ( v333 );
            v335 = v334;
            if (v335 == true)
            {
                v330 = v332;
                block = 6;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 8:
            v336 = __consts_0.ExportedMethods;
            v337 = __consts_0.py____test_rsession_webjs_Globals.osessid;
            v338 = v336.show_all_statuses(v337,comeback);
            block = 4;
            break;
        }
    }
}

function ll_strconcat__String_String (obj_0,arg0_0) {
    var v299,v300,v301;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v300 = obj_0;
            v301 = (v300+arg0_0);
            v299 = v301;
            block = 1;
            break;
            case 1:
            return ( v299 );
        }
    }
}

function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions_StopIteration instance>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
function ll_listnext__Record_index__Signed__iterable_0 (iter_2) {
    var v415,v416,v417,v418,v419,v420,v421,iter_3,index_4,l_8,v422,v423,v424,v425,v426,v427,v428,etype_4,evalue_4;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v416 = iter_2.iterable;
            v417 = iter_2.index;
            v418 = v416;
            v419 = v418.length;
            v420 = (v417>=v419);
            v421 = v420;
            if (v421 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_3 = iter_2;
                index_4 = v417;
                l_8 = v416;
                block = 1;
                break;
            }
            case 1:
            v422 = (index_4+1);
            iter_3.index = v422;
            v424 = l_8;
            v425 = v424[index_4];
            v415 = v425;
            block = 2;
            break;
            case 2:
            return ( v415 );
            case 3:
            v426 = __consts_0.exceptions_StopIteration;
            v427 = v426.meta;
            v428 = v426;
            etype_4 = v427;
            evalue_4 = v428;
            block = 4;
            break;
            case 4:
            throw(evalue_4);
        }
    }
}

function update_rsync () {
    var v354,v355,v356,v357,v358,v359,v360,v361,v362,elem_7,v363,v364,v365,v366,v367,v368,v369,v370,v371,elem_8,v372,v373,v374,v375,v376,v377,v378,v379,v380,v381,v382,text_0,elem_9,v383,v384,v385,v386,v387;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v355 = __consts_0.py____test_rsession_webjs_Globals.ofinished;
            v356 = v355;
            if (v356 == true)
            {
                block = 4;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v357 = __consts_0.Document;
            v358 = v357.getElementById(__consts_0.const_str__39);
            v359 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v360 = v359;
            v361 = (v360==1);
            v362 = v361;
            if (v362 == true)
            {
                v384 = v358;
                block = 6;
                break;
            }
            else{
                elem_7 = v358;
                block = 2;
                break;
            }
            case 2:
            v363 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v364 = ll_char_mul__Char_Signed ( '.',v363 );
            v365 = ll_strconcat__String_String ( __consts_0.const_str__40,v364 );
            v366 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v367 = (v366+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v367;
            v369 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v370 = (v369>5);
            v371 = v370;
            if (v371 == true)
            {
                text_0 = v365;
                elem_9 = elem_7;
                block = 5;
                break;
            }
            else{
                elem_8 = elem_7;
                v372 = v365;
                block = 3;
                break;
            }
            case 3:
            v373 = new StringBuilder();
            v373.ll_append(__consts_0.const_str__41);
            v375 = ll_str__StringR_StringConst_String ( undefined,v372 );
            v373.ll_append(v375);
            v373.ll_append(__consts_0.const_str__42);
            v378 = v373.ll_build();
            v379 = elem_8.childNodes;
            v380 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v379,0 );
            v380.nodeValue = v378;
            setTimeout ( 'update_rsync()',1000 );
            block = 4;
            break;
            case 4:
            return ( v354 );
            case 5:
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            elem_8 = elem_9;
            v372 = text_0;
            block = 3;
            break;
            case 6:
            v385 = v384.childNodes;
            v386 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v385,0 );
            v386.nodeValue = __consts_0.const_str__39;
            block = 4;
            break;
        }
    }
}

function process (msg_0) {
    var v429,v430,v431,v432,msg_1,v433,v434,v435,v436,v437,v438,v439,msg_2,v440,v441,v442,msg_3,v443,v444,v445,msg_4,v446,v447,v448,msg_5,v449,v450,v451,msg_6,v452,v453,v454,msg_7,v455,v456,v457,msg_8,v458,v459,v460,msg_9,v461,v462,v463,v464,v465,v466,v467,v468,v469,v470,v471,v472,v473,v474,v475,msg_10,v476,v477,v478,msg_11,v479,v480,v481,msg_12,module_part_0,v482,v483,v484,v485,v486,v487,v488,v489,v490,v491,v492,v493,v494,v495,v496,v497,v498,v499,v500,msg_13,v501,v502,v503,msg_14,v504,v505,v506,module_part_1,v507,v508,v509,v510,v511,v512,v513,v514,v515,msg_15,v516,v517,v518,v519,v520,v521,v522,v523,v524,v525,v526,v527,v528,v529,v530,v531,v532,v533,v534,v535,v536,v537,v538,v539,v540,v541,v542,v543,v544,v545,v546,v547,v548,v549,v550,v551,v552,v553,v554,v555,msg_16,v556,v557,v558,msg_17,v559,v560,v561,v562,v563,v564,msg_18,v565,v566,v567,v568,v569,v570,v571,v572,v573,v574,v575,v576,v577,v578,v579,v580,v581,v582,v583,msg_19,v584,v585,v586,v587,v588,v589,v590,v591,v592,v593,v594,v595,v596,v597,v598,v599,v600,v601,v602,v603,v604,v605,v606,v607,v608,v609,v610,v611,v612,v613,v614,v615,main_t_0,v616,v617,v618,v619;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v430 = get_dict_len ( msg_0 );
            v431 = (v430==0);
            v432 = v431;
            if (v432 == true)
            {
                v429 = false;
                block = 12;
                break;
            }
            else{
                msg_1 = msg_0;
                block = 1;
                break;
            }
            case 1:
            v433 = __consts_0.Document;
            v434 = v433.getElementById(__consts_0.const_str__43);
            v435 = __consts_0.Document;
            v436 = v435.getElementById(__consts_0.const_str__44);
            v437 = ll_dict_getitem__Dict_String__String__String ( msg_1,__consts_0.const_str__45 );
            v438 = ll_streq__String_String ( v437,__consts_0.const_str__46 );
            v439 = v438;
            if (v439 == true)
            {
                main_t_0 = v436;
                v616 = msg_1;
                block = 29;
                break;
            }
            else{
                msg_2 = msg_1;
                block = 2;
                break;
            }
            case 2:
            v440 = ll_dict_getitem__Dict_String__String__String ( msg_2,__consts_0.const_str__45 );
            v441 = ll_streq__String_String ( v440,__consts_0.const_str__47 );
            v442 = v441;
            if (v442 == true)
            {
                msg_19 = msg_2;
                block = 28;
                break;
            }
            else{
                msg_3 = msg_2;
                block = 3;
                break;
            }
            case 3:
            v443 = ll_dict_getitem__Dict_String__String__String ( msg_3,__consts_0.const_str__45 );
            v444 = ll_streq__String_String ( v443,__consts_0.const_str__48 );
            v445 = v444;
            if (v445 == true)
            {
                msg_18 = msg_3;
                block = 27;
                break;
            }
            else{
                msg_4 = msg_3;
                block = 4;
                break;
            }
            case 4:
            v446 = ll_dict_getitem__Dict_String__String__String ( msg_4,__consts_0.const_str__45 );
            v447 = ll_streq__String_String ( v446,__consts_0.const_str__49 );
            v448 = v447;
            if (v448 == true)
            {
                msg_16 = msg_4;
                block = 24;
                break;
            }
            else{
                msg_5 = msg_4;
                block = 5;
                break;
            }
            case 5:
            v449 = ll_dict_getitem__Dict_String__String__String ( msg_5,__consts_0.const_str__45 );
            v450 = ll_streq__String_String ( v449,__consts_0.const_str__50 );
            v451 = v450;
            if (v451 == true)
            {
                msg_15 = msg_5;
                block = 23;
                break;
            }
            else{
                msg_6 = msg_5;
                block = 6;
                break;
            }
            case 6:
            v452 = ll_dict_getitem__Dict_String__String__String ( msg_6,__consts_0.const_str__45 );
            v453 = ll_streq__String_String ( v452,__consts_0.const_str__51 );
            v454 = v453;
            if (v454 == true)
            {
                msg_13 = msg_6;
                block = 20;
                break;
            }
            else{
                msg_7 = msg_6;
                block = 7;
                break;
            }
            case 7:
            v455 = ll_dict_getitem__Dict_String__String__String ( msg_7,__consts_0.const_str__45 );
            v456 = ll_streq__String_String ( v455,__consts_0.const_str__52 );
            v457 = v456;
            if (v457 == true)
            {
                msg_10 = msg_7;
                block = 17;
                break;
            }
            else{
                msg_8 = msg_7;
                block = 8;
                break;
            }
            case 8:
            v458 = ll_dict_getitem__Dict_String__String__String ( msg_8,__consts_0.const_str__45 );
            v459 = ll_streq__String_String ( v458,__consts_0.const_str__53 );
            v460 = v459;
            if (v460 == true)
            {
                block = 16;
                break;
            }
            else{
                msg_9 = msg_8;
                block = 9;
                break;
            }
            case 9:
            v461 = ll_dict_getitem__Dict_String__String__String ( msg_9,__consts_0.const_str__45 );
            v462 = ll_streq__String_String ( v461,__consts_0.const_str__54 );
            v463 = v462;
            if (v463 == true)
            {
                block = 15;
                break;
            }
            else{
                v464 = msg_9;
                block = 10;
                break;
            }
            case 10:
            v465 = ll_dict_getitem__Dict_String__String__String ( v464,__consts_0.const_str__45 );
            v466 = ll_streq__String_String ( v465,__consts_0.const_str__55 );
            v467 = v466;
            if (v467 == true)
            {
                block = 14;
                break;
            }
            else{
                block = 11;
                break;
            }
            case 11:
            v468 = __consts_0.py____test_rsession_webjs_Globals.odata_empty;
            v469 = v468;
            if (v469 == true)
            {
                block = 13;
                break;
            }
            else{
                v429 = true;
                block = 12;
                break;
            }
            case 12:
            return ( v429 );
            case 13:
            v470 = __consts_0.Document;
            v471 = v470.getElementById(__consts_0.const_str__27);
            scroll_down_if_needed ( v471 );
            v429 = true;
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
            v476 = ll_dict_getitem__Dict_String__String__String ( msg_10,__consts_0.const_str__56 );
            v477 = get_elem ( v476 );
            v478 = !!v477;
            if (v478 == true)
            {
                msg_12 = msg_10;
                module_part_0 = v477;
                block = 19;
                break;
            }
            else{
                msg_11 = msg_10;
                block = 18;
                break;
            }
            case 18:
            v479 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v480 = v479;
            ll_append__List_Dict_String__String___Dict_String_ ( v480,msg_11 );
            v429 = true;
            block = 12;
            break;
            case 19:
            v482 = create_elem ( __consts_0.const_str__14 );
            v483 = create_elem ( __consts_0.const_str__15 );
            v484 = ll_dict_getitem__Dict_String__String__String ( msg_12,__consts_0.const_str__57 );
            v485 = new Object();
            v485.item0 = v484;
            v487 = v485.item0;
            v488 = new StringBuilder();
            v488.ll_append(__consts_0.const_str__58);
            v490 = ll_str__StringR_StringConst_String ( undefined,v487 );
            v488.ll_append(v490);
            v488.ll_append(__consts_0.const_str__59);
            v493 = v488.ll_build();
            v494 = create_text_elem ( v493 );
            v495 = v483;
            v495.appendChild(v494);
            v497 = v482;
            v497.appendChild(v483);
            v499 = module_part_0;
            v499.appendChild(v482);
            block = 11;
            break;
            case 20:
            v501 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__56 );
            v502 = get_elem ( v501 );
            v503 = !!v502;
            if (v503 == true)
            {
                module_part_1 = v502;
                block = 22;
                break;
            }
            else{
                msg_14 = msg_13;
                block = 21;
                break;
            }
            case 21:
            v504 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v505 = v504;
            ll_append__List_Dict_String__String___Dict_String_ ( v505,msg_14 );
            v429 = true;
            block = 12;
            break;
            case 22:
            v507 = create_elem ( __consts_0.const_str__14 );
            v508 = create_elem ( __consts_0.const_str__15 );
            v509 = create_text_elem ( __consts_0.const_str__60 );
            v510 = v508;
            v510.appendChild(v509);
            v512 = v507;
            v512.appendChild(v508);
            v514 = module_part_1;
            v514.appendChild(v507);
            block = 11;
            break;
            case 23:
            v516 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__61 );
            v517 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__62 );
            v518 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__63 );
            v519 = new Object();
            v519.item0 = v516;
            v519.item1 = v517;
            v519.item2 = v518;
            v523 = v519.item0;
            v524 = v519.item1;
            v525 = v519.item2;
            v526 = new StringBuilder();
            v526.ll_append(__consts_0.const_str__64);
            v528 = ll_str__StringR_StringConst_String ( undefined,v523 );
            v526.ll_append(v528);
            v526.ll_append(__consts_0.const_str__65);
            v531 = ll_str__StringR_StringConst_String ( undefined,v524 );
            v526.ll_append(v531);
            v526.ll_append(__consts_0.const_str__66);
            v534 = ll_str__StringR_StringConst_String ( undefined,v525 );
            v526.ll_append(v534);
            v526.ll_append(__consts_0.const_str__67);
            v537 = v526.ll_build();
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            v539 = new StringBuilder();
            v539.ll_append(__consts_0.const_str__68);
            v541 = ll_str__StringR_StringConst_String ( undefined,v537 );
            v539.ll_append(v541);
            v543 = v539.ll_build();
            __consts_0.Document.title = v543;
            v545 = new StringBuilder();
            v545.ll_append(__consts_0.const_str__41);
            v547 = ll_str__StringR_StringConst_String ( undefined,v537 );
            v545.ll_append(v547);
            v545.ll_append(__consts_0.const_str__42);
            v550 = v545.ll_build();
            v551 = __consts_0.Document;
            v552 = v551.getElementById(__consts_0.const_str__39);
            v553 = v552.childNodes;
            v554 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v553,0 );
            v554.nodeValue = v550;
            block = 11;
            break;
            case 24:
            v556 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__69 );
            v557 = get_elem ( v556 );
            v558 = !!v557;
            if (v558 == true)
            {
                v562 = msg_16;
                v563 = v557;
                block = 26;
                break;
            }
            else{
                msg_17 = msg_16;
                block = 25;
                break;
            }
            case 25:
            v559 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v560 = v559;
            ll_append__List_Dict_String__String___Dict_String_ ( v560,msg_17 );
            v429 = true;
            block = 12;
            break;
            case 26:
            add_received_item_outcome ( v562,v563 );
            block = 11;
            break;
            case 27:
            v565 = __consts_0.Document;
            v566 = ll_dict_getitem__Dict_String__String__String ( msg_18,__consts_0.const_str__70 );
            v567 = v565.getElementById(v566);
            v568 = v567.style;
            v568.background = __consts_0.const_str__71;
            v570 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v571 = ll_dict_getitem__Dict_String__String__String ( msg_18,__consts_0.const_str__70 );
            v572 = ll_dict_getitem__Dict_String__String__String ( v570,v571 );
            v573 = new Object();
            v573.item0 = v572;
            v575 = v573.item0;
            v576 = new StringBuilder();
            v577 = ll_str__StringR_StringConst_String ( undefined,v575 );
            v576.ll_append(v577);
            v576.ll_append(__consts_0.const_str__72);
            v580 = v576.ll_build();
            v581 = v567.childNodes;
            v582 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v581,0 );
            v582.nodeValue = v580;
            block = 11;
            break;
            case 28:
            v584 = __consts_0.Document;
            v585 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__70 );
            v586 = v584.getElementById(v585);
            v587 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v588 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__70 );
            v589 = ll_dict_getitem__Dict_String__List_String___String ( v587,v588 );
            v590 = v589;
            v591 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__56 );
            ll_prepend__List_String__String ( v590,v591 );
            v593 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v594 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__70 );
            v595 = ll_dict_getitem__Dict_String__List_String___String ( v593,v594 );
            v596 = ll_len__List_String_ ( v595 );
            v597 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v598 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__70 );
            v599 = ll_dict_getitem__Dict_String__String__String ( v597,v598 );
            v600 = new Object();
            v600.item0 = v599;
            v600.item1 = v596;
            v603 = v600.item0;
            v604 = v600.item1;
            v605 = new StringBuilder();
            v606 = ll_str__StringR_StringConst_String ( undefined,v603 );
            v605.ll_append(v606);
            v605.ll_append(__consts_0.const_str__73);
            v609 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v604 );
            v605.ll_append(v609);
            v605.ll_append(__consts_0.const_str__42);
            v612 = v605.ll_build();
            v613 = v586.childNodes;
            v614 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v613,0 );
            v614.nodeValue = v612;
            block = 11;
            break;
            case 29:
            v617 = make_module_box ( v616 );
            v618 = main_t_0;
            v618.appendChild(v617);
            block = 11;
            break;
        }
    }
}

function show_interrupt () {
    var v647,v648,v649,v650,v651,v652,v653,v654;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__74;
            v650 = __consts_0.Document;
            v651 = v650.getElementById(__consts_0.const_str__39);
            v652 = v651.childNodes;
            v653 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v652,0 );
            v653.nodeValue = __consts_0.const_str__75;
            block = 1;
            break;
            case 1:
            return ( v647 );
        }
    }
}

function ll_prepend__List_String__String (l_10,newitem_1) {
    var v811,v812,v813,v814,v815,v816,l_11,newitem_2,dst_0,v817,v818,newitem_3,v819,v820,v821,l_12,newitem_4,dst_1,v822,v823,v824,v825,v826;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v812 = l_10;
            v813 = v812.length;
            v814 = l_10;
            v815 = (v813+1);
            v814.length = v815;
            l_11 = l_10;
            newitem_2 = newitem_1;
            dst_0 = v813;
            block = 1;
            break;
            case 1:
            v817 = (dst_0>0);
            v818 = v817;
            if (v818 == true)
            {
                l_12 = l_11;
                newitem_4 = newitem_2;
                dst_1 = dst_0;
                block = 4;
                break;
            }
            else{
                newitem_3 = newitem_2;
                v819 = l_11;
                block = 2;
                break;
            }
            case 2:
            v820 = v819;
            v820[0]=newitem_3;
            block = 3;
            break;
            case 3:
            return ( v811 );
            case 4:
            v822 = (dst_1-1);
            v823 = l_12;
            v824 = l_12;
            v825 = v824[v822];
            v823[dst_1]=v825;
            l_11 = l_12;
            newitem_2 = newitem_4;
            dst_0 = v822;
            block = 1;
            break;
        }
    }
}

function scroll_down_if_needed (mbox_2) {
    var v632,v633,v634,v635,v636,v637,v638;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v633 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v634 = v633;
            if (v634 == true)
            {
                v635 = mbox_2;
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            return ( v632 );
            case 2:
            v636 = v635.parentNode;
            v637 = v636;
            v637.scrollIntoView();
            block = 1;
            break;
        }
    }
}

function ll_newdict__Dict_String__List_String__LlT (DICT_0) {
    var v388,v389;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v389 = new Object();
            v388 = v389;
            block = 1;
            break;
            case 1:
            return ( v388 );
        }
    }
}

function ll_dict_kvi__Dict_String__String__List_String_LlT_ (d_3,LIST_0,func_1) {
    var v339,v340,v341,v342,v343,v344,i_0,it_0,result_0,v345,v346,v347,i_1,it_1,result_1,v348,v349,v350,v351,it_2,result_2,v352,v353;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v340 = d_3;
            v341 = get_dict_len ( v340 );
            v342 = ll_newlist__List_String_LlT_Signed ( undefined,v341 );
            v343 = d_3;
            v344 = dict_items_iterator ( v343 );
            i_0 = 0;
            it_0 = v344;
            result_0 = v342;
            block = 1;
            break;
            case 1:
            v345 = it_0;
            v346 = v345.ll_go_next();
            v347 = v346;
            if (v347 == true)
            {
                i_1 = i_0;
                it_1 = it_0;
                result_1 = result_0;
                block = 3;
                break;
            }
            else{
                v339 = result_0;
                block = 2;
                break;
            }
            case 2:
            return ( v339 );
            case 3:
            v348 = result_1;
            v349 = it_1;
            v350 = v349.ll_current_key();
            v348[i_1]=v350;
            it_2 = it_1;
            result_2 = result_1;
            v352 = i_1;
            block = 4;
            break;
            case 4:
            v353 = (v352+1);
            i_0 = v353;
            it_0 = it_2;
            result_0 = result_2;
            block = 1;
            break;
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_D (ITER_1,lst_1) {
    var v411,v412,v413,v414;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v412 = new Object();
            v412.iterable = lst_1;
            v412.index = 0;
            v411 = v412;
            block = 1;
            break;
            case 1:
            return ( v411 );
        }
    }
}

function ll_append__List_Dict_String__String___Dict_String_ (l_9,newitem_0) {
    var v655,v656,v657,v658,v659,v660,v661,v662;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v656 = l_9;
            v657 = v656.length;
            v658 = l_9;
            v659 = (v657+1);
            v658.length = v659;
            v661 = l_9;
            v661[v657]=newitem_0;
            block = 1;
            break;
            case 1:
            return ( v655 );
        }
    }
}

function ll_len__List_Dict_String__String__ (l_5) {
    var v390,v391,v392;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v391 = l_5;
            v392 = v391.length;
            v390 = v392;
            block = 1;
            break;
            case 1:
            return ( v390 );
        }
    }
}

function show_crash () {
    var v639,v640,v641,v642,v643,v644,v645,v646;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__76;
            v642 = __consts_0.Document;
            v643 = v642.getElementById(__consts_0.const_str__39);
            v644 = v643.childNodes;
            v645 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v644,0 );
            v645.nodeValue = __consts_0.const_str__77;
            block = 1;
            break;
            case 1:
            return ( v639 );
        }
    }
}

function ll_listslice_startonly__List_Dict_String__String__ (RESLIST_0,l1_0,start_0) {
    var v393,v394,v395,v396,v397,v398,v399,v400,v401,v402,l1_1,i_2,j_0,l_6,len1_0,v403,v404,l1_2,i_3,j_1,l_7,len1_1,v405,v406,v407,v408,v409,v410;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v394 = l1_0;
            v395 = v394.length;
            v396 = (start_0>=0);
            undefined;
            v398 = (start_0<=v395);
            undefined;
            v400 = (v395-start_0);
            undefined;
            v402 = ll_newlist__List_Dict_String__String__LlT_Signed ( undefined,v400 );
            l1_1 = l1_0;
            i_2 = start_0;
            j_0 = 0;
            l_6 = v402;
            len1_0 = v395;
            block = 1;
            break;
            case 1:
            v403 = (i_2<len1_0);
            v404 = v403;
            if (v404 == true)
            {
                l1_2 = l1_1;
                i_3 = i_2;
                j_1 = j_0;
                l_7 = l_6;
                len1_1 = len1_0;
                block = 3;
                break;
            }
            else{
                v393 = l_6;
                block = 2;
                break;
            }
            case 2:
            return ( v393 );
            case 3:
            v405 = l_7;
            v406 = l1_2;
            v407 = v406[i_3];
            v405[j_1]=v407;
            v409 = (i_3+1);
            v410 = (j_1+1);
            l1_1 = l1_2;
            i_2 = v409;
            j_0 = v410;
            l_6 = l_7;
            len1_0 = len1_1;
            block = 1;
            break;
        }
    }
}

function ll_int_str__IntegerR_SignedConst_Signed (repr_0,i_6) {
    var v830,v831;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v831 = ll_int2dec__Signed ( i_6 );
            v830 = v831;
            block = 1;
            break;
            case 1:
            return ( v830 );
        }
    }
}

function add_received_item_outcome (msg_20,module_part_2) {
    var v663,v664,v665,v666,msg_21,module_part_3,v667,v668,v669,v670,v671,v672,v673,v674,v675,v676,v677,v678,v679,v680,v681,v682,v683,v684,v685,msg_22,module_part_4,item_name_6,td_0,v686,v687,v688,v689,msg_23,module_part_5,item_name_7,td_1,v690,v691,v692,v693,v694,v695,v696,v697,v698,v699,v700,v701,v702,v703,v704,v705,v706,v707,v708,v709,msg_24,module_part_6,td_2,v710,v711,v712,v713,v714,module_part_7,td_3,v715,v716,v717,v718,v719,v720,v721,v722,v723,v724,v725,v726,v727,v728,v729,v730,v731,v732,v733,v734,v735,v736,v737,v738,v739,v740,v741,v742,v743,v744,v745,v746,v747,v748,v749,msg_25,module_part_8,td_4,v750,v751,v752,msg_26,module_part_9,item_name_8,td_5,v753,v754,v755,v756,msg_27,module_part_10,item_name_9,td_6,v757,v758,v759,v760,v761,v762,v763,v764,v765,v766,v767,v768,v769,v770,v771,v772,v773,v774,v775,v776,msg_28,module_part_11,td_7,v777,v778,v779,msg_29,module_part_12,v780,v781,v782,v783,v784,v785,v786,v787,v788,v789,v790,v791,v792,v793,v794,v795,v796,v797,v798,v799,v800,v801,v802,v803,v804,v805,v806,v807,v808,v809,v810;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v664 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__70 );
            v665 = ll_strlen__String ( v664 );
            v666 = !!v665;
            if (v666 == true)
            {
                msg_29 = msg_20;
                module_part_12 = module_part_2;
                block = 11;
                break;
            }
            else{
                msg_21 = msg_20;
                module_part_3 = module_part_2;
                block = 1;
                break;
            }
            case 1:
            v667 = create_elem ( __consts_0.const_str__15 );
            v668 = v667;
            v669 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__56 );
            v670 = new Object();
            v670.item0 = v669;
            v672 = v670.item0;
            v673 = new StringBuilder();
            v673.ll_append(__consts_0.const_str__78);
            v675 = ll_str__StringR_StringConst_String ( undefined,v672 );
            v673.ll_append(v675);
            v673.ll_append(__consts_0.const_str__35);
            v678 = v673.ll_build();
            v668.setAttribute(__consts_0.const_str__36,v678);
            v680 = v667;
            v680.setAttribute(__consts_0.const_str__37,__consts_0.const_str__79);
            v682 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__56 );
            v683 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__80 );
            v684 = ll_streq__String_String ( v683,__consts_0.const_str__21 );
            v685 = v684;
            if (v685 == true)
            {
                msg_28 = msg_21;
                module_part_11 = module_part_3;
                td_7 = v667;
                block = 10;
                break;
            }
            else{
                msg_22 = msg_21;
                module_part_4 = module_part_3;
                item_name_6 = v682;
                td_0 = v667;
                block = 2;
                break;
            }
            case 2:
            v686 = ll_dict_getitem__Dict_String__String__String ( msg_22,__consts_0.const_str__81 );
            v687 = ll_streq__String_String ( v686,__consts_0.const_str__82 );
            v688 = !v687;
            v689 = v688;
            if (v689 == true)
            {
                msg_26 = msg_22;
                module_part_9 = module_part_4;
                item_name_8 = item_name_6;
                td_5 = td_0;
                block = 8;
                break;
            }
            else{
                msg_23 = msg_22;
                module_part_5 = module_part_4;
                item_name_7 = item_name_6;
                td_1 = td_0;
                block = 3;
                break;
            }
            case 3:
            v690 = create_elem ( __consts_0.const_str__83 );
            v691 = v690;
            v692 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__56 );
            v693 = new Object();
            v693.item0 = v692;
            v695 = v693.item0;
            v696 = new StringBuilder();
            v696.ll_append(__consts_0.const_str__84);
            v698 = ll_str__StringR_StringConst_String ( undefined,v695 );
            v696.ll_append(v698);
            v696.ll_append(__consts_0.const_str__35);
            v701 = v696.ll_build();
            v691.setAttribute(__consts_0.const_str__85,v701);
            v703 = create_text_elem ( __consts_0.const_str__86 );
            v704 = v690;
            v704.appendChild(v703);
            v706 = td_1;
            v706.appendChild(v690);
            v708 = __consts_0.ExportedMethods;
            v709 = v708.show_fail(item_name_7,fail_come_back);
            msg_24 = msg_23;
            module_part_6 = module_part_5;
            td_2 = td_1;
            block = 4;
            break;
            case 4:
            v710 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__69 );
            v711 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__87,v710 );
            v712 = (v711%50);
            v713 = (v712==0);
            v714 = v713;
            if (v714 == true)
            {
                msg_25 = msg_24;
                module_part_8 = module_part_6;
                td_4 = td_2;
                block = 7;
                break;
            }
            else{
                module_part_7 = module_part_6;
                td_3 = td_2;
                v715 = msg_24;
                block = 5;
                break;
            }
            case 5:
            v716 = ll_dict_getitem__Dict_String__String__String ( v715,__consts_0.const_str__69 );
            v717 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__87,v716 );
            v718 = (v717+1);
            __consts_0.const_tuple__87[v716]=v718;
            v720 = ll_strconcat__String_String ( __consts_0.const_str__88,v716 );
            v721 = get_elem ( v720 );
            v722 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__89,v716 );
            v723 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__87,v716 );
            v724 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__90,v716 );
            v725 = new Object();
            v725.item0 = v722;
            v725.item1 = v723;
            v725.item2 = v724;
            v729 = v725.item0;
            v730 = v725.item1;
            v731 = v725.item2;
            v732 = new StringBuilder();
            v733 = ll_str__StringR_StringConst_String ( undefined,v729 );
            v732.ll_append(v733);
            v732.ll_append(__consts_0.const_str__73);
            v736 = v730.toString();
            v732.ll_append(v736);
            v732.ll_append(__consts_0.const_str__91);
            v739 = v731.toString();
            v732.ll_append(v739);
            v732.ll_append(__consts_0.const_str__42);
            v742 = v732.ll_build();
            v743 = v721.childNodes;
            v744 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v743,0 );
            v744.nodeValue = v742;
            v746 = module_part_7.childNodes;
            v747 = ll_getitem__dum_nocheckConst_List_ExternalType__Si ( undefined,v746,-1 );
            v748 = v747;
            v748.appendChild(td_3);
            block = 6;
            break;
            case 6:
            return ( v663 );
            case 7:
            v750 = create_elem ( __consts_0.const_str__14 );
            v751 = module_part_8;
            v751.appendChild(v750);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v715 = msg_25;
            block = 5;
            break;
            case 8:
            v753 = ll_dict_getitem__Dict_String__String__String ( msg_26,__consts_0.const_str__81 );
            v754 = ll_streq__String_String ( v753,__consts_0.const_str__92 );
            v755 = !v754;
            v756 = v755;
            if (v756 == true)
            {
                msg_27 = msg_26;
                module_part_10 = module_part_9;
                item_name_9 = item_name_8;
                td_6 = td_5;
                block = 9;
                break;
            }
            else{
                msg_23 = msg_26;
                module_part_5 = module_part_9;
                item_name_7 = item_name_8;
                td_1 = td_5;
                block = 3;
                break;
            }
            case 9:
            v757 = __consts_0.ExportedMethods;
            v758 = v757.show_skip(item_name_9,skip_come_back);
            v759 = create_elem ( __consts_0.const_str__83 );
            v760 = v759;
            v761 = ll_dict_getitem__Dict_String__String__String ( msg_27,__consts_0.const_str__56 );
            v762 = new Object();
            v762.item0 = v761;
            v764 = v762.item0;
            v765 = new StringBuilder();
            v765.ll_append(__consts_0.const_str__93);
            v767 = ll_str__StringR_StringConst_String ( undefined,v764 );
            v765.ll_append(v767);
            v765.ll_append(__consts_0.const_str__35);
            v770 = v765.ll_build();
            v760.setAttribute(__consts_0.const_str__85,v770);
            v772 = create_text_elem ( __consts_0.const_str__94 );
            v773 = v759;
            v773.appendChild(v772);
            v775 = td_6;
            v775.appendChild(v759);
            msg_24 = msg_27;
            module_part_6 = module_part_10;
            td_2 = td_6;
            block = 4;
            break;
            case 10:
            v777 = create_text_elem ( __consts_0.const_str__95 );
            v778 = td_7;
            v778.appendChild(v777);
            msg_24 = msg_28;
            module_part_6 = module_part_11;
            td_2 = td_7;
            block = 4;
            break;
            case 11:
            v780 = __consts_0.Document;
            v781 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v782 = v780.getElementById(v781);
            v783 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v784 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v785 = ll_dict_getitem__Dict_String__List_String___String ( v783,v784 );
            v786 = v785;
            v787 = ll_pop_default__dum_nocheckConst_List_String_ ( undefined,v786 );
            v788 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v789 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v790 = ll_dict_getitem__Dict_String__List_String___String ( v788,v789 );
            v791 = ll_len__List_String_ ( v790 );
            v792 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v793 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v794 = ll_dict_getitem__Dict_String__String__String ( v792,v793 );
            v795 = new Object();
            v795.item0 = v794;
            v795.item1 = v791;
            v798 = v795.item0;
            v799 = v795.item1;
            v800 = new StringBuilder();
            v801 = ll_str__StringR_StringConst_String ( undefined,v798 );
            v800.ll_append(v801);
            v800.ll_append(__consts_0.const_str__73);
            v804 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v799 );
            v800.ll_append(v804);
            v800.ll_append(__consts_0.const_str__42);
            v807 = v800.ll_build();
            v808 = v782.childNodes;
            v809 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v808,0 );
            v809.nodeValue = v807;
            msg_21 = msg_29;
            module_part_3 = module_part_12;
            block = 1;
            break;
        }
    }
}

function ll_char_mul__Char_Signed (ch_0,times_0) {
    var v620,v621,v622,v623,ch_1,times_1,i_4,buf_0,v624,v625,v626,v627,v628,ch_2,times_2,i_5,buf_1,v629,v630,v631;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v621 = new StringBuilder();
            v622 = v621;
            v622.ll_allocate(times_0);
            ch_1 = ch_0;
            times_1 = times_0;
            i_4 = 0;
            buf_0 = v621;
            block = 1;
            break;
            case 1:
            v624 = (i_4<times_1);
            v625 = v624;
            if (v625 == true)
            {
                ch_2 = ch_1;
                times_2 = times_1;
                i_5 = i_4;
                buf_1 = buf_0;
                block = 4;
                break;
            }
            else{
                v626 = buf_0;
                block = 2;
                break;
            }
            case 2:
            v627 = v626;
            v628 = v627.ll_build();
            v620 = v628;
            block = 3;
            break;
            case 3:
            return ( v620 );
            case 4:
            v629 = buf_1;
            v629.ll_append_char(ch_2);
            v631 = (i_5+1);
            ch_1 = ch_2;
            times_1 = times_2;
            i_4 = v631;
            buf_0 = buf_1;
            block = 1;
            break;
        }
    }
}

function make_module_box (msg_30) {
    var v832,v833,v834,v835,v836,v837,v838,v839,v840,v841,v842,v843,v844,v845,v846,v847,v848,v849,v850,v851,v852,v853,v854,v855,v856,v857,v858,v859,v860,v861,v862,v863,v864,v865,v866,v867,v868,v869,v870,v871,v872,v873,v874,v875,v876,v877,v878,v879,v880,v881,v882,v883,v884,v885,v886,v887,v888,v889,v890,v891;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v833 = create_elem ( __consts_0.const_str__14 );
            v834 = create_elem ( __consts_0.const_str__15 );
            v835 = v833;
            v835.appendChild(v834);
            v837 = v834;
            v838 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__96 );
            v839 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__97 );
            v840 = new Object();
            v840.item0 = v838;
            v840.item1 = v839;
            v843 = v840.item0;
            v844 = v840.item1;
            v845 = new StringBuilder();
            v846 = ll_str__StringR_StringConst_String ( undefined,v843 );
            v845.ll_append(v846);
            v845.ll_append(__consts_0.const_str__98);
            v849 = ll_str__StringR_StringConst_String ( undefined,v844 );
            v845.ll_append(v849);
            v845.ll_append(__consts_0.const_str__42);
            v852 = v845.ll_build();
            v853 = create_text_elem ( v852 );
            v837.appendChild(v853);
            v855 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__97 );
            v856 = ll_int__String_Signed ( v855,10 );
            v857 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__90[v857]=v856;
            v859 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__96 );
            v860 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__89[v860]=v859;
            v862 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v863 = ll_strconcat__String_String ( __consts_0.const_str__88,v862 );
            v834.id = v863;
            v865 = v834;
            v866 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v867 = new Object();
            v867.item0 = v866;
            v869 = v867.item0;
            v870 = new StringBuilder();
            v870.ll_append(__consts_0.const_str__78);
            v872 = ll_str__StringR_StringConst_String ( undefined,v869 );
            v870.ll_append(v872);
            v870.ll_append(__consts_0.const_str__35);
            v875 = v870.ll_build();
            v865.setAttribute(__consts_0.const_str__36,v875);
            v877 = v834;
            v877.setAttribute(__consts_0.const_str__37,__consts_0.const_str__79);
            v879 = create_elem ( __consts_0.const_str__15 );
            v880 = v833;
            v880.appendChild(v879);
            v882 = create_elem ( __consts_0.const_str__99 );
            v883 = v879;
            v883.appendChild(v882);
            v885 = create_elem ( __consts_0.const_str__12 );
            v886 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v885.id = v886;
            v888 = v882;
            v888.appendChild(v885);
            v890 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__87[v890]=0;
            v832 = v833;
            block = 1;
            break;
            case 1:
            return ( v832 );
        }
    }
}

function ll_len__List_String_ (l_13) {
    var v827,v828,v829;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v828 = l_13;
            v829 = v828.length;
            v827 = v829;
            block = 1;
            break;
            case 1:
            return ( v827 );
        }
    }
}

function ll_dict_getitem__Dict_String__Signed__String (d_4,key_8) {
    var v913,v914,v915,v916,v917,v918,v919,etype_5,evalue_5,key_9,v920,v921,v922;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v914 = d_4;
            v915 = (v914[key_8]!=undefined);
            v916 = v915;
            if (v916 == true)
            {
                key_9 = key_8;
                v920 = d_4;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v917 = __consts_0.exceptions_KeyError;
            v918 = v917.meta;
            v919 = v917;
            etype_5 = v918;
            evalue_5 = v919;
            block = 2;
            break;
            case 2:
            throw(evalue_5);
            case 3:
            v921 = v920;
            v922 = v921[key_9];
            v913 = v922;
            block = 4;
            break;
            case 4:
            return ( v913 );
        }
    }
}

function ll_int2dec__Signed (i_7) {
    var v898,v899;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v899 = i_7.toString();
            v898 = v899;
            block = 1;
            break;
            case 1:
            return ( v898 );
        }
    }
}

function ll_pop_default__dum_nocheckConst_List_String_ (func_3,l_17) {
    var v941,v942,v943,l_18,length_4,v944,v945,v946,v947,v948,v949,res_0,newlength_0,v950,v951,v952;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v942 = l_17;
            v943 = v942.length;
            l_18 = l_17;
            length_4 = v943;
            block = 1;
            break;
            case 1:
            v944 = (length_4>0);
            undefined;
            v946 = (length_4-1);
            v947 = l_18;
            v948 = v947[v946];
            ll_null_item__List_String_ ( l_18 );
            res_0 = v948;
            newlength_0 = v946;
            v950 = l_18;
            block = 2;
            break;
            case 2:
            v951 = v950;
            v951.length = newlength_0;
            v941 = res_0;
            block = 3;
            break;
            case 3:
            return ( v941 );
        }
    }
}

function ll_strlen__String (obj_1) {
    var v900,v901,v902;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v901 = obj_1;
            v902 = v901.length;
            v900 = v902;
            block = 1;
            break;
            case 1:
            return ( v900 );
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed (self_1,length_1) {
    var v896,v897;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v897 = ll_newlist__List_Dict_String__String__LlT_Signed_0 ( undefined,length_1 );
            v896 = v897;
            block = 1;
            break;
            case 1:
            return ( v896 );
        }
    }
}

function skip_come_back (msg_32) {
    var v937,v938,v939,v940;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v938 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__57 );
            v939 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__100 );
            __consts_0.const_tuple__31[v939]=v938;
            block = 1;
            break;
            case 1:
            return ( v937 );
        }
    }
}

function ll_newlist__List_String_LlT_Signed (LIST_1,length_0) {
    var v892,v893,v894,v895;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v893 = new Array();
            v894 = v893;
            v894.length = length_0;
            v892 = v893;
            block = 1;
            break;
            case 1:
            return ( v892 );
        }
    }
}

function ll_getitem__dum_nocheckConst_List_ExternalType__Si (func_2,l_14,index_5) {
    var v923,v924,v925,v926,v927,l_15,index_6,length_2,v928,v929,v930,v931,index_7,v932,v933,v934,l_16,length_3,v935,v936;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v924 = l_14;
            v925 = v924.length;
            v926 = (index_5<0);
            v927 = v926;
            if (v927 == true)
            {
                l_16 = l_14;
                length_3 = v925;
                v935 = index_5;
                block = 4;
                break;
            }
            else{
                l_15 = l_14;
                index_6 = index_5;
                length_2 = v925;
                block = 1;
                break;
            }
            case 1:
            v928 = (index_6>=0);
            undefined;
            v930 = (index_6<length_2);
            undefined;
            index_7 = index_6;
            v932 = l_15;
            block = 2;
            break;
            case 2:
            v933 = v932;
            v934 = v933[index_7];
            v923 = v934;
            block = 3;
            break;
            case 3:
            return ( v923 );
            case 4:
            v936 = (v935+length_3);
            l_15 = l_16;
            index_6 = v936;
            length_2 = length_3;
            block = 1;
            break;
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed_0 (LIST_2,length_5) {
    var v1043,v1044,v1045,v1046;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1044 = new Array();
            v1045 = v1044;
            v1045.length = length_5;
            v1043 = v1044;
            block = 1;
            break;
            case 1:
            return ( v1043 );
        }
    }
}

function fail_come_back (msg_31) {
    var v903,v904,v905,v906,v907,v908,v909,v910,v911,v912;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v904 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__101 );
            v905 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__102 );
            v906 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__103 );
            v907 = new Object();
            v907.item0 = v904;
            v907.item1 = v905;
            v907.item2 = v906;
            v911 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__100 );
            __consts_0.const_tuple[v911]=v907;
            block = 1;
            break;
            case 1:
            return ( v903 );
        }
    }
}

function ll_int__String_Signed (s_2,base_0) {
    var v953,v954,v955,v956,v957,v958,etype_6,evalue_6,s_3,base_1,v959,s_4,base_2,v960,v961,s_5,base_3,v962,v963,s_6,base_4,i_8,strlen_0,v964,v965,s_7,base_5,i_9,strlen_1,v966,v967,v968,v969,v970,s_8,base_6,i_10,strlen_2,v971,v972,v973,v974,s_9,base_7,i_11,strlen_3,v975,v976,v977,v978,s_10,base_8,val_0,i_12,sign_0,strlen_4,v979,v980,s_11,val_1,i_13,sign_1,strlen_5,v981,v982,val_2,sign_2,v983,v984,v985,v986,v987,v988,v989,v990,v991,v992,s_12,val_3,i_14,sign_3,strlen_6,v993,v994,v995,v996,s_13,val_4,sign_4,strlen_7,v997,v998,s_14,base_9,val_5,i_15,sign_5,strlen_8,v999,v1000,v1001,v1002,v1003,s_15,base_10,c_0,val_6,i_16,sign_6,strlen_9,v1004,v1005,s_16,base_11,c_1,val_7,i_17,sign_7,strlen_10,v1006,v1007,s_17,base_12,c_2,val_8,i_18,sign_8,strlen_11,v1008,s_18,base_13,c_3,val_9,i_19,sign_9,strlen_12,v1009,v1010,s_19,base_14,val_10,i_20,sign_10,strlen_13,v1011,v1012,s_20,base_15,val_11,i_21,digit_0,sign_11,strlen_14,v1013,v1014,s_21,base_16,i_22,digit_1,sign_12,strlen_15,v1015,v1016,v1017,v1018,s_22,base_17,c_4,val_12,i_23,sign_13,strlen_16,v1019,s_23,base_18,c_5,val_13,i_24,sign_14,strlen_17,v1020,v1021,s_24,base_19,val_14,i_25,sign_15,strlen_18,v1022,v1023,v1024,s_25,base_20,c_6,val_15,i_26,sign_16,strlen_19,v1025,s_26,base_21,c_7,val_16,i_27,sign_17,strlen_20,v1026,v1027,s_27,base_22,val_17,i_28,sign_18,strlen_21,v1028,v1029,v1030,s_28,base_23,strlen_22,v1031,v1032,s_29,base_24,strlen_23,v1033,v1034,s_30,base_25,i_29,strlen_24,v1035,v1036,v1037,v1038,s_31,base_26,strlen_25,v1039,v1040;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v954 = (2<=base_0);
            v955 = v954;
            if (v955 == true)
            {
                s_3 = s_2;
                base_1 = base_0;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v956 = __consts_0.exceptions_ValueError;
            v957 = v956.meta;
            v958 = v956;
            etype_6 = v957;
            evalue_6 = v958;
            block = 2;
            break;
            case 2:
            throw(evalue_6);
            case 3:
            v959 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v960 = v959;
            block = 4;
            break;
            case 4:
            v961 = v960;
            if (v961 == true)
            {
                s_5 = s_4;
                base_3 = base_2;
                block = 5;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 5:
            v962 = s_5;
            v963 = v962.length;
            s_6 = s_5;
            base_4 = base_3;
            i_8 = 0;
            strlen_0 = v963;
            block = 6;
            break;
            case 6:
            v964 = (i_8<strlen_0);
            v965 = v964;
            if (v965 == true)
            {
                s_30 = s_6;
                base_25 = base_4;
                i_29 = i_8;
                strlen_24 = strlen_0;
                block = 35;
                break;
            }
            else{
                s_7 = s_6;
                base_5 = base_4;
                i_9 = i_8;
                strlen_1 = strlen_0;
                block = 7;
                break;
            }
            case 7:
            v966 = (i_9<strlen_1);
            v967 = v966;
            if (v967 == true)
            {
                s_8 = s_7;
                base_6 = base_5;
                i_10 = i_9;
                strlen_2 = strlen_1;
                block = 9;
                break;
            }
            else{
                block = 8;
                break;
            }
            case 8:
            v968 = __consts_0.exceptions_ValueError;
            v969 = v968.meta;
            v970 = v968;
            etype_6 = v969;
            evalue_6 = v970;
            block = 2;
            break;
            case 9:
            v971 = s_8;
            v972 = v971.charAt(i_10);
            v973 = (v972=='-');
            v974 = v973;
            if (v974 == true)
            {
                s_29 = s_8;
                base_24 = base_6;
                strlen_23 = strlen_2;
                v1033 = i_10;
                block = 34;
                break;
            }
            else{
                s_9 = s_8;
                base_7 = base_6;
                i_11 = i_10;
                strlen_3 = strlen_2;
                block = 10;
                break;
            }
            case 10:
            v975 = s_9;
            v976 = v975.charAt(i_11);
            v977 = (v976=='+');
            v978 = v977;
            if (v978 == true)
            {
                s_28 = s_9;
                base_23 = base_7;
                strlen_22 = strlen_3;
                v1031 = i_11;
                block = 33;
                break;
            }
            else{
                s_10 = s_9;
                base_8 = base_7;
                val_0 = 0;
                i_12 = i_11;
                sign_0 = 1;
                strlen_4 = strlen_3;
                block = 11;
                break;
            }
            case 11:
            v979 = (i_12<strlen_4);
            v980 = v979;
            if (v980 == true)
            {
                s_14 = s_10;
                base_9 = base_8;
                val_5 = val_0;
                i_15 = i_12;
                sign_5 = sign_0;
                strlen_8 = strlen_4;
                block = 19;
                break;
            }
            else{
                s_11 = s_10;
                val_1 = val_0;
                i_13 = i_12;
                sign_1 = sign_0;
                strlen_5 = strlen_4;
                block = 12;
                break;
            }
            case 12:
            v981 = (i_13<strlen_5);
            v982 = v981;
            if (v982 == true)
            {
                s_12 = s_11;
                val_3 = val_1;
                i_14 = i_13;
                sign_3 = sign_1;
                strlen_6 = strlen_5;
                block = 17;
                break;
            }
            else{
                val_2 = val_1;
                sign_2 = sign_1;
                v983 = i_13;
                v984 = strlen_5;
                block = 13;
                break;
            }
            case 13:
            v985 = (v983==v984);
            v986 = v985;
            if (v986 == true)
            {
                v990 = sign_2;
                v991 = val_2;
                block = 15;
                break;
            }
            else{
                block = 14;
                break;
            }
            case 14:
            v987 = __consts_0.exceptions_ValueError;
            v988 = v987.meta;
            v989 = v987;
            etype_6 = v988;
            evalue_6 = v989;
            block = 2;
            break;
            case 15:
            v992 = (v990*v991);
            v953 = v992;
            block = 16;
            break;
            case 16:
            return ( v953 );
            case 17:
            v993 = s_12;
            v994 = v993.charAt(i_14);
            v995 = (v994==' ');
            v996 = v995;
            if (v996 == true)
            {
                s_13 = s_12;
                val_4 = val_3;
                sign_4 = sign_3;
                strlen_7 = strlen_6;
                v997 = i_14;
                block = 18;
                break;
            }
            else{
                val_2 = val_3;
                sign_2 = sign_3;
                v983 = i_14;
                v984 = strlen_6;
                block = 13;
                break;
            }
            case 18:
            v998 = (v997+1);
            s_11 = s_13;
            val_1 = val_4;
            i_13 = v998;
            sign_1 = sign_4;
            strlen_5 = strlen_7;
            block = 12;
            break;
            case 19:
            v999 = s_14;
            v1000 = v999.charAt(i_15);
            v1001 = v1000.charCodeAt(0);
            v1002 = (97<=v1001);
            v1003 = v1002;
            if (v1003 == true)
            {
                s_25 = s_14;
                base_20 = base_9;
                c_6 = v1001;
                val_15 = val_5;
                i_26 = i_15;
                sign_16 = sign_5;
                strlen_19 = strlen_8;
                block = 30;
                break;
            }
            else{
                s_15 = s_14;
                base_10 = base_9;
                c_0 = v1001;
                val_6 = val_5;
                i_16 = i_15;
                sign_6 = sign_5;
                strlen_9 = strlen_8;
                block = 20;
                break;
            }
            case 20:
            v1004 = (65<=c_0);
            v1005 = v1004;
            if (v1005 == true)
            {
                s_22 = s_15;
                base_17 = base_10;
                c_4 = c_0;
                val_12 = val_6;
                i_23 = i_16;
                sign_13 = sign_6;
                strlen_16 = strlen_9;
                block = 27;
                break;
            }
            else{
                s_16 = s_15;
                base_11 = base_10;
                c_1 = c_0;
                val_7 = val_6;
                i_17 = i_16;
                sign_7 = sign_6;
                strlen_10 = strlen_9;
                block = 21;
                break;
            }
            case 21:
            v1006 = (48<=c_1);
            v1007 = v1006;
            if (v1007 == true)
            {
                s_17 = s_16;
                base_12 = base_11;
                c_2 = c_1;
                val_8 = val_7;
                i_18 = i_17;
                sign_8 = sign_7;
                strlen_11 = strlen_10;
                block = 22;
                break;
            }
            else{
                s_11 = s_16;
                val_1 = val_7;
                i_13 = i_17;
                sign_1 = sign_7;
                strlen_5 = strlen_10;
                block = 12;
                break;
            }
            case 22:
            v1008 = (c_2<=57);
            s_18 = s_17;
            base_13 = base_12;
            c_3 = c_2;
            val_9 = val_8;
            i_19 = i_18;
            sign_9 = sign_8;
            strlen_12 = strlen_11;
            v1009 = v1008;
            block = 23;
            break;
            case 23:
            v1010 = v1009;
            if (v1010 == true)
            {
                s_19 = s_18;
                base_14 = base_13;
                val_10 = val_9;
                i_20 = i_19;
                sign_10 = sign_9;
                strlen_13 = strlen_12;
                v1011 = c_3;
                block = 24;
                break;
            }
            else{
                s_11 = s_18;
                val_1 = val_9;
                i_13 = i_19;
                sign_1 = sign_9;
                strlen_5 = strlen_12;
                block = 12;
                break;
            }
            case 24:
            v1012 = (v1011-48);
            s_20 = s_19;
            base_15 = base_14;
            val_11 = val_10;
            i_21 = i_20;
            digit_0 = v1012;
            sign_11 = sign_10;
            strlen_14 = strlen_13;
            block = 25;
            break;
            case 25:
            v1013 = (digit_0>=base_15);
            v1014 = v1013;
            if (v1014 == true)
            {
                s_11 = s_20;
                val_1 = val_11;
                i_13 = i_21;
                sign_1 = sign_11;
                strlen_5 = strlen_14;
                block = 12;
                break;
            }
            else{
                s_21 = s_20;
                base_16 = base_15;
                i_22 = i_21;
                digit_1 = digit_0;
                sign_12 = sign_11;
                strlen_15 = strlen_14;
                v1015 = val_11;
                block = 26;
                break;
            }
            case 26:
            v1016 = (v1015*base_16);
            v1017 = (v1016+digit_1);
            v1018 = (i_22+1);
            s_10 = s_21;
            base_8 = base_16;
            val_0 = v1017;
            i_12 = v1018;
            sign_0 = sign_12;
            strlen_4 = strlen_15;
            block = 11;
            break;
            case 27:
            v1019 = (c_4<=90);
            s_23 = s_22;
            base_18 = base_17;
            c_5 = c_4;
            val_13 = val_12;
            i_24 = i_23;
            sign_14 = sign_13;
            strlen_17 = strlen_16;
            v1020 = v1019;
            block = 28;
            break;
            case 28:
            v1021 = v1020;
            if (v1021 == true)
            {
                s_24 = s_23;
                base_19 = base_18;
                val_14 = val_13;
                i_25 = i_24;
                sign_15 = sign_14;
                strlen_18 = strlen_17;
                v1022 = c_5;
                block = 29;
                break;
            }
            else{
                s_16 = s_23;
                base_11 = base_18;
                c_1 = c_5;
                val_7 = val_13;
                i_17 = i_24;
                sign_7 = sign_14;
                strlen_10 = strlen_17;
                block = 21;
                break;
            }
            case 29:
            v1023 = (v1022-65);
            v1024 = (v1023+10);
            s_20 = s_24;
            base_15 = base_19;
            val_11 = val_14;
            i_21 = i_25;
            digit_0 = v1024;
            sign_11 = sign_15;
            strlen_14 = strlen_18;
            block = 25;
            break;
            case 30:
            v1025 = (c_6<=122);
            s_26 = s_25;
            base_21 = base_20;
            c_7 = c_6;
            val_16 = val_15;
            i_27 = i_26;
            sign_17 = sign_16;
            strlen_20 = strlen_19;
            v1026 = v1025;
            block = 31;
            break;
            case 31:
            v1027 = v1026;
            if (v1027 == true)
            {
                s_27 = s_26;
                base_22 = base_21;
                val_17 = val_16;
                i_28 = i_27;
                sign_18 = sign_17;
                strlen_21 = strlen_20;
                v1028 = c_7;
                block = 32;
                break;
            }
            else{
                s_15 = s_26;
                base_10 = base_21;
                c_0 = c_7;
                val_6 = val_16;
                i_16 = i_27;
                sign_6 = sign_17;
                strlen_9 = strlen_20;
                block = 20;
                break;
            }
            case 32:
            v1029 = (v1028-97);
            v1030 = (v1029+10);
            s_20 = s_27;
            base_15 = base_22;
            val_11 = val_17;
            i_21 = i_28;
            digit_0 = v1030;
            sign_11 = sign_18;
            strlen_14 = strlen_21;
            block = 25;
            break;
            case 33:
            v1032 = (v1031+1);
            s_10 = s_28;
            base_8 = base_23;
            val_0 = 0;
            i_12 = v1032;
            sign_0 = 1;
            strlen_4 = strlen_22;
            block = 11;
            break;
            case 34:
            v1034 = (v1033+1);
            s_10 = s_29;
            base_8 = base_24;
            val_0 = 0;
            i_12 = v1034;
            sign_0 = -1;
            strlen_4 = strlen_23;
            block = 11;
            break;
            case 35:
            v1035 = s_30;
            v1036 = v1035.charAt(i_29);
            v1037 = (v1036==' ');
            v1038 = v1037;
            if (v1038 == true)
            {
                s_31 = s_30;
                base_26 = base_25;
                strlen_25 = strlen_24;
                v1039 = i_29;
                block = 36;
                break;
            }
            else{
                s_7 = s_30;
                base_5 = base_25;
                i_9 = i_29;
                strlen_1 = strlen_24;
                block = 7;
                break;
            }
            case 36:
            v1040 = (v1039+1);
            s_6 = s_31;
            base_4 = base_26;
            i_8 = v1040;
            strlen_0 = strlen_25;
            block = 6;
            break;
        }
    }
}

function ll_null_item__List_String_ (lst_2) {
    var v1041,v1042;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            undefined;
            block = 1;
            break;
            case 1:
            return ( v1041 );
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
function exceptions_StandardError_meta () {
}

exceptions_StandardError_meta.prototype.toString = function (){
    return ( '<exceptions_StandardError_meta instance>' );
}

inherits(exceptions_StandardError_meta,exceptions_Exception_meta);
function exceptions_ValueError_meta () {
}

exceptions_ValueError_meta.prototype.toString = function (){
    return ( '<exceptions_ValueError_meta instance>' );
}

inherits(exceptions_ValueError_meta,exceptions_StandardError_meta);
function py____test_rsession_webjs_Options_meta () {
}

py____test_rsession_webjs_Options_meta.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Options_meta instance>' );
}

inherits(py____test_rsession_webjs_Options_meta,Object_meta);
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
function py____test_rsession_webjs_Globals_meta () {
}

py____test_rsession_webjs_Globals_meta.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals_meta instance>' );
}

inherits(py____test_rsession_webjs_Globals_meta,Object_meta);
__consts_0 = {};
__consts_0.const_str__66 = ' failures, ';
__consts_0.const_str__34 = "show_host('";
__consts_0.const_str__65 = ' run, ';
__consts_0.exceptions_KeyError__112 = exceptions_KeyError;
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.exceptions_ValueError__106 = exceptions_ValueError;
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.const_str__83 = 'a';
__consts_0.const_str__42 = ']';
__consts_0.const_str__49 = 'ReceivedItemOutcome';
__consts_0.const_str__78 = "show_info('";
__consts_0.const_str__58 = '- skipped (';
__consts_0.const_str__38 = 'hide_host()';
__consts_0.const_str__79 = 'hide_info()';
__consts_0.const_str__29 = '#message';
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__12 = 'tbody';
__consts_0.const_tuple__31 = {};
__consts_0.const_str__59 = ')';
__consts_0.const_str__44 = 'main_table';
__consts_0.const_str__75 = 'Tests [interrupted]';
__consts_0.const_str__35 = "')";
__consts_0.const_str__53 = 'RsyncFinished';
__consts_0.const_str__88 = '_txt_';
__consts_0.const_tuple__26 = undefined;
__consts_0.const_tuple__24 = undefined;
__consts_0.py____test_rsession_webjs_Globals__115 = py____test_rsession_webjs_Globals;
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.const_list__114 = [];
__consts_0.const_str__16 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.const_tuple__87 = {};
__consts_0.const_str__102 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_str__67 = ' skipped';
__consts_0.const_str__48 = 'HostReady';
__consts_0.const_str__64 = 'FINISHED ';
__consts_0.const_str__40 = 'Rsyncing';
__consts_0.const_str__2 = 'info';
__consts_0.const_str__15 = 'td';
__consts_0.const_str__23 = 'true';
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.const_str__86 = 'F';
__consts_0.const_str__37 = 'onmouseout';
__consts_0.const_str__45 = 'type';
__consts_0.const_str__97 = 'length';
__consts_0.const_str__80 = 'passed';
__consts_0.const_str__95 = '.';
__consts_0.const_str__51 = 'FailedTryiter';
__consts_0.const_str__33 = '#ff0000';
__consts_0.const_str__20 = 'checked';
__consts_0.const_str__27 = 'messagebox';
__consts_0.const_str__56 = 'fullitemname';
__consts_0.const_str__99 = 'table';
__consts_0.const_str__68 = 'Py.test ';
__consts_0.const_str__63 = 'skips';
__consts_0.const_str__55 = 'CrashedExecution';
__consts_0.exceptions_StopIteration__108 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.const_str__9 = '\n';
__consts_0.const_str__14 = 'tr';
__consts_0.const_str__28 = 'pre';
__consts_0.const_str__74 = 'Py.test [interrupted]';
__consts_0.const_str__7 = '\n======== Stdout: ========\n';
__consts_0.const_str__71 = '#00ff00';
__consts_0.const_str__4 = 'beige';
__consts_0.const_str__94 = 's';
__consts_0.const_tuple = {};
__consts_0.const_str__101 = 'traceback';
__consts_0.const_str__43 = 'testmain';
__consts_0.const_str__93 = "javascript:show_skip('";
__consts_0.const_str__73 = '[';
__consts_0.const_str__77 = 'Tests [crashed]';
__consts_0.const_str__57 = 'reason';
__consts_0.const_str__84 = "javascript:show_traceback('";
__consts_0.const_str__39 = 'Tests';
__consts_0.const_str__61 = 'run';
__consts_0.const_str__52 = 'SkippedTryiter';
__consts_0.const_str__82 = 'None';
__consts_0.const_str__21 = 'True';
__consts_0.const_str__70 = 'hostkey';
__consts_0.const_str__62 = 'fails';
__consts_0.const_str__46 = 'ItemStart';
__consts_0.const_str__96 = 'itemname';
__consts_0.const_str__50 = 'TestFinished';
__consts_0.const_str__11 = 'jobs';
__consts_0.py____test_rsession_webjs_Options__110 = py____test_rsession_webjs_Options;
__consts_0.const_list = undefined;
__consts_0.const_str__8 = '\n========== Stderr: ==========\n';
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.const_str__103 = 'stderr';
__consts_0.const_str__85 = 'href';
__consts_0.const_tuple__89 = {};
__consts_0.const_str__3 = 'visible';
__consts_0.const_str__92 = 'False';
__consts_0.py____test_rsession_webjs_Options_meta = new py____test_rsession_webjs_Options_meta();
__consts_0.const_str__36 = 'onmouseover';
__consts_0.const_str__60 = '- FAILED TO LOAD MODULE';
__consts_0.const_str__98 = '[0/';
__consts_0.const_tuple__90 = {};
__consts_0.const_str__47 = 'SendItem';
__consts_0.const_str__69 = 'fullmodulename';
__consts_0.const_str__81 = 'skipped';
__consts_0.const_str__32 = 'hostsbody';
__consts_0.const_str__72 = '[0]';
__consts_0.const_str__10 = 'hidden';
__consts_0.const_str__6 = '====== Traceback: =========\n';
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_str__100 = 'item_name';
__consts_0.const_str__41 = 'Tests [';
__consts_0.Document = document;
__consts_0.const_str__91 = '/';
__consts_0.py____test_rsession_webjs_Options = new py____test_rsession_webjs_Options();
__consts_0.const_str__76 = 'Py.test [crashed]';
__consts_0.const_str__54 = 'InterruptedExecution';
__consts_0.const_str__19 = 'opt_scroll';
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__112;
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__106;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__115;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__16;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__16;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ofinished = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple__24;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__114;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__26;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__108;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
__consts_0.py____test_rsession_webjs_Options_meta.class_ = __consts_0.py____test_rsession_webjs_Options__110;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
__consts_0.py____test_rsession_webjs_Options.meta = __consts_0.py____test_rsession_webjs_Options_meta;
__consts_0.py____test_rsession_webjs_Options.oscroll = true;
