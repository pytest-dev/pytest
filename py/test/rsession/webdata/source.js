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
    var v0,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12;
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
            block = 1;
            break;
            case 1:
            return ( v0 );
        }
    }
}

function show_info (data_0) {
    var v39,v40,v41,v42,v43,data_1,info_0,v44,v45,v46,info_1,v47,v48,v49,v50,v51,v52,data_2,info_2,v53,v54,v55,v56;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v40 = __consts_0.Document;
            v41 = v40.getElementById(__consts_0.const_str__2);
            v42 = v41.style;
            v42.visibility = __consts_0.const_str__3;
            data_1 = data_0;
            info_0 = v41;
            block = 1;
            break;
            case 1:
            v44 = info_0.childNodes;
            v45 = ll_len__List_ExternalType_ ( v44 );
            v46 = !!v45;
            if (v46 == true)
            {
                data_2 = data_1;
                info_2 = info_0;
                block = 4;
                break;
            }
            else{
                info_1 = info_0;
                v47 = data_1;
                block = 2;
                break;
            }
            case 2:
            v48 = create_text_elem ( v47 );
            v49 = info_1;
            v49.appendChild(v48);
            v51 = info_1.style;
            v51.backgroundColor = __consts_0.const_str__4;
            block = 3;
            break;
            case 3:
            return ( v39 );
            case 4:
            v53 = info_2;
            v54 = info_2.childNodes;
            v55 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v54,0 );
            v53.removeChild(v55);
            data_1 = data_2;
            info_0 = info_2;
            block = 1;
            break;
        }
    }
}

function ll_len__List_ExternalType_ (l_0) {
    var v116,v117,v118;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v117 = l_0;
            v118 = v117.length;
            v116 = v118;
            block = 1;
            break;
            case 1:
            return ( v116 );
        }
    }
}

function main () {
    var v13,v14,v15,v16,v17;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v14 = __consts_0.ExportedMethods;
            v15 = v14.show_hosts(host_init);
            v16 = __consts_0.ExportedMethods;
            v17 = v16.show_sessid(sessid_comeback);
            block = 1;
            break;
            case 1:
            return ( v13 );
        }
    }
}

function show_traceback (item_name_1) {
    var v21,v22,v23,v24,v25,v26,v27,v28,v29,v30,v31,v32,v33,v34,v35,v36,v37,v38;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v22 = ll_dict_getitem__Dict_String__Record_item2__Str_St ( __consts_0.const_tuple,item_name_1 );
            v23 = v22.item0;
            v24 = v22.item1;
            v25 = v22.item2;
            v26 = new StringBuilder();
            v26.ll_append(__consts_0.const_str__7);
            v28 = ll_str__StringR_StringConst_String ( undefined,v23 );
            v26.ll_append(v28);
            v26.ll_append(__consts_0.const_str__8);
            v31 = ll_str__StringR_StringConst_String ( undefined,v24 );
            v26.ll_append(v31);
            v26.ll_append(__consts_0.const_str__9);
            v34 = ll_str__StringR_StringConst_String ( undefined,v25 );
            v26.ll_append(v34);
            v26.ll_append(__consts_0.const_str__10);
            v37 = v26.ll_build();
            set_msgbox ( item_name_1,v37 );
            block = 1;
            break;
            case 1:
            return ( v21 );
        }
    }
}

function ll_str__StringR_StringConst_String (self_0,s_0) {
    var v194;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v194 = s_0;
            block = 1;
            break;
            case 1:
            return ( v194 );
        }
    }
}

function sessid_comeback (id_0) {
    var v180,v181,v182,v183;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.osessid = id_0;
            v182 = __consts_0.ExportedMethods;
            v183 = v182.show_all_statuses(id_0,comeback);
            block = 1;
            break;
            case 1:
            return ( v180 );
        }
    }
}

function set_msgbox (item_name_2,data_3) {
    var v195,v196,item_name_3,data_4,msgbox_0,v197,v198,v199,item_name_4,data_5,msgbox_1,v200,v201,v202,v203,v204,v205,v206,v207,v208,v209,item_name_5,data_6,msgbox_2,v210,v211,v212,v213;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v196 = get_elem ( __consts_0.const_str__12 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v196;
            block = 1;
            break;
            case 1:
            v197 = msgbox_0.childNodes;
            v198 = ll_len__List_ExternalType_ ( v197 );
            v199 = !!v198;
            if (v199 == true)
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
            v200 = create_elem ( __consts_0.const_str__13 );
            v201 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__10 );
            v202 = ll_strconcat__String_String ( v201,data_5 );
            v203 = create_text_elem ( v202 );
            v204 = v200;
            v204.appendChild(v203);
            v206 = msgbox_1;
            v206.appendChild(v200);
            __consts_0.Document.location = __consts_0.const_str__14;
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 3:
            return ( v195 );
            case 4:
            v210 = msgbox_2;
            v211 = msgbox_2.childNodes;
            v212 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v211,0 );
            v210.removeChild(v212);
            item_name_3 = item_name_5;
            data_4 = data_6;
            msgbox_0 = msgbox_2;
            block = 1;
            break;
        }
    }
}

function host_init (host_dict_0) {
    var v132,v133,v134,v135,v136,v137,host_dict_1,tbody_3,v138,v139,last_exc_value_1,host_dict_2,tbody_4,host_0,v140,v141,v142,v143,v144,v145,v146,v147,v148,v149,v150,v151,v152,v153,v154,v155,v156,v157,v158,v159,v160,v161,v162,v163,v164,v165,v166,host_dict_3,v167,v168,v169,v170,v171,v172,v173,v174,last_exc_value_2,key_0,v175,v176,v177,v178,v179;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v133 = __consts_0.Document;
            v134 = v133.getElementById(__consts_0.const_str__15);
            v135 = host_dict_0;
            v136 = ll_dict_kvi__Dict_String__String__List_String_LlT_ ( v135,undefined,undefined );
            v137 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v136 );
            host_dict_1 = host_dict_0;
            tbody_3 = v134;
            v138 = v137;
            block = 1;
            break;
            case 1:
            try {
                v139 = ll_listnext__Record_index__Signed__iterable_0 ( v138 );
                host_dict_2 = host_dict_1;
                tbody_4 = tbody_3;
                host_0 = v139;
                v140 = v138;
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
            v141 = create_elem ( __consts_0.const_str__16 );
            v142 = tbody_4;
            v142.appendChild(v141);
            v144 = create_elem ( __consts_0.const_str__17 );
            v145 = v144.style;
            v145.background = __consts_0.const_str__18;
            v147 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v148 = create_text_elem ( v147 );
            v149 = v144;
            v149.appendChild(v148);
            v144.id = host_0;
            v152 = v141;
            v152.appendChild(v144);
            v154 = v144;
            v155 = new StringBuilder();
            v155.ll_append(__consts_0.const_str__19);
            v157 = ll_str__StringR_StringConst_String ( undefined,host_0 );
            v155.ll_append(v157);
            v155.ll_append(__consts_0.const_str__20);
            v160 = v155.ll_build();
            v154.setAttribute(__consts_0.const_str__21,v160);
            v162 = v144;
            v162.setAttribute(__consts_0.const_str__22,__consts_0.const_str__23);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
            setTimeout ( 'update_rsync()',1000 );
            host_dict_1 = host_dict_2;
            tbody_3 = tbody_4;
            v138 = v140;
            block = 1;
            break;
            case 3:
            __consts_0.py____test_rsession_webjs_Globals.ohost_dict = host_dict_3;
            v168 = ll_newdict__Dict_String__List_String__LlT ( undefined );
            __consts_0.py____test_rsession_webjs_Globals.ohost_pending = v168;
            v170 = host_dict_3;
            v171 = ll_dict_kvi__Dict_String__String__List_String_LlT_ ( v170,undefined,undefined );
            v172 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v171 );
            v173 = v172;
            block = 4;
            break;
            case 4:
            try {
                v174 = ll_listnext__Record_index__Signed__iterable_0 ( v173 );
                key_0 = v174;
                v175 = v173;
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
            v176 = new Array();
            v176.length = 0;
            v178 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v178[key_0]=v176;
            v173 = v175;
            block = 4;
            break;
            case 6:
            return ( v132 );
        }
    }
}

function get_elem (el_0) {
    var v241,v242,v243;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v242 = __consts_0.Document;
            v243 = v242.getElementById(el_0);
            v241 = v243;
            block = 1;
            break;
            case 1:
            return ( v241 );
        }
    }
}

function hide_messagebox () {
    var v107,v108,v109,mbox_0,v110,v111,mbox_1,v112,v113,v114,v115;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v108 = __consts_0.Document;
            v109 = v108.getElementById(__consts_0.const_str__12);
            mbox_0 = v109;
            block = 1;
            break;
            case 1:
            v110 = mbox_0.childNodes;
            v111 = ll_list_is_true__List_ExternalType_ ( v110 );
            if (v111 == true)
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
            return ( v107 );
            case 3:
            v112 = mbox_1;
            v113 = mbox_1.childNodes;
            v114 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v113,0 );
            v112.removeChild(v114);
            mbox_0 = mbox_1;
            block = 1;
            break;
        }
    }
}

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__24;
    this.ohost = __consts_0.const_str__24;
    this.orsync_dots = 0;
    this.ohost_dict = __consts_0.const_tuple__25;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__27;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals instance>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
function create_elem (s_1) {
    var v244,v245,v246;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v245 = __consts_0.Document;
            v246 = v245.createElement(s_1);
            v244 = v246;
            block = 1;
            break;
            case 1:
            return ( v244 );
        }
    }
}

function ll_dict_getitem__Dict_String__Record_item2__Str_St (d_0,key_1) {
    var v184,v185,v186,v187,v188,v189,v190,etype_0,evalue_0,key_2,v191,v192,v193;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v185 = d_0;
            v186 = (v185[key_1]!=undefined);
            v187 = v186;
            if (v187 == true)
            {
                key_2 = key_1;
                v191 = d_0;
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
            etype_0 = v189;
            evalue_0 = v190;
            block = 2;
            break;
            case 2:
            throw(evalue_0);
            case 3:
            v192 = v191;
            v193 = v192[key_2];
            v184 = v193;
            block = 4;
            break;
            case 4:
            return ( v184 );
        }
    }
}

