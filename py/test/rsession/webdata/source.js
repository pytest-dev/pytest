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

function show_skip (item_name_0) {
    var v25,v26,v27;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v26 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple,item_name_0 );
            set_msgbox ( item_name_0,v26 );
            block = 1;
            break;
            case 1:
            return ( v25 );
        }
    }
}

function show_traceback (item_name_1) {
    var v28,v29,v30,v31,v32,v33,v34,v35,v36,v37,v38,v39,v40,v41,v42,v43,v44,v45;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v29 = ll_dict_getitem__Dict_String__Record_item2__Str_St ( __consts_0.const_tuple__2,item_name_1 );
            v30 = v29.item0;
            v31 = v29.item1;
            v32 = v29.item2;
            v33 = new StringBuilder();
            v33.ll_append(__consts_0.const_str__3);
            v35 = ll_str__StringR_StringConst_String ( undefined,v30 );
            v33.ll_append(v35);
            v33.ll_append(__consts_0.const_str__4);
            v38 = ll_str__StringR_StringConst_String ( undefined,v31 );
            v33.ll_append(v38);
            v33.ll_append(__consts_0.const_str__5);
            v41 = ll_str__StringR_StringConst_String ( undefined,v32 );
            v33.ll_append(v41);
            v33.ll_append(__consts_0.const_str__6);
            v44 = v33.ll_build();
            set_msgbox ( item_name_1,v44 );
            block = 1;
            break;
            case 1:
            return ( v28 );
        }
    }
}

function set_msgbox (item_name_2,data_3) {
    var v138,v139,item_name_3,data_4,msgbox_0,v140,v141,v142,item_name_4,data_5,msgbox_1,v143,v144,v145,v146,v147,v148,v149,v150,v151,v152,item_name_5,data_6,msgbox_2,v153,v154,v155,v156;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v139 = get_elem ( __consts_0.const_str__7 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v139;
            block = 1;
            break;
            case 1:
            v140 = msgbox_0.childNodes;
            v141 = ll_len__List_ExternalType_ ( v140 );
            v142 = !!v141;
            if (v142 == true)
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
            v143 = create_elem ( __consts_0.const_str__8 );
            v144 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__6 );
            v145 = ll_strconcat__String_String ( v144,data_5 );
            v146 = create_text_elem ( v145 );
            v147 = v143;
            v147.appendChild(v146);
            v149 = msgbox_1;
            v149.appendChild(v143);
            __consts_0.Document.location = __consts_0.const_str__10;
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 3:
            return ( v138 );
            case 4:
            v153 = msgbox_2;
            v154 = msgbox_2.childNodes;
            v155 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v154,0 );
            v153.removeChild(v155);
            item_name_3 = item_name_5;
            data_4 = data_6;
            msgbox_0 = msgbox_2;
            block = 1;
            break;
        }
    }
}

function create_elem (s_1) {
    var v174,v175,v176;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v175 = __consts_0.Document;
            v176 = v175.createElement(s_1);
            v174 = v176;
            block = 1;
            break;
            case 1:
            return ( v174 );
        }
    }
}

function ll_len__List_ExternalType_ (l_0) {
    var v171,v172,v173;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v172 = l_0;
            v173 = v172.length;
            v171 = v173;
            block = 1;
            break;
            case 1:
            return ( v171 );
        }
    }
}

function ll_str__StringR_StringConst_String (self_0,s_0) {
    var v167;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v167 = s_0;
            block = 1;
            break;
            case 1:
            return ( v167 );
        }
    }
}

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__12;
    this.ohost = __consts_0.const_str__12;
    this.orsync_dots = 0;
    this.ofinished = false;
    this.ohost_dict = __consts_0.const_tuple__13;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__15;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals instance>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
function ll_dict_getitem__Dict_String__Record_item2__Str_St (d_1,key_2) {
    var v157,v158,v159,v160,v161,v162,v163,etype_1,evalue_1,key_3,v164,v165,v166;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v158 = d_1;
            v159 = (v158[key_2]!=undefined);
            v160 = v159;
            if (v160 == true)
            {
                key_3 = key_2;
                v164 = d_1;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v161 = __consts_0.exceptions_KeyError;
            v162 = v161.meta;
            v163 = v161;
            etype_1 = v162;
            evalue_1 = v163;
            block = 2;
            break;
            case 2:
            throw(evalue_1);
            case 3:
            v165 = v164;
            v166 = v165[key_3];
            v157 = v166;
            block = 4;
            break;
            case 4:
            return ( v157 );
        }
    }
}

function ll_strconcat__String_String (obj_0,arg0_0) {
    var v177,v178,v179;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v178 = obj_0;
            v179 = (v178+arg0_0);
            v177 = v179;
            block = 1;
            break;
            case 1:
            return ( v177 );
        }
    }
}

function exceptions_Exception () {
}

exceptions_Exception.prototype.toString = function (){
    return ( '<exceptions_Exception instance>' );
}

inherits(exceptions_Exception,Object);
function show_info (data_0) {
    var v46,v47,v48,v49,v50,data_1,info_0,v51,v52,v53,info_1,v54,v55,v56,v57,v58,v59,data_2,info_2,v60,v61,v62,v63;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v47 = __consts_0.Document;
            v48 = v47.getElementById(__consts_0.const_str__17);
            v49 = v48.style;
            v49.visibility = __consts_0.const_str__18;
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
            v58.backgroundColor = __consts_0.const_str__19;
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

function hide_messagebox () {
    var v114,v115,v116,mbox_0,v117,v118,mbox_1,v119,v120,v121,v122;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v115 = __consts_0.Document;
            v116 = v115.getElementById(__consts_0.const_str__7);
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

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalT (func_0,l_1,index_0) {
    var v183,v184,v185,l_2,index_1,v186,v187,v188,v189,index_2,v190,v191,v192;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v184 = (index_0>=0);
            undefined;
            l_2 = l_1;
            index_1 = index_0;
            block = 1;
            break;
            case 1:
            v186 = l_2;
            v187 = v186.length;
            v188 = (index_1<v187);
            undefined;
            index_2 = index_1;
            v190 = l_2;
            block = 2;
            break;
            case 2:
            v191 = v190;
            v192 = v191[index_2];
            v183 = v192;
            block = 3;
            break;
            case 3:
            return ( v183 );
        }
    }
}

function get_elem (el_0) {
    var v168,v169,v170;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v169 = __consts_0.Document;
            v170 = v169.getElementById(el_0);
            v168 = v170;
            block = 1;
            break;
            case 1:
            return ( v168 );
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
            v71 = v70.getElementById(__consts_0.const_str__20);
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
            v74 = create_elem ( __consts_0.const_str__21 );
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
            v81 = create_elem ( __consts_0.const_str__22 );
            v82 = create_elem ( __consts_0.const_str__23 );
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
            v92.visibility = __consts_0.const_str__18;
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

function exceptions_StandardError () {
}

exceptions_StandardError.prototype.toString = function (){
    return ( '<exceptions_StandardError instance>' );
}

inherits(exceptions_StandardError,exceptions_Exception);
function ll_listnext__Record_index__Signed__iterable_0 (iter_0) {
    var v214,v215,v216,v217,v218,v219,v220,iter_1,index_3,l_4,v221,v222,v223,v224,v225,v226,v227,etype_3,evalue_3;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v215 = iter_0.iterable;
            v216 = iter_0.index;
            v217 = v215;
            v218 = v217.length;
            v219 = (v216>=v218);
            v220 = v219;
            if (v220 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_1 = iter_0;
                index_3 = v216;
                l_4 = v215;
                block = 1;
                break;
            }
            case 1:
            v221 = (index_3+1);
            iter_1.index = v221;
            v223 = l_4;
            v224 = v223[index_3];
            v214 = v224;
            block = 2;
            break;
            case 2:
            return ( v214 );
            case 3:
            v225 = __consts_0.exceptions_StopIteration;
            v226 = v225.meta;
            v227 = v225;
            etype_3 = v226;
            evalue_3 = v227;
            block = 4;
            break;
            case 4:
            throw(evalue_3);
        }
    }
}

function ll_list_is_true__List_ExternalType_ (l_3) {
    var v193,v194,v195,v196,v197,v198,v199;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v194 = !!l_3;
            v195 = v194;
            if (v195 == true)
            {
                v196 = l_3;
                block = 2;
                break;
            }
            else{
                v193 = v194;
                block = 1;
                break;
            }
            case 1:
            return ( v193 );
            case 2:
            v197 = v196;
            v198 = v197.length;
            v199 = (v198!=0);
            v193 = v199;
            block = 1;
            break;
        }
    }
}

