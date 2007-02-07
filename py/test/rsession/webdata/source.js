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
            v33.ll_append(__consts_0.const_str__2);
            v35 = ll_str__StringR_StringConst_String ( undefined,v30 );
            v33.ll_append(v35);
            v33.ll_append(__consts_0.const_str__3);
            v38 = ll_str__StringR_StringConst_String ( undefined,v31 );
            v33.ll_append(v38);
            v33.ll_append(__consts_0.const_str__4);
            v41 = ll_str__StringR_StringConst_String ( undefined,v32 );
            v33.ll_append(v41);
            v33.ll_append(__consts_0.const_str__5);
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
            v66 = v65.getElementById(__consts_0.const_str__7);
            v67 = v66.style;
            v67.visibility = __consts_0.const_str__8;
            block = 1;
            break;
            case 1:
            return ( v64 );
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
            v22 = v21.getElementById(__consts_0.const_str__11);
            v23 = v22;
            v23.setAttribute(__consts_0.const_str__12,__consts_0.const_str__13);
            block = 1;
            break;
            case 1:
            return ( v14 );
        }
    }
}

function sessid_comeback (id_0) {
    var v206,v207,v208,v209;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.osessid = id_0;
            v208 = __consts_0.ExportedMethods;
            v209 = v208.show_all_statuses(id_0,comeback);
            block = 1;
            break;
            case 1:
            return ( v206 );
        }
    }
}

function show_skip (item_name_0) {
    var v25,v26,v27;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v26 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__14,item_name_0 );
            set_msgbox ( item_name_0,v26 );
            block = 1;
            break;
            case 1:
            return ( v25 );
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

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__16;
    this.ohost = __consts_0.const_str__16;
    this.orsync_dots = 0;
    this.ofinished = false;
    this.ohost_dict = __consts_0.const_tuple__17;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__19;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals instance>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
function hide_messagebox () {
    var v114,v115,v116,mbox_0,v117,v118,mbox_1,v119,v120,v121,v122;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v115 = __consts_0.Document;
            v116 = v115.getElementById(__consts_0.const_str__20);
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

function show_info (data_0) {
    var v46,v47,v48,v49,v50,data_1,info_0,v51,v52,v53,info_1,v54,v55,v56,v57,v58,v59,data_2,info_2,v60,v61,v62,v63;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v47 = __consts_0.Document;
            v48 = v47.getElementById(__consts_0.const_str__7);
            v49 = v48.style;
            v49.visibility = __consts_0.const_str__21;
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
            v58.backgroundColor = __consts_0.const_str__22;
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

function comeback (msglist_0) {
    var v226,v227,v228,v229,msglist_1,v230,v231,v232,v233,msglist_2,v234,v235,last_exc_value_3,msglist_3,v236,v237,v238,v239,msglist_4,v240,v241,v242,v243,v244,v245,last_exc_value_4,v246,v247,v248,v249,v250,v251,v252;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v227 = ll_len__List_Dict_String__String__ ( msglist_0 );
            v228 = (v227==0);
            v229 = v228;
            if (v229 == true)
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
            v230 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v231 = 0;
            v232 = ll_listslice_startonly__List_Dict_String__String__ ( undefined,v230,v231 );
            v233 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,v232 );
            msglist_2 = msglist_1;
            v234 = v233;
            block = 2;
            break;
            case 2:
            try {
                v235 = ll_listnext__Record_index__Signed__iterable ( v234 );
                msglist_3 = msglist_2;
                v236 = v234;
                v237 = v235;
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
            v238 = process ( v237 );
            v239 = v238;
            if (v239 == true)
            {
                msglist_2 = msglist_3;
                v234 = v236;
                block = 2;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 4:
            return ( v226 );
            case 5:
            v240 = new Array();
            v240.length = 0;
            __consts_0.py____test_rsession_webjs_Globals.opending = v240;
            v243 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,msglist_4 );
            v244 = v243;
            block = 6;
            break;
            case 6:
            try {
                v245 = ll_listnext__Record_index__Signed__iterable ( v244 );
                v246 = v244;
                v247 = v245;
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
            v248 = process ( v247 );
            v249 = v248;
            if (v249 == true)
            {
                v244 = v246;
                block = 6;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 8:
            v250 = __consts_0.ExportedMethods;
            v251 = __consts_0.py____test_rsession_webjs_Globals.osessid;
            v252 = v250.show_all_statuses(v251,comeback);
            block = 4;
            break;
        }
    }
}

function ll_list_is_true__List_ExternalType_ (l_0) {
    var v263,v264,v265,v266,v267,v268,v269;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v264 = !!l_0;
            v265 = v264;
            if (v265 == true)
            {
                v266 = l_0;
                block = 2;
                break;
            }
            else{
                v263 = v264;
                block = 1;
                break;
            }
            case 1:
            return ( v263 );
            case 2:
            v267 = v266;
            v268 = v267.length;
            v269 = (v268!=0);
            v263 = v269;
            block = 1;
            break;
        }
    }
}