function create_text_elem (txt_0) {
    var v119,v120,v121;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v120 = __consts_0.Document;
            v121 = v120.createTextNode(txt_0);
            v119 = v121;
            block = 1;
            break;
            case 1:
            return ( v119 );
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
function hide_info () {
    var v57,v58,v59,v60,v61;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v58 = __consts_0.Document;
            v59 = v58.getElementById(__consts_0.const_str__2);
            v60 = v59.style;
            v60.visibility = __consts_0.const_str__29;
            block = 1;
            break;
            case 1:
            return ( v57 );
        }
    }
}

function show_skip (item_name_0) {
    var v18,v19,v20;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v19 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__30,item_name_0 );
            set_msgbox ( item_name_0,v19 );
            block = 1;
            break;
            case 1:
            return ( v18 );
        }
    }
}

function show_host (host_name_0) {
    var v62,v63,v64,v65,v66,host_name_1,elem_0,v67,v68,v69,v70,host_name_2,tbody_0,elem_1,v71,v72,last_exc_value_0,host_name_3,tbody_1,elem_2,item_0,v73,v74,v75,v76,v77,v78,v79,v80,v81,v82,host_name_4,tbody_2,elem_3,v83,v84,v85,v86,v87,v88,host_name_5,elem_4,v89,v90,v91,v92;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v63 = __consts_0.Document;
            v64 = v63.getElementById(__consts_0.const_str__31);
            v65 = v64.childNodes;
            v66 = ll_list_is_true__List_ExternalType_ ( v65 );
            if (v66 == true)
            {
                host_name_5 = host_name_0;
                elem_4 = v64;
                block = 6;
                break;
            }
            else{
                host_name_1 = host_name_0;
                elem_0 = v64;
                block = 1;
                break;
            }
            case 1:
            v67 = create_elem ( __consts_0.const_str__32 );
            v68 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v69 = ll_dict_getitem__Dict_String__List_String___String ( v68,host_name_1 );
            v70 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v69 );
            host_name_2 = host_name_1;
            tbody_0 = v67;
            elem_1 = elem_0;
            v71 = v70;
            block = 2;
            break;
            case 2:
            try {
                v72 = ll_listnext__Record_index__Signed__iterable_0 ( v71 );
                host_name_3 = host_name_2;
                tbody_1 = tbody_0;
                elem_2 = elem_1;
                item_0 = v72;
                v73 = v71;
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
            v74 = create_elem ( __consts_0.const_str__16 );
            v75 = create_elem ( __consts_0.const_str__17 );
            v76 = v75;
            v77 = create_text_elem ( item_0 );
            v76.appendChild(v77);
            v79 = v74;
            v79.appendChild(v75);
            v81 = tbody_1;
            v81.appendChild(v74);
            host_name_2 = host_name_3;
            tbody_0 = tbody_1;
            elem_1 = elem_2;
            v71 = v73;
            block = 2;
            break;
            case 4:
            v83 = elem_3;
            v83.appendChild(tbody_2);
            v85 = elem_3.style;
            v85.visibility = __consts_0.const_str__3;
            __consts_0.py____test_rsession_webjs_Globals.ohost = host_name_4;
            setTimeout ( 'reshow_host()',100 );
            block = 5;
            break;
            case 5:
            return ( v62 );
            case 6:
            v89 = elem_4;
            v90 = elem_4.childNodes;
            v91 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v90,0 );
            v89.removeChild(v91);
            host_name_1 = host_name_5;
            elem_0 = elem_4;
            block = 1;
            break;
        }
    }
}

function update_rsync () {
    var v293,v294,v295,v296,v297,v298,v299,elem_7,v300,v301,v302,v303,v304,v305,v306,v307,v308,elem_8,v309,v310,v311,v312,v313,v314,v315,v316,v317,v318,v319,text_0,elem_9,v320,v321,v322,v323,v324;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v294 = __consts_0.Document;
            v295 = v294.getElementById(__consts_0.const_str__33);
            v296 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v297 = v296;
            v298 = (v297==1);
            v299 = v298;
            if (v299 == true)
            {
                v321 = v295;
                block = 5;
                break;
            }
            else{
                elem_7 = v295;
                block = 1;
                break;
            }
            case 1:
            v300 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v301 = ll_char_mul__Char_Signed ( '.',v300 );
            v302 = ll_strconcat__String_String ( __consts_0.const_str__34,v301 );
            v303 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v304 = (v303+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v304;
            v306 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v307 = (v306>5);
            v308 = v307;
            if (v308 == true)
            {
                text_0 = v302;
                elem_9 = elem_7;
                block = 4;
                break;
            }
            else{
                elem_8 = elem_7;
                v309 = v302;
                block = 2;
                break;
            }
            case 2:
            v310 = new StringBuilder();
            v310.ll_append(__consts_0.const_str__35);
            v312 = ll_str__StringR_StringConst_String ( undefined,v309 );
            v310.ll_append(v312);
            v310.ll_append(__consts_0.const_str__36);
            v315 = v310.ll_build();
            v316 = elem_8.childNodes;
            v317 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v316,0 );
            v317.nodeValue = v315;
            setTimeout ( 'update_rsync()',1000 );
            block = 3;
            break;
            case 3:
            return ( v293 );
            case 4:
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            elem_8 = elem_9;
            v309 = text_0;
            block = 2;
            break;
            case 5:
            v322 = v321.childNodes;
            v323 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v322,0 );
            v323.nodeValue = __consts_0.const_str__33;
            block = 3;
            break;
        }
    }
}

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalT (func_0,l_1,index_0) {
    var v122,v123,v124,l_2,index_1,v125,v126,v127,v128,index_2,v129,v130,v131;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v123 = (index_0>=0);
            undefined;
            l_2 = l_1;
            index_1 = index_0;
            block = 1;
            break;
            case 1:
            v125 = l_2;
            v126 = v125.length;
            v127 = (index_1<v126);
            undefined;
            index_2 = index_1;
            v129 = l_2;
            block = 2;
            break;
            case 2:
            v130 = v129;
            v131 = v130[index_2];
            v122 = v131;
            block = 3;
            break;
            case 3:
            return ( v122 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_S (ITER_0,lst_0) {
    var v265,v266,v267,v268;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v266 = new Object();
            v266.iterable = lst_0;
            v266.index = 0;
            v265 = v266;
            block = 1;
            break;
            case 1:
            return ( v265 );
        }
    }
}

function ll_dict_getitem__Dict_String__List_String___String (d_3,key_5) {
    var v334,v335,v336,v337,v338,v339,v340,etype_3,evalue_3,key_6,v341,v342,v343;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v335 = d_3;
            v336 = (v335[key_5]!=undefined);
            v337 = v336;
            if (v337 == true)
            {
                key_6 = key_5;
                v341 = d_3;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v338 = __consts_0.exceptions_KeyError;
            v339 = v338.meta;
            v340 = v338;
            etype_3 = v339;
            evalue_3 = v340;
            block = 2;
            break;
            case 2:
            throw(evalue_3);
            case 3:
            v342 = v341;
            v343 = v342[key_6];
            v334 = v343;
            block = 4;
            break;
            case 4:
            return ( v334 );
        }
    }
}

function hide_host () {
    var v93,v94,v95,elem_5,v96,v97,v98,v99,v100,v101,v102,elem_6,v103,v104,v105,v106;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v94 = __consts_0.Document;
            v95 = v94.getElementById(__consts_0.const_str__31);
            elem_5 = v95;
            block = 1;
            break;
            case 1:
            v96 = elem_5.childNodes;
            v97 = ll_len__List_ExternalType_ ( v96 );
            v98 = !!v97;
            if (v98 == true)
            {
                elem_6 = elem_5;
                block = 4;
                break;
            }
            else{
                v99 = elem_5;
                block = 2;
                break;
            }
            case 2:
            v100 = v99.style;
            v100.visibility = __consts_0.const_str__29;
            __consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__24;
            block = 3;
            break;
            case 3:
            return ( v93 );
            case 4:
            v103 = elem_6;
            v104 = elem_6.childNodes;
            v105 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v104,0 );
            v103.removeChild(v105);
            elem_5 = elem_6;
            block = 1;
            break;
        }
    }
}

function ll_dict_kvi__Dict_String__String__List_String_LlT_ (d_1,LIST_0,func_1) {
    var v250,v251,v252,v253,v254,v255,i_0,it_0,result_0,v256,v257,v258,i_1,it_1,result_1,v259,v260,v261,v262,it_2,result_2,v263,v264;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v251 = d_1;
            v252 = get_dict_len ( v251 );
            v253 = ll_newlist__List_String_LlT_Signed ( undefined,v252 );
            v254 = d_1;
            v255 = dict_items_iterator ( v254 );
            i_0 = 0;
            it_0 = v255;
            result_0 = v253;
            block = 1;
            break;
            case 1:
            v256 = it_0;
            v257 = v256.ll_go_next();
            v258 = v257;
            if (v258 == true)
            {
                i_1 = i_0;
                it_1 = it_0;
                result_1 = result_0;
                block = 3;
                break;
            }
            else{
                v250 = result_0;
                block = 2;
                break;
            }
            case 2:
            return ( v250 );
            case 3:
            v259 = result_1;
            v260 = it_1;
            v261 = v260.ll_current_key();
            v259[i_1]=v261;
            it_2 = it_1;
            result_2 = result_1;
            v263 = i_1;
            block = 4;
            break;
            case 4:
            v264 = (v263+1);
            i_0 = v264;
            it_0 = it_2;
            result_0 = result_2;
            block = 1;
            break;
        }
    }
}

function ll_newdict__Dict_String__List_String__LlT (DICT_0) {
    var v325,v326;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v326 = new Object();
            v325 = v326;
            block = 1;
            break;
            case 1:
            return ( v325 );
        }
    }
}