function ll_dict_getitem__Dict_String__List_String___String (d_2,key_4) {
    var v200,v201,v202,v203,v204,v205,v206,etype_2,evalue_2,key_5,v207,v208,v209;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v201 = d_2;
            v202 = (v201[key_4]!=undefined);
            v203 = v202;
            if (v203 == true)
            {
                key_5 = key_4;
                v207 = d_2;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v204 = __consts_0.exceptions_KeyError;
            v205 = v204.meta;
            v206 = v204;
            etype_2 = v205;
            evalue_2 = v206;
            block = 2;
            break;
            case 2:
            throw(evalue_2);
            case 3:
            v208 = v207;
            v209 = v208[key_5];
            v200 = v209;
            block = 4;
            break;
            case 4:
            return ( v200 );
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
            v66 = v65.getElementById(__consts_0.const_str__17);
            v67 = v66.style;
            v67.visibility = __consts_0.const_str__25;
            block = 1;
            break;
            case 1:
            return ( v64 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_S (ITER_0,lst_0) {
    var v210,v211,v212,v213;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v211 = new Object();
            v211.iterable = lst_0;
            v211.index = 0;
            v210 = v211;
            block = 1;
            break;
            case 1:
            return ( v210 );
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
function hide_host () {
    var v100,v101,v102,elem_5,v103,v104,v105,v106,v107,v108,v109,elem_6,v110,v111,v112,v113;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v101 = __consts_0.Document;
            v102 = v101.getElementById(__consts_0.const_str__20);
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
            v107.visibility = __consts_0.const_str__25;
            __consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__12;
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
            v22 = v21.getElementById(__consts_0.const_str__27);
            v23 = v22;
            v23.setAttribute(__consts_0.const_str__28,__consts_0.const_str__29);
            block = 1;
            break;
            case 1:
            return ( v14 );
        }
    }
}

function create_text_elem (txt_0) {
    var v180,v181,v182;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v181 = __consts_0.Document;
            v182 = v181.createTextNode(txt_0);
            v180 = v182;
            block = 1;
            break;
            case 1:
            return ( v180 );
        }
    }
}

function ll_dict_getitem__Dict_String__String__String (d_0,key_0) {
    var v128,v129,v130,v131,v132,v133,v134,etype_0,evalue_0,key_1,v135,v136,v137;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v129 = d_0;
            v130 = (v129[key_0]!=undefined);
            v131 = v130;
            if (v131 == true)
            {
                key_1 = key_0;
                v135 = d_0;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v132 = __consts_0.exceptions_KeyError;
            v133 = v132.meta;
            v134 = v132;
            etype_0 = v133;
            evalue_0 = v134;
            block = 2;
            break;
            case 2:
            throw(evalue_0);
            case 3:
            v136 = v135;
            v137 = v136[key_1];
            v128 = v137;
            block = 4;
            break;
            case 4:
            return ( v128 );
        }
    }
}

function host_init (host_dict_0) {
    var v234,v235,v236,v237,v238,v239,host_dict_1,tbody_3,v240,v241,last_exc_value_1,host_dict_2,tbody_4,host_0,v242,v243,v244,v245,v246,v247,v248,v249,v250,v251,v252,v253,v254,v255,v256,v257,v258,v259,v260,v261,v262,v263,v264,v265,v266,v267,v268,host_dict_3,v269,v270,v271,v272,v273,v274,v275,v276,last_exc_value_2,key_6,v277,v278,v279,v280,v281;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v235 = __consts_0.Document;
            v236 = v235.getElementById(__consts_0.const_str__30);
            v237 = host_dict_0;
            v238 = ll_dict_kvi__Dict_String__String__List_String_LlT_ ( v237,undefined,undefined );
            v239 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v238 );
            host_dict_1 = host_dict_0;
            tbody_3 = v236;
            v240 = v239;
            block = 1;
            break;
            case 1:
            try {
                v241 = ll_listnext__Record_index__Signed__iterable_0 ( v240 );
                host_dict_2 = host_dict_1;
                tbody_4 = tbody_3;
                host_0 = v241;
                v242 = v240;
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
            v243 = create_elem ( __consts_0.const_str__22 );
            v244 = tbody_4;
            v244.appendChild(v243);
            v246 = create_elem ( __consts_0.const_str__23 );
            v247 = v246.style;
            v247.background = __consts_0.const_str__31;
            v249 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v250 = create_text_elem ( v249 );
            v251 = v246;
            v251.appendChild(v250);
            v246.id = host_0;
            v254 = v243;
            v254.appendChild(v246);
            v256 = v246;
            v257 = new StringBuilder();
            v257.ll_append(__consts_0.const_str__32);
            v259 = ll_str__StringR_StringConst_String ( undefined,host_0 );
            v257.ll_append(v259);
            v257.ll_append(__consts_0.const_str__33);
            v262 = v257.ll_build();
            v256.setAttribute(__consts_0.const_str__34,v262);
            v264 = v246;
            v264.setAttribute(__consts_0.const_str__35,__consts_0.const_str__36);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
            setTimeout ( 'update_rsync()',1000 );
            host_dict_1 = host_dict_2;
            tbody_3 = tbody_4;
            v240 = v242;
            block = 1;
            break;
            case 3:
            __consts_0.py____test_rsession_webjs_Globals.ohost_dict = host_dict_3;
            v270 = ll_newdict__Dict_String__List_String__LlT ( undefined );
            __consts_0.py____test_rsession_webjs_Globals.ohost_pending = v270;
            v272 = host_dict_3;
            v273 = ll_dict_kvi__Dict_String__String__List_String_LlT_ ( v272,undefined,undefined );
            v274 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v273 );
            v275 = v274;
            block = 4;
            break;
            case 4:
            try {
                v276 = ll_listnext__Record_index__Signed__iterable_0 ( v275 );
                key_6 = v276;
                v277 = v275;
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
            v278 = new Array();
            v278.length = 0;
            v280 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v280[key_6]=v278;
            v275 = v277;
            block = 4;
            break;
            case 6:
            return ( v234 );
        }
    }
}

function reshow_host () {
    var v228,v229,v230,v231,v232,v233;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v229 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v230 = ll_streq__String_String ( v229,__consts_0.const_str__12 );
            v231 = v230;
            if (v231 == true)
            {
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v232 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v232 );
            block = 2;
            break;
            case 2:
            return ( v228 );
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

function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions_StopIteration instance>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
function ll_dict_kvi__Dict_String__String__List_String_LlT_ (d_3,LIST_0,func_1) {
    var v302,v303,v304,v305,v306,v307,i_0,it_0,result_0,v308,v309,v310,i_1,it_1,result_1,v311,v312,v313,v314,it_2,result_2,v315,v316;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v303 = d_3;
            v304 = get_dict_len ( v303 );
            v305 = ll_newlist__List_String_LlT_Signed ( undefined,v304 );
            v306 = d_3;
            v307 = dict_items_iterator ( v306 );
            i_0 = 0;
            it_0 = v307;
            result_0 = v305;
            block = 1;
            break;
            case 1:
            v308 = it_0;
            v309 = v308.ll_go_next();
            v310 = v309;
            if (v310 == true)
            {
                i_1 = i_0;
                it_1 = it_0;
                result_1 = result_0;
                block = 3;
                break;
            }
            else{
                v302 = result_0;
                block = 2;
                break;
            }
            case 2:
            return ( v302 );
            case 3:
            v311 = result_1;
            v312 = it_1;
            v313 = v312.ll_current_key();
            v311[i_1]=v313;
            it_2 = it_1;
            result_2 = result_1;
            v315 = i_1;
            block = 4;
            break;
            case 4:
            v316 = (v315+1);
            i_0 = v316;
            it_0 = it_2;
            result_0 = result_2;
            block = 1;
            break;
        }
    }
}

function key_pressed (key_7) {
    var v286,v287,v288,v289,v290,v291,v292,v293,v294,v295,v296,v297,v298,v299,v300,v301;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v287 = key_7.charCode;
            v288 = (v287==115);
            v289 = v288;
            if (v289 == true)
            {
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            return ( v286 );
            case 2:
            v290 = __consts_0.Document;
            v291 = v290.getElementById(__consts_0.const_str__27);
            v292 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v293 = v292;
            if (v293 == true)
            {
                v298 = v291;
                block = 4;
                break;
            }
            else{
                v294 = v291;
                block = 3;
                break;
            }
            case 3:
            v295 = v294;
            v295.setAttribute(__consts_0.const_str__28,__consts_0.const_str__38);
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 1;
            break;
            case 4:
            v299 = v298;
            v299.removeAttribute(__consts_0.const_str__28);
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 1;
            break;
        }
    }
}

function sessid_comeback (id_0) {
    var v282,v283,v284,v285;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.osessid = id_0;
            v284 = __consts_0.ExportedMethods;
            v285 = v284.show_all_statuses(id_0,comeback);
            block = 1;
            break;
            case 1:
            return ( v282 );
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
function update_rsync () {
    var v317,v318,v319,v320,v321,v322,v323,v324,v325,elem_7,v326,v327,v328,v329,v330,v331,v332,v333,v334,elem_8,v335,v336,v337,v338,v339,v340,v341,v342,v343,v344,v345,text_0,elem_9,v346,v347,v348,v349,v350;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v318 = __consts_0.py____test_rsession_webjs_Globals.ofinished;
            v319 = v318;
            if (v319 == true)
            {
                block = 4;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v320 = __consts_0.Document;
            v321 = v320.getElementById(__consts_0.const_str__39);
            v322 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v323 = v322;
            v324 = (v323==1);
            v325 = v324;
            if (v325 == true)
            {
                v347 = v321;
                block = 6;
                break;
            }
            else{
                elem_7 = v321;
                block = 2;
                break;
            }
            case 2:
            v326 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v327 = ll_char_mul__Char_Signed ( '.',v326 );
            v328 = ll_strconcat__String_String ( __consts_0.const_str__40,v327 );
            v329 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v330 = (v329+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v330;
            v332 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v333 = (v332>5);
            v334 = v333;
            if (v334 == true)
            {
                text_0 = v328;
                elem_9 = elem_7;
                block = 5;
                break;
            }
            else{
                elem_8 = elem_7;
                v335 = v328;
                block = 3;
                break;
            }
            case 3:
            v336 = new StringBuilder();
            v336.ll_append(__consts_0.const_str__41);
            v338 = ll_str__StringR_StringConst_String ( undefined,v335 );
            v336.ll_append(v338);
            v336.ll_append(__consts_0.const_str__42);
            v341 = v336.ll_build();
            v342 = elem_8.childNodes;
            v343 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v342,0 );
            v343.nodeValue = v341;
            setTimeout ( 'update_rsync()',1000 );
            block = 4;
            break;
            case 4:
            return ( v317 );
            case 5:
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            elem_8 = elem_9;
            v335 = text_0;
            block = 3;
            break;
            case 6:
            v348 = v347.childNodes;
            v349 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v348,0 );
            v349.nodeValue = __consts_0.const_str__39;
            block = 4;
            break;
        }
    }
}