function host_init (host_dict_0) {
    var v158,v159,v160,v161,v162,v163,host_dict_1,tbody_3,v164,v165,last_exc_value_1,host_dict_2,tbody_4,host_0,v166,v167,v168,v169,v170,v171,v172,v173,v174,v175,v176,v177,v178,v179,v180,v181,v182,v183,v184,v185,v186,v187,v188,v189,v190,v191,v192,host_dict_3,v193,v194,v195,v196,v197,v198,v199,v200,last_exc_value_2,key_2,v201,v202,v203,v204,v205;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v159 = __consts_0.Document;
            v160 = v159.getElementById(__consts_0.const_str__23);
            v161 = host_dict_0;
            v162 = ll_dict_kvi__Dict_String__String__List_String_LlT_ ( v161,undefined,undefined );
            v163 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v162 );
            host_dict_1 = host_dict_0;
            tbody_3 = v160;
            v164 = v163;
            block = 1;
            break;
            case 1:
            try {
                v165 = ll_listnext__Record_index__Signed__iterable_0 ( v164 );
                host_dict_2 = host_dict_1;
                tbody_4 = tbody_3;
                host_0 = v165;
                v166 = v164;
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
            v167 = create_elem ( __consts_0.const_str__24 );
            v168 = tbody_4;
            v168.appendChild(v167);
            v170 = create_elem ( __consts_0.const_str__25 );
            v171 = v170.style;
            v171.background = __consts_0.const_str__26;
            v173 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v174 = create_text_elem ( v173 );
            v175 = v170;
            v175.appendChild(v174);
            v170.id = host_0;
            v178 = v167;
            v178.appendChild(v170);
            v180 = v170;
            v181 = new StringBuilder();
            v181.ll_append(__consts_0.const_str__27);
            v183 = ll_str__StringR_StringConst_String ( undefined,host_0 );
            v181.ll_append(v183);
            v181.ll_append(__consts_0.const_str__28);
            v186 = v181.ll_build();
            v180.setAttribute(__consts_0.const_str__29,v186);
            v188 = v170;
            v188.setAttribute(__consts_0.const_str__30,__consts_0.const_str__31);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            __consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
            setTimeout ( 'update_rsync()',1000 );
            host_dict_1 = host_dict_2;
            tbody_3 = tbody_4;
            v164 = v166;
            block = 1;
            break;
            case 3:
            __consts_0.py____test_rsession_webjs_Globals.ohost_dict = host_dict_3;
            v194 = ll_newdict__Dict_String__List_String__LlT ( undefined );
            __consts_0.py____test_rsession_webjs_Globals.ohost_pending = v194;
            v196 = host_dict_3;
            v197 = ll_dict_kvi__Dict_String__String__List_String_LlT_ ( v196,undefined,undefined );
            v198 = ll_listiter__Record_index__Signed__iterable_List_S ( undefined,v197 );
            v199 = v198;
            block = 4;
            break;
            case 4:
            try {
                v200 = ll_listnext__Record_index__Signed__iterable_0 ( v199 );
                key_2 = v200;
                v201 = v199;
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
            v202 = new Array();
            v202.length = 0;
            v204 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v204[key_2]=v202;
            v199 = v201;
            block = 4;
            break;
            case 6:
            return ( v158 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_S (ITER_1,lst_1) {
    var v531,v532,v533,v534;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v532 = new Object();
            v532.iterable = lst_1;
            v532.index = 0;
            v531 = v532;
            block = 1;
            break;
            case 1:
            return ( v531 );
        }
    }
}

function process (msg_0) {
    var v325,v326,v327,v328,msg_1,v329,v330,v331,v332,v333,v334,v335,msg_2,v336,v337,v338,msg_3,v339,v340,v341,msg_4,v342,v343,v344,msg_5,v345,v346,v347,msg_6,v348,v349,v350,msg_7,v351,v352,v353,msg_8,v354,v355,v356,msg_9,v357,v358,v359,v360,v361,v362,v363,v364,v365,v366,v367,v368,v369,v370,v371,msg_10,v372,v373,v374,msg_11,v375,v376,v377,msg_12,module_part_0,v378,v379,v380,v381,v382,v383,v384,v385,v386,v387,v388,v389,v390,v391,v392,v393,v394,v395,v396,msg_13,v397,v398,v399,msg_14,v400,v401,v402,module_part_1,v403,v404,v405,v406,v407,v408,v409,v410,v411,msg_15,v412,v413,v414,v415,v416,v417,v418,v419,v420,v421,v422,v423,v424,v425,v426,v427,v428,v429,v430,v431,v432,v433,v434,v435,v436,v437,v438,v439,v440,v441,v442,v443,v444,v445,v446,v447,v448,v449,v450,v451,msg_16,v452,v453,v454,msg_17,v455,v456,v457,v458,v459,v460,msg_18,v461,v462,v463,v464,v465,v466,v467,v468,v469,v470,v471,v472,v473,v474,v475,v476,v477,v478,v479,msg_19,v480,v481,v482,v483,v484,v485,v486,v487,v488,v489,v490,v491,v492,v493,v494,v495,v496,v497,v498,v499,v500,v501,v502,v503,v504,v505,v506,v507,v508,v509,v510,v511,main_t_0,v512,v513,v514,v515;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v326 = get_dict_len ( msg_0 );
            v327 = (v326==0);
            v328 = v327;
            if (v328 == true)
            {
                v325 = false;
                block = 12;
                break;
            }
            else{
                msg_1 = msg_0;
                block = 1;
                break;
            }
            case 1:
            v329 = __consts_0.Document;
            v330 = v329.getElementById(__consts_0.const_str__32);
            v331 = __consts_0.Document;
            v332 = v331.getElementById(__consts_0.const_str__33);
            v333 = ll_dict_getitem__Dict_String__String__String ( msg_1,__consts_0.const_str__34 );
            v334 = ll_streq__String_String ( v333,__consts_0.const_str__35 );
            v335 = v334;
            if (v335 == true)
            {
                main_t_0 = v332;
                v512 = msg_1;
                block = 29;
                break;
            }
            else{
                msg_2 = msg_1;
                block = 2;
                break;
            }
            case 2:
            v336 = ll_dict_getitem__Dict_String__String__String ( msg_2,__consts_0.const_str__34 );
            v337 = ll_streq__String_String ( v336,__consts_0.const_str__36 );
            v338 = v337;
            if (v338 == true)
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
            v339 = ll_dict_getitem__Dict_String__String__String ( msg_3,__consts_0.const_str__34 );
            v340 = ll_streq__String_String ( v339,__consts_0.const_str__37 );
            v341 = v340;
            if (v341 == true)
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
            v342 = ll_dict_getitem__Dict_String__String__String ( msg_4,__consts_0.const_str__34 );
            v343 = ll_streq__String_String ( v342,__consts_0.const_str__38 );
            v344 = v343;
            if (v344 == true)
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
            v345 = ll_dict_getitem__Dict_String__String__String ( msg_5,__consts_0.const_str__34 );
            v346 = ll_streq__String_String ( v345,__consts_0.const_str__39 );
            v347 = v346;
            if (v347 == true)
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
            v348 = ll_dict_getitem__Dict_String__String__String ( msg_6,__consts_0.const_str__34 );
            v349 = ll_streq__String_String ( v348,__consts_0.const_str__40 );
            v350 = v349;
            if (v350 == true)
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
            v351 = ll_dict_getitem__Dict_String__String__String ( msg_7,__consts_0.const_str__34 );
            v352 = ll_streq__String_String ( v351,__consts_0.const_str__41 );
            v353 = v352;
            if (v353 == true)
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
            v354 = ll_dict_getitem__Dict_String__String__String ( msg_8,__consts_0.const_str__34 );
            v355 = ll_streq__String_String ( v354,__consts_0.const_str__42 );
            v356 = v355;
            if (v356 == true)
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
            v357 = ll_dict_getitem__Dict_String__String__String ( msg_9,__consts_0.const_str__34 );
            v358 = ll_streq__String_String ( v357,__consts_0.const_str__43 );
            v359 = v358;
            if (v359 == true)
            {
                block = 15;
                break;
            }
            else{
                v360 = msg_9;
                block = 10;
                break;
            }
            case 10:
            v361 = ll_dict_getitem__Dict_String__String__String ( v360,__consts_0.const_str__34 );
            v362 = ll_streq__String_String ( v361,__consts_0.const_str__44 );
            v363 = v362;
            if (v363 == true)
            {
                block = 14;
                break;
            }
            else{
                block = 11;
                break;
            }
            case 11:
            v364 = __consts_0.py____test_rsession_webjs_Globals.odata_empty;
            v365 = v364;
            if (v365 == true)
            {
                block = 13;
                break;
            }
            else{
                v325 = true;
                block = 12;
                break;
            }
            case 12:
            return ( v325 );
            case 13:
            v366 = __consts_0.Document;
            v367 = v366.getElementById(__consts_0.const_str__20);
            scroll_down_if_needed ( v367 );
            v325 = true;
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
            v372 = ll_dict_getitem__Dict_String__String__String ( msg_10,__consts_0.const_str__45 );
            v373 = get_elem ( v372 );
            v374 = !!v373;
            if (v374 == true)
            {
                msg_12 = msg_10;
                module_part_0 = v373;
                block = 19;
                break;
            }
            else{
                msg_11 = msg_10;
                block = 18;
                break;
            }
            case 18:
            v375 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v376 = v375;
            ll_append__List_Dict_String__String___Dict_String_ ( v376,msg_11 );
            v325 = true;
            block = 12;
            break;
            case 19:
            v378 = create_elem ( __consts_0.const_str__24 );
            v379 = create_elem ( __consts_0.const_str__25 );
            v380 = ll_dict_getitem__Dict_String__String__String ( msg_12,__consts_0.const_str__46 );
            v381 = new Object();
            v381.item0 = v380;
            v383 = v381.item0;
            v384 = new StringBuilder();
            v384.ll_append(__consts_0.const_str__47);
            v386 = ll_str__StringR_StringConst_String ( undefined,v383 );
            v384.ll_append(v386);
            v384.ll_append(__consts_0.const_str__48);
            v389 = v384.ll_build();
            v390 = create_text_elem ( v389 );
            v391 = v379;
            v391.appendChild(v390);
            v393 = v378;
            v393.appendChild(v379);
            v395 = module_part_0;
            v395.appendChild(v378);
            block = 11;
            break;
            case 20:
            v397 = ll_dict_getitem__Dict_String__String__String ( msg_13,__consts_0.const_str__45 );
            v398 = get_elem ( v397 );
            v399 = !!v398;
            if (v399 == true)
            {
                module_part_1 = v398;
                block = 22;
                break;
            }
            else{
                msg_14 = msg_13;
                block = 21;
                break;
            }
            case 21:
            v400 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v401 = v400;
            ll_append__List_Dict_String__String___Dict_String_ ( v401,msg_14 );
            v325 = true;
            block = 12;
            break;
            case 22:
            v403 = create_elem ( __consts_0.const_str__24 );
            v404 = create_elem ( __consts_0.const_str__25 );
            v405 = create_text_elem ( __consts_0.const_str__49 );
            v406 = v404;
            v406.appendChild(v405);
            v408 = v403;
            v408.appendChild(v404);
            v410 = module_part_1;
            v410.appendChild(v403);
            block = 11;
            break;
            case 23:
            v412 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__50 );
            v413 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__51 );
            v414 = ll_dict_getitem__Dict_String__String__String ( msg_15,__consts_0.const_str__52 );
            v415 = new Object();
            v415.item0 = v412;
            v415.item1 = v413;
            v415.item2 = v414;
            v419 = v415.item0;
            v420 = v415.item1;
            v421 = v415.item2;
            v422 = new StringBuilder();
            v422.ll_append(__consts_0.const_str__53);
            v424 = ll_str__StringR_StringConst_String ( undefined,v419 );
            v422.ll_append(v424);
            v422.ll_append(__consts_0.const_str__54);
            v427 = ll_str__StringR_StringConst_String ( undefined,v420 );
            v422.ll_append(v427);
            v422.ll_append(__consts_0.const_str__55);
            v430 = ll_str__StringR_StringConst_String ( undefined,v421 );
            v422.ll_append(v430);
            v422.ll_append(__consts_0.const_str__56);
            v433 = v422.ll_build();
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            v435 = new StringBuilder();
            v435.ll_append(__consts_0.const_str__57);
            v437 = ll_str__StringR_StringConst_String ( undefined,v433 );
            v435.ll_append(v437);
            v439 = v435.ll_build();
            __consts_0.Document.title = v439;
            v441 = new StringBuilder();
            v441.ll_append(__consts_0.const_str__58);
            v443 = ll_str__StringR_StringConst_String ( undefined,v433 );
            v441.ll_append(v443);
            v441.ll_append(__consts_0.const_str__59);
            v446 = v441.ll_build();
            v447 = __consts_0.Document;
            v448 = v447.getElementById(__consts_0.const_str__60);
            v449 = v448.childNodes;
            v450 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v449,0 );
            v450.nodeValue = v446;
            block = 11;
            break;
            case 24:
            v452 = ll_dict_getitem__Dict_String__String__String ( msg_16,__consts_0.const_str__61 );
            v453 = get_elem ( v452 );
            v454 = !!v453;
            if (v454 == true)
            {
                v458 = msg_16;
                v459 = v453;
                block = 26;
                break;
            }
            else{
                msg_17 = msg_16;
                block = 25;
                break;
            }
            case 25:
            v455 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v456 = v455;
            ll_append__List_Dict_String__String___Dict_String_ ( v456,msg_17 );
            v325 = true;
            block = 12;
            break;
            case 26:
            add_received_item_outcome ( v458,v459 );
            block = 11;
            break;
            case 27:
            v461 = __consts_0.Document;
            v462 = ll_dict_getitem__Dict_String__String__String ( msg_18,__consts_0.const_str__62 );
            v463 = v461.getElementById(v462);
            v464 = v463.style;
            v464.background = __consts_0.const_str__63;
            v466 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v467 = ll_dict_getitem__Dict_String__String__String ( msg_18,__consts_0.const_str__62 );
            v468 = ll_dict_getitem__Dict_String__String__String ( v466,v467 );
            v469 = new Object();
            v469.item0 = v468;
            v471 = v469.item0;
            v472 = new StringBuilder();
            v473 = ll_str__StringR_StringConst_String ( undefined,v471 );
            v472.ll_append(v473);
            v472.ll_append(__consts_0.const_str__64);
            v476 = v472.ll_build();
            v477 = v463.childNodes;
            v478 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v477,0 );
            v478.nodeValue = v476;
            block = 11;
            break;
            case 28:
            v480 = __consts_0.Document;
            v481 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__62 );
            v482 = v480.getElementById(v481);
            v483 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v484 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__62 );
            v485 = ll_dict_getitem__Dict_String__List_String___String ( v483,v484 );
            v486 = v485;
            v487 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__45 );
            ll_prepend__List_String__String ( v486,v487 );
            v489 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v490 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__62 );
            v491 = ll_dict_getitem__Dict_String__List_String___String ( v489,v490 );
            v492 = ll_len__List_String_ ( v491 );
            v493 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v494 = ll_dict_getitem__Dict_String__String__String ( msg_19,__consts_0.const_str__62 );
            v495 = ll_dict_getitem__Dict_String__String__String ( v493,v494 );
            v496 = new Object();
            v496.item0 = v495;
            v496.item1 = v492;
            v499 = v496.item0;
            v500 = v496.item1;
            v501 = new StringBuilder();
            v502 = ll_str__StringR_StringConst_String ( undefined,v499 );
            v501.ll_append(v502);
            v501.ll_append(__consts_0.const_str__65);
            v505 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v500 );
            v501.ll_append(v505);
            v501.ll_append(__consts_0.const_str__59);
            v508 = v501.ll_build();
            v509 = v482.childNodes;
            v510 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v509,0 );
            v510.nodeValue = v508;
            block = 11;
            break;
            case 29:
            v513 = make_module_box ( v512 );
            v514 = main_t_0;
            v514.appendChild(v513);
            block = 11;
            break;
        }
    }
}