function exceptions_KeyError () {
}

exceptions_KeyError.prototype.toString = function (){
    return ( '<exceptions_KeyError instance>' );
}

inherits(exceptions_KeyError,exceptions_LookupError);
function ll_strconcat__String_String (obj_0,arg0_0) {
    var v247,v248,v249;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v248 = obj_0;
            v249 = (v248+arg0_0);
            v247 = v249;
            block = 1;
            break;
            case 1:
            return ( v247 );
        }
    }
}

function ll_dict_getitem__Dict_String__String__String (d_2,key_3) {
    var v283,v284,v285,v286,v287,v288,v289,etype_2,evalue_2,key_4,v290,v291,v292;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v284 = d_2;
            v285 = (v284[key_3]!=undefined);
            v286 = v285;
            if (v286 == true)
            {
                key_4 = key_3;
                v290 = d_2;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v287 = __consts_0.exceptions_KeyError;
            v288 = v287.meta;
            v289 = v287;
            etype_2 = v288;
            evalue_2 = v289;
            block = 2;
            break;
            case 2:
            throw(evalue_2);
            case 3:
            v291 = v290;
            v292 = v291[key_4];
            v283 = v292;
            block = 4;
            break;
            case 4:
            return ( v283 );
        }
    }
}

function ll_list_is_true__List_ExternalType_ (l_4) {
    var v327,v328,v329,v330,v331,v332,v333;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v328 = !!l_4;
            v329 = v328;
            if (v329 == true)
            {
                v330 = l_4;
                block = 2;
                break;
            }
            else{
                v327 = v328;
                block = 1;
                break;
            }
            case 1:
            return ( v327 );
            case 2:
            v331 = v330;
            v332 = v331.length;
            v333 = (v332!=0);
            v327 = v333;
            block = 1;
            break;
        }
    }
}

function comeback (msglist_0) {
    var v214,v215,v216,v217,msglist_1,v218,v219,v220,v221,msglist_2,v222,v223,last_exc_value_3,msglist_3,v224,v225,v226,v227,msglist_4,v228,v229,v230,v231,v232,v233,last_exc_value_4,v234,v235,v236,v237,v238,v239,v240;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v215 = ll_len__List_Dict_String__String__ ( msglist_0 );
            v216 = (v215==0);
            v217 = v216;
            if (v217 == true)
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
            v218 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v219 = 0;
            v220 = ll_listslice_startonly__List_Dict_String__String__ ( undefined,v218,v219 );
            v221 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,v220 );
            msglist_2 = msglist_1;
            v222 = v221;
            block = 2;
            break;
            case 2:
            try {
                v223 = ll_listnext__Record_index__Signed__iterable ( v222 );
                msglist_3 = msglist_2;
                v224 = v222;
                v225 = v223;
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
            v226 = process ( v225 );
            v227 = v226;
            if (v227 == true)
            {
                msglist_2 = msglist_3;
                v222 = v224;
                block = 2;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 4:
            return ( v214 );
            case 5:
            v228 = new Array();
            v228.length = 0;
            __consts_0.py____test_rsession_webjs_Globals.opending = v228;
            v231 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,msglist_4 );
            v232 = v231;
            block = 6;
            break;
            case 6:
            try {
                v233 = ll_listnext__Record_index__Signed__iterable ( v232 );
                v234 = v232;
                v235 = v233;
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
            v236 = process ( v235 );
            v237 = v236;
            if (v237 == true)
            {
                v232 = v234;
                block = 6;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 8:
            v238 = __consts_0.ExportedMethods;
            v239 = __consts_0.py____test_rsession_webjs_Globals.osessid;
            v240 = v238.show_all_statuses(v239,comeback);
            block = 4;
            break;
        }
    }
}

function ll_listnext__Record_index__Signed__iterable_0 (iter_0) {
    var v269,v270,v271,v272,v273,v274,v275,iter_1,index_3,l_3,v276,v277,v278,v279,v280,v281,v282,etype_1,evalue_1;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v270 = iter_0.iterable;
            v271 = iter_0.index;
            v272 = v270;
            v273 = v272.length;
            v274 = (v271>=v273);
            v275 = v274;
            if (v275 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_1 = iter_0;
                index_3 = v271;
                l_3 = v270;
                block = 1;
                break;
            }
            case 1:
            v276 = (index_3+1);
            iter_1.index = v276;
            v278 = l_3;
            v279 = v278[index_3];
            v269 = v279;
            block = 2;
            break;
            case 2:
            return ( v269 );
            case 3:
            v280 = __consts_0.exceptions_StopIteration;
            v281 = v280.meta;
            v282 = v280;
            etype_1 = v281;
            evalue_1 = v282;
            block = 4;
            break;
            case 4:
            throw(evalue_1);
        }
    }
}

function ll_listnext__Record_index__Signed__iterable (iter_2) {
    var v391,v392,v393,v394,v395,v396,v397,iter_3,index_4,l_8,v398,v399,v400,v401,v402,v403,v404,etype_4,evalue_4;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v392 = iter_2.iterable;
            v393 = iter_2.index;
            v394 = v392;
            v395 = v394.length;
            v396 = (v393>=v395);
            v397 = v396;
            if (v397 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_3 = iter_2;
                index_4 = v393;
                l_8 = v392;
                block = 1;
                break;
            }
            case 1:
            v398 = (index_4+1);
            iter_3.index = v398;
            v400 = l_8;
            v401 = v400[index_4];
            v391 = v401;
            block = 2;
            break;
            case 2:
            return ( v391 );
            case 3:
            v402 = __consts_0.exceptions_StopIteration;
            v403 = v402.meta;
            v404 = v402;
            etype_4 = v403;
            evalue_4 = v404;
            block = 4;
            break;
            case 4:
            throw(evalue_4);
        }
    }
}