function ll_streq__String_String (s1_0,s2_0) {
    var v353,v354,v355,v356,s2_1,v357,v358,v359,v360,v361,v362;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v354 = !!s1_0;
            v355 = !v354;
            v356 = v355;
            if (v356 == true)
            {
                v360 = s2_0;
                block = 3;
                break;
            }
            else{
                s2_1 = s2_0;
                v357 = s1_0;
                block = 1;
                break;
            }
            case 1:
            v358 = v357;
            v359 = (v358==s2_1);
            v353 = v359;
            block = 2;
            break;
            case 2:
            return ( v353 );
            case 3:
            v361 = !!v360;
            v362 = !v361;
            v353 = v362;
            block = 2;
            break;
        }
    }
}

function ll_newdict__Dict_String__List_String__LlT (DICT_0) {
    var v351,v352;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v352 = new Object();
            v351 = v352;
            block = 1;
            break;
            case 1:
            return ( v351 );
        }
    }
}

function ll_char_mul__Char_Signed (ch_0,times_0) {
    var v394,v395,v396,v397,ch_1,times_1,i_2,buf_0,v398,v399,v400,v401,v402,ch_2,times_2,i_3,buf_1,v403,v404,v405;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v395 = new StringBuilder();
            v396 = v395;
            v396.ll_allocate(times_0);
            ch_1 = ch_0;
            times_1 = times_0;
            i_2 = 0;
            buf_0 = v395;
            block = 1;
            break;
            case 1:
            v398 = (i_2<times_1);
            v399 = v398;
            if (v399 == true)
            {
                ch_2 = ch_1;
                times_2 = times_1;
                i_3 = i_2;
                buf_1 = buf_0;
                block = 4;
                break;
            }
            else{
                v400 = buf_0;
                block = 2;
                break;
            }
            case 2:
            v401 = v400;
            v402 = v401.ll_build();
            v394 = v402;
            block = 3;
            break;
            case 3:
            return ( v394 );
            case 4:
            v403 = buf_1;
            v403.ll_append_char(ch_2);
            v405 = (i_3+1);
            ch_1 = ch_2;
            times_1 = times_2;
            i_2 = v405;
            buf_0 = buf_1;
            block = 1;
            break;
        }
    }
}

function ll_newlist__List_String_LlT_Signed (LIST_1,length_0) {
    var v363,v364,v365,v366;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v364 = new Array();
            v365 = v364;
            v365.length = length_0;
            v363 = v364;
            block = 1;
            break;
            case 1:
            return ( v363 );
        }
    }
}

function comeback (msglist_0) {
    var v367,v368,v369,v370,msglist_1,v371,v372,v373,v374,msglist_2,v375,v376,last_exc_value_3,msglist_3,v377,v378,v379,v380,msglist_4,v381,v382,v383,v384,v385,v386,last_exc_value_4,v387,v388,v389,v390,v391,v392,v393;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v368 = ll_len__List_Dict_String__String__ ( msglist_0 );
            v369 = (v368==0);
            v370 = v369;
            if (v370 == true)
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
            v371 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v372 = 0;
            v373 = ll_listslice_startonly__List_Dict_String__String__ ( undefined,v371,v372 );
            v374 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,v373 );
            msglist_2 = msglist_1;
            v375 = v374;
            block = 2;
            break;
            case 2:
            try {
                v376 = ll_listnext__Record_index__Signed__iterable ( v375 );
                msglist_3 = msglist_2;
                v377 = v375;
                v378 = v376;
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
            v379 = process ( v378 );
            v380 = v379;
            if (v380 == true)
            {
                msglist_2 = msglist_3;
                v375 = v377;
                block = 2;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 4:
            return ( v367 );
            case 5:
            v381 = new Array();
            v381.length = 0;
            __consts_0.py____test_rsession_webjs_Globals.opending = v381;
            v384 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,msglist_4 );
            v385 = v384;
            block = 6;
            break;
            case 6:
            try {
                v386 = ll_listnext__Record_index__Signed__iterable ( v385 );
                v387 = v385;
                v388 = v386;
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
            v389 = process ( v388 );
            v390 = v389;
            if (v390 == true)
            {
                v385 = v387;
                block = 6;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 8:
            v391 = __consts_0.ExportedMethods;
            v392 = __consts_0.py____test_rsession_webjs_Globals.osessid;
            v393 = v391.show_all_statuses(v392,comeback);
            block = 4;
            break;
        }
    }
}