function ll_str__StringR_StringConst_String (self_0,s_0) {
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

function ll_dict_getitem__Dict_String__List_String___String (d_3,key_6) {
    var v782,v783,v784,v785,v786,v787,v788,etype_4,evalue_4,key_7,v789,v790,v791;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v783 = d_3;
            v784 = (v783[key_6]!=undefined);
            v785 = v784;
            if (v785 == true)
            {
                key_7 = key_6;
                v789 = d_3;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v786 = __consts_0.exceptions_KeyError;
            v787 = v786.meta;
            v788 = v786;
            etype_4 = v787;
            evalue_4 = v788;
            block = 2;
            break;
            case 2:
            throw(evalue_4);
            case 3:
            v790 = v789;
            v791 = v790[key_7];
            v782 = v791;
            block = 4;
            break;
            case 4:
            return ( v782 );
        }
    }
}

function scroll_down_if_needed (mbox_2) {
    var v598,v599,v600,v601,v602,v603,v604;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v599 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v600 = v599;
            if (v600 == true)
            {
                v601 = mbox_2;
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            return ( v598 );
            case 2:
            v602 = v601.parentNode;
            v603 = v602;
            v603.scrollIntoView();
            block = 1;
            break;
        }
    }
}

function ll_len__List_ExternalType_ (l_3) {
    var v280,v281,v282;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v281 = l_3;
            v282 = v281.length;
            v280 = v282;
            block = 1;
            break;
            case 1:
            return ( v280 );
        }
    }
}

function show_interrupt () {
    var v613,v614,v615,v616,v617,v618,v619,v620;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__67;
            v616 = __consts_0.Document;
            v617 = v616.getElementById(__consts_0.const_str__60);
            v618 = v617.childNodes;
            v619 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v618,0 );
            v619.nodeValue = __consts_0.const_str__68;
            block = 1;
            break;
            case 1:
            return ( v613 );
        }
    }
}

function ll_len__List_String_ (l_13) {
    var v808,v809,v810;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v809 = l_13;
            v810 = v809.length;
            v808 = v810;
            block = 1;
            break;
            case 1:
            return ( v808 );
        }
    }
}

function create_text_elem (txt_0) {
    var v283,v284,v285;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v284 = __consts_0.Document;
            v285 = v284.createTextNode(txt_0);
            v283 = v285;
            block = 1;
            break;
            case 1:
            return ( v283 );
        }
    }
}

function ll_listnext__Record_index__Signed__iterable (iter_0) {
    var v311,v312,v313,v314,v315,v316,v317,iter_1,index_3,l_7,v318,v319,v320,v321,v322,v323,v324,etype_2,evalue_2;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v312 = iter_0.iterable;
            v313 = iter_0.index;
            v314 = v312;
            v315 = v314.length;
            v316 = (v313>=v315);
            v317 = v316;
            if (v317 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_1 = iter_0;
                index_3 = v313;
                l_7 = v312;
                block = 1;
                break;
            }
            case 1:
            v318 = (index_3+1);
            iter_1.index = v318;
            v320 = l_7;
            v321 = v320[index_3];
            v311 = v321;
            block = 2;
            break;
            case 2:
            return ( v311 );
            case 3:
            v322 = __consts_0.exceptions_StopIteration;
            v323 = v322.meta;
            v324 = v322;
            etype_2 = v323;
            evalue_2 = v324;
            block = 4;
            break;
            case 4:
            throw(evalue_2);
        }
    }
}

function set_msgbox (item_name_2,data_3) {
    var v139,v140,item_name_3,data_4,msgbox_0,v141,v142,v143,item_name_4,data_5,msgbox_1,v144,v145,v146,v147,v148,v149,v150,v151,v152,v153,item_name_5,data_6,msgbox_2,v154,v155,v156,v157;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v140 = get_elem ( __consts_0.const_str__20 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v140;
            block = 1;
            break;
            case 1:
            v141 = msgbox_0.childNodes;
            v142 = ll_len__List_ExternalType_ ( v141 );
            v143 = !!v142;
            if (v143 == true)
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
            v144 = create_elem ( __consts_0.const_str__70 );
            v145 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__5 );
            v146 = ll_strconcat__String_String ( v145,data_5 );
            v147 = create_text_elem ( v146 );
            v148 = v144;
            v148.appendChild(v147);
            v150 = msgbox_1;
            v150.appendChild(v144);
            __consts_0.Document.location = __consts_0.const_str__71;
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 3:
            return ( v139 );
            case 4:
            v154 = msgbox_2;
            v155 = msgbox_2.childNodes;
            v156 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v155,0 );
            v154.removeChild(v156);
            item_name_3 = item_name_5;
            data_4 = data_6;
            msgbox_0 = msgbox_2;
            block = 1;
            break;
        }
    }
}

function create_elem (s_1) {
    var v549,v550,v551;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v550 = __consts_0.Document;
            v551 = v550.createElement(s_1);
            v549 = v551;
            block = 1;
            break;
            case 1:
            return ( v549 );
        }
    }
}

function show_crash () {
    var v605,v606,v607,v608,v609,v610,v611,v612;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__72;
            v608 = __consts_0.Document;
            v609 = v608.getElementById(__consts_0.const_str__60);
            v610 = v609.childNodes;
            v611 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v610,0 );
            v611.nodeValue = __consts_0.const_str__73;
            block = 1;
            break;
            case 1:
            return ( v605 );
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
function exceptions_KeyError () {
}

exceptions_KeyError.prototype.toString = function (){
    return ( '<exceptions_KeyError instance>' );
}

inherits(exceptions_KeyError,exceptions_LookupError);
function ll_dict_getitem__Dict_String__Record_item2__Str_St (d_0,key_0) {
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

function ll_len__List_Dict_String__String__ (l_4) {
    var v286,v287,v288;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v287 = l_4;
            v288 = v287.length;
            v286 = v288;
            block = 1;
            break;
            case 1:
            return ( v286 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_D (ITER_0,lst_0) {
    var v307,v308,v309,v310;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v308 = new Object();
            v308.iterable = lst_0;
            v308.index = 0;
            v307 = v308;
            block = 1;
            break;
            case 1:
            return ( v307 );
        }
    }
}

function make_module_box (msg_30) {
    var v813,v814,v815,v816,v817,v818,v819,v820,v821,v822,v823,v824,v825,v826,v827,v828,v829,v830,v831,v832,v833,v834,v835,v836,v837,v838,v839,v840,v841,v842,v843,v844,v845,v846,v847,v848,v849,v850,v851,v852,v853,v854,v855,v856,v857,v858,v859,v860,v861,v862,v863,v864,v865,v866,v867,v868,v869,v870,v871,v872;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v814 = create_elem ( __consts_0.const_str__24 );
            v815 = create_elem ( __consts_0.const_str__25 );
            v816 = v814;
            v816.appendChild(v815);
            v818 = v815;
            v819 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__74 );
            v820 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__75 );
            v821 = new Object();
            v821.item0 = v819;
            v821.item1 = v820;
            v824 = v821.item0;
            v825 = v821.item1;
            v826 = new StringBuilder();
            v827 = ll_str__StringR_StringConst_String ( undefined,v824 );
            v826.ll_append(v827);
            v826.ll_append(__consts_0.const_str__76);
            v830 = ll_str__StringR_StringConst_String ( undefined,v825 );
            v826.ll_append(v830);
            v826.ll_append(__consts_0.const_str__59);
            v833 = v826.ll_build();
            v834 = create_text_elem ( v833 );
            v818.appendChild(v834);
            v836 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__75 );
            v837 = ll_int__String_Signed ( v836,10 );
            v838 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__45 );
            __consts_0.const_tuple__77[v838]=v837;
            v840 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__74 );
            v841 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__45 );
            __consts_0.const_tuple__78[v841]=v840;
            v843 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__45 );
            v844 = ll_strconcat__String_String ( __consts_0.const_str__79,v843 );
            v815.id = v844;
            v846 = v815;
            v847 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__45 );
            v848 = new Object();
            v848.item0 = v847;
            v850 = v848.item0;
            v851 = new StringBuilder();
            v851.ll_append(__consts_0.const_str__80);
            v853 = ll_str__StringR_StringConst_String ( undefined,v850 );
            v851.ll_append(v853);
            v851.ll_append(__consts_0.const_str__28);
            v856 = v851.ll_build();
            v846.setAttribute(__consts_0.const_str__29,v856);
            v858 = v815;
            v858.setAttribute(__consts_0.const_str__30,__consts_0.const_str__81);
            v860 = create_elem ( __consts_0.const_str__25 );
            v861 = v814;
            v861.appendChild(v860);
            v863 = create_elem ( __consts_0.const_str__82 );
            v864 = v860;
            v864.appendChild(v863);
            v866 = create_elem ( __consts_0.const_str__83 );
            v867 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__45 );
            v866.id = v867;
            v869 = v863;
            v869.appendChild(v866);
            v871 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__45 );
            __consts_0.const_tuple__84[v871]=0;
            v813 = v814;
            block = 1;
            break;
            case 1:
            return ( v813 );
        }
    }
}