function process (msg_0) {
    var v405,v406,v407,v408,msg_1,v409,v410,v411,v412,v413,v414,v415,msg_2,v416,v417,v418,msg_3,v419,v420,v421,msg_4,v422,v423,v424,msg_5,v425,v426,v427,msg_6,v428,v429,v430,msg_7,v431,v432,v433,v434,v435,v436,v437,v438,v439,v440,v441,v442,v443,msg_8,v444,v445,v446,msg_9,v447,v448,v449,msg_10,module_part_0,v450,v451,v452,v453,v454,v455,v456,v457,v458,v459,v460,v461,v462,v463,v464,v465,v466,v467,v468,msg_11,v469,v470,v471,msg_12,v472,v473,v474,module_part_1,v475,v476,v477,v478,v479,v480,v481,v482,v483,msg_13,v484,v485,v486,v487,v488,v489,v490,v491,v492,v493,v494,v495,v496,v497,v498,v499,v500,v501,v502,v503,v504,v505,v506,v507,v508,v509,v510,v511,v512,v513,v514,v515,v516,v517,v518,v519,v520,v521,v522,msg_14,v523,v524,v525,msg_15,v526,v527,v528,v529,v530,v531,msg_16,v532,v533,v534,v535,v536,v537,v538,v539,v540,v541,v542,v543,v544,v545,v546,v547,v548,v549,v550,msg_17,v551,v552,v553,v554,v555,v556,v557,v558,v559,v560,v561,v562,v563,v564,v565,v566,v567,v568,v569,v570,v571,v572,v573,v574,v575,v576,v577,v578,v579,v580,v581,v582,main_t_0,v583,v584,v585,v586;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v406 = get_dict_len ( msg_0 );
            v407 = (v406==0);
            v408 = v407;
            if (v408 == true)
            {
                v405 = false;
                block = 10;
                break;
            }
            else{
                msg_1 = msg_0;
                block = 1;
                break;
            }
            case 1:
            v409 = __consts_0.Document;
            v410 = v409.getElementById(__consts_0.const_str__38);
            v411 = __consts_0.Document;
            v412 = v411.getElementById(__consts_0.const_str__39);
            v413 = ll_dict_getitem__Dict_String__String__String ( msg_1,__consts_0.const_str__40 );
            v414 = ll_streq__String_String ( v413,__consts_0.const_str__41 );
            v415 = v414;
            if (v415 == true)
            {
                main_t_0 = v412;
                v583 = msg_1;
                block = 25;
                break;
            }
            else{
                msg_2 = msg_1;
                block = 2;
                break;
            }
            case 2:
            v416 = ll_dict_getitem__Dict_String__String__String ( msg_2,__consts_0.const_str__40 );
            v417 = ll_streq__String_String ( v416,__consts_0.const_str__42 );
            v418 = v417;
            if (v418 == true)
            {
                msg_17 = msg_2;
                block = 24;
                break;
            }
            else{
                msg_3 = msg_2;
                block = 3;
                break;
            }
            case 3:
            v419 = ll_dict_getitem__Dict_String__String__String ( msg_3,__consts_0.const_str__40 );
            v420 = ll_streq__String_String ( v419,__consts_0.const_str__43 );
            v421 = v420;
            if (v421 == true)
            {
                msg_16 = msg_3;
                block = 23;
                break;
            }
            else{
                msg_4 = msg_3;
                block = 4;
                break;
            }
            case 4:
            v422 = ll_dict_getitem__Dict_String__String__String ( msg_4,__consts_0.const_str__40 );
            v423 = ll_streq__String_String ( v422,__consts_0.const_str__44 );
            v424 = v423;
            if (v424 == true)
            {
                msg_14 = msg_4;
                block = 20;
                break;
            }
            else{
                msg_5 = msg_4;
                block = 5;
                break;
            }
            case 5:
            v425 = ll_dict_getitem__Dict_String__String__String ( msg_5,__consts_0.const_str__40 );
            v426 = ll_streq__String_String ( v425,__consts_0.const_str__45 );
            v427 = v426;
            if (v427 == true)
            {
                msg_13 = msg_5;
                block = 19;
                break;
            }
            else{
                msg_6 = msg_5;
                block = 6;
                break;
            }
            case 6:
            v428 = ll_dict_getitem__Dict_String__String__String ( msg_6,__consts_0.const_str__40 );
            v429 = ll_streq__String_String ( v428,__consts_0.const_str__46 );
            v430 = v429;
            if (v430 == true)
            {
                msg_11 = msg_6;
                block = 16;
                break;
            }
            else{
                msg_7 = msg_6;
                block = 7;
                break;
            }
            case 7:
            v431 = ll_dict_getitem__Dict_String__String__String ( msg_7,__consts_0.const_str__40 );
            v432 = ll_streq__String_String ( v431,__consts_0.const_str__47 );
            v433 = v432;
            if (v433 == true)
            {
                msg_8 = msg_7;
                block = 13;
                break;
            }
            else{
                v434 = msg_7;
                block = 8;
                break;
            }
            case 8:
            v435 = ll_dict_getitem__Dict_String__String__String ( v434,__consts_0.const_str__40 );
            v436 = ll_streq__String_String ( v435,__consts_0.const_str__48 );
            v437 = v436;
            if (v437 == true)
            {
                block = 12;
                break;
            }
            else{
                block = 9;
                break;
            }
            case 9:
            v438 = __consts_0.py____test_rsession_webjs_Globals.odata_empty;
            v439 = v438;
            if (v439 == true)
            {
                block = 11;
                break;
            }
            else{
                v405 = true;
                block = 10;
                break;
            }
            case 10:
            return ( v405 );
            case 11:
            v440 = __consts_0.Document;
            v441 = v440.getElementById(__consts_0.const_str__12);
            scroll_down_if_needed ( v441 );
            v405 = true;
            block = 10;
            break;
            case 12:
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = true;
            block = 9;
            break;
            case 13:
            v444 = ll_dict_getitem__Dict_String__String__String ( msg_8,__consts_0.const_str__49 );
            v445 = get_elem ( v444 );
            v446 = !!v445;
            if (v446 == true)
            {
                msg_10 = msg_8;
                module_part_0 = v445;
                block = 15;
                break;
            }
            else{
                msg_9 = msg_8;
                block = 14;
                break;
            }
            case 14:
            v447 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v448 = v447;
            ll_append__List_Dict_String__String___Dict_String_ ( v448,msg_9 );
            v405 = true;
            block = 10;
            break;
            case 15:
            v450 = create_elem ( __consts_0.const_str__16 );
            v451 = create_elem ( __consts_0.const_str__17 );
            v452 = ll_dict_getitem__Dict_String__String__String ( msg_10,__consts_0.const_str__50 );
            v453 = new Object();
            v453.item0 = v452;
            v455 = v453.item0;
            v456 = new StringBuilder();
            v456.ll_append(__consts_0.const_str__51);
            v458 = ll_str__StringR_StringConst_String ( undefined,v455 );
            v456.ll_append(v458);
            v456.ll_append(__consts_0.const_str__52);
            v461 = v456.ll_build();
            v462 = create_text_elem ( v461 );
            v463 = v451;
            v463.appendChild(v462);
            v465 = v450;
            v465.appendChild(v451);
            v467 = module_part_0;
            v467.appendChild(v450);
            block = 9;
            break;
            case 16:
            v469 = ll_dict_getitem__Dict_String__String__String ( msg_11,__consts_0.const_str__49 );
            v470 = get_elem ( v469 );
            v471 = !!v470;
            if (v471 == true)
            {
                module_part_1 = v470;
                block = 18;
                break;
            }
            else{
                msg_12 = msg_11;
                block = 17;
                break;
            }
            case 17:
            v472 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v473 = v472;
            ll_append__List_Dict_String__String___Dict_String_ ( v473,msg_12 );
            v405 = true;
            block = 10;
            break;
            case 18:
            v475 = create_elem ( __consts_0.const_str__16 );
            v476 = create_elem ( __consts_0.const_str__17 );
            v477 = create_text_elem ( __consts_0.const_str__53 );
            v478 = v476;
            v478.appendChild(v477);
            v480 = v475;
            v480.appendChild(v476);
            v482 = module_part_1;
            v482.appendChild(v475);
            block = 9;
            break;
            case 19:
            v484 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__54 );
            v485 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__55 );
            v486 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__56 );
            v487 = new Object();
            v487.item0 = v484;
            v487.item1 = v485;
            v487.item2 = v486;
            v491 = v487.item0;
            v492 = v487.item1;
            v493 = v487.item2;
            v494 = new StringBuilder();
            v494.ll_append(__consts_0.const_str__57);
            v496 = ll_str__StringR_StringConst_String ( undefined,v491 );
            v494.ll_append(v496);
            v494.ll_append(__consts_0.const_str__58);
            v499 = ll_str__StringR_StringConst_String ( undefined,v492 );
            v494.ll_append(v499);
            v494.ll_append(__consts_0.const_str__59);
            v502 = ll_str__StringR_StringConst_String ( undefined,v493 );
            v494.ll_append(v502);
            v494.ll_append(__consts_0.const_str__60);
            v505 = v494.ll_build();
            v506 = new StringBuilder();
            v506.ll_append(__consts_0.const_str__61);
            v508 = ll_str__StringR_StringConst_String ( undefined,v505 );
            v506.ll_append(v508);
            v510 = v506.ll_build();
            __consts_0.Document.title = v510;
            v512 = new StringBuilder();
            v512.ll_append(__consts_0.const_str__35);
            v514 = ll_str__StringR_StringConst_String ( undefined,v505 );
            v512.ll_append(v514);
            v512.ll_append(__consts_0.const_str__36);
            v517 = v512.ll_build();
            v518 = __consts_0.Document;
            v519 = v518.getElementById(__consts_0.const_str__33);
            v520 = v519.childNodes;
            v521 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v520,0 );
            v521.nodeValue = v517;
            block = 9;
            break;
            case 20:
            v523 = ll_dict_getitem__Dict_String__String__String ( msg_14,__consts_0.const_str__62 );
            v524 = get_elem ( v523 );
            v525 = !!v524;
            if (v525 == true)
            {
                v529 = msg_14;
                v530 = v524;
                block = 22;
                break;
            }
            else{
                msg_15 = msg_14;
                block = 21;
                break;
            }
            case 21:
            v526 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v527 = v526;
            ll_append__List_Dict_String__String___Dict_String_ ( v527,msg_15 );
            v405 = true;
            block = 10;
            break;
            case 22:
            add_received_item_outcome ( v529,v530 );
            block = 9;
            break;
            case 23:
            v532 = __consts_0.Document;
            v533 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__63 );
            v534 = v532.getElementById(v533);
            v535 = v534.style;
            v535.background = __consts_0.const_str__64;
            v537 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v538 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__63 );
            v539 = ll_dict_getitem__Dict_String__String__String ( v537,v538 );
            v540 = new Object();
            v540.item0 = v539;
            v542 = v540.item0;
            v543 = new StringBuilder();
            v544 = ll_str__StringR_StringConst_String ( undefined,v542 );
            v543.ll_append(v544);
            v543.ll_append(__consts_0.const_str__65);
            v547 = v543.ll_build();
            v548 = v534.childNodes;
            v549 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v548,0 );
            v549.nodeValue = v547;
            block = 9;
            break;
            case 24:
            v551 = __consts_0.Document;
            v552 = ll_dict_getitem__Dict_String__String__String ( msg_17,__consts_0.const_str__63 );
            v553 = v551.getElementById(v552);
            v554 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v555 = ll_dict_getitem__Dict_String__String__String ( msg_17,__consts_0.const_str__63 );
            v556 = ll_dict_getitem__Dict_String__List_String___String ( v554,v555 );
            v557 = v556;
            v558 = ll_dict_getitem__Dict_String__String__String ( msg_17,__consts_0.const_str__49 );
            ll_prepend__List_String__String ( v557,v558 );
            v560 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v561 = ll_dict_getitem__Dict_String__String__String ( msg_17,__consts_0.const_str__63 );
            v562 = ll_dict_getitem__Dict_String__List_String___String ( v560,v561 );
            v563 = ll_len__List_String_ ( v562 );
            v564 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v565 = ll_dict_getitem__Dict_String__String__String ( msg_17,__consts_0.const_str__63 );
            v566 = ll_dict_getitem__Dict_String__String__String ( v564,v565 );
            v567 = new Object();
            v567.item0 = v566;
            v567.item1 = v563;
            v570 = v567.item0;
            v571 = v567.item1;
            v572 = new StringBuilder();
            v573 = ll_str__StringR_StringConst_String ( undefined,v570 );
            v572.ll_append(v573);
            v572.ll_append(__consts_0.const_str__66);
            v576 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v571 );
            v572.ll_append(v576);
            v572.ll_append(__consts_0.const_str__36);
            v579 = v572.ll_build();
            v580 = v553.childNodes;
            v581 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v580,0 );
            v581.nodeValue = v579;
            block = 9;
            break;
            case 25:
            v584 = make_module_box ( v583 );
            v585 = main_t_0;
            v585.appendChild(v584);
            block = 9;
            break;
        }
    }
}

function ll_int_str__IntegerR_SignedConst_Signed (repr_0,i_6) {
    var v782,v783;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v783 = ll_int2dec__Signed ( i_6 );
            v782 = v783;
            block = 1;
            break;
            case 1:
            return ( v782 );
        }
    }
}

function reshow_host () {
    var v344,v345,v346,v347,v348,v349;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v345 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v346 = ll_streq__String_String ( v345,__consts_0.const_str__24 );
            v347 = v346;
            if (v347 == true)
            {
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v348 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v348 );
            block = 2;
            break;
            case 2:
            return ( v344 );
        }
    }
}