function process (msg_0) {
    var v445,v446,v447,v448,msg_1,v449,v450,v451,v452,v453,v454,v455,msg_2,v456,v457,v458,msg_3,v459,v460,v461,msg_4,v462,v463,v464,msg_5,v465,v466,v467,msg_6,v468,v469,v470,msg_7,v471,v472,v473,msg_8,v474,v475,v476,msg_9,v477,v478,v479,v480,v481,v482,v483,v484,v485,v486,v487,v488,v489,v490,v491,msg_10,v492,v493,v494,msg_11,v495,v496,v497,msg_12,module_part_0,v498,v499,v500,v501,v502,v503,v504,v505,v506,v507,v508,v509,v510,v511,v512,v513,v514,v515,v516,msg_13,v517,v518,v519,msg_14,v520,v521,v522,module_part_1,v523,v524,v525,v526,v527,v528,v529,v530,v531,msg_15,v532,v533,v534,v535,v536,v537,v538,v539,v540,v541,v542,v543,v544,v545,v546,v547,v548,v549,v550,v551,v552,v553,v554,v555,v556,v557,v558,v559,v560,v561,v562,v563,v564,v565,v566,v567,v568,v569,v570,v571,msg_16,v572,v573,v574,msg_17,v575,v576,v577,v578,v579,v580,msg_18,v581,v582,v583,v584,v585,v586,v587,v588,v589,v590,v591,v592,v593,v594,v595,v596,v597,v598,v599,msg_19,v600,v601,v602,v603,v604,v605,v606,v607,v608,v609,v610,v611,v612,v613,v614,v615,v616,v617,v618,v619,v620,v621,v622,v623,v624,v625,v626,v627,v628,v629,v630,v631,main_t_0,v632,v633,v634,v635;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v446 = get_dict_len ( msg_0 );
            v447 = (v446==0);
            v448 = v447;
            if (v448 == true)
            {
                v445 = false;
                block = 12;
                break;
            }
            else{
                msg_1 = msg_0;
                block = 1;
                break;
            }
            case 1:
            v449 = __consts_0.Document;
            v450 = v449.getElementById(__consts_0.const_str__43);
            v451 = __consts_0.Document;
            v452 = v451.getElementById(__consts_0.const_str__44);
            v453 = ll_dict_getitem__Dict_String__String__String ( msg_1,__consts_0.const_str__45 );
            v454 = ll_streq__String_String ( v453,__consts_0.const_str__46 );
            v455 = v454;
            if (v455 == true)
            {
                main_t_0 = v452;
                v632 = msg_1;
                block = 29;
                break;
            }
            else{
                msg_2 = msg_1;
                block = 2;
                break;
            }
            case 2:
            v456 = ll_dict_getitem__Dict_String__String__String ( msg_2,__consts_0.const_str__45 );
            v457 = ll_streq__String_String ( v456,__consts_0.const_str__47 );
            v458 = v457;
            if (v458 == true)
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
            v459 = ll_dict_getitem__Dict_String__String__String ( msg_3,__consts_0.const_str__45 );
            v460 = ll_streq__String_String ( v459,__consts_0.const_str__48 );
            v461 = v460;
            if (v461 == true)
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
            v462 = ll_dict_getitem__Dict_String__String__String ( msg_4,__consts_0.const_str__45 );
            v463 = ll_streq__String_String ( v462,__consts_0.const_str__49 );
            v464 = v463;
            if (v464 == true)
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
            v465 = ll_dict_getitem__Dict_String__String__String ( msg_5,__consts_0.const_str__45 );
            v466 = ll_streq__String_String ( v465,__consts_0.const_str__50 );
            v467 = v466;
            if (v467 == true)
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
            v468 = ll_dict_getitem__Dict_String__String__String ( msg_6,__consts_0.const_str__45 );
            v469 = ll_streq__String_String ( v468,__consts_0.const_str__51 );
            v470 = v469;
            if (v470 == true)
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
            v471 = ll_dict_getitem__Dict_String__String__String ( msg_7,__consts_0.const_str__45 );
            v472 = ll_streq__String_String ( v471,__consts_0.const_str__52 );
            v473 = v472;
            if (v473 == true)
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
            v474 = ll_dict_getitem__Dict_String__String__String ( msg_8,__consts_0.const_str__45 );
            v475 = ll_streq__String_String ( v474,__consts_0.const_str__53 );
            v476 = v475;
            if (v476 == true)
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
            v477 = ll_dict_getitem__Dict_String__String__String ( msg_9,__consts_0.const_str__45 );
            v478 = ll_streq__String_String ( v477,__consts_0.const_str__54 );
            v479 = v478;
            if (v479 == true)
            {
                block = 15;
                break;
            }
            else{
                v480 = msg_9;
                block = 10;
                break;
            }
            case 10:
            v481 = ll_dict_getitem__Dict_String__String__String ( v480,__consts_0.const_str__45 );
            v482 = ll_streq__String_String ( v481,__consts_0.const_str__55 );
            v483 = v482;
            if (v483 == true)
            {
                block = 14;
                break;
            }
            else{
                block = 11;
                break;
            }
            case 11:
            v484 = __consts_0.py____test_rsession_webjs_Globals.odata_empty;
            v485 = v484;
            if (v485 == true)
            {
                block = 13;
                break;
            }
            else{
                v445 = true;
                block = 12;
                break;
            }
            case 12:
            return ( v445 );
            case 13:
            v486 = __consts_0.Document;
            v487 = v486.getElementById(__consts_0.const_str__7);
            scroll_down_if_needed ( v487 );
            v445 = true;
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
            v492 = ll_dict_getitem__Dict_String__String__String ( msg_10,__consts_0.const_str__56 );
            v493 = get_elem ( v492 );
            v494 = !!v493;
            if (v494 == true)
            {
                msg_12 = msg_10;
                module_part_0 = v493;
                block = 19;
                break;
            }
            else{
                msg_11 = msg_10;
                block = 18;
                break;
            }
            case 18:
            v495 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v496 = v495;
            ll_append__List_Dict_String__String___Dict_String_ ( v496,msg_11 );
            v445 = true;
            block = 12;
            break;
            case 19:
            v498 = create_elem ( __consts_0.const_str__22 );
            v499 = create_elem ( __consts_0.const_str__23 );
            v500 = ll_dict_getitem__Dict_String__String__String ( msg_12,__consts_0.const_str__57 );
            v501 = new Object();
            v501.item0 = v500;
            v503 = v501.item0;
            v504 = new StringBuilder();
            v504.ll_append(__consts_0.const_str__58);
            v506 = ll_str__StringR_StringConst_String ( undefined,v503 );
            v504.ll_append(v506);
            v504.ll_append(__consts_0.const_str__59);
            v509 = v504.ll_build();
            v510 = create_text_elem ( v509 );
            v511 = v499;
            v511.appendChild(v510);
            v513 = v498;
            v513.appendChild(v499);
            v515 = module_part_0;
            v515.appendChild(v498);
            block = 11;
            break;
            case 20:
            v517 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__56 );
            v518 = get_elem ( v517 );
            v519 = !!v518;
            if (v519 == true)
            {
                module_part_1 = v518;
                block = 22;
                break;
            }
            else{
                msg_14 = msg_13;
                block = 21;
                break;
            }
            case 21:
            v520 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v521 = v520;
            ll_append__List_Dict_String__String___Dict_String_ ( v521,msg_14 );
            v445 = true;
            block = 12;
            break;
            case 22:
            v523 = create_elem ( __consts_0.const_str__22 );
            v524 = create_elem ( __consts_0.const_str__23 );
            v525 = create_text_elem ( __consts_0.const_str__60 );
            v526 = v524;
            v526.appendChild(v525);
            v528 = v523;
            v528.appendChild(v524);
            v530 = module_part_1;
            v530.appendChild(v523);
            block = 11;
            break;
            case 23:
            v532 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__61 );
            v533 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__62 );
            v534 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__63 );
            v535 = new Object();
            v535.item0 = v532;
            v535.item1 = v533;
            v535.item2 = v534;
            v539 = v535.item0;
            v540 = v535.item1;
            v541 = v535.item2;
            v542 = new StringBuilder();
            v542.ll_append(__consts_0.const_str__64);
            v544 = ll_str__StringR_StringConst_String ( undefined,v539 );
            v542.ll_append(v544);
            v542.ll_append(__consts_0.const_str__65);
            v547 = ll_str__StringR_StringConst_String ( undefined,v540 );
            v542.ll_append(v547);
            v542.ll_append(__consts_0.const_str__66);
            v550 = ll_str__StringR_StringConst_String ( undefined,v541 );
            v542.ll_append(v550);
            v542.ll_append(__consts_0.const_str__67);
            v553 = v542.ll_build();
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            v555 = new StringBuilder();
            v555.ll_append(__consts_0.const_str__68);
            v557 = ll_str__StringR_StringConst_String ( undefined,v553 );
            v555.ll_append(v557);
            v559 = v555.ll_build();
            __consts_0.Document.title = v559;
            v561 = new StringBuilder();
            v561.ll_append(__consts_0.const_str__41);
            v563 = ll_str__StringR_StringConst_String ( undefined,v553 );
            v561.ll_append(v563);
            v561.ll_append(__consts_0.const_str__42);
            v566 = v561.ll_build();
            v567 = __consts_0.Document;
            v568 = v567.getElementById(__consts_0.const_str__39);
            v569 = v568.childNodes;
            v570 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v569,0 );
            v570.nodeValue = v566;
            block = 11;
            break;
            case 24:
            v572 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__69 );
            v573 = get_elem ( v572 );
            v574 = !!v573;
            if (v574 == true)
            {
                v578 = msg_16;
                v579 = v573;
                block = 26;
                break;
            }
            else{
                msg_17 = msg_16;
                block = 25;
                break;
            }
            case 25:
            v575 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v576 = v575;
            ll_append__List_Dict_String__String___Dict_String_ ( v576,msg_17 );
            v445 = true;
            block = 12;
            break;
            case 26:
            add_received_item_outcome ( v578,v579 );
            block = 11;
            break;
            case 27:
            v581 = __consts_0.Document;
            v582 = ll_dict_getitem__Dict_String__String__String ( msg_18,__consts_0.const_str__70 );
            v583 = v581.getElementById(v582);
            v584 = v583.style;
            v584.background = __consts_0.const_str__71;
            v586 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v587 = ll_dict_getitem__Dict_String__String__String ( msg_18,__consts_0.const_str__70 );
            v588 = ll_dict_getitem__Dict_String__String__String ( v586,v587 );
            v589 = new Object();
            v589.item0 = v588;
            v591 = v589.item0;
            v592 = new StringBuilder();
            v593 = ll_str__StringR_StringConst_String ( undefined,v591 );
            v592.ll_append(v593);
            v592.ll_append(__consts_0.const_str__72);
            v596 = v592.ll_build();
            v597 = v583.childNodes;
            v598 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v597,0 );
            v598.nodeValue = v596;
            block = 11;
            break;
            case 28:
            v600 = __consts_0.Document;
            v601 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__70 );
            v602 = v600.getElementById(v601);
            v603 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v604 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__70 );
            v605 = ll_dict_getitem__Dict_String__List_String___String ( v603,v604 );
            v606 = v605;
            v607 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__56 );
            ll_prepend__List_String__String ( v606,v607 );
            v609 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v610 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__70 );
            v611 = ll_dict_getitem__Dict_String__List_String___String ( v609,v610 );
            v612 = ll_len__List_String_ ( v611 );
            v613 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v614 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__70 );
            v615 = ll_dict_getitem__Dict_String__String__String ( v613,v614 );
            v616 = new Object();
            v616.item0 = v615;
            v616.item1 = v612;
            v619 = v616.item0;
            v620 = v616.item1;
            v621 = new StringBuilder();
            v622 = ll_str__StringR_StringConst_String ( undefined,v619 );
            v621.ll_append(v622);
            v621.ll_append(__consts_0.const_str__73);
            v625 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v620 );
            v621.ll_append(v625);
            v621.ll_append(__consts_0.const_str__42);
            v628 = v621.ll_build();
            v629 = v602.childNodes;
            v630 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v629,0 );
            v630.nodeValue = v628;
            block = 11;
            break;
            case 29:
            v633 = make_module_box ( v632 );
            v634 = main_t_0;
            v634.appendChild(v633);
            block = 11;
            break;
        }
    }
}

function ll_len__List_Dict_String__String__ (l_5) {
    var v406,v407,v408;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v407 = l_5;
            v408 = v407.length;
            v406 = v408;
            block = 1;
            break;
            case 1:
            return ( v406 );
        }
    }
}

function ll_append__List_Dict_String__String___Dict_String_ (l_9,newitem_0) {
    var v659,v660,v661,v662,v663,v664,v665,v666;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v660 = l_9;
            v661 = v660.length;
            v662 = l_9;
            v663 = (v661+1);
            v662.length = v663;
            v665 = l_9;
            v665[v661]=newitem_0;
            block = 1;
            break;
            case 1:
            return ( v659 );
        }
    }
}

function ll_int_str__IntegerR_SignedConst_Signed (repr_0,i_6) {
    var v834,v835;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v835 = ll_int2dec__Signed ( i_6 );
            v834 = v835;
            block = 1;
            break;
            case 1:
            return ( v834 );
        }
    }
}