function hide_host () {
    var v100,v101,v102,elem_5,v103,v104,v105,v106,v107,v108,v109,elem_6,v110,v111,v112,v113;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v101 = __consts_0.Document;
            v102 = v101.getElementById(__consts_0.const_str__85);
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
            v107.visibility = __consts_0.const_str__8;
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

function ll_dict_getitem__Dict_String__String__String (d_1,key_4) {
    var v253,v254,v255,v256,v257,v258,v259,etype_1,evalue_1,key_5,v260,v261,v262;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v254 = d_1;
            v255 = (v254[key_4]!=undefined);
            v256 = v255;
            if (v256 == true)
            {
                key_5 = key_4;
                v260 = d_1;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v257 = __consts_0.exceptions_KeyError;
            v258 = v257.meta;
            v259 = v257;
            etype_1 = v258;
            evalue_1 = v259;
            block = 2;
            break;
            case 2:
            throw(evalue_1);
            case 3:
            v261 = v260;
            v262 = v261[key_5];
            v253 = v262;
            block = 4;
            break;
            case 4:
            return ( v253 );
        }
    }
}

function ll_prepend__List_String__String (l_10,newitem_1) {
    var v792,v793,v794,v795,v796,v797,l_11,newitem_2,dst_0,v798,v799,newitem_3,v800,v801,v802,l_12,newitem_4,dst_1,v803,v804,v805,v806,v807;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v793 = l_10;
            v794 = v793.length;
            v795 = l_10;
            v796 = (v794+1);
            v795.length = v796;
            l_11 = l_10;
            newitem_2 = newitem_1;
            dst_0 = v794;
            block = 1;
            break;
            case 1:
            v798 = (dst_0>0);
            v799 = v798;
            if (v799 == true)
            {
                l_12 = l_11;
                newitem_4 = newitem_2;
                dst_1 = dst_0;
                block = 4;
                break;
            }
            else{
                newitem_3 = newitem_2;
                v800 = l_11;
                block = 2;
                break;
            }
            case 2:
            v801 = v800;
            v801[0]=newitem_3;
            block = 3;
            break;
            case 3:
            return ( v792 );
            case 4:
            v803 = (dst_1-1);
            v804 = l_12;
            v805 = l_12;
            v806 = v805[v803];
            v804[dst_1]=v806;
            l_11 = l_12;
            newitem_2 = newitem_4;
            dst_0 = v803;
            block = 1;
            break;
        }
    }
}

function ll_append__List_Dict_String__String___Dict_String_ (l_9,newitem_0) {
    var v624,v625,v626,v627,v628,v629,v630,v631;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v625 = l_9;
            v626 = v625.length;
            v627 = l_9;
            v628 = (v626+1);
            v627.length = v628;
            v630 = l_9;
            v630[v626]=newitem_0;
            block = 1;
            break;
            case 1:
            return ( v624 );
        }
    }
}

function ll_dict_kvi__Dict_String__String__List_String_LlT_ (d_2,LIST_0,func_1) {
    var v516,v517,v518,v519,v520,v521,i_2,it_0,result_0,v522,v523,v524,i_3,it_1,result_1,v525,v526,v527,v528,it_2,result_2,v529,v530;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v517 = d_2;
            v518 = get_dict_len ( v517 );
            v519 = ll_newlist__List_String_LlT_Signed ( undefined,v518 );
            v520 = d_2;
            v521 = dict_items_iterator ( v520 );
            i_2 = 0;
            it_0 = v521;
            result_0 = v519;
            block = 1;
            break;
            case 1:
            v522 = it_0;
            v523 = v522.ll_go_next();
            v524 = v523;
            if (v524 == true)
            {
                i_3 = i_2;
                it_1 = it_0;
                result_1 = result_0;
                block = 3;
                break;
            }
            else{
                v516 = result_0;
                block = 2;
                break;
            }
            case 2:
            return ( v516 );
            case 3:
            v525 = result_1;
            v526 = it_1;
            v527 = v526.ll_current_key();
            v525[i_3]=v527;
            it_2 = it_1;
            result_2 = result_1;
            v529 = i_3;
            block = 4;
            break;
            case 4:
            v530 = (v529+1);
            i_2 = v530;
            it_0 = it_2;
            result_0 = result_2;
            block = 1;
            break;
        }
    }
}

function ll_listslice_startonly__List_Dict_String__String__ (RESLIST_0,l1_0,start_0) {
    var v289,v290,v291,v292,v293,v294,v295,v296,v297,v298,l1_1,i_0,j_0,l_5,len1_0,v299,v300,l1_2,i_1,j_1,l_6,len1_1,v301,v302,v303,v304,v305,v306;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v290 = l1_0;
            v291 = v290.length;
            v292 = (start_0>=0);
            undefined;
            v294 = (start_0<=v291);
            undefined;
            v296 = (v291-start_0);
            undefined;
            v298 = ll_newlist__List_Dict_String__String__LlT_Signed ( undefined,v296 );
            l1_1 = l1_0;
            i_0 = start_0;
            j_0 = 0;
            l_5 = v298;
            len1_0 = v291;
            block = 1;
            break;
            case 1:
            v299 = (i_0<len1_0);
            v300 = v299;
            if (v300 == true)
            {
                l1_2 = l1_1;
                i_1 = i_0;
                j_1 = j_0;
                l_6 = l_5;
                len1_1 = len1_0;
                block = 3;
                break;
            }
            else{
                v289 = l_5;
                block = 2;
                break;
            }
            case 2:
            return ( v289 );
            case 3:
            v301 = l_6;
            v302 = l1_2;
            v303 = v302[i_1];
            v301[j_1]=v303;
            v305 = (i_1+1);
            v306 = (j_1+1);
            l1_1 = l1_2;
            i_0 = v305;
            j_0 = v306;
            l_5 = l_6;
            len1_0 = len1_1;
            block = 1;
            break;
        }
    }
}

function get_elem (el_0) {
    var v621,v622,v623;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v622 = __consts_0.Document;
            v623 = v622.getElementById(el_0);
            v621 = v623;
            block = 1;
            break;
            case 1:
            return ( v621 );
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
            v71 = v70.getElementById(__consts_0.const_str__85);
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
            v74 = create_elem ( __consts_0.const_str__83 );
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
            v81 = create_elem ( __consts_0.const_str__24 );
            v82 = create_elem ( __consts_0.const_str__25 );
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
            v92.visibility = __consts_0.const_str__21;
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
    var v970,v971,v972,v973,v974,v975;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v971 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v972 = ll_streq__String_String ( v971,__consts_0.const_str__16 );
            v973 = v972;
            if (v973 == true)
            {
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v974 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v974 );
            block = 2;
            break;
            case 2:
            return ( v970 );
        }
    }
}

function key_pressed (key_3) {
    var v210,v211,v212,v213,v214,v215,v216,v217,v218,v219,v220,v221,v222,v223,v224,v225;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v211 = key_3.charCode;
            v212 = (v211==115);
            v213 = v212;
            if (v213 == true)
            {
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            return ( v210 );
            case 2:
            v214 = __consts_0.Document;
            v215 = v214.getElementById(__consts_0.const_str__11);
            v216 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v217 = v216;
            if (v217 == true)
            {
                v222 = v215;
                block = 4;
                break;
            }
            else{
                v218 = v215;
                block = 3;
                break;
            }
            case 3:
            v219 = v218;
            v219.setAttribute(__consts_0.const_str__12,__consts_0.const_str__86);
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 1;
            break;
            case 4:
            v223 = v222;
            v223.removeAttribute(__consts_0.const_str__12);
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 1;
            break;
        }
    }
}

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalT (func_0,l_1,index_0) {
    var v270,v271,v272,l_2,index_1,v273,v274,v275,v276,index_2,v277,v278,v279;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v271 = (index_0>=0);
            undefined;
            l_2 = l_1;
            index_1 = index_0;
            block = 1;
            break;
            case 1:
            v273 = l_2;
            v274 = v273.length;
            v275 = (index_1<v274);
            undefined;
            index_2 = index_1;
            v277 = l_2;
            block = 2;
            break;
            case 2:
            v278 = v277;
            v279 = v278[index_2];
            v270 = v279;
            block = 3;
            break;
            case 3:
            return ( v270 );
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
function ll_listnext__Record_index__Signed__iterable_0 (iter_2) {
    var v535,v536,v537,v538,v539,v540,v541,iter_3,index_4,l_8,v542,v543,v544,v545,v546,v547,v548,etype_3,evalue_3;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v536 = iter_2.iterable;
            v537 = iter_2.index;
            v538 = v536;
            v539 = v538.length;
            v540 = (v537>=v539);
            v541 = v540;
            if (v541 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_3 = iter_2;
                index_4 = v537;
                l_8 = v536;
                block = 1;
                break;
            }
            case 1:
            v542 = (index_4+1);
            iter_3.index = v542;
            v544 = l_8;
            v545 = v544[index_4];
            v535 = v545;
            block = 2;
            break;
            case 2:
            return ( v535 );
            case 3:
            v546 = __consts_0.exceptions_StopIteration;
            v547 = v546.meta;
            v548 = v546;
            etype_3 = v547;
            evalue_3 = v548;
            block = 4;
            break;
            case 4:
            throw(evalue_3);
        }
    }
}