function ll_char_mul__Char_Signed (ch_0,times_0) {
    var v350,v351,v352,v353,ch_1,times_1,i_2,buf_0,v354,v355,v356,v357,v358,ch_2,times_2,i_3,buf_1,v359,v360,v361;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v351 = new StringBuilder();
            v352 = v351;
            v352.ll_allocate(times_0);
            ch_1 = ch_0;
            times_1 = times_0;
            i_2 = 0;
            buf_0 = v351;
            block = 1;
            break;
            case 1:
            v354 = (i_2<times_1);
            v355 = v354;
            if (v355 == true)
            {
                ch_2 = ch_1;
                times_2 = times_1;
                i_3 = i_2;
                buf_1 = buf_0;
                block = 4;
                break;
            }
            else{
                v356 = buf_0;
                block = 2;
                break;
            }
            case 2:
            v357 = v356;
            v358 = v357.ll_build();
            v350 = v358;
            block = 3;
            break;
            case 3:
            return ( v350 );
            case 4:
            v359 = buf_1;
            v359.ll_append_char(ch_2);
            v361 = (i_3+1);
            ch_1 = ch_2;
            times_1 = times_2;
            i_2 = v361;
            buf_0 = buf_1;
            block = 1;
            break;
        }
    }
}

function ll_len__List_Dict_String__String__ (l_5) {
    var v366,v367,v368;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v367 = l_5;
            v368 = v367.length;
            v366 = v368;
            block = 1;
            break;
            case 1:
            return ( v366 );
        }
    }
}

function ll_newlist__List_String_LlT_Signed (LIST_1,length_0) {
    var v362,v363,v364,v365;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v363 = new Array();
            v364 = v363;
            v364.length = length_0;
            v362 = v363;
            block = 1;
            break;
            case 1:
            return ( v362 );
        }
    }
}

function ll_len__List_String_ (l_13) {
    var v779,v780,v781;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v780 = l_13;
            v781 = v780.length;
            v779 = v781;
            block = 1;
            break;
            case 1:
            return ( v779 );
        }
    }
}

function ll_prepend__List_String__String (l_10,newitem_1) {
    var v763,v764,v765,v766,v767,v768,l_11,newitem_2,dst_0,v769,v770,newitem_3,v771,v772,v773,l_12,newitem_4,dst_1,v774,v775,v776,v777,v778;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v764 = l_10;
            v765 = v764.length;
            v766 = l_10;
            v767 = (v765+1);
            v766.length = v767;
            l_11 = l_10;
            newitem_2 = newitem_1;
            dst_0 = v765;
            block = 1;
            break;
            case 1:
            v769 = (dst_0>0);
            v770 = v769;
            if (v770 == true)
            {
                l_12 = l_11;
                newitem_4 = newitem_2;
                dst_1 = dst_0;
                block = 4;
                break;
            }
            else{
                newitem_3 = newitem_2;
                v771 = l_11;
                block = 2;
                break;
            }
            case 2:
            v772 = v771;
            v772[0]=newitem_3;
            block = 3;
            break;
            case 3:
            return ( v763 );
            case 4:
            v774 = (dst_1-1);
            v775 = l_12;
            v776 = l_12;
            v777 = v776[v774];
            v775[dst_1]=v777;
            l_11 = l_12;
            newitem_2 = newitem_4;
            dst_0 = v774;
            block = 1;
            break;
        }
    }
}

function ll_listslice_startonly__List_Dict_String__String__ (RESLIST_0,l1_0,start_0) {
    var v369,v370,v371,v372,v373,v374,v375,v376,v377,v378,l1_1,i_4,j_0,l_6,len1_0,v379,v380,l1_2,i_5,j_1,l_7,len1_1,v381,v382,v383,v384,v385,v386;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v370 = l1_0;
            v371 = v370.length;
            v372 = (start_0>=0);
            undefined;
            v374 = (start_0<=v371);
            undefined;
            v376 = (v371-start_0);
            undefined;
            v378 = ll_newlist__List_Dict_String__String__LlT_Signed ( undefined,v376 );
            l1_1 = l1_0;
            i_4 = start_0;
            j_0 = 0;
            l_6 = v378;
            len1_0 = v371;
            block = 1;
            break;
            case 1:
            v379 = (i_4<len1_0);
            v380 = v379;
            if (v380 == true)
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
                v369 = l_6;
                block = 2;
                break;
            }
            case 2:
            return ( v369 );
            case 3:
            v381 = l_7;
            v382 = l1_2;
            v383 = v382[i_5];
            v381[j_1]=v383;
            v385 = (i_5+1);
            v386 = (j_1+1);
            l1_1 = l1_2;
            i_4 = v385;
            j_0 = v386;
            l_6 = l_7;
            len1_0 = len1_1;
            block = 1;
            break;
        }
    }
}

function make_module_box (msg_28) {
    var v784,v785,v786,v787,v788,v789,v790,v791,v792,v793,v794,v795,v796,v797,v798,v799,v800,v801,v802,v803,v804,v805,v806,v807,v808,v809,v810,v811,v812,v813,v814,v815,v816,v817,v818,v819,v820,v821,v822,v823,v824,v825,v826,v827,v828,v829,v830,v831,v832,v833,v834,v835,v836,v837,v838,v839,v840,v841,v842,v843;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v785 = create_elem ( __consts_0.const_str__16 );
            v786 = create_elem ( __consts_0.const_str__17 );
            v787 = v785;
            v787.appendChild(v786);
            v789 = v786;
            v790 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__67 );
            v791 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__68 );
            v792 = new Object();
            v792.item0 = v790;
            v792.item1 = v791;
            v795 = v792.item0;
            v796 = v792.item1;
            v797 = new StringBuilder();
            v798 = ll_str__StringR_StringConst_String ( undefined,v795 );
            v797.ll_append(v798);
            v797.ll_append(__consts_0.const_str__69);
            v801 = ll_str__StringR_StringConst_String ( undefined,v796 );
            v797.ll_append(v801);
            v797.ll_append(__consts_0.const_str__36);
            v804 = v797.ll_build();
            v805 = create_text_elem ( v804 );
            v789.appendChild(v805);
            v807 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__68 );
            v808 = ll_int__String_Signed ( v807,10 );
            v809 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__49 );
            __consts_0.const_tuple__70[v809]=v808;
            v811 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__67 );
            v812 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__49 );
            __consts_0.const_tuple__71[v812]=v811;
            v814 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__49 );
            v815 = ll_strconcat__String_String ( __consts_0.const_str__72,v814 );
            v786.id = v815;
            v817 = v786;
            v818 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__49 );
            v819 = new Object();
            v819.item0 = v818;
            v821 = v819.item0;
            v822 = new StringBuilder();
            v822.ll_append(__consts_0.const_str__73);
            v824 = ll_str__StringR_StringConst_String ( undefined,v821 );
            v822.ll_append(v824);
            v822.ll_append(__consts_0.const_str__20);
            v827 = v822.ll_build();
            v817.setAttribute(__consts_0.const_str__21,v827);
            v829 = v786;
            v829.setAttribute(__consts_0.const_str__22,__consts_0.const_str__74);
            v831 = create_elem ( __consts_0.const_str__17 );
            v832 = v785;
            v832.appendChild(v831);
            v834 = create_elem ( __consts_0.const_str__75 );
            v835 = v831;
            v835.appendChild(v834);
            v837 = create_elem ( __consts_0.const_str__32 );
            v838 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__49 );
            v837.id = v838;
            v840 = v834;
            v840.appendChild(v837);
            v842 = ll_dict_getitem__Dict_String__String__String ( msg_28,__consts_0.const_str__49 );
            __consts_0.const_tuple__76[v842]=0;
            v784 = v785;
            block = 1;
            break;
            case 1:
            return ( v784 );
        }
    }
}

function ll_int2dec__Signed (i_7) {
    var v844,v845;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v845 = i_7.toString();
            v844 = v845;
            block = 1;
            break;
            case 1:
            return ( v844 );
        }
    }
}

function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions_StopIteration instance>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
function scroll_down_if_needed (mbox_2) {
    var v597,v598,v599,v600,v601,v602,v603,v604,v605,v606;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v598 = __consts_0.Window.scrollMaxY;
            v599 = __consts_0.Window.scrollY;
            v600 = (v598-v599);
            v601 = (v600<50);
            v602 = v601;
            if (v602 == true)
            {
                v603 = mbox_2;
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            return ( v597 );
            case 2:
            v604 = v603.parentNode;
            v605 = v604;
            v605.scrollIntoView();
            block = 1;
            break;
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_D (ITER_1,lst_1) {
    var v387,v388,v389,v390;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v388 = new Object();
            v388.iterable = lst_1;
            v388.index = 0;
            v387 = v388;
            block = 1;
            break;
            case 1:
            return ( v387 );
        }
    }
}

function ll_append__List_Dict_String__String___Dict_String_ (l_9,newitem_0) {
    var v607,v608,v609,v610,v611,v612,v613,v614;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v608 = l_9;
            v609 = v608.length;
            v610 = l_9;
            v611 = (v609+1);
            v610.length = v611;
            v613 = l_9;
            v613[v609]=newitem_0;
            block = 1;
            break;
            case 1:
            return ( v607 );
        }
    }
}