function ll_listslice_startonly__List_Dict_String__String__ (RESLIST_0,l1_0,start_0) {
    var v409,v410,v411,v412,v413,v414,v415,v416,v417,v418,l1_1,i_4,j_0,l_6,len1_0,v419,v420,l1_2,i_5,j_1,l_7,len1_1,v421,v422,v423,v424,v425,v426;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v410 = l1_0;
            v411 = v410.length;
            v412 = (start_0>=0);
            undefined;
            v414 = (start_0<=v411);
            undefined;
            v416 = (v411-start_0);
            undefined;
            v418 = ll_newlist__List_Dict_String__String__LlT_Signed ( undefined,v416 );
            l1_1 = l1_0;
            i_4 = start_0;
            j_0 = 0;
            l_6 = v418;
            len1_0 = v411;
            block = 1;
            break;
            case 1:
            v419 = (i_4<len1_0);
            v420 = v419;
            if (v420 == true)
            {
                l1_2 = l1_1;
                i_5 = i_4;
                j_1 = j_0;
                l_7 = l_6;
                len1_1 = len1_0;
                block = 3;
                break;
            }
            else{
                v409 = l_6;
                block = 2;
                break;
            }
            case 2:
            return ( v409 );
            case 3:
            v421 = l_7;
            v422 = l1_2;
            v423 = v422[i_5];
            v421[j_1]=v423;
            v425 = (i_5+1);
            v426 = (j_1+1);
            l1_1 = l1_2;
            i_4 = v425;
            j_0 = v426;
            l_6 = l_7;
            len1_0 = len1_1;
            block = 1;
            break;
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed (self_1,length_1) {
    var v898,v899;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v899 = ll_newlist__List_Dict_String__String__LlT_Signed_0 ( undefined,length_1 );
            v898 = v899;
            block = 1;
            break;
            case 1:
            return ( v898 );
        }
    }
}

function ll_listnext__Record_index__Signed__iterable (iter_2) {
    var v431,v432,v433,v434,v435,v436,v437,iter_3,index_4,l_8,v438,v439,v440,v441,v442,v443,v444,etype_4,evalue_4;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v432 = iter_2.iterable;
            v433 = iter_2.index;
            v434 = v432;
            v435 = v434.length;
            v436 = (v433>=v435);
            v437 = v436;
            if (v437 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_3 = iter_2;
                index_4 = v433;
                l_8 = v432;
                block = 1;
                break;
            }
            case 1:
            v438 = (index_4+1);
            iter_3.index = v438;
            v440 = l_8;
            v441 = v440[index_4];
            v431 = v441;
            block = 2;
            break;
            case 2:
            return ( v431 );
            case 3:
            v442 = __consts_0.exceptions_StopIteration;
            v443 = v442.meta;
            v444 = v442;
            etype_4 = v443;
            evalue_4 = v444;
            block = 4;
            break;
            case 4:
            throw(evalue_4);
        }
    }
}

function show_interrupt () {
    var v651,v652,v653,v654,v655,v656,v657,v658;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__74;
            v654 = __consts_0.Document;
            v655 = v654.getElementById(__consts_0.const_str__39);
            v656 = v655.childNodes;
            v657 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v656,0 );
            v657.nodeValue = __consts_0.const_str__75;
            block = 1;
            break;
            case 1:
            return ( v651 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_D (ITER_1,lst_1) {
    var v427,v428,v429,v430;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v428 = new Object();
            v428.iterable = lst_1;
            v428.index = 0;
            v427 = v428;
            block = 1;
            break;
            case 1:
            return ( v427 );
        }
    }
}

function ll_prepend__List_String__String (l_10,newitem_1) {
    var v815,v816,v817,v818,v819,v820,l_11,newitem_2,dst_0,v821,v822,newitem_3,v823,v824,v825,l_12,newitem_4,dst_1,v826,v827,v828,v829,v830;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v816 = l_10;
            v817 = v816.length;
            v818 = l_10;
            v819 = (v817+1);
            v818.length = v819;
            l_11 = l_10;
            newitem_2 = newitem_1;
            dst_0 = v817;
            block = 1;
            break;
            case 1:
            v821 = (dst_0>0);
            v822 = v821;
            if (v822 == true)
            {
                l_12 = l_11;
                newitem_4 = newitem_2;
                dst_1 = dst_0;
                block = 4;
                break;
            }
            else{
                newitem_3 = newitem_2;
                v823 = l_11;
                block = 2;
                break;
            }
            case 2:
            v824 = v823;
            v824[0]=newitem_3;
            block = 3;
            break;
            case 3:
            return ( v815 );
            case 4:
            v826 = (dst_1-1);
            v827 = l_12;
            v828 = l_12;
            v829 = v828[v826];
            v827[dst_1]=v829;
            l_11 = l_12;
            newitem_2 = newitem_4;
            dst_0 = v826;
            block = 1;
            break;
        }
    }
}

function ll_len__List_String_ (l_13) {
    var v831,v832,v833;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v832 = l_13;
            v833 = v832.length;
            v831 = v833;
            block = 1;
            break;
            case 1:
            return ( v831 );
        }
    }
}

function add_received_item_outcome (msg_20,module_part_2) {
    var v667,v668,v669,v670,msg_21,module_part_3,v671,v672,v673,v674,v675,v676,v677,v678,v679,v680,v681,v682,v683,v684,v685,v686,v687,v688,v689,msg_22,module_part_4,item_name_6,td_0,v690,v691,v692,v693,msg_23,module_part_5,item_name_7,td_1,v694,v695,v696,v697,v698,v699,v700,v701,v702,v703,v704,v705,v706,v707,v708,v709,v710,v711,v712,v713,msg_24,module_part_6,td_2,v714,v715,v716,v717,v718,module_part_7,td_3,v719,v720,v721,v722,v723,v724,v725,v726,v727,v728,v729,v730,v731,v732,v733,v734,v735,v736,v737,v738,v739,v740,v741,v742,v743,v744,v745,v746,v747,v748,v749,v750,v751,v752,v753,msg_25,module_part_8,td_4,v754,v755,v756,msg_26,module_part_9,item_name_8,td_5,v757,v758,v759,v760,msg_27,module_part_10,item_name_9,td_6,v761,v762,v763,v764,v765,v766,v767,v768,v769,v770,v771,v772,v773,v774,v775,v776,v777,v778,v779,v780,msg_28,module_part_11,td_7,v781,v782,v783,msg_29,module_part_12,v784,v785,v786,v787,v788,v789,v790,v791,v792,v793,v794,v795,v796,v797,v798,v799,v800,v801,v802,v803,v804,v805,v806,v807,v808,v809,v810,v811,v812,v813,v814;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v668 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__70 );
            v669 = ll_strlen__String ( v668 );
            v670 = !!v669;
            if (v670 == true)
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
            v671 = create_elem ( __consts_0.const_str__23 );
            v672 = v671;
            v673 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__56 );
            v674 = new Object();
            v674.item0 = v673;
            v676 = v674.item0;
            v677 = new StringBuilder();
            v677.ll_append(__consts_0.const_str__76);
            v679 = ll_str__StringR_StringConst_String ( undefined,v676 );
            v677.ll_append(v679);
            v677.ll_append(__consts_0.const_str__33);
            v682 = v677.ll_build();
            v672.setAttribute(__consts_0.const_str__34,v682);
            v684 = v671;
            v684.setAttribute(__consts_0.const_str__35,__consts_0.const_str__77);
            v686 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__56 );
            v687 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__78 );
            v688 = ll_streq__String_String ( v687,__consts_0.const_str__29 );
            v689 = v688;
            if (v689 == true)
            {
                msg_28 = msg_21;
                module_part_11 = module_part_3;
                td_7 = v671;
                block = 10;
                break;
            }
            else{
                msg_22 = msg_21;
                module_part_4 = module_part_3;
                item_name_6 = v686;
                td_0 = v671;
                block = 2;
                break;
            }
            case 2:
            v690 = ll_dict_getitem__Dict_String__String__String ( msg_22,__consts_0.const_str__79 );
            v691 = ll_streq__String_String ( v690,__consts_0.const_str__80 );
            v692 = !v691;
            v693 = v692;
            if (v693 == true)
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
            v694 = create_elem ( __consts_0.const_str__81 );
            v695 = v694;
            v696 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__56 );
            v697 = new Object();
            v697.item0 = v696;
            v699 = v697.item0;
            v700 = new StringBuilder();
            v700.ll_append(__consts_0.const_str__82);
            v702 = ll_str__StringR_StringConst_String ( undefined,v699 );
            v700.ll_append(v702);
            v700.ll_append(__consts_0.const_str__33);
            v705 = v700.ll_build();
            v695.setAttribute(__consts_0.const_str__83,v705);
            v707 = create_text_elem ( __consts_0.const_str__84 );
            v708 = v694;
            v708.appendChild(v707);
            v710 = td_1;
            v710.appendChild(v694);
            v712 = __consts_0.ExportedMethods;
            v713 = v712.show_fail(item_name_7,fail_come_back);
            msg_24 = msg_23;
            module_part_6 = module_part_5;
            td_2 = td_1;
            block = 4;
            break;
            case 4:
            v714 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__69 );
            v715 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__85,v714 );
            v716 = (v715%50);
            v717 = (v716==0);
            v718 = v717;
            if (v718 == true)
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
                v719 = msg_24;
                block = 5;
                break;
            }
            case 5:
            v720 = ll_dict_getitem__Dict_String__String__String ( v719,__consts_0.const_str__69 );
            v721 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__85,v720 );
            v722 = (v721+1);
            __consts_0.const_tuple__85[v720]=v722;
            v724 = ll_strconcat__String_String ( __consts_0.const_str__86,v720 );
            v725 = get_elem ( v724 );
            v726 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__87,v720 );
            v727 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__85,v720 );
            v728 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__88,v720 );
            v729 = new Object();
            v729.item0 = v726;
            v729.item1 = v727;
            v729.item2 = v728;
            v733 = v729.item0;
            v734 = v729.item1;
            v735 = v729.item2;
            v736 = new StringBuilder();
            v737 = ll_str__StringR_StringConst_String ( undefined,v733 );
            v736.ll_append(v737);
            v736.ll_append(__consts_0.const_str__73);
            v740 = v734.toString();
            v736.ll_append(v740);
            v736.ll_append(__consts_0.const_str__89);
            v743 = v735.toString();
            v736.ll_append(v743);
            v736.ll_append(__consts_0.const_str__42);
            v746 = v736.ll_build();
            v747 = v725.childNodes;
            v748 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v747,0 );
            v748.nodeValue = v746;
            v750 = module_part_7.childNodes;
            v751 = ll_getitem__dum_nocheckConst_List_ExternalType__Si ( undefined,v750,-1 );
            v752 = v751;
            v752.appendChild(td_3);
            block = 6;
            break;
            case 6:
            return ( v667 );
            case 7:
            v754 = create_elem ( __consts_0.const_str__22 );
            v755 = module_part_8;
            v755.appendChild(v754);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v719 = msg_25;
            block = 5;
            break;
            case 8:
            v757 = ll_dict_getitem__Dict_String__String__String ( msg_26,__consts_0.const_str__79 );
            v758 = ll_streq__String_String ( v757,__consts_0.const_str__90 );
            v759 = !v758;
            v760 = v759;
            if (v760 == true)
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
            v761 = __consts_0.ExportedMethods;
            v762 = v761.show_skip(item_name_9,skip_come_back);
            v763 = create_elem ( __consts_0.const_str__81 );
            v764 = v763;
            v765 = ll_dict_getitem__Dict_String__String__String ( msg_27,__consts_0.const_str__56 );
            v766 = new Object();
            v766.item0 = v765;
            v768 = v766.item0;
            v769 = new StringBuilder();
            v769.ll_append(__consts_0.const_str__91);
            v771 = ll_str__StringR_StringConst_String ( undefined,v768 );
            v769.ll_append(v771);
            v769.ll_append(__consts_0.const_str__33);
            v774 = v769.ll_build();
            v764.setAttribute(__consts_0.const_str__83,v774);
            v776 = create_text_elem ( __consts_0.const_str__92 );
            v777 = v763;
            v777.appendChild(v776);
            v779 = td_6;
            v779.appendChild(v763);
            msg_24 = msg_27;
            module_part_6 = module_part_10;
            td_2 = td_6;
            block = 4;
            break;
            case 10:
            v781 = create_text_elem ( __consts_0.const_str__93 );
            v782 = td_7;
            v782.appendChild(v781);
            msg_24 = msg_28;
            module_part_6 = module_part_11;
            td_2 = td_7;
            block = 4;
            break;
            case 11:
            v784 = __consts_0.Document;
            v785 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v786 = v784.getElementById(v785);
            v787 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v788 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v789 = ll_dict_getitem__Dict_String__List_String___String ( v787,v788 );
            v790 = v789;
            v791 = ll_pop_default__dum_nocheckConst_List_String_ ( undefined,v790 );
            v792 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v793 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v794 = ll_dict_getitem__Dict_String__List_String___String ( v792,v793 );
            v795 = ll_len__List_String_ ( v794 );
            v796 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v797 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v798 = ll_dict_getitem__Dict_String__String__String ( v796,v797 );
            v799 = new Object();
            v799.item0 = v798;
            v799.item1 = v795;
            v802 = v799.item0;
            v803 = v799.item1;
            v804 = new StringBuilder();
            v805 = ll_str__StringR_StringConst_String ( undefined,v802 );
            v804.ll_append(v805);
            v804.ll_append(__consts_0.const_str__73);
            v808 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v803 );
            v804.ll_append(v808);
            v804.ll_append(__consts_0.const_str__42);
            v811 = v804.ll_build();
            v812 = v786.childNodes;
            v813 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v812,0 );
            v813.nodeValue = v811;
            msg_21 = msg_29;
            module_part_3 = module_part_12;
            block = 1;
            break;
        }
    }
}