function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions_StopIteration instance>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
function ll_newlist__List_Dict_String__String__LlT_Signed (self_1,length_1) {
    var v968,v969;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v969 = ll_newlist__List_Dict_String__String__LlT_Signed_0 ( undefined,length_1 );
            v968 = v969;
            block = 1;
            break;
            case 1:
            return ( v968 );
        }
    }
}

function update_rsync () {
    var v552,v553,v554,v555,v556,v557,v558,v559,v560,elem_7,v561,v562,v563,v564,v565,v566,v567,v568,v569,elem_8,v570,v571,v572,v573,v574,v575,v576,v577,v578,v579,v580,text_0,elem_9,v581,v582,v583,v584,v585;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v553 = __consts_0.py____test_rsession_webjs_Globals.ofinished;
            v554 = v553;
            if (v554 == true)
            {
                block = 4;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v555 = __consts_0.Document;
            v556 = v555.getElementById(__consts_0.const_str__60);
            v557 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v558 = v557;
            v559 = (v558==1);
            v560 = v559;
            if (v560 == true)
            {
                v582 = v556;
                block = 6;
                break;
            }
            else{
                elem_7 = v556;
                block = 2;
                break;
            }
            case 2:
            v561 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v562 = ll_char_mul__Char_Signed ( '.',v561 );
            v563 = ll_strconcat__String_String ( __consts_0.const_str__87,v562 );
            v564 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v565 = (v564+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v565;
            v567 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v568 = (v567>5);
            v569 = v568;
            if (v569 == true)
            {
                text_0 = v563;
                elem_9 = elem_7;
                block = 5;
                break;
            }
            else{
                elem_8 = elem_7;
                v570 = v563;
                block = 3;
                break;
            }
            case 3:
            v571 = new StringBuilder();
            v571.ll_append(__consts_0.const_str__58);
            v573 = ll_str__StringR_StringConst_String ( undefined,v570 );
            v571.ll_append(v573);
            v571.ll_append(__consts_0.const_str__59);
            v576 = v571.ll_build();
            v577 = elem_8.childNodes;
            v578 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v577,0 );
            v578.nodeValue = v576;
            setTimeout ( 'update_rsync()',1000 );
            block = 4;
            break;
            case 4:
            return ( v552 );
            case 5:
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            elem_8 = elem_9;
            v570 = text_0;
            block = 3;
            break;
            case 6:
            v583 = v582.childNodes;
            v584 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v583,0 );
            v584.nodeValue = __consts_0.const_str__60;
            block = 4;
            break;
        }
    }
}

function ll_newdict__Dict_String__List_String__LlT (DICT_0) {
    var v586,v587;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v587 = new Object();
            v586 = v587;
            block = 1;
            break;
            case 1:
            return ( v586 );
        }
    }
}

function ll_streq__String_String (s1_0,s2_0) {
    var v588,v589,v590,v591,s2_1,v592,v593,v594,v595,v596,v597;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v589 = !!s1_0;
            v590 = !v589;
            v591 = v590;
            if (v591 == true)
            {
                v595 = s2_0;
                block = 3;
                break;
            }
            else{
                s2_1 = s2_0;
                v592 = s1_0;
                block = 1;
                break;
            }
            case 1:
            v593 = v592;
            v594 = (v593==s2_1);
            v588 = v594;
            block = 2;
            break;
            case 2:
            return ( v588 );
            case 3:
            v596 = !!v595;
            v597 = !v596;
            v588 = v597;
            block = 2;
            break;
        }
    }
}

function add_received_item_outcome (msg_20,module_part_2) {
    var v632,v633,v634,v635,msg_21,module_part_3,v636,v637,v638,v639,v640,v641,v642,v643,v644,v645,v646,v647,v648,v649,v650,v651,v652,v653,v654,msg_22,module_part_4,item_name_6,td_0,v655,v656,v657,v658,msg_23,module_part_5,item_name_7,td_1,v659,v660,v661,v662,v663,v664,v665,v666,v667,v668,v669,v670,v671,v672,v673,v674,v675,v676,v677,v678,v679,v680,msg_24,module_part_6,td_2,v681,v682,v683,v684,v685,module_part_7,td_3,v686,v687,v688,v689,v690,v691,v692,v693,v694,v695,v696,v697,v698,v699,v700,v701,v702,v703,v704,v705,v706,v707,v708,v709,v710,v711,v712,v713,v714,v715,v716,v717,v718,v719,v720,msg_25,module_part_8,td_4,v721,v722,v723,msg_26,module_part_9,item_name_8,td_5,v724,v725,v726,v727,msg_27,module_part_10,item_name_9,td_6,v728,v729,v730,v731,v732,v733,v734,v735,v736,v737,v738,v739,v740,v741,v742,v743,v744,v745,v746,v747,msg_28,module_part_11,td_7,v748,v749,v750,msg_29,module_part_12,v751,v752,v753,v754,v755,v756,v757,v758,v759,v760,v761,v762,v763,v764,v765,v766,v767,v768,v769,v770,v771,v772,v773,v774,v775,v776,v777,v778,v779,v780,v781;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v633 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__62 );
            v634 = ll_strlen__String ( v633 );
            v635 = !!v634;
            if (v635 == true)
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
            v636 = create_elem ( __consts_0.const_str__25 );
            v637 = v636;
            v638 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__45 );
            v639 = new Object();
            v639.item0 = v638;
            v641 = v639.item0;
            v642 = new StringBuilder();
            v642.ll_append(__consts_0.const_str__80);
            v644 = ll_str__StringR_StringConst_String ( undefined,v641 );
            v642.ll_append(v644);
            v642.ll_append(__consts_0.const_str__28);
            v647 = v642.ll_build();
            v637.setAttribute(__consts_0.const_str__29,v647);
            v649 = v636;
            v649.setAttribute(__consts_0.const_str__30,__consts_0.const_str__81);
            v651 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__45 );
            v652 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__88 );
            v653 = ll_streq__String_String ( v652,__consts_0.const_str__13 );
            v654 = v653;
            if (v654 == true)
            {
                msg_28 = msg_21;
                module_part_11 = module_part_3;
                td_7 = v636;
                block = 10;
                break;
            }
            else{
                msg_22 = msg_21;
                module_part_4 = module_part_3;
                item_name_6 = v651;
                td_0 = v636;
                block = 2;
                break;
            }
            case 2:
            v655 = ll_dict_getitem__Dict_String__String__String ( msg_22,__consts_0.const_str__89 );
            v656 = ll_streq__String_String ( v655,__consts_0.const_str__90 );
            v657 = !v656;
            v658 = v657;
            if (v658 == true)
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
            v659 = create_elem ( __consts_0.const_str__91 );
            v660 = v659;
            v661 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__45 );
            v662 = new Object();
            v662.item0 = v661;
            v664 = v662.item0;
            v665 = new StringBuilder();
            v665.ll_append(__consts_0.const_str__92);
            v667 = ll_str__StringR_StringConst_String ( undefined,v664 );
            v665.ll_append(v667);
            v665.ll_append(__consts_0.const_str__28);
            v670 = v665.ll_build();
            v660.setAttribute(__consts_0.const_str__93,v670);
            v672 = create_text_elem ( __consts_0.const_str__94 );
            v673 = v659;
            v673.setAttribute(__consts_0.const_str__95,__consts_0.const_str__96);
            v675 = v659;
            v675.appendChild(v672);
            v677 = td_1;
            v677.appendChild(v659);
            v679 = __consts_0.ExportedMethods;
            v680 = v679.show_fail(item_name_7,fail_come_back);
            msg_24 = msg_23;
            module_part_6 = module_part_5;
            td_2 = td_1;
            block = 4;
            break;
            case 4:
            v681 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__61 );
            v682 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__84,v681 );
            v683 = (v682%50);
            v684 = (v683==0);
            v685 = v684;
            if (v685 == true)
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
                v686 = msg_24;
                block = 5;
                break;
            }
            case 5:
            v687 = ll_dict_getitem__Dict_String__String__String ( v686,__consts_0.const_str__61 );
            v688 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__84,v687 );
            v689 = (v688+1);
            __consts_0.const_tuple__84[v687]=v689;
            v691 = ll_strconcat__String_String ( __consts_0.const_str__79,v687 );
            v692 = get_elem ( v691 );
            v693 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__78,v687 );
            v694 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__84,v687 );
            v695 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__77,v687 );
            v696 = new Object();
            v696.item0 = v693;
            v696.item1 = v694;
            v696.item2 = v695;
            v700 = v696.item0;
            v701 = v696.item1;
            v702 = v696.item2;
            v703 = new StringBuilder();
            v704 = ll_str__StringR_StringConst_String ( undefined,v700 );
            v703.ll_append(v704);
            v703.ll_append(__consts_0.const_str__65);
            v707 = v701.toString();
            v703.ll_append(v707);
            v703.ll_append(__consts_0.const_str__97);
            v710 = v702.toString();
            v703.ll_append(v710);
            v703.ll_append(__consts_0.const_str__59);
            v713 = v703.ll_build();
            v714 = v692.childNodes;
            v715 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v714,0 );
            v715.nodeValue = v713;
            v717 = module_part_7.childNodes;
            v718 = ll_getitem__dum_nocheckConst_List_ExternalType__Si ( undefined,v717,-1 );
            v719 = v718;
            v719.appendChild(td_3);
            block = 6;
            break;
            case 6:
            return ( v632 );
            case 7:
            v721 = create_elem ( __consts_0.const_str__24 );
            v722 = module_part_8;
            v722.appendChild(v721);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v686 = msg_25;
            block = 5;
            break;
            case 8:
            v724 = ll_dict_getitem__Dict_String__String__String ( msg_26,__consts_0.const_str__89 );
            v725 = ll_streq__String_String ( v724,__consts_0.const_str__98 );
            v726 = !v725;
            v727 = v726;
            if (v727 == true)
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
            v728 = __consts_0.ExportedMethods;
            v729 = v728.show_skip(item_name_9,skip_come_back);
            v730 = create_elem ( __consts_0.const_str__91 );
            v731 = v730;
            v732 = ll_dict_getitem__Dict_String__String__String ( msg_27,__consts_0.const_str__45 );
            v733 = new Object();
            v733.item0 = v732;
            v735 = v733.item0;
            v736 = new StringBuilder();
            v736.ll_append(__consts_0.const_str__99);
            v738 = ll_str__StringR_StringConst_String ( undefined,v735 );
            v736.ll_append(v738);
            v736.ll_append(__consts_0.const_str__28);
            v741 = v736.ll_build();
            v731.setAttribute(__consts_0.const_str__93,v741);
            v743 = create_text_elem ( __consts_0.const_str__100 );
            v744 = v730;
            v744.appendChild(v743);
            v746 = td_6;
            v746.appendChild(v730);
            msg_24 = msg_27;
            module_part_6 = module_part_10;
            td_2 = td_6;
            block = 4;
            break;
            case 10:
            v748 = create_text_elem ( __consts_0.const_str__101 );
            v749 = td_7;
            v749.appendChild(v748);
            msg_24 = msg_28;
            module_part_6 = module_part_11;
            td_2 = td_7;
            block = 4;
            break;
            case 11:
            v751 = __consts_0.Document;
            v752 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__62 );
            v753 = v751.getElementById(v752);
            v754 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v755 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__62 );
            v756 = ll_dict_getitem__Dict_String__List_String___String ( v754,v755 );
            v757 = v756;
            v758 = ll_pop_default__dum_nocheckConst_List_String_ ( undefined,v757 );
            v759 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v760 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__62 );
            v761 = ll_dict_getitem__Dict_String__List_String___String ( v759,v760 );
            v762 = ll_len__List_String_ ( v761 );
            v763 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v764 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__62 );
            v765 = ll_dict_getitem__Dict_String__String__String ( v763,v764 );
            v766 = new Object();
            v766.item0 = v765;
            v766.item1 = v762;
            v769 = v766.item0;
            v770 = v766.item1;
            v771 = new StringBuilder();
            v772 = ll_str__StringR_StringConst_String ( undefined,v769 );
            v771.ll_append(v772);
            v771.ll_append(__consts_0.const_str__65);
            v775 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v770 );
            v771.ll_append(v775);
            v771.ll_append(__consts_0.const_str__59);
            v778 = v771.ll_build();
            v779 = v753.childNodes;
            v780 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v779,0 );
            v780.nodeValue = v778;
            msg_21 = msg_29;
            module_part_3 = module_part_12;
            block = 1;
            break;
        }
    }
}