function add_received_item_outcome (msg_18,module_part_2) {
    var v615,v616,v617,v618,msg_19,module_part_3,v619,v620,v621,v622,v623,v624,v625,v626,v627,v628,v629,v630,v631,v632,v633,v634,v635,v636,v637,msg_20,module_part_4,item_name_6,td_0,v638,v639,v640,v641,msg_21,module_part_5,item_name_7,td_1,v642,v643,v644,v645,v646,v647,v648,v649,v650,v651,v652,v653,v654,v655,v656,v657,v658,v659,v660,v661,msg_22,module_part_6,td_2,v662,v663,v664,v665,v666,module_part_7,td_3,v667,v668,v669,v670,v671,v672,v673,v674,v675,v676,v677,v678,v679,v680,v681,v682,v683,v684,v685,v686,v687,v688,v689,v690,v691,v692,v693,v694,v695,v696,v697,v698,v699,v700,v701,msg_23,module_part_8,td_4,v702,v703,v704,msg_24,module_part_9,item_name_8,td_5,v705,v706,v707,v708,msg_25,module_part_10,item_name_9,td_6,v709,v710,v711,v712,v713,v714,v715,v716,v717,v718,v719,v720,v721,v722,v723,v724,v725,v726,v727,v728,msg_26,module_part_11,td_7,v729,v730,v731,msg_27,module_part_12,v732,v733,v734,v735,v736,v737,v738,v739,v740,v741,v742,v743,v744,v745,v746,v747,v748,v749,v750,v751,v752,v753,v754,v755,v756,v757,v758,v759,v760,v761,v762;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v616 = ll_dict_getitem__Dict_String__String__String ( msg_18,__consts_0.const_str__63 );
            v617 = ll_strlen__String ( v616 );
            v618 = !!v617;
            if (v618 == true)
            {
                msg_27 = msg_18;
                module_part_12 = module_part_2;
                block = 11;
                break;
            }
            else{
                msg_19 = msg_18;
                module_part_3 = module_part_2;
                block = 1;
                break;
            }
            case 1:
            v619 = create_elem ( __consts_0.const_str__17 );
            v620 = v619;
            v621 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__49 );
            v622 = new Object();
            v622.item0 = v621;
            v624 = v622.item0;
            v625 = new StringBuilder();
            v625.ll_append(__consts_0.const_str__73);
            v627 = ll_str__StringR_StringConst_String ( undefined,v624 );
            v625.ll_append(v627);
            v625.ll_append(__consts_0.const_str__20);
            v630 = v625.ll_build();
            v620.setAttribute(__consts_0.const_str__21,v630);
            v632 = v619;
            v632.setAttribute(__consts_0.const_str__22,__consts_0.const_str__74);
            v634 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__49 );
            v635 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__78 );
            v636 = ll_streq__String_String ( v635,__consts_0.const_str__79 );
            v637 = v636;
            if (v637 == true)
            {
                msg_26 = msg_19;
                module_part_11 = module_part_3;
                td_7 = v619;
                block = 10;
                break;
            }
            else{
                msg_20 = msg_19;
                module_part_4 = module_part_3;
                item_name_6 = v634;
                td_0 = v619;
                block = 2;
                break;
            }
            case 2:
            v638 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__80 );
            v639 = ll_streq__String_String ( v638,__consts_0.const_str__81 );
            v640 = !v639;
            v641 = v640;
            if (v641 == true)
            {
                msg_24 = msg_20;
                module_part_9 = module_part_4;
                item_name_8 = item_name_6;
                td_5 = td_0;
                block = 8;
                break;
            }
            else{
                msg_21 = msg_20;
                module_part_5 = module_part_4;
                item_name_7 = item_name_6;
                td_1 = td_0;
                block = 3;
                break;
            }
            case 3:
            v642 = create_elem ( __consts_0.const_str__82 );
            v643 = v642;
            v644 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__49 );
            v645 = new Object();
            v645.item0 = v644;
            v647 = v645.item0;
            v648 = new StringBuilder();
            v648.ll_append(__consts_0.const_str__83);
            v650 = ll_str__StringR_StringConst_String ( undefined,v647 );
            v648.ll_append(v650);
            v648.ll_append(__consts_0.const_str__20);
            v653 = v648.ll_build();
            v643.setAttribute(__consts_0.const_str__84,v653);
            v655 = create_text_elem ( __consts_0.const_str__85 );
            v656 = v642;
            v656.appendChild(v655);
            v658 = td_1;
            v658.appendChild(v642);
            v660 = __consts_0.ExportedMethods;
            v661 = v660.show_fail(item_name_7,fail_come_back);
            msg_22 = msg_21;
            module_part_6 = module_part_5;
            td_2 = td_1;
            block = 4;
            break;
            case 4:
            v662 = ll_dict_getitem__Dict_String__String__String ( msg_22,__consts_0.const_str__62 );
            v663 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__76,v662 );
            v664 = (v663%50);
            v665 = (v664==0);
            v666 = v665;
            if (v666 == true)
            {
                msg_23 = msg_22;
                module_part_8 = module_part_6;
                td_4 = td_2;
                block = 7;
                break;
            }
            else{
                module_part_7 = module_part_6;
                td_3 = td_2;
                v667 = msg_22;
                block = 5;
                break;
            }
            case 5:
            v668 = ll_dict_getitem__Dict_String__String__String ( v667,__consts_0.const_str__62 );
            v669 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__76,v668 );
            v670 = (v669+1);
            __consts_0.const_tuple__76[v668]=v670;
            v672 = ll_strconcat__String_String ( __consts_0.const_str__72,v668 );
            v673 = get_elem ( v672 );
            v674 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__71,v668 );
            v675 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__76,v668 );
            v676 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__70,v668 );
            v677 = new Object();
            v677.item0 = v674;
            v677.item1 = v675;
            v677.item2 = v676;
            v681 = v677.item0;
            v682 = v677.item1;
            v683 = v677.item2;
            v684 = new StringBuilder();
            v685 = ll_str__StringR_StringConst_String ( undefined,v681 );
            v684.ll_append(v685);
            v684.ll_append(__consts_0.const_str__66);
            v688 = v682.toString();
            v684.ll_append(v688);
            v684.ll_append(__consts_0.const_str__86);
            v691 = v683.toString();
            v684.ll_append(v691);
            v684.ll_append(__consts_0.const_str__36);
            v694 = v684.ll_build();
            v695 = v673.childNodes;
            v696 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v695,0 );
            v696.nodeValue = v694;
            v698 = module_part_7.childNodes;
            v699 = ll_getitem__dum_nocheckConst_List_ExternalType__Si ( undefined,v698,-1 );
            v700 = v699;
            v700.appendChild(td_3);
            block = 6;
            break;
            case 6:
            return ( v615 );
            case 7:
            v702 = create_elem ( __consts_0.const_str__16 );
            v703 = module_part_8;
            v703.appendChild(v702);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v667 = msg_23;
            block = 5;
            break;
            case 8:
            v705 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__80 );
            v706 = ll_streq__String_String ( v705,__consts_0.const_str__87 );
            v707 = !v706;
            v708 = v707;
            if (v708 == true)
            {
                msg_25 = msg_24;
                module_part_10 = module_part_9;
                item_name_9 = item_name_8;
                td_6 = td_5;
                block = 9;
                break;
            }
            else{
                msg_21 = msg_24;
                module_part_5 = module_part_9;
                item_name_7 = item_name_8;
                td_1 = td_5;
                block = 3;
                break;
            }
            case 9:
            v709 = __consts_0.ExportedMethods;
            v710 = v709.show_skip(item_name_9,skip_come_back);
            v711 = create_elem ( __consts_0.const_str__82 );
            v712 = v711;
            v713 = ll_dict_getitem__Dict_String__String__String ( msg_25,__consts_0.const_str__49 );
            v714 = new Object();
            v714.item0 = v713;
            v716 = v714.item0;
            v717 = new StringBuilder();
            v717.ll_append(__consts_0.const_str__88);
            v719 = ll_str__StringR_StringConst_String ( undefined,v716 );
            v717.ll_append(v719);
            v717.ll_append(__consts_0.const_str__20);
            v722 = v717.ll_build();
            v712.setAttribute(__consts_0.const_str__84,v722);
            v724 = create_text_elem ( __consts_0.const_str__89 );
            v725 = v711;
            v725.appendChild(v724);
            v727 = td_6;
            v727.appendChild(v711);
            msg_22 = msg_25;
            module_part_6 = module_part_10;
            td_2 = td_6;
            block = 4;
            break;
            case 10:
            v729 = create_text_elem ( __consts_0.const_str__90 );
            v730 = td_7;
            v730.appendChild(v729);
            msg_22 = msg_26;
            module_part_6 = module_part_11;
            td_2 = td_7;
            block = 4;
            break;
            case 11:
            v732 = __consts_0.Document;
            v733 = ll_dict_getitem__Dict_String__String__String ( msg_27,__consts_0.const_str__63 );
            v734 = v732.getElementById(v733);
            v735 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v736 = ll_dict_getitem__Dict_String__String__String ( msg_27,__consts_0.const_str__63 );
            v737 = ll_dict_getitem__Dict_String__List_String___String ( v735,v736 );
            v738 = v737;
            v739 = ll_pop_default__dum_nocheckConst_List_String_ ( undefined,v738 );
            v740 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v741 = ll_dict_getitem__Dict_String__String__String ( msg_27,__consts_0.const_str__63 );
            v742 = ll_dict_getitem__Dict_String__List_String___String ( v740,v741 );
            v743 = ll_len__List_String_ ( v742 );
            v744 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v745 = ll_dict_getitem__Dict_String__String__String ( msg_27,__consts_0.const_str__63 );
            v746 = ll_dict_getitem__Dict_String__String__String ( v744,v745 );
            v747 = new Object();
            v747.item0 = v746;
            v747.item1 = v743;
            v750 = v747.item0;
            v751 = v747.item1;
            v752 = new StringBuilder();
            v753 = ll_str__StringR_StringConst_String ( undefined,v750 );
            v752.ll_append(v753);
            v752.ll_append(__consts_0.const_str__66);
            v756 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v751 );
            v752.ll_append(v756);
            v752.ll_append(__consts_0.const_str__36);
            v759 = v752.ll_build();
            v760 = v734.childNodes;
            v761 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v760,0 );
            v761.nodeValue = v759;
            msg_19 = msg_27;
            module_part_3 = module_part_12;
            block = 1;
            break;
        }
    }
}

function ll_streq__String_String (s1_0,s2_0) {
    var v587,v588,v589,v590,s2_1,v591,v592,v593,v594,v595,v596;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v588 = !!s1_0;
            v589 = !v588;
            v590 = v589;
            if (v590 == true)
            {
                v594 = s2_0;
                block = 3;
                break;
            }
            else{
                s2_1 = s2_0;
                v591 = s1_0;
                block = 1;
                break;
            }
            case 1:
            v592 = v591;
            v593 = (v592==s2_1);
            v587 = v593;
            block = 2;
            break;
            case 2:
            return ( v587 );
            case 3:
            v595 = !!v594;
            v596 = !v595;
            v587 = v596;
            block = 2;
            break;
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed (self_1,length_1) {
    var v846,v847;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v847 = ll_newlist__List_Dict_String__String__LlT_Signed_0 ( undefined,length_1 );
            v846 = v847;
            block = 1;
            break;
            case 1:
            return ( v846 );
        }
    }
}