function scroll_down_if_needed (mbox_2) {
    var v636,v637,v638,v639,v640,v641,v642;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v637 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v638 = v637;
            if (v638 == true)
            {
                v639 = mbox_2;
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            return ( v636 );
            case 2:
            v640 = v639.parentNode;
            v641 = v640;
            v641.scrollIntoView();
            block = 1;
            break;
        }
    }
}

function ll_int2dec__Signed (i_7) {
    var v896,v897;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v897 = i_7.toString();
            v896 = v897;
            block = 1;
            break;
            case 1:
            return ( v896 );
        }
    }
}

function skip_come_back (msg_32) {
    var v941,v942,v943,v944;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v942 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__57 );
            v943 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__94 );
            __consts_0.const_tuple[v943]=v942;
            block = 1;
            break;
            case 1:
            return ( v941 );
        }
    }
}

function show_crash () {
    var v643,v644,v645,v646,v647,v648,v649,v650;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__95;
            v646 = __consts_0.Document;
            v647 = v646.getElementById(__consts_0.const_str__39);
            v648 = v647.childNodes;
            v649 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v648,0 );
            v649.nodeValue = __consts_0.const_str__96;
            block = 1;
            break;
            case 1:
            return ( v643 );
        }
    }
}

function ll_getitem__dum_nocheckConst_List_ExternalType__Si (func_2,l_14,index_5) {
    var v927,v928,v929,v930,v931,l_15,index_6,length_3,v932,v933,v934,v935,index_7,v936,v937,v938,l_16,length_4,v939,v940;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v928 = l_14;
            v929 = v928.length;
            v930 = (index_5<0);
            v931 = v930;
            if (v931 == true)
            {
                l_16 = l_14;
                length_4 = v929;
                v939 = index_5;
                block = 4;
                break;
            }
            else{
                l_15 = l_14;
                index_6 = index_5;
                length_3 = v929;
                block = 1;
                break;
            }
            case 1:
            v932 = (index_6>=0);
            undefined;
            v934 = (index_6<length_3);
            undefined;
            index_7 = index_6;
            v936 = l_15;
            block = 2;
            break;
            case 2:
            v937 = v936;
            v938 = v937[index_7];
            v927 = v938;
            block = 3;
            break;
            case 3:
            return ( v927 );
            case 4:
            v940 = (v939+length_4);
            l_15 = l_16;
            index_6 = v940;
            length_3 = length_4;
            block = 1;
            break;
        }
    }
}

function ll_pop_default__dum_nocheckConst_List_String_ (func_3,l_17) {
    var v945,v946,v947,l_18,length_5,v948,v949,v950,v951,v952,v953,res_0,newlength_0,v954,v955,v956;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v946 = l_17;
            v947 = v946.length;
            l_18 = l_17;
            length_5 = v947;
            block = 1;
            break;
            case 1:
            v948 = (length_5>0);
            undefined;
            v950 = (length_5-1);
            v951 = l_18;
            v952 = v951[v950];
            ll_null_item__List_String_ ( l_18 );
            res_0 = v952;
            newlength_0 = v950;
            v954 = l_18;
            block = 2;
            break;
            case 2:
            v955 = v954;
            v955.length = newlength_0;
            v945 = res_0;
            block = 3;
            break;
            case 3:
            return ( v945 );
        }
    }
}

function make_module_box (msg_30) {
    var v836,v837,v838,v839,v840,v841,v842,v843,v844,v845,v846,v847,v848,v849,v850,v851,v852,v853,v854,v855,v856,v857,v858,v859,v860,v861,v862,v863,v864,v865,v866,v867,v868,v869,v870,v871,v872,v873,v874,v875,v876,v877,v878,v879,v880,v881,v882,v883,v884,v885,v886,v887,v888,v889,v890,v891,v892,v893,v894,v895;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v837 = create_elem ( __consts_0.const_str__22 );
            v838 = create_elem ( __consts_0.const_str__23 );
            v839 = v837;
            v839.appendChild(v838);
            v841 = v838;
            v842 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__97 );
            v843 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__98 );
            v844 = new Object();
            v844.item0 = v842;
            v844.item1 = v843;
            v847 = v844.item0;
            v848 = v844.item1;
            v849 = new StringBuilder();
            v850 = ll_str__StringR_StringConst_String ( undefined,v847 );
            v849.ll_append(v850);
            v849.ll_append(__consts_0.const_str__99);
            v853 = ll_str__StringR_StringConst_String ( undefined,v848 );
            v849.ll_append(v853);
            v849.ll_append(__consts_0.const_str__42);
            v856 = v849.ll_build();
            v857 = create_text_elem ( v856 );
            v841.appendChild(v857);
            v859 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__98 );
            v860 = ll_int__String_Signed ( v859,10 );
            v861 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__88[v861]=v860;
            v863 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__97 );
            v864 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__87[v864]=v863;
            v866 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v867 = ll_strconcat__String_String ( __consts_0.const_str__86,v866 );
            v838.id = v867;
            v869 = v838;
            v870 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v871 = new Object();
            v871.item0 = v870;
            v873 = v871.item0;
            v874 = new StringBuilder();
            v874.ll_append(__consts_0.const_str__76);
            v876 = ll_str__StringR_StringConst_String ( undefined,v873 );
            v874.ll_append(v876);
            v874.ll_append(__consts_0.const_str__33);
            v879 = v874.ll_build();
            v869.setAttribute(__consts_0.const_str__34,v879);
            v881 = v838;
            v881.setAttribute(__consts_0.const_str__35,__consts_0.const_str__77);
            v883 = create_elem ( __consts_0.const_str__23 );
            v884 = v837;
            v884.appendChild(v883);
            v886 = create_elem ( __consts_0.const_str__100 );
            v887 = v883;
            v887.appendChild(v886);
            v889 = create_elem ( __consts_0.const_str__21 );
            v890 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v889.id = v890;
            v892 = v886;
            v892.appendChild(v889);
            v894 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__85[v894]=0;
            v836 = v837;
            block = 1;
            break;
            case 1:
            return ( v836 );
        }
    }
}