function ll_int_str__IntegerR_SignedConst_Signed (repr_0,i_4) {
    var v811,v812;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v812 = ll_int2dec__Signed ( i_4 );
            v811 = v812;
            block = 1;
            break;
            case 1:
            return ( v811 );
        }
    }
}

function ll_dict_getitem__Dict_String__Signed__String (d_4,key_8) {
    var v1005,v1006,v1007,v1008,v1009,v1010,v1011,etype_6,evalue_6,key_9,v1012,v1013,v1014;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1006 = d_4;
            v1007 = (v1006[key_8]!=undefined);
            v1008 = v1007;
            if (v1008 == true)
            {
                key_9 = key_8;
                v1012 = d_4;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v1009 = __consts_0.exceptions_KeyError;
            v1010 = v1009.meta;
            v1011 = v1009;
            etype_6 = v1010;
            evalue_6 = v1011;
            block = 2;
            break;
            case 2:
            throw(evalue_6);
            case 3:
            v1013 = v1012;
            v1014 = v1013[key_9];
            v1005 = v1014;
            block = 4;
            break;
            case 4:
            return ( v1005 );
        }
    }
}

function ll_int2dec__Signed (i_29) {
    var v1045,v1046;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1046 = i_29.toString();
            v1045 = v1046;
            block = 1;
            break;
            case 1:
            return ( v1045 );
        }
    }
}

function ll_strconcat__String_String (obj_0,arg0_0) {
    var v873,v874,v875;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v874 = obj_0;
            v875 = (v874+arg0_0);
            v873 = v875;
            block = 1;
            break;
            case 1:
            return ( v873 );
        }
    }
}