function skip_come_back (msg_30) {
    var v973,v974,v975,v976;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v974 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__50 );
            v975 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__91 );
            __consts_0.const_tuple__30[v975]=v974;
            block = 1;
            break;
            case 1:
            return ( v973 );
        }
    }
}

function ll_pop_default__dum_nocheckConst_List_String_ (func_3,l_17) {
    var v977,v978,v979,l_18,length_4,v980,v981,v982,v983,v984,v985,res_0,newlength_0,v986,v987,v988;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v978 = l_17;
            v979 = v978.length;
            l_18 = l_17;
            length_4 = v979;
            block = 1;
            break;
            case 1:
            v980 = (length_4>0);
            undefined;
            v982 = (length_4-1);
            v983 = l_18;
            v984 = v983[v982];
            ll_null_item__List_String_ ( l_18 );
            res_0 = v984;
            newlength_0 = v982;
            v986 = l_18;
            block = 2;
            break;
            case 2:
            v987 = v986;
            v987.length = newlength_0;
            v977 = res_0;
            block = 3;
            break;
            case 3:
            return ( v977 );
        }
    }
}

function ll_strlen__String (obj_1) {
    var v936,v937,v938;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v937 = obj_1;
            v938 = v937.length;
            v936 = v938;
            block = 1;
            break;
            case 1:
            return ( v936 );
        }
    }
}

function ll_int__String_Signed (s_2,base_0) {
    var v848,v849,v850,v851,v852,v853,etype_5,evalue_5,s_3,base_1,v854,s_4,base_2,v855,v856,s_5,base_3,v857,v858,s_6,base_4,i_8,strlen_0,v859,v860,s_7,base_5,i_9,strlen_1,v861,v862,v863,v864,v865,s_8,base_6,i_10,strlen_2,v866,v867,v868,v869,s_9,base_7,i_11,strlen_3,v870,v871,v872,v873,s_10,base_8,val_0,i_12,sign_0,strlen_4,v874,v875,s_11,val_1,i_13,sign_1,strlen_5,v876,v877,val_2,sign_2,v878,v879,v880,v881,v882,v883,v884,v885,v886,v887,s_12,val_3,i_14,sign_3,strlen_6,v888,v889,v890,v891,s_13,val_4,sign_4,strlen_7,v892,v893,s_14,base_9,val_5,i_15,sign_5,strlen_8,v894,v895,v896,v897,v898,s_15,base_10,c_0,val_6,i_16,sign_6,strlen_9,v899,v900,s_16,base_11,c_1,val_7,i_17,sign_7,strlen_10,v901,v902,s_17,base_12,c_2,val_8,i_18,sign_8,strlen_11,v903,s_18,base_13,c_3,val_9,i_19,sign_9,strlen_12,v904,v905,s_19,base_14,val_10,i_20,sign_10,strlen_13,v906,v907,s_20,base_15,val_11,i_21,digit_0,sign_11,strlen_14,v908,v909,s_21,base_16,i_22,digit_1,sign_12,strlen_15,v910,v911,v912,v913,s_22,base_17,c_4,val_12,i_23,sign_13,strlen_16,v914,s_23,base_18,c_5,val_13,i_24,sign_14,strlen_17,v915,v916,s_24,base_19,val_14,i_25,sign_15,strlen_18,v917,v918,v919,s_25,base_20,c_6,val_15,i_26,sign_16,strlen_19,v920,s_26,base_21,c_7,val_16,i_27,sign_17,strlen_20,v921,v922,s_27,base_22,val_17,i_28,sign_18,strlen_21,v923,v924,v925,s_28,base_23,strlen_22,v926,v927,s_29,base_24,strlen_23,v928,v929,s_30,base_25,i_29,strlen_24,v930,v931,v932,v933,s_31,base_26,strlen_25,v934,v935;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v849 = (2<=base_0);
            v850 = v849;
            if (v850 == true)
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
            v851 = __consts_0.exceptions_ValueError;
            v852 = v851.meta;
            v853 = v851;
            etype_5 = v852;
            evalue_5 = v853;
            block = 2;
            break;
            case 2:
            throw(evalue_5);
            case 3:
            v854 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v855 = v854;
            block = 4;
            break;
            case 4:
            v856 = v855;
            if (v856 == true)
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
            v857 = s_5;
            v858 = v857.length;
            s_6 = s_5;
            base_4 = base_3;
            i_8 = 0;
            strlen_0 = v858;
            block = 6;
            break;
            case 6:
            v859 = (i_8<strlen_0);
            v860 = v859;
            if (v860 == true)
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
            v861 = (i_9<strlen_1);
            v862 = v861;
            if (v862 == true)
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
            v863 = __consts_0.exceptions_ValueError;
            v864 = v863.meta;
            v865 = v863;
            etype_5 = v864;
            evalue_5 = v865;
            block = 2;
            break;
            case 9:
            v866 = s_8;
            v867 = v866[i_10];
            v868 = (v867=='-');
            v869 = v868;
            if (v869 == true)
            {
                s_29 = s_8;
                base_24 = base_6;
                strlen_23 = strlen_2;
                v928 = i_10;
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
            v870 = s_9;
            v871 = v870[i_11];
            v872 = (v871=='+');
            v873 = v872;
            if (v873 == true)
            {
                s_28 = s_9;
                base_23 = base_7;
                strlen_22 = strlen_3;
                v926 = i_11;
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
            v874 = (i_12<strlen_4);
            v875 = v874;
            if (v875 == true)
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
            v876 = (i_13<strlen_5);
            v877 = v876;
            if (v877 == true)
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
                v878 = i_13;
                v879 = strlen_5;
                block = 13;
                break;
            }
            case 13:
            v880 = (v878==v879);
            v881 = v880;
            if (v881 == true)
            {
                v885 = sign_2;
                v886 = val_2;
                block = 15;
                break;
            }
            else{
                block = 14;
                break;
            }
            case 14:
            v882 = __consts_0.exceptions_ValueError;
            v883 = v882.meta;
            v884 = v882;
            etype_5 = v883;
            evalue_5 = v884;
            block = 2;
            break;
            case 15:
            v887 = (v885*v886);
            v848 = v887;
            block = 16;
            break;
            case 16:
            return ( v848 );
            case 17:
            v888 = s_12;
            v889 = v888[i_14];
            v890 = (v889==' ');
            v891 = v890;
            if (v891 == true)
            {
                s_13 = s_12;
                val_4 = val_3;
                sign_4 = sign_3;
                strlen_7 = strlen_6;
                v892 = i_14;
                block = 18;
                break;
            }
            else{
                val_2 = val_3;
                sign_2 = sign_3;
                v878 = i_14;
                v879 = strlen_6;
                block = 13;
                break;
            }
            case 18:
            v893 = (v892+1);
            s_11 = s_13;
            val_1 = val_4;
            i_13 = v893;
            sign_1 = sign_4;
            strlen_5 = strlen_7;
            block = 12;
            break;
            case 19:
            v894 = s_14;
            v895 = v894[i_15];
            v896 = v895.charCodeAt(0);
            v897 = (97<=v896);
            v898 = v897;
            if (v898 == true)
            {
                s_25 = s_14;
                base_20 = base_9;
                c_6 = v896;
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
                c_0 = v896;
                val_6 = val_5;
                i_16 = i_15;
                sign_6 = sign_5;
                strlen_9 = strlen_8;
                block = 20;
                break;
            }
            case 20:
            v899 = (65<=c_0);
            v900 = v899;
            if (v900 == true)
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
            v901 = (48<=c_1);
            v902 = v901;
            if (v902 == true)
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
            v903 = (c_2<=57);
            s_18 = s_17;
            base_13 = base_12;
            c_3 = c_2;
            val_9 = val_8;
            i_19 = i_18;
            sign_9 = sign_8;
            strlen_12 = strlen_11;
            v904 = v903;
            block = 23;
            break;
            case 23:
            v905 = v904;
            if (v905 == true)
            {
                s_19 = s_18;
                base_14 = base_13;
                val_10 = val_9;
                i_20 = i_19;
                sign_10 = sign_9;
                strlen_13 = strlen_12;
                v906 = c_3;
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
            v907 = (v906-48);
            s_20 = s_19;
            base_15 = base_14;
            val_11 = val_10;
            i_21 = i_20;
            digit_0 = v907;
            sign_11 = sign_10;
            strlen_14 = strlen_13;
            block = 25;
            break;
            case 25:
            v908 = (digit_0>=base_15);
            v909 = v908;
            if (v909 == true)
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
                v910 = val_11;
                block = 26;
                break;
            }
            case 26:
            v911 = (v910*base_16);
            v912 = (v911+digit_1);
            v913 = (i_22+1);
            s_10 = s_21;
            base_8 = base_16;
            val_0 = v912;
            i_12 = v913;
            sign_0 = sign_12;
            strlen_4 = strlen_15;
            block = 11;
            break;
            case 27:
            v914 = (c_4<=90);
            s_23 = s_22;
            base_18 = base_17;
            c_5 = c_4;
            val_13 = val_12;
            i_24 = i_23;
            sign_14 = sign_13;
            strlen_17 = strlen_16;
            v915 = v914;
            block = 28;
            break;
            case 28:
            v916 = v915;
            if (v916 == true)
            {
                s_24 = s_23;
                base_19 = base_18;
                val_14 = val_13;
                i_25 = i_24;
                sign_15 = sign_14;
                strlen_18 = strlen_17;
                v917 = c_5;
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
            v918 = (v917-65);
            v919 = (v918+10);
            s_20 = s_24;
            base_15 = base_19;
            val_11 = val_14;
            i_21 = i_25;
            digit_0 = v919;
            sign_11 = sign_15;
            strlen_14 = strlen_18;
            block = 25;
            break;
            case 30:
            v920 = (c_6<=122);
            s_26 = s_25;
            base_21 = base_20;
            c_7 = c_6;
            val_16 = val_15;
            i_27 = i_26;
            sign_17 = sign_16;
            strlen_20 = strlen_19;
            v921 = v920;
            block = 31;
            break;
            case 31:
            v922 = v921;
            if (v922 == true)
            {
                s_27 = s_26;
                base_22 = base_21;
                val_17 = val_16;
                i_28 = i_27;
                sign_18 = sign_17;
                strlen_21 = strlen_20;
                v923 = c_7;
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
            v924 = (v923-97);
            v925 = (v924+10);
            s_20 = s_27;
            base_15 = base_22;
            val_11 = val_17;
            i_21 = i_28;
            digit_0 = v925;
            sign_11 = sign_18;
            strlen_14 = strlen_21;
            block = 25;
            break;
            case 33:
            v927 = (v926+1);
            s_10 = s_28;
            base_8 = base_23;
            val_0 = 0;
            i_12 = v927;
            sign_0 = 1;
            strlen_4 = strlen_22;
            block = 11;
            break;
            case 34:
            v929 = (v928+1);
            s_10 = s_29;
            base_8 = base_24;
            val_0 = 0;
            i_12 = v929;
            sign_0 = -1;
            strlen_4 = strlen_23;
            block = 11;
            break;
            case 35:
            v930 = s_30;
            v931 = v930[i_29];
            v932 = (v931==' ');
            v933 = v932;
            if (v933 == true)
            {
                s_31 = s_30;
                base_26 = base_25;
                strlen_25 = strlen_24;
                v934 = i_29;
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
            v935 = (v934+1);
            s_6 = s_31;
            base_4 = base_26;
            i_8 = v935;
            strlen_0 = strlen_25;
            block = 6;
            break;
        }
    }
}

function fail_come_back (msg_29) {
    var v939,v940,v941,v942,v943,v944,v945,v946,v947,v948;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v940 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__93 );
            v941 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__94 );
            v942 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__95 );
            v943 = new Object();
            v943.item0 = v940;
            v943.item1 = v941;
            v943.item2 = v942;
            v947 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__91 );
            __consts_0.const_tuple[v947]=v943;
            block = 1;
            break;
            case 1:
            return ( v939 );
        }
    }
}