function ll_strlen__String (obj_1) {
    var v904,v905,v906;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v905 = obj_1;
            v906 = v905.length;
            v904 = v906;
            block = 1;
            break;
            case 1:
            return ( v904 );
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed_0 (LIST_2,length_2) {
    var v900,v901,v902,v903;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v901 = new Array();
            v902 = v901;
            v902.length = length_2;
            v900 = v901;
            block = 1;
            break;
            case 1:
            return ( v900 );
        }
    }
}

function fail_come_back (msg_31) {
    var v907,v908,v909,v910,v911,v912,v913,v914,v915,v916;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v908 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__101 );
            v909 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__102 );
            v910 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__103 );
            v911 = new Object();
            v911.item0 = v908;
            v911.item1 = v909;
            v911.item2 = v910;
            v915 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__94 );
            __consts_0.const_tuple__2[v915]=v911;
            block = 1;
            break;
            case 1:
            return ( v907 );
        }
    }
}

function ll_dict_getitem__Dict_String__Signed__String (d_4,key_8) {
    var v917,v918,v919,v920,v921,v922,v923,etype_5,evalue_5,key_9,v924,v925,v926;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v918 = d_4;
            v919 = (v918[key_8]!=undefined);
            v920 = v919;
            if (v920 == true)
            {
                key_9 = key_8;
                v924 = d_4;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v921 = __consts_0.exceptions_KeyError;
            v922 = v921.meta;
            v923 = v921;
            etype_5 = v922;
            evalue_5 = v923;
            block = 2;
            break;
            case 2:
            throw(evalue_5);
            case 3:
            v925 = v924;
            v926 = v925[key_9];
            v917 = v926;
            block = 4;
            break;
            case 4:
            return ( v917 );
        }
    }
}

function ll_null_item__List_String_ (lst_2) {
    var v957,v958;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            undefined;
            block = 1;
            break;
            case 1:
            return ( v957 );
        }
    }
}