function ll_int__String_Signed (s_2,base_0) {
    var v876,v877,v878,v879,v880,v881,etype_5,evalue_5,s_3,base_1,v882,s_4,base_2,v883,v884,s_5,base_3,v885,v886,s_6,base_4,i_5,strlen_0,v887,v888,s_7,base_5,i_6,strlen_1,v889,v890,v891,v892,v893,s_8,base_6,i_7,strlen_2,v894,v895,v896,v897,s_9,base_7,i_8,strlen_3,v898,v899,v900,v901,s_10,base_8,val_0,i_9,sign_0,strlen_4,v902,v903,s_11,val_1,i_10,sign_1,strlen_5,v904,v905,val_2,sign_2,v906,v907,v908,v909,v910,v911,v912,v913,v914,v915,s_12,val_3,i_11,sign_3,strlen_6,v916,v917,v918,v919,s_13,val_4,sign_4,strlen_7,v920,v921,s_14,base_9,val_5,i_12,sign_5,strlen_8,v922,v923,v924,v925,v926,s_15,base_10,c_0,val_6,i_13,sign_6,strlen_9,v927,v928,s_16,base_11,c_1,val_7,i_14,sign_7,strlen_10,v929,v930,s_17,base_12,c_2,val_8,i_15,sign_8,strlen_11,v931,s_18,base_13,c_3,val_9,i_16,sign_9,strlen_12,v932,v933,s_19,base_14,val_10,i_17,sign_10,strlen_13,v934,v935,s_20,base_15,val_11,i_18,digit_0,sign_11,strlen_14,v936,v937,s_21,base_16,i_19,digit_1,sign_12,strlen_15,v938,v939,v940,v941,s_22,base_17,c_4,val_12,i_20,sign_13,strlen_16,v942,s_23,base_18,c_5,val_13,i_21,sign_14,strlen_17,v943,v944,s_24,base_19,val_14,i_22,sign_15,strlen_18,v945,v946,v947,s_25,base_20,c_6,val_15,i_23,sign_16,strlen_19,v948,s_26,base_21,c_7,val_16,i_24,sign_17,strlen_20,v949,v950,s_27,base_22,val_17,i_25,sign_18,strlen_21,v951,v952,v953,s_28,base_23,strlen_22,v954,v955,s_29,base_24,strlen_23,v956,v957,s_30,base_25,i_26,strlen_24,v958,v959,v960,v961,s_31,base_26,strlen_25,v962,v963;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v877 = (2<=base_0);
            v878 = v877;
            if (v878 == true)
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
            v879 = __consts_0.exceptions_ValueError;
            v880 = v879.meta;
            v881 = v879;
            etype_5 = v880;
            evalue_5 = v881;
            block = 2;
            break;
            case 2:
            throw(evalue_5);
            case 3:
            v882 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v883 = v882;
            block = 4;
            break;
            case 4:
            v884 = v883;
            if (v884 == true)
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
            v885 = s_5;
            v886 = v885.length;
            s_6 = s_5;
            base_4 = base_3;
            i_5 = 0;
            strlen_0 = v886;
            block = 6;
            break;
            case 6:
            v887 = (i_5<strlen_0);
            v888 = v887;
            if (v888 == true)
            {
                s_30 = s_6;
                base_25 = base_4;
                i_26 = i_5;
                strlen_24 = strlen_0;
                block = 35;
                break;
            }
            else{
                s_7 = s_6;
                base_5 = base_4;
                i_6 = i_5;
                strlen_1 = strlen_0;
                block = 7;
                break;
            }
            case 7:
            v889 = (i_6<strlen_1);
            v890 = v889;
            if (v890 == true)
            {
                s_8 = s_7;
                base_6 = base_5;
                i_7 = i_6;
                strlen_2 = strlen_1;
                block = 9;
                break;
            }
            else{
                block = 8;
                break;
            }
            case 8:
            v891 = __consts_0.exceptions_ValueError;
            v892 = v891.meta;
            v893 = v891;
            etype_5 = v892;
            evalue_5 = v893;
            block = 2;
            break;
            case 9:
            v894 = s_8;
            v895 = v894.charAt(i_7);
            v896 = (v895=='-');
            v897 = v896;
            if (v897 == true)
            {
                s_29 = s_8;
                base_24 = base_6;
                strlen_23 = strlen_2;
                v956 = i_7;
                block = 34;
                break;
            }
            else{
                s_9 = s_8;
                base_7 = base_6;
                i_8 = i_7;
                strlen_3 = strlen_2;
                block = 10;
                break;
            }
            case 10:
            v898 = s_9;
            v899 = v898.charAt(i_8);
            v900 = (v899=='+');
            v901 = v900;
            if (v901 == true)
            {
                s_28 = s_9;
                base_23 = base_7;
                strlen_22 = strlen_3;
                v954 = i_8;
                block = 33;
                break;
            }
            else{
                s_10 = s_9;
                base_8 = base_7;
                val_0 = 0;
                i_9 = i_8;
                sign_0 = 1;
                strlen_4 = strlen_3;
                block = 11;
                break;
            }
            case 11:
            v902 = (i_9<strlen_4);
            v903 = v902;
            if (v903 == true)
            {
                s_14 = s_10;
                base_9 = base_8;
                val_5 = val_0;
                i_12 = i_9;
                sign_5 = sign_0;
                strlen_8 = strlen_4;
                block = 19;
                break;
            }
            else{
                s_11 = s_10;
                val_1 = val_0;
                i_10 = i_9;
                sign_1 = sign_0;
                strlen_5 = strlen_4;
                block = 12;
                break;
            }
            case 12:
            v904 = (i_10<strlen_5);
            v905 = v904;
            if (v905 == true)
            {
                s_12 = s_11;
                val_3 = val_1;
                i_11 = i_10;
                sign_3 = sign_1;
                strlen_6 = strlen_5;
                block = 17;
                break;
            }
            else{
                val_2 = val_1;
                sign_2 = sign_1;
                v906 = i_10;
                v907 = strlen_5;
                block = 13;
                break;
            }
            case 13:
            v908 = (v906==v907);
            v909 = v908;
            if (v909 == true)
            {
                v913 = sign_2;
                v914 = val_2;
                block = 15;
                break;
            }
            else{
                block = 14;
                break;
            }
            case 14:
            v910 = __consts_0.exceptions_ValueError;
            v911 = v910.meta;
            v912 = v910;
            etype_5 = v911;
            evalue_5 = v912;
            block = 2;
            break;
            case 15:
            v915 = (v913*v914);
            v876 = v915;
            block = 16;
            break;
            case 16:
            return ( v876 );
            case 17:
            v916 = s_12;
            v917 = v916.charAt(i_11);
            v918 = (v917==' ');
            v919 = v918;
            if (v919 == true)
            {
                s_13 = s_12;
                val_4 = val_3;
                sign_4 = sign_3;
                strlen_7 = strlen_6;
                v920 = i_11;
                block = 18;
                break;
            }
            else{
                val_2 = val_3;
                sign_2 = sign_3;
                v906 = i_11;
                v907 = strlen_6;
                block = 13;
                break;
            }
            case 18:
            v921 = (v920+1);
            s_11 = s_13;
            val_1 = val_4;
            i_10 = v921;
            sign_1 = sign_4;
            strlen_5 = strlen_7;
            block = 12;
            break;
            case 19:
            v922 = s_14;
            v923 = v922.charAt(i_12);
            v924 = v923.charCodeAt(0);
            v925 = (97<=v924);
            v926 = v925;
            if (v926 == true)
            {
                s_25 = s_14;
                base_20 = base_9;
                c_6 = v924;
                val_15 = val_5;
                i_23 = i_12;
                sign_16 = sign_5;
                strlen_19 = strlen_8;
                block = 30;
                break;
            }
            else{
                s_15 = s_14;
                base_10 = base_9;
                c_0 = v924;
                val_6 = val_5;
                i_13 = i_12;
                sign_6 = sign_5;
                strlen_9 = strlen_8;
                block = 20;
                break;
            }
            case 20:
            v927 = (65<=c_0);
            v928 = v927;
            if (v928 == true)
            {
                s_22 = s_15;
                base_17 = base_10;
                c_4 = c_0;
                val_12 = val_6;
                i_20 = i_13;
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
                i_14 = i_13;
                sign_7 = sign_6;
                strlen_10 = strlen_9;
                block = 21;
                break;
            }
            case 21:
            v929 = (48<=c_1);
            v930 = v929;
            if (v930 == true)
            {
                s_17 = s_16;
                base_12 = base_11;
                c_2 = c_1;
                val_8 = val_7;
                i_15 = i_14;
                sign_8 = sign_7;
                strlen_11 = strlen_10;
                block = 22;
                break;
            }
            else{
                s_11 = s_16;
                val_1 = val_7;
                i_10 = i_14;
                sign_1 = sign_7;
                strlen_5 = strlen_10;
                block = 12;
                break;
            }
            case 22:
            v931 = (c_2<=57);
            s_18 = s_17;
            base_13 = base_12;
            c_3 = c_2;
            val_9 = val_8;
            i_16 = i_15;
            sign_9 = sign_8;
            strlen_12 = strlen_11;
            v932 = v931;
            block = 23;
            break;
            case 23:
            v933 = v932;
            if (v933 == true)
            {
                s_19 = s_18;
                base_14 = base_13;
                val_10 = val_9;
                i_17 = i_16;
                sign_10 = sign_9;
                strlen_13 = strlen_12;
                v934 = c_3;
                block = 24;
                break;
            }
            else{
                s_11 = s_18;
                val_1 = val_9;
                i_10 = i_16;
                sign_1 = sign_9;
                strlen_5 = strlen_12;
                block = 12;
                break;
            }
            case 24:
            v935 = (v934-48);
            s_20 = s_19;
            base_15 = base_14;
            val_11 = val_10;
            i_18 = i_17;
            digit_0 = v935;
            sign_11 = sign_10;
            strlen_14 = strlen_13;
            block = 25;
            break;
            case 25:
            v936 = (digit_0>=base_15);
            v937 = v936;
            if (v937 == true)
            {
                s_11 = s_20;
                val_1 = val_11;
                i_10 = i_18;
                sign_1 = sign_11;
                strlen_5 = strlen_14;
                block = 12;
                break;
            }
            else{
                s_21 = s_20;
                base_16 = base_15;
                i_19 = i_18;
                digit_1 = digit_0;
                sign_12 = sign_11;
                strlen_15 = strlen_14;
                v938 = val_11;
                block = 26;
                break;
            }
            case 26:
            v939 = (v938*base_16);
            v940 = (v939+digit_1);
            v941 = (i_19+1);
            s_10 = s_21;
            base_8 = base_16;
            val_0 = v940;
            i_9 = v941;
            sign_0 = sign_12;
            strlen_4 = strlen_15;
            block = 11;
            break;
            case 27:
            v942 = (c_4<=90);
            s_23 = s_22;
            base_18 = base_17;
            c_5 = c_4;
            val_13 = val_12;
            i_21 = i_20;
            sign_14 = sign_13;
            strlen_17 = strlen_16;
            v943 = v942;
            block = 28;
            break;
            case 28:
            v944 = v943;
            if (v944 == true)
            {
                s_24 = s_23;
                base_19 = base_18;
                val_14 = val_13;
                i_22 = i_21;
                sign_15 = sign_14;
                strlen_18 = strlen_17;
                v945 = c_5;
                block = 29;
                break;
            }
            else{
                s_16 = s_23;
                base_11 = base_18;
                c_1 = c_5;
                val_7 = val_13;
                i_14 = i_21;
                sign_7 = sign_14;
                strlen_10 = strlen_17;
                block = 21;
                break;
            }
            case 29:
            v946 = (v945-65);
            v947 = (v946+10);
            s_20 = s_24;
            base_15 = base_19;
            val_11 = val_14;
            i_18 = i_22;
            digit_0 = v947;
            sign_11 = sign_15;
            strlen_14 = strlen_18;
            block = 25;
            break;
            case 30:
            v948 = (c_6<=122);
            s_26 = s_25;
            base_21 = base_20;
            c_7 = c_6;
            val_16 = val_15;
            i_24 = i_23;
            sign_17 = sign_16;
            strlen_20 = strlen_19;
            v949 = v948;
            block = 31;
            break;
            case 31:
            v950 = v949;
            if (v950 == true)
            {
                s_27 = s_26;
                base_22 = base_21;
                val_17 = val_16;
                i_25 = i_24;
                sign_18 = sign_17;
                strlen_21 = strlen_20;
                v951 = c_7;
                block = 32;
                break;
            }
            else{
                s_15 = s_26;
                base_10 = base_21;
                c_0 = c_7;
                val_6 = val_16;
                i_13 = i_24;
                sign_6 = sign_17;
                strlen_9 = strlen_20;
                block = 20;
                break;
            }
            case 32:
            v952 = (v951-97);
            v953 = (v952+10);
            s_20 = s_27;
            base_15 = base_22;
            val_11 = val_17;
            i_18 = i_25;
            digit_0 = v953;
            sign_11 = sign_18;
            strlen_14 = strlen_21;
            block = 25;
            break;
            case 33:
            v955 = (v954+1);
            s_10 = s_28;
            base_8 = base_23;
            val_0 = 0;
            i_9 = v955;
            sign_0 = 1;
            strlen_4 = strlen_22;
            block = 11;
            break;
            case 34:
            v957 = (v956+1);
            s_10 = s_29;
            base_8 = base_24;
            val_0 = 0;
            i_9 = v957;
            sign_0 = -1;
            strlen_4 = strlen_23;
            block = 11;
            break;
            case 35:
            v958 = s_30;
            v959 = v958.charAt(i_26);
            v960 = (v959==' ');
            v961 = v960;
            if (v961 == true)
            {
                s_31 = s_30;
                base_26 = base_25;
                strlen_25 = strlen_24;
                v962 = i_26;
                block = 36;
                break;
            }
            else{
                s_7 = s_30;
                base_5 = base_25;
                i_6 = i_26;
                strlen_1 = strlen_24;
                block = 7;
                break;
            }
            case 36:
            v963 = (v962+1);
            s_6 = s_31;
            base_4 = base_26;
            i_5 = v963;
            strlen_0 = strlen_25;
            block = 6;
            break;
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed_0 (LIST_2,length_2) {
    var v976,v977,v978,v979;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v977 = new Array();
            v978 = v977;
            v978.length = length_2;
            v976 = v977;
            block = 1;
            break;
            case 1:
            return ( v976 );
        }
    }
}

function ll_newlist__List_String_LlT_Signed (LIST_1,length_0) {
    var v964,v965,v966,v967;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v965 = new Array();
            v966 = v965;
            v966.length = length_0;
            v964 = v965;
            block = 1;
            break;
            case 1:
            return ( v964 );
        }
    }
}

function ll_pop_default__dum_nocheckConst_List_String_ (func_3,l_17) {
    var v1033,v1034,v1035,l_18,length_5,v1036,v1037,v1038,v1039,v1040,v1041,res_0,newlength_0,v1042,v1043,v1044;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1034 = l_17;
            v1035 = v1034.length;
            l_18 = l_17;
            length_5 = v1035;
            block = 1;
            break;
            case 1:
            v1036 = (length_5>0);
            undefined;
            v1038 = (length_5-1);
            v1039 = l_18;
            v1040 = v1039[v1038];
            ll_null_item__List_String_ ( l_18 );
            res_0 = v1040;
            newlength_0 = v1038;
            v1042 = l_18;
            block = 2;
            break;
            case 2:
            v1043 = v1042;
            v1043.length = newlength_0;
            v1033 = res_0;
            block = 3;
            break;
            case 3:
            return ( v1033 );
        }
    }
}