function ll_null_item__List_String_ (lst_2) {
    var v993,v994;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            undefined;
            block = 1;
            break;
            case 1:
            return ( v993 );
        }
    }
}

function ll_dict_getitem__Dict_String__Signed__String (d_4,key_7) {
    var v949,v950,v951,v952,v953,v954,v955,etype_6,evalue_6,key_8,v956,v957,v958;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v950 = d_4;
            v951 = (v950[key_7]!=undefined);
            v952 = v951;
            if (v952 == true)
            {
                key_8 = key_7;
                v956 = d_4;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v953 = __consts_0.exceptions_KeyError;
            v954 = v953.meta;
            v955 = v953;
            etype_6 = v954;
            evalue_6 = v955;
            block = 2;
            break;
            case 2:
            throw(evalue_6);
            case 3:
            v957 = v956;
            v958 = v957[key_8];
            v949 = v958;
            block = 4;
            break;
            case 4:
            return ( v949 );
        }
    }
}

function ll_getitem__dum_nocheckConst_List_ExternalType__Si (func_2,l_14,index_5) {
    var v959,v960,v961,v962,v963,l_15,index_6,length_2,v964,v965,v966,v967,index_7,v968,v969,v970,l_16,length_3,v971,v972;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v960 = l_14;
            v961 = v960.length;
            v962 = (index_5<0);
            v963 = v962;
            if (v963 == true)
            {
                l_16 = l_14;
                length_3 = v961;
                v971 = index_5;
                block = 4;
                break;
            }
            else{
                l_15 = l_14;
                index_6 = index_5;
                length_2 = v961;
                block = 1;
                break;
            }
            case 1:
            v964 = (index_6>=0);
            undefined;
            v966 = (index_6<length_2);
            undefined;
            index_7 = index_6;
            v968 = l_15;
            block = 2;
            break;
            case 2:
            v969 = v968;
            v970 = v969[index_7];
            v959 = v970;
            block = 3;
            break;
            case 3:
            return ( v959 );
            case 4:
            v972 = (v971+length_3);
            l_15 = l_16;
            index_6 = v972;
            length_2 = length_3;
            block = 1;
            break;
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed_0 (LIST_2,length_5) {
    var v989,v990,v991,v992;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v990 = new Array();
            v991 = v990;
            v991.length = length_5;
            v989 = v990;
            block = 1;
            break;
            case 1:
            return ( v989 );
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
function exceptions_LookupError_meta () {
}

exceptions_LookupError_meta.prototype.toString = function (){
    return ( '<exceptions_LookupError_meta instance>' );
}

inherits(exceptions_LookupError_meta,exceptions_StandardError_meta);
function exceptions_ValueError_meta () {
}

exceptions_ValueError_meta.prototype.toString = function (){
    return ( '<exceptions_ValueError_meta instance>' );
}

inherits(exceptions_ValueError_meta,exceptions_StandardError_meta);
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
__consts_0.const_str__59 = ' failures, ';
__consts_0.const_str__19 = "show_host('";
__consts_0.const_str__72 = '_txt_';
__consts_0.exceptions_ValueError__97 = exceptions_ValueError;
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.const_str__82 = 'a';
__consts_0.const_str__36 = ']';
__consts_0.const_str__44 = 'ReceivedItemOutcome';
__consts_0.const_str__73 = "show_info('";
__consts_0.const_str__51 = '- skipped (';
__consts_0.const_str__23 = 'hide_host()';
__consts_0.const_str__74 = 'hide_info()';
__consts_0.const_str__14 = '#message';
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__32 = 'tbody';
__consts_0.const_tuple = {};
__consts_0.const_str__52 = ')';
__consts_0.const_str__39 = 'main_table';
__consts_0.exceptions_KeyError__101 = exceptions_KeyError;
__consts_0.const_str__20 = "')";
__consts_0.const_str__48 = 'RsyncFinished';
__consts_0.Window = window;
__consts_0.const_str__58 = ' run, ';
__consts_0.const_str__94 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_tuple__70 = {};
__consts_0.const_str__43 = 'HostReady';
__consts_0.const_str__57 = 'FINISHED ';
__consts_0.const_str__34 = 'Rsyncing';
__consts_0.const_str__2 = 'info';
__consts_0.const_tuple__25 = undefined;
__consts_0.const_str__29 = 'hidden';
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.const_str__85 = 'F';
__consts_0.const_str__22 = 'onmouseout';
__consts_0.const_str__40 = 'type';
__consts_0.const_str__78 = 'passed';
__consts_0.const_str__90 = '.';
__consts_0.const_str__46 = 'FailedTryiter';
__consts_0.py____test_rsession_webjs_Globals__104 = py____test_rsession_webjs_Globals;
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.const_tuple__27 = undefined;
__consts_0.const_list__103 = [];
__consts_0.const_str__24 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.const_str__18 = '#ff0000';
__consts_0.const_str__12 = 'messagebox';
__consts_0.const_str__49 = 'fullitemname';
__consts_0.const_str__75 = 'table';
__consts_0.const_str__61 = 'Py.test ';
__consts_0.const_str__56 = 'skips';
__consts_0.exceptions_StopIteration__99 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_str__10 = '\n';
__consts_0.const_str__13 = 'pre';
__consts_0.const_str__8 = '\n======== Stdout: ========\n';
__consts_0.const_str__64 = '#00ff00';
__consts_0.const_str__4 = 'beige';
__consts_0.const_str__68 = 'length';
__consts_0.const_tuple__30 = {};
__consts_0.const_str__93 = 'traceback';
__consts_0.const_str__38 = 'testmain';
__consts_0.const_str__88 = "javascript:show_skip('";
__consts_0.const_str__66 = '[';
__consts_0.const_str__50 = 'reason';
__consts_0.const_str__83 = "javascript:show_traceback('";
__consts_0.const_str__33 = 'Tests';
__consts_0.const_str__89 = 's';
__consts_0.const_str__54 = 'run';
__consts_0.const_str__47 = 'SkippedTryiter';
__consts_0.const_str__81 = 'None';
__consts_0.const_str__79 = 'True';
__consts_0.const_str__86 = '/';
__consts_0.const_str__63 = 'hostkey';
__consts_0.const_str__55 = 'fails';
__consts_0.const_str__41 = 'ItemStart';
__consts_0.const_str__67 = 'itemname';
__consts_0.const_str__45 = 'TestFinished';
__consts_0.const_str__31 = 'jobs';
__consts_0.const_str__9 = '\n========== Stderr: ==========\n';
__consts_0.const_str__60 = ' skipped';
__consts_0.const_str__95 = 'stderr';
__consts_0.const_str__84 = 'href';
__consts_0.const_tuple__71 = {};
__consts_0.const_str__3 = 'visible';
__consts_0.const_str__87 = 'False';
__consts_0.const_str__21 = 'onmouseover';
__consts_0.const_str__53 = '- FAILED TO LOAD MODULE';
__consts_0.const_str__69 = '[0/';
__consts_0.const_list = undefined;
__consts_0.const_str__42 = 'SendItem';
__consts_0.const_str__62 = 'fullmodulename';
__consts_0.const_str__80 = 'skipped';
__consts_0.const_str__15 = 'hostsbody';
__consts_0.const_str__65 = '[0]';
__consts_0.const_str__17 = 'td';
__consts_0.const_str__7 = '====== Traceback: =========\n';
__consts_0.const_str__16 = 'tr';
__consts_0.const_str__91 = 'item_name';
__consts_0.const_str__35 = 'Tests [';
__consts_0.Document = document;
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.const_tuple__76 = {};
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__97;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__101;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__104;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__24;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__24;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple__25;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__103;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__27;
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__99;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