function ll_int__String_Signed (s_2,base_0) {
    var v959,v960,v961,v962,v963,v964,etype_6,evalue_6,s_3,base_1,v965,s_4,base_2,v966,v967,s_5,base_3,v968,v969,s_6,base_4,i_8,strlen_0,v970,v971,s_7,base_5,i_9,strlen_1,v972,v973,v974,v975,v976,s_8,base_6,i_10,strlen_2,v977,v978,v979,v980,s_9,base_7,i_11,strlen_3,v981,v982,v983,v984,s_10,base_8,val_0,i_12,sign_0,strlen_4,v985,v986,s_11,val_1,i_13,sign_1,strlen_5,v987,v988,val_2,sign_2,v989,v990,v991,v992,v993,v994,v995,v996,v997,v998,s_12,val_3,i_14,sign_3,strlen_6,v999,v1000,v1001,v1002,s_13,val_4,sign_4,strlen_7,v1003,v1004,s_14,base_9,val_5,i_15,sign_5,strlen_8,v1005,v1006,v1007,v1008,v1009,s_15,base_10,c_0,val_6,i_16,sign_6,strlen_9,v1010,v1011,s_16,base_11,c_1,val_7,i_17,sign_7,strlen_10,v1012,v1013,s_17,base_12,c_2,val_8,i_18,sign_8,strlen_11,v1014,s_18,base_13,c_3,val_9,i_19,sign_9,strlen_12,v1015,v1016,s_19,base_14,val_10,i_20,sign_10,strlen_13,v1017,v1018,s_20,base_15,val_11,i_21,digit_0,sign_11,strlen_14,v1019,v1020,s_21,base_16,i_22,digit_1,sign_12,strlen_15,v1021,v1022,v1023,v1024,s_22,base_17,c_4,val_12,i_23,sign_13,strlen_16,v1025,s_23,base_18,c_5,val_13,i_24,sign_14,strlen_17,v1026,v1027,s_24,base_19,val_14,i_25,sign_15,strlen_18,v1028,v1029,v1030,s_25,base_20,c_6,val_15,i_26,sign_16,strlen_19,v1031,s_26,base_21,c_7,val_16,i_27,sign_17,strlen_20,v1032,v1033,s_27,base_22,val_17,i_28,sign_18,strlen_21,v1034,v1035,v1036,s_28,base_23,strlen_22,v1037,v1038,s_29,base_24,strlen_23,v1039,v1040,s_30,base_25,i_29,strlen_24,v1041,v1042,v1043,v1044,s_31,base_26,strlen_25,v1045,v1046;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v960 = (2<=base_0);
            v961 = v960;
            if (v961 == true)
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
            v962 = __consts_0.exceptions_ValueError;
            v963 = v962.meta;
            v964 = v962;
            etype_6 = v963;
            evalue_6 = v964;
            block = 2;
            break;
            case 2:
            throw(evalue_6);
            case 3:
            v965 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v966 = v965;
            block = 4;
            break;
            case 4:
            v967 = v966;
            if (v967 == true)
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
            v968 = s_5;
            v969 = v968.length;
            s_6 = s_5;
            base_4 = base_3;
            i_8 = 0;
            strlen_0 = v969;
            block = 6;
            break;
            case 6:
            v970 = (i_8<strlen_0);
            v971 = v970;
            if (v971 == true)
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
            v972 = (i_9<strlen_1);
            v973 = v972;
            if (v973 == true)
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
            v974 = __consts_0.exceptions_ValueError;
            v975 = v974.meta;
            v976 = v974;
            etype_6 = v975;
            evalue_6 = v976;
            block = 2;
            break;
            case 9:
            v977 = s_8;
            v978 = v977.charAt(i_10);
            v979 = (v978=='-');
            v980 = v979;
            if (v980 == true)
            {
                s_29 = s_8;
                base_24 = base_6;
                strlen_23 = strlen_2;
                v1039 = i_10;
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
            v981 = s_9;
            v982 = v981.charAt(i_11);
            v983 = (v982=='+');
            v984 = v983;
            if (v984 == true)
            {
                s_28 = s_9;
                base_23 = base_7;
                strlen_22 = strlen_3;
                v1037 = i_11;
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
            v985 = (i_12<strlen_4);
            v986 = v985;
            if (v986 == true)
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
            v987 = (i_13<strlen_5);
            v988 = v987;
            if (v988 == true)
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
                v989 = i_13;
                v990 = strlen_5;
                block = 13;
                break;
            }
            case 13:
            v991 = (v989==v990);
            v992 = v991;
            if (v992 == true)
            {
                v996 = sign_2;
                v997 = val_2;
                block = 15;
                break;
            }
            else{
                block = 14;
                break;
            }
            case 14:
            v993 = __consts_0.exceptions_ValueError;
            v994 = v993.meta;
            v995 = v993;
            etype_6 = v994;
            evalue_6 = v995;
            block = 2;
            break;
            case 15:
            v998 = (v996*v997);
            v959 = v998;
            block = 16;
            break;
            case 16:
            return ( v959 );
            case 17:
            v999 = s_12;
            v1000 = v999.charAt(i_14);
            v1001 = (v1000==' ');
            v1002 = v1001;
            if (v1002 == true)
            {
                s_13 = s_12;
                val_4 = val_3;
                sign_4 = sign_3;
                strlen_7 = strlen_6;
                v1003 = i_14;
                block = 18;
                break;
            }
            else{
                val_2 = val_3;
                sign_2 = sign_3;
                v989 = i_14;
                v990 = strlen_6;
                block = 13;
                break;
            }
            case 18:
            v1004 = (v1003+1);
            s_11 = s_13;
            val_1 = val_4;
            i_13 = v1004;
            sign_1 = sign_4;
            strlen_5 = strlen_7;
            block = 12;
            break;
            case 19:
            v1005 = s_14;
            v1006 = v1005.charAt(i_15);
            v1007 = v1006.charCodeAt(0);
            v1008 = (97<=v1007);
            v1009 = v1008;
            if (v1009 == true)
            {
                s_25 = s_14;
                base_20 = base_9;
                c_6 = v1007;
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
                c_0 = v1007;
                val_6 = val_5;
                i_16 = i_15;
                sign_6 = sign_5;
                strlen_9 = strlen_8;
                block = 20;
                break;
            }
            case 20:
            v1010 = (65<=c_0);
            v1011 = v1010;
            if (v1011 == true)
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
            v1012 = (48<=c_1);
            v1013 = v1012;
            if (v1013 == true)
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
            v1014 = (c_2<=57);
            s_18 = s_17;
            base_13 = base_12;
            c_3 = c_2;
            val_9 = val_8;
            i_19 = i_18;
            sign_9 = sign_8;
            strlen_12 = strlen_11;
            v1015 = v1014;
            block = 23;
            break;
            case 23:
            v1016 = v1015;
            if (v1016 == true)
            {
                s_19 = s_18;
                base_14 = base_13;
                val_10 = val_9;
                i_20 = i_19;
                sign_10 = sign_9;
                strlen_13 = strlen_12;
                v1017 = c_3;
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
            v1018 = (v1017-48);
            s_20 = s_19;
            base_15 = base_14;
            val_11 = val_10;
            i_21 = i_20;
            digit_0 = v1018;
            sign_11 = sign_10;
            strlen_14 = strlen_13;
            block = 25;
            break;
            case 25:
            v1019 = (digit_0>=base_15);
            v1020 = v1019;
            if (v1020 == true)
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
                v1021 = val_11;
                block = 26;
                break;
            }
            case 26:
            v1022 = (v1021*base_16);
            v1023 = (v1022+digit_1);
            v1024 = (i_22+1);
            s_10 = s_21;
            base_8 = base_16;
            val_0 = v1023;
            i_12 = v1024;
            sign_0 = sign_12;
            strlen_4 = strlen_15;
            block = 11;
            break;
            case 27:
            v1025 = (c_4<=90);
            s_23 = s_22;
            base_18 = base_17;
            c_5 = c_4;
            val_13 = val_12;
            i_24 = i_23;
            sign_14 = sign_13;
            strlen_17 = strlen_16;
            v1026 = v1025;
            block = 28;
            break;
            case 28:
            v1027 = v1026;
            if (v1027 == true)
            {
                s_24 = s_23;
                base_19 = base_18;
                val_14 = val_13;
                i_25 = i_24;
                sign_15 = sign_14;
                strlen_18 = strlen_17;
                v1028 = c_5;
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
            v1029 = (v1028-65);
            v1030 = (v1029+10);
            s_20 = s_24;
            base_15 = base_19;
            val_11 = val_14;
            i_21 = i_25;
            digit_0 = v1030;
            sign_11 = sign_15;
            strlen_14 = strlen_18;
            block = 25;
            break;
            case 30:
            v1031 = (c_6<=122);
            s_26 = s_25;
            base_21 = base_20;
            c_7 = c_6;
            val_16 = val_15;
            i_27 = i_26;
            sign_17 = sign_16;
            strlen_20 = strlen_19;
            v1032 = v1031;
            block = 31;
            break;
            case 31:
            v1033 = v1032;
            if (v1033 == true)
            {
                s_27 = s_26;
                base_22 = base_21;
                val_17 = val_16;
                i_28 = i_27;
                sign_18 = sign_17;
                strlen_21 = strlen_20;
                v1034 = c_7;
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
            v1035 = (v1034-97);
            v1036 = (v1035+10);
            s_20 = s_27;
            base_15 = base_22;
            val_11 = val_17;
            i_21 = i_28;
            digit_0 = v1036;
            sign_11 = sign_18;
            strlen_14 = strlen_21;
            block = 25;
            break;
            case 33:
            v1038 = (v1037+1);
            s_10 = s_28;
            base_8 = base_23;
            val_0 = 0;
            i_12 = v1038;
            sign_0 = 1;
            strlen_4 = strlen_22;
            block = 11;
            break;
            case 34:
            v1040 = (v1039+1);
            s_10 = s_29;
            base_8 = base_24;
            val_0 = 0;
            i_12 = v1040;
            sign_0 = -1;
            strlen_4 = strlen_23;
            block = 11;
            break;
            case 35:
            v1041 = s_30;
            v1042 = v1041.charAt(i_29);
            v1043 = (v1042==' ');
            v1044 = v1043;
            if (v1044 == true)
            {
                s_31 = s_30;
                base_26 = base_25;
                strlen_25 = strlen_24;
                v1045 = i_29;
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
            v1046 = (v1045+1);
            s_6 = s_31;
            base_4 = base_26;
            i_8 = v1046;
            strlen_0 = strlen_25;
            block = 6;
            break;
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
function py____test_rsession_webjs_Globals_meta () {
}

py____test_rsession_webjs_Globals_meta.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals_meta instance>' );
}

inherits(py____test_rsession_webjs_Globals_meta,Object_meta);
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
function exceptions_StopIteration_meta () {
}

exceptions_StopIteration_meta.prototype.toString = function (){
    return ( '<exceptions_StopIteration_meta instance>' );
}

inherits(exceptions_StopIteration_meta,exceptions_Exception_meta);
__consts_0 = {};
__consts_0.const_str__66 = ' failures, ';
__consts_0.const_str__32 = "show_host('";
__consts_0.const_str__65 = ' run, ';
__consts_0.py____test_rsession_webjs_Options__108 = py____test_rsession_webjs_Options;
__consts_0.py____test_rsession_webjs_Options_meta = new py____test_rsession_webjs_Options_meta();
__consts_0.py____test_rsession_webjs_Options = new py____test_rsession_webjs_Options();
__consts_0.const_str__81 = 'a';
__consts_0.const_str__42 = ']';
__consts_0.const_tuple__13 = undefined;
__consts_0.py____test_rsession_webjs_Globals__115 = py____test_rsession_webjs_Globals;
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.const_tuple__15 = undefined;
__consts_0.const_list__114 = [];
__consts_0.const_str__12 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.const_str__49 = 'ReceivedItemOutcome';
__consts_0.const_str__76 = "show_info('";
__consts_0.const_str__36 = 'hide_host()';
__consts_0.const_str__77 = 'hide_info()';
__consts_0.const_str__10 = '#message';
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__21 = 'tbody';
__consts_0.const_str__95 = 'Py.test [crashed]';
__consts_0.const_str__59 = ')';
__consts_0.const_str__44 = 'main_table';
__consts_0.const_str__75 = 'Tests [interrupted]';
__consts_0.exceptions_KeyError__112 = exceptions_KeyError;
__consts_0.const_str__33 = "')";
__consts_0.exceptions_StopIteration__110 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.const_str__53 = 'RsyncFinished';
__consts_0.const_str__86 = '_txt_';
__consts_0.const_tuple__85 = {};
__consts_0.const_str__102 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_list = undefined;
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_str__64 = 'FINISHED ';
__consts_0.const_str__40 = 'Rsyncing';
__consts_0.const_str__17 = 'info';
__consts_0.const_str__25 = 'hidden';
__consts_0.const_str__38 = 'true';
__consts_0.exceptions_ValueError__106 = exceptions_ValueError;
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.const_str__84 = 'F';
__consts_0.const_str__35 = 'onmouseout';
__consts_0.const_str__45 = 'type';
__consts_0.const_str__98 = 'length';
__consts_0.const_str__78 = 'passed';
__consts_0.const_str__93 = '.';
__consts_0.const_str__51 = 'FailedTryiter';
__consts_0.const_tuple__88 = {};
__consts_0.const_str__31 = '#ff0000';
__consts_0.const_str__28 = 'checked';
__consts_0.const_str__7 = 'messagebox';
__consts_0.const_str__56 = 'fullitemname';
__consts_0.const_str__100 = 'table';
__consts_0.const_str__68 = 'Py.test ';
__consts_0.const_str__63 = 'skips';
__consts_0.const_str__55 = 'CrashedExecution';
__consts_0.const_str__6 = '\n';
__consts_0.const_str__8 = 'pre';
__consts_0.const_str__74 = 'Py.test [interrupted]';
__consts_0.const_str__4 = '\n======== Stdout: ========\n';
__consts_0.const_str__71 = '#00ff00';
__consts_0.const_str__19 = 'beige';
__consts_0.const_str__92 = 's';
__consts_0.const_tuple__2 = {};
__consts_0.const_str__101 = 'traceback';
__consts_0.const_str__43 = 'testmain';
__consts_0.const_str__91 = "javascript:show_skip('";
__consts_0.const_str__73 = '[';
__consts_0.const_str__96 = 'Tests [crashed]';
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.const_str__57 = 'reason';
__consts_0.const_str__82 = "javascript:show_traceback('";
__consts_0.const_str__39 = 'Tests';
__consts_0.const_tuple = {};
__consts_0.const_str__61 = 'run';
__consts_0.const_str__52 = 'SkippedTryiter';
__consts_0.const_str__80 = 'None';
__consts_0.const_str__29 = 'True';
__consts_0.const_str__89 = '/';
__consts_0.const_str__58 = '- skipped (';
__consts_0.const_str__70 = 'hostkey';
__consts_0.const_str__62 = 'fails';
__consts_0.const_str__46 = 'ItemStart';
__consts_0.const_str__97 = 'itemname';
__consts_0.const_str__50 = 'TestFinished';
__consts_0.const_str__20 = 'jobs';
__consts_0.const_str__5 = '\n========== Stderr: ==========\n';
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.const_str__67 = ' skipped';
__consts_0.const_tuple__87 = {};
__consts_0.const_str__103 = 'stderr';
__consts_0.const_str__83 = 'href';
__consts_0.const_str__18 = 'visible';
__consts_0.const_str__90 = 'False';
__consts_0.const_str__48 = 'HostRSyncRootReady';
__consts_0.const_str__34 = 'onmouseover';
__consts_0.const_str__60 = '- FAILED TO LOAD MODULE';
__consts_0.const_str__99 = '[0/';
__consts_0.const_str__47 = 'SendItem';
__consts_0.const_str__69 = 'fullmodulename';
__consts_0.const_str__79 = 'skipped';
__consts_0.const_str__30 = 'hostsbody';
__consts_0.const_str__72 = '[0]';
__consts_0.const_str__23 = 'td';
__consts_0.const_str__3 = '====== Traceback: =========\n';
__consts_0.const_str__22 = 'tr';
__consts_0.const_str__94 = 'item_name';
__consts_0.const_str__41 = 'Tests [';
__consts_0.Document = document;
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.const_str__54 = 'InterruptedExecution';
__consts_0.const_str__27 = 'opt_scroll';
__consts_0.py____test_rsession_webjs_Options_meta.class_ = __consts_0.py____test_rsession_webjs_Options__108;
__consts_0.py____test_rsession_webjs_Options.meta = __consts_0.py____test_rsession_webjs_Options_meta;
__consts_0.py____test_rsession_webjs_Options.oscroll = true;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__115;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__12;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__12;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ofinished = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple__13;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__114;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__15;
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__110;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__106;
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__112;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