function skip_come_back (msg_32) {
    var v1029,v1030,v1031,v1032;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1030 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__46 );
            v1031 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__103 );
            __consts_0.const_tuple__14[v1031]=v1030;
            block = 1;
            break;
            case 1:
            return ( v1029 );
        }
    }
}

function ll_getitem__dum_nocheckConst_List_ExternalType__Si (func_2,l_14,index_5) {
    var v1015,v1016,v1017,v1018,v1019,l_15,index_6,length_3,v1020,v1021,v1022,v1023,index_7,v1024,v1025,v1026,l_16,length_4,v1027,v1028;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1016 = l_14;
            v1017 = v1016.length;
            v1018 = (index_5<0);
            v1019 = v1018;
            if (v1019 == true)
            {
                l_16 = l_14;
                length_4 = v1017;
                v1027 = index_5;
                block = 4;
                break;
            }
            else{
                l_15 = l_14;
                index_6 = index_5;
                length_3 = v1017;
                block = 1;
                break;
            }
            case 1:
            v1020 = (index_6>=0);
            undefined;
            v1022 = (index_6<length_3);
            undefined;
            index_7 = index_6;
            v1024 = l_15;
            block = 2;
            break;
            case 2:
            v1025 = v1024;
            v1026 = v1025[index_7];
            v1015 = v1026;
            block = 3;
            break;
            case 3:
            return ( v1015 );
            case 4:
            v1028 = (v1027+length_4);
            l_15 = l_16;
            index_6 = v1028;
            length_3 = length_4;
            block = 1;
            break;
        }
    }
}

function ll_char_mul__Char_Signed (ch_0,times_0) {
    var v980,v981,v982,v983,ch_1,times_1,i_27,buf_0,v984,v985,v986,v987,v988,ch_2,times_2,i_28,buf_1,v989,v990,v991;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v981 = new StringBuilder();
            v982 = v981;
            v982.ll_allocate(times_0);
            ch_1 = ch_0;
            times_1 = times_0;
            i_27 = 0;
            buf_0 = v981;
            block = 1;
            break;
            case 1:
            v984 = (i_27<times_1);
            v985 = v984;
            if (v985 == true)
            {
                ch_2 = ch_1;
                times_2 = times_1;
                i_28 = i_27;
                buf_1 = buf_0;
                block = 4;
                break;
            }
            else{
                v986 = buf_0;
                block = 2;
                break;
            }
            case 2:
            v987 = v986;
            v988 = v987.ll_build();
            v980 = v988;
            block = 3;
            break;
            case 3:
            return ( v980 );
            case 4:
            v989 = buf_1;
            v989.ll_append_char(ch_2);
            v991 = (i_28+1);
            ch_1 = ch_2;
            times_1 = times_2;
            i_27 = v991;
            buf_0 = buf_1;
            block = 1;
            break;
        }
    }
}

function fail_come_back (msg_31) {
    var v995,v996,v997,v998,v999,v1000,v1001,v1002,v1003,v1004;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v996 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__104 );
            v997 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__105 );
            v998 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__106 );
            v999 = new Object();
            v999.item0 = v996;
            v999.item1 = v997;
            v999.item2 = v998;
            v1003 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__103 );
            __consts_0.const_tuple[v1003]=v999;
            block = 1;
            break;
            case 1:
            return ( v995 );
        }
    }
}

function ll_strlen__String (obj_1) {
    var v992,v993,v994;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v993 = obj_1;
            v994 = v993.length;
            v992 = v994;
            block = 1;
            break;
            case 1:
            return ( v992 );
        }
    }
}

function ll_null_item__List_String_ (lst_2) {
    var v1047,v1048;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            undefined;
            block = 1;
            break;
            case 1:
            return ( v1047 );
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
__consts_0 = {};
__consts_0.const_str__55 = ' failures, ';
__consts_0.const_str__27 = "show_host('";
__consts_0.const_str__79 = '_txt_';
__consts_0.const_tuple__84 = {};
__consts_0.const_str__91 = 'a';
__consts_0.const_str__95 = 'class';
__consts_0.const_str__59 = ']';
__consts_0.const_str__38 = 'ReceivedItemOutcome';
__consts_0.const_str__80 = "show_info('";
__consts_0.const_str__47 = '- skipped (';
__consts_0.const_str__31 = 'hide_host()';
__consts_0.const_str__81 = 'hide_info()';
__consts_0.const_str__49 = '- FAILED TO LOAD MODULE';
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__83 = 'tbody';
__consts_0.exceptions_StopIteration__110 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_str__48 = ')';
__consts_0.const_str__33 = 'main_table';
__consts_0.const_str__68 = 'Tests [interrupted]';
__consts_0.exceptions_KeyError__112 = exceptions_KeyError;
__consts_0.const_str__28 = "')";
__consts_0.const_str__42 = 'RsyncFinished';
__consts_0.const_str__54 = ' run, ';
__consts_0.py____test_rsession_webjs_Options__114 = py____test_rsession_webjs_Options;
__consts_0.py____test_rsession_webjs_Options_meta = new py____test_rsession_webjs_Options_meta();
__consts_0.py____test_rsession_webjs_Options = new py____test_rsession_webjs_Options();
__consts_0.const_tuple__77 = {};
__consts_0.const_str__105 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_str__96 = 'error';
__consts_0.exceptions_ValueError__108 = exceptions_ValueError;
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.const_str__56 = ' skipped';
__consts_0.const_str__53 = 'FINISHED ';
__consts_0.const_str__87 = 'Rsyncing';
__consts_0.const_str__7 = 'info';
__consts_0.const_str__25 = 'td';
__consts_0.const_str__86 = 'true';
__consts_0.const_tuple__78 = {};
__consts_0.const_str__94 = 'F';
__consts_0.const_str__30 = 'onmouseout';
__consts_0.const_str__34 = 'type';
__consts_0.const_str__88 = 'passed';
__consts_0.const_str__101 = '.';
__consts_0.const_str__40 = 'FailedTryiter';
__consts_0.const_str__26 = '#ff0000';
__consts_0.const_tuple__19 = undefined;
__consts_0.const_str__12 = 'checked';
__consts_0.const_str__20 = 'messagebox';
__consts_0.py____test_rsession_webjs_Globals__117 = py____test_rsession_webjs_Globals;
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.const_str__45 = 'fullitemname';
__consts_0.const_str__82 = 'table';
__consts_0.const_str__57 = 'Py.test ';
__consts_0.const_str__52 = 'skips';
__consts_0.const_str__44 = 'CrashedExecution';
__consts_0.const_str__5 = '\n';
__consts_0.const_tuple__14 = {};
__consts_0.const_str__70 = 'pre';
__consts_0.const_str__67 = 'Py.test [interrupted]';
__consts_0.const_str__3 = '\n======== Stdout: ========\n';
__consts_0.const_str__63 = '#00ff00';
__consts_0.const_str__22 = 'beige';
__consts_0.const_str__75 = 'length';
__consts_0.const_tuple__17 = undefined;
__consts_0.const_list__116 = [];
__consts_0.const_str__16 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.const_str__104 = 'traceback';
__consts_0.const_str__32 = 'testmain';
__consts_0.const_str__99 = "javascript:show_skip('";
__consts_0.const_str__65 = '[';
__consts_0.const_str__73 = 'Tests [crashed]';
__consts_0.const_str__46 = 'reason';
__consts_0.const_str__92 = "javascript:show_traceback('";
__consts_0.const_str__60 = 'Tests';
__consts_0.const_tuple = {};
__consts_0.const_str__100 = 's';
__consts_0.const_str__50 = 'run';
__consts_0.const_str__41 = 'SkippedTryiter';
__consts_0.const_str__90 = 'None';
__consts_0.const_str__13 = 'True';
__consts_0.const_str__97 = '/';
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.const_str__62 = 'hostkey';
__consts_0.const_str__51 = 'fails';
__consts_0.const_str__35 = 'ItemStart';
__consts_0.const_str__74 = 'itemname';
__consts_0.const_str__39 = 'TestFinished';
__consts_0.const_str__85 = 'jobs';
__consts_0.const_str__4 = '\n========== Stderr: ==========\n';
__consts_0.const_str__106 = 'stderr';
__consts_0.const_str__93 = 'href';
__consts_0.const_str__21 = 'visible';
__consts_0.const_str__98 = 'False';
__consts_0.const_str__37 = 'HostRSyncRootReady';
__consts_0.const_str__29 = 'onmouseover';
__consts_0.const_str__71 = '#message';
__consts_0.const_str__76 = '[0/';
__consts_0.const_list = undefined;
__consts_0.const_str__36 = 'SendItem';
__consts_0.const_str__61 = 'fullmodulename';
__consts_0.const_str__89 = 'skipped';
__consts_0.const_str__23 = 'hostsbody';
__consts_0.const_str__64 = '[0]';
__consts_0.const_str__8 = 'hidden';
__consts_0.const_str__2 = '====== Traceback: =========\n';
__consts_0.const_str__24 = 'tr';
__consts_0.const_str__103 = 'item_name';
__consts_0.const_str__58 = 'Tests [';
__consts_0.Document = document;
__consts_0.const_str__72 = 'Py.test [crashed]';
__consts_0.const_str__43 = 'InterruptedExecution';
__consts_0.const_str__11 = 'opt_scroll';
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__110;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
__consts_0.py____test_rsession_webjs_Options_meta.class_ = __consts_0.py____test_rsession_webjs_Options__114;
__consts_0.py____test_rsession_webjs_Options.meta = __consts_0.py____test_rsession_webjs_Options_meta;
__consts_0.py____test_rsession_webjs_Options.oscroll = true;
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__108;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__117;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__16;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__16;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ofinished = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple__17;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__116;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__19;
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__112;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
