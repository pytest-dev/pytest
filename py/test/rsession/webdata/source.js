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

function hide_host () {
    var v100,v101,v102,elem_5,v103,v104,v105,v106,v107,v108,v109,elem_6,v110,v111,v112,v113;
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
            v107.visibility = __consts_0.const_str__3;
            __consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__5;
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

function py____test_rsession_webjs_Globals () {
    this.odata_empty = false;
    this.osessid = __consts_0.const_str__5;
    this.ohost = __consts_0.const_str__5;
    this.orsync_dots = 0;
    this.ofinished = false;
    this.ohost_dict = __consts_0.const_tuple;
    this.opending = __consts_0.const_list;
    this.orsync_done = false;
    this.ohost_pending = __consts_0.const_tuple__8;
}

py____test_rsession_webjs_Globals.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals instance>' );
}

inherits(py____test_rsession_webjs_Globals,Object);
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

function show_info (data_0) {
    var v46,v47,v48,v49,v50,data_1,info_0,v51,v52,v53,info_1,v54,v55,v56,v57,v58,v59,data_2,info_2,v60,v61,v62,v63;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v47 = __consts_0.Document;
            v48 = v47.getElementById(__consts_0.const_str__9);
            v49 = v48.style;
            v49.visibility = __consts_0.const_str__10;
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
            v58.backgroundColor = __consts_0.const_str__11;
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

function show_host (host_name_0) {
    var v69,v70,v71,v72,v73,host_name_1,elem_0,v74,v75,v76,v77,host_name_2,tbody_0,elem_1,v78,v79,last_exc_value_0,host_name_3,tbody_1,elem_2,item_0,v80,v81,v82,v83,v84,v85,v86,v87,v88,v89,host_name_4,tbody_2,elem_3,v90,v91,v92,v93,v94,v95,host_name_5,elem_4,v96,v97,v98,v99;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v70 = __consts_0.Document;
            v71 = v70.getElementById(__consts_0.const_str__2);
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
            v81 = create_elem ( __consts_0.const_str__13 );
            v82 = create_elem ( __consts_0.const_str__14 );
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
            v92.visibility = __consts_0.const_str__10;
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

function ll_getitem_nonneg__dum_nocheckConst_List_ExternalT (func_0,l_1,index_0) {
    var v131,v132,v133,l_2,index_1,v134,v135,v136,v137,index_2,v138,v139,v140;
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

function show_skip (item_name_0) {
    var v25,v26,v27;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v26 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__15,item_name_0 );
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

function set_msgbox (item_name_2,data_3) {
    var v198,v199,item_name_3,data_4,msgbox_0,v200,v201,v202,item_name_4,data_5,msgbox_1,v203,v204,v205,v206,v207,v208,v209,v210,v211,v212,item_name_5,data_6,msgbox_2,v213,v214,v215,v216;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v199 = get_elem ( __consts_0.const_str__17 );
            item_name_3 = item_name_2;
            data_4 = data_3;
            msgbox_0 = v199;
            block = 1;
            break;
            case 1:
            v200 = msgbox_0.childNodes;
            v201 = ll_len__List_ExternalType_ ( v200 );
            v202 = !!v201;
            if (v202 == true)
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
            v203 = create_elem ( __consts_0.const_str__18 );
            v204 = ll_strconcat__String_String ( item_name_4,__consts_0.const_str__19 );
            v205 = ll_strconcat__String_String ( v204,data_5 );
            v206 = create_text_elem ( v205 );
            v207 = v203;
            v207.appendChild(v206);
            v209 = msgbox_1;
            v209.appendChild(v203);
            __consts_0.Document.location = __consts_0.const_str__20;
            __consts_0.py____test_rsession_webjs_Globals.odata_empty = false;
            block = 3;
            break;
            case 3:
            return ( v198 );
            case 4:
            v213 = msgbox_2;
            v214 = msgbox_2.childNodes;
            v215 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v214,0 );
            v213.removeChild(v215);
            item_name_3 = item_name_5;
            data_4 = data_6;
            msgbox_0 = msgbox_2;
            block = 1;
            break;
        }
    }
}

function ll_list_is_true__List_ExternalType_ (l_3) {
    var v144,v145,v146,v147,v148,v149,v150;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v145 = !!l_3;
            v146 = v145;
            if (v146 == true)
            {
                v147 = l_3;
                block = 2;
                break;
            }
            else{
                v144 = v145;
                block = 1;
                break;
            }
            case 1:
            return ( v144 );
            case 2:
            v148 = v147;
            v149 = v148.length;
            v150 = (v149!=0);
            v144 = v150;
            block = 1;
            break;
        }
    }
}

function ll_listnext__Record_index__Signed__iterable_0 (iter_0) {
    var v168,v169,v170,v171,v172,v173,v174,iter_1,index_3,l_4,v175,v176,v177,v178,v179,v180,v181,etype_1,evalue_1;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v169 = iter_0.iterable;
            v170 = iter_0.index;
            v171 = v169;
            v172 = v171.length;
            v173 = (v170>=v172);
            v174 = v173;
            if (v174 == true)
            {
                block = 3;
                break;
            }
            else{
                iter_1 = iter_0;
                index_3 = v170;
                l_4 = v169;
                block = 1;
                break;
            }
            case 1:
            v175 = (index_3+1);
            iter_1.index = v175;
            v177 = l_4;
            v178 = v177[index_3];
            v168 = v178;
            block = 2;
            break;
            case 2:
            return ( v168 );
            case 3:
            v179 = __consts_0.exceptions_StopIteration;
            v180 = v179.meta;
            v181 = v179;
            etype_1 = v180;
            evalue_1 = v181;
            block = 4;
            break;
            case 4:
            throw(evalue_1);
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
            v66 = v65.getElementById(__consts_0.const_str__9);
            v67 = v66.style;
            v67.visibility = __consts_0.const_str__3;
            block = 1;
            break;
            case 1:
            return ( v64 );
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
            v116 = v115.getElementById(__consts_0.const_str__17);
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

function exceptions_Exception () {
}

exceptions_Exception.prototype.toString = function (){
    return ( '<exceptions_Exception instance>' );
}

inherits(exceptions_Exception,Object);
function exceptions_StopIteration () {
}

exceptions_StopIteration.prototype.toString = function (){
    return ( '<exceptions_StopIteration instance>' );
}

inherits(exceptions_StopIteration,exceptions_Exception);
function create_elem (s_0) {
    var v151,v152,v153;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v152 = __consts_0.Document;
            v153 = v152.createElement(s_0);
            v151 = v153;
            block = 1;
            break;
            case 1:
            return ( v151 );
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
function ll_dict_getitem__Dict_String__String__String (d_1,key_2) {
    var v188,v189,v190,v191,v192,v193,v194,etype_2,evalue_2,key_3,v195,v196,v197;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v189 = d_1;
            v190 = (v189[key_2]!=undefined);
            v191 = v190;
            if (v191 == true)
            {
                key_3 = key_2;
                v195 = d_1;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v192 = __consts_0.exceptions_KeyError;
            v193 = v192.meta;
            v194 = v192;
            etype_2 = v193;
            evalue_2 = v194;
            block = 2;
            break;
            case 2:
            throw(evalue_2);
            case 3:
            v196 = v195;
            v197 = v196[key_3];
            v188 = v197;
            block = 4;
            break;
            case 4:
            return ( v188 );
        }
    }
}

function show_traceback (item_name_1) {
    var v28,v29,v30,v31,v32,v33,v34,v35,v36,v37,v38,v39,v40,v41,v42,v43,v44,v45;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v29 = ll_dict_getitem__Dict_String__Record_item2__Str_St ( __consts_0.const_tuple__23,item_name_1 );
            v30 = v29.item0;
            v31 = v29.item1;
            v32 = v29.item2;
            v33 = new StringBuilder();
            v33.ll_append(__consts_0.const_str__24);
            v35 = ll_str__StringR_StringConst_String ( undefined,v30 );
            v33.ll_append(v35);
            v33.ll_append(__consts_0.const_str__25);
            v38 = ll_str__StringR_StringConst_String ( undefined,v31 );
            v33.ll_append(v38);
            v33.ll_append(__consts_0.const_str__26);
            v41 = ll_str__StringR_StringConst_String ( undefined,v32 );
            v33.ll_append(v41);
            v33.ll_append(__consts_0.const_str__19);
            v44 = v33.ll_build();
            set_msgbox ( item_name_1,v44 );
            block = 1;
            break;
            case 1:
            return ( v28 );
        }
    }
}

function ll_dict_getitem__Dict_String__List_String___String (d_0,key_0) {
    var v154,v155,v156,v157,v158,v159,v160,etype_0,evalue_0,key_1,v161,v162,v163;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v155 = d_0;
            v156 = (v155[key_0]!=undefined);
            v157 = v156;
            if (v157 == true)
            {
                key_1 = key_0;
                v161 = d_0;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v158 = __consts_0.exceptions_KeyError;
            v159 = v158.meta;
            v160 = v158;
            etype_0 = v159;
            evalue_0 = v160;
            block = 2;
            break;
            case 2:
            throw(evalue_0);
            case 3:
            v162 = v161;
            v163 = v162[key_1];
            v154 = v163;
            block = 4;
            break;
            case 4:
            return ( v154 );
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
            v22 = v21.getElementById(__consts_0.const_str__28);
            v23 = v22;
            v23.setAttribute(__consts_0.const_str__29,__consts_0.const_str__30);
            block = 1;
            break;
            case 1:
            return ( v14 );
        }
    }
}

function ll_listiter__Record_index__Signed__iterable_List_S (ITER_0,lst_0) {
    var v164,v165,v166,v167;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v165 = new Object();
            v165.iterable = lst_0;
            v165.index = 0;
            v164 = v165;
            block = 1;
            break;
            case 1:
            return ( v164 );
        }
    }
}

function create_text_elem (txt_0) {
    var v141,v142,v143;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v142 = __consts_0.Document;
            v143 = v142.createTextNode(txt_0);
            v141 = v143;
            block = 1;
            break;
            case 1:
            return ( v141 );
        }
    }
}

function reshow_host () {
    var v182,v183,v184,v185,v186,v187;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v183 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            v184 = ll_streq__String_String ( v183,__consts_0.const_str__5 );
            v185 = v184;
            if (v185 == true)
            {
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v186 = __consts_0.py____test_rsession_webjs_Globals.ohost;
            show_host ( v186 );
            block = 2;
            break;
            case 2:
            return ( v182 );
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
            v236 = v235.getElementById(__consts_0.const_str__31);
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
            v243 = create_elem ( __consts_0.const_str__13 );
            v244 = tbody_4;
            v244.appendChild(v243);
            v246 = create_elem ( __consts_0.const_str__14 );
            v247 = v246.style;
            v247.background = __consts_0.const_str__32;
            v249 = ll_dict_getitem__Dict_String__String__String ( host_dict_2,host_0 );
            v250 = create_text_elem ( v249 );
            v251 = v246;
            v251.appendChild(v250);
            v246.id = host_0;
            v254 = v243;
            v254.appendChild(v246);
            v256 = v246;
            v257 = new StringBuilder();
            v257.ll_append(__consts_0.const_str__33);
            v259 = ll_str__StringR_StringConst_String ( undefined,host_0 );
            v257.ll_append(v259);
            v257.ll_append(__consts_0.const_str__34);
            v262 = v257.ll_build();
            v256.setAttribute(__consts_0.const_str__35,v262);
            v264 = v246;
            v264.setAttribute(__consts_0.const_str__36,__consts_0.const_str__37);
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

function get_elem (el_0) {
    var v217,v218,v219;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v218 = __consts_0.Document;
            v219 = v218.getElementById(el_0);
            v217 = v219;
            block = 1;
            break;
            case 1:
            return ( v217 );
        }
    }
}

function ll_strconcat__String_String (obj_0,arg0_0) {
    var v220,v221,v222;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v221 = obj_0;
            v222 = (v221+arg0_0);
            v220 = v222;
            block = 1;
            break;
            case 1:
            return ( v220 );
        }
    }
}

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
function ll_dict_getitem__Dict_String__Record_item2__Str_St (d_2,key_4) {
    var v223,v224,v225,v226,v227,v228,v229,etype_3,evalue_3,key_5,v230,v231,v232;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v224 = d_2;
            v225 = (v224[key_4]!=undefined);
            v226 = v225;
            if (v226 == true)
            {
                key_5 = key_4;
                v230 = d_2;
                block = 3;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v227 = __consts_0.exceptions_KeyError;
            v228 = v227.meta;
            v229 = v227;
            etype_3 = v228;
            evalue_3 = v229;
            block = 2;
            break;
            case 2:
            throw(evalue_3);
            case 3:
            v231 = v230;
            v232 = v231[key_5];
            v223 = v232;
            block = 4;
            break;
            case 4:
            return ( v223 );
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

function ll_streq__String_String (s1_0,s2_0) {
    var v302,v303,v304,v305,s2_1,v306,v307,v308,v309,v310,v311;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v303 = !!s1_0;
            v304 = !v303;
            v305 = v304;
            if (v305 == true)
            {
                v309 = s2_0;
                block = 3;
                break;
            }
            else{
                s2_1 = s2_0;
                v306 = s1_0;
                block = 1;
                break;
            }
            case 1:
            v307 = v306;
            v308 = (v307==s2_1);
            v302 = v308;
            block = 2;
            break;
            case 2:
            return ( v302 );
            case 3:
            v310 = !!v309;
            v311 = !v310;
            v302 = v311;
            block = 2;
            break;
        }
    }
}

function ll_str__StringR_StringConst_String (self_0,s_1) {
    var v233;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v233 = s_1;
            block = 1;
            break;
            case 1:
            return ( v233 );
        }
    }
}

function exceptions_KeyError () {
}

exceptions_KeyError.prototype.toString = function (){
    return ( '<exceptions_KeyError instance>' );
}

inherits(exceptions_KeyError,exceptions_LookupError);
function ll_dict_kvi__Dict_String__String__List_String_LlT_ (d_3,LIST_0,func_1) {
    var v312,v313,v314,v315,v316,v317,i_0,it_0,result_0,v318,v319,v320,i_1,it_1,result_1,v321,v322,v323,v324,it_2,result_2,v325,v326;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v313 = d_3;
            v314 = get_dict_len ( v313 );
            v315 = ll_newlist__List_String_LlT_Signed ( undefined,v314 );
            v316 = d_3;
            v317 = dict_items_iterator ( v316 );
            i_0 = 0;
            it_0 = v317;
            result_0 = v315;
            block = 1;
            break;
            case 1:
            v318 = it_0;
            v319 = v318.ll_go_next();
            v320 = v319;
            if (v320 == true)
            {
                i_1 = i_0;
                it_1 = it_0;
                result_1 = result_0;
                block = 3;
                break;
            }
            else{
                v312 = result_0;
                block = 2;
                break;
            }
            case 2:
            return ( v312 );
            case 3:
            v321 = result_1;
            v322 = it_1;
            v323 = v322.ll_current_key();
            v321[i_1]=v323;
            it_2 = it_1;
            result_2 = result_1;
            v325 = i_1;
            block = 4;
            break;
            case 4:
            v326 = (v325+1);
            i_0 = v326;
            it_0 = it_2;
            result_0 = result_2;
            block = 1;
            break;
        }
    }
}

function update_rsync () {
    var v327,v328,v329,v330,v331,v332,v333,v334,v335,elem_7,v336,v337,v338,v339,v340,v341,v342,v343,v344,elem_8,v345,v346,v347,v348,v349,v350,v351,v352,v353,v354,v355,text_0,elem_9,v356,v357,v358,v359,v360;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v328 = __consts_0.py____test_rsession_webjs_Globals.ofinished;
            v329 = v328;
            if (v329 == true)
            {
                block = 4;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            v330 = __consts_0.Document;
            v331 = v330.getElementById(__consts_0.const_str__38);
            v332 = __consts_0.py____test_rsession_webjs_Globals.orsync_done;
            v333 = v332;
            v334 = (v333==1);
            v335 = v334;
            if (v335 == true)
            {
                v357 = v331;
                block = 6;
                break;
            }
            else{
                elem_7 = v331;
                block = 2;
                break;
            }
            case 2:
            v336 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v337 = ll_char_mul__Char_Signed ( '.',v336 );
            v338 = ll_strconcat__String_String ( __consts_0.const_str__39,v337 );
            v339 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v340 = (v339+1);
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = v340;
            v342 = __consts_0.py____test_rsession_webjs_Globals.orsync_dots;
            v343 = (v342>5);
            v344 = v343;
            if (v344 == true)
            {
                text_0 = v338;
                elem_9 = elem_7;
                block = 5;
                break;
            }
            else{
                elem_8 = elem_7;
                v345 = v338;
                block = 3;
                break;
            }
            case 3:
            v346 = new StringBuilder();
            v346.ll_append(__consts_0.const_str__40);
            v348 = ll_str__StringR_StringConst_String ( undefined,v345 );
            v346.ll_append(v348);
            v346.ll_append(__consts_0.const_str__41);
            v351 = v346.ll_build();
            v352 = elem_8.childNodes;
            v353 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v352,0 );
            v353.nodeValue = v351;
            setTimeout ( 'update_rsync()',1000 );
            block = 4;
            break;
            case 4:
            return ( v327 );
            case 5:
            __consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
            elem_8 = elem_9;
            v345 = text_0;
            block = 3;
            break;
            case 6:
            v358 = v357.childNodes;
            v359 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v358,0 );
            v359.nodeValue = __consts_0.const_str__38;
            block = 4;
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
            v291 = v290.getElementById(__consts_0.const_str__28);
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
            v295.setAttribute(__consts_0.const_str__29,__consts_0.const_str__42);
            __consts_0.py____test_rsession_webjs_Options.oscroll = true;
            block = 1;
            break;
            case 4:
            v299 = v298;
            v299.removeAttribute(__consts_0.const_str__29);
            __consts_0.py____test_rsession_webjs_Options.oscroll = false;
            block = 1;
            break;
        }
    }
}

function ll_newdict__Dict_String__List_String__LlT (DICT_0) {
    var v361,v362;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v362 = new Object();
            v361 = v362;
            block = 1;
            break;
            case 1:
            return ( v361 );
        }
    }
}

function comeback (msglist_0) {
    var v363,v364,v365,v366,msglist_1,v367,v368,v369,v370,msglist_2,v371,v372,last_exc_value_3,msglist_3,v373,v374,v375,v376,msglist_4,v377,v378,v379,v380,v381,v382,last_exc_value_4,v383,v384,v385,v386,v387,v388,v389;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v364 = ll_len__List_Dict_String__String__ ( msglist_0 );
            v365 = (v364==0);
            v366 = v365;
            if (v366 == true)
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
            v367 = __consts_0.py____test_rsession_webjs_Globals.opending;
            v368 = 0;
            v369 = ll_listslice_startonly__List_Dict_String__String__ ( undefined,v367,v368 );
            v370 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,v369 );
            msglist_2 = msglist_1;
            v371 = v370;
            block = 2;
            break;
            case 2:
            try {
                v372 = ll_listnext__Record_index__Signed__iterable ( v371 );
                msglist_3 = msglist_2;
                v373 = v371;
                v374 = v372;
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
            v375 = process ( v374 );
            v376 = v375;
            if (v376 == true)
            {
                msglist_2 = msglist_3;
                v371 = v373;
                block = 2;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 4:
            return ( v363 );
            case 5:
            v377 = new Array();
            v377.length = 0;
            __consts_0.py____test_rsession_webjs_Globals.opending = v377;
            v380 = ll_listiter__Record_index__Signed__iterable_List_D ( undefined,msglist_4 );
            v381 = v380;
            block = 6;
            break;
            case 6:
            try {
                v382 = ll_listnext__Record_index__Signed__iterable ( v381 );
                v383 = v381;
                v384 = v382;
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
            v385 = process ( v384 );
            v386 = v385;
            if (v386 == true)
            {
                v381 = v383;
                block = 6;
                break;
            }
            else{
                block = 4;
                break;
            }
            case 8:
            v387 = __consts_0.ExportedMethods;
            v388 = __consts_0.py____test_rsession_webjs_Globals.osessid;
            v389 = v387.show_all_statuses(v388,comeback);
            block = 4;
            break;
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
            v487 = v486.getElementById(__consts_0.const_str__17);
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
            v498 = create_elem ( __consts_0.const_str__13 );
            v499 = create_elem ( __consts_0.const_str__14 );
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
            v523 = create_elem ( __consts_0.const_str__13 );
            v524 = create_elem ( __consts_0.const_str__14 );
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
            v561.ll_append(__consts_0.const_str__40);
            v563 = ll_str__StringR_StringConst_String ( undefined,v553 );
            v561.ll_append(v563);
            v561.ll_append(__consts_0.const_str__41);
            v566 = v561.ll_build();
            v567 = __consts_0.Document;
            v568 = v567.getElementById(__consts_0.const_str__38);
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
            v621.ll_append(__consts_0.const_str__41);
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

function ll_prepend__List_String__String (l_10,newitem_1) {
    var v817,v818,v819,v820,v821,v822,l_11,newitem_2,dst_0,v823,v824,newitem_3,v825,v826,v827,l_12,newitem_4,dst_1,v828,v829,v830,v831,v832;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v818 = l_10;
            v819 = v818.length;
            v820 = l_10;
            v821 = (v819+1);
            v820.length = v821;
            l_11 = l_10;
            newitem_2 = newitem_1;
            dst_0 = v819;
            block = 1;
            break;
            case 1:
            v823 = (dst_0>0);
            v824 = v823;
            if (v824 == true)
            {
                l_12 = l_11;
                newitem_4 = newitem_2;
                dst_1 = dst_0;
                block = 4;
                break;
            }
            else{
                newitem_3 = newitem_2;
                v825 = l_11;
                block = 2;
                break;
            }
            case 2:
            v826 = v825;
            v826[0]=newitem_3;
            block = 3;
            break;
            case 3:
            return ( v817 );
            case 4:
            v828 = (dst_1-1);
            v829 = l_12;
            v830 = l_12;
            v831 = v830[v828];
            v829[dst_1]=v831;
            l_11 = l_12;
            newitem_2 = newitem_4;
            dst_0 = v828;
            block = 1;
            break;
        }
    }
}

function ll_int_str__IntegerR_SignedConst_Signed (repr_0,i_6) {
    var v836,v837;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v837 = ll_int2dec__Signed ( i_6 );
            v836 = v837;
            block = 1;
            break;
            case 1:
            return ( v836 );
        }
    }
}

function ll_newlist__List_String_LlT_Signed (LIST_1,length_0) {
    var v390,v391,v392,v393;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v391 = new Array();
            v392 = v391;
            v392.length = length_0;
            v390 = v391;
            block = 1;
            break;
            case 1:
            return ( v390 );
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

function ll_len__List_String_ (l_13) {
    var v833,v834,v835;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v834 = l_13;
            v835 = v834.length;
            v833 = v835;
            block = 1;
            break;
            case 1:
            return ( v833 );
        }
    }
}

function ll_newlist__List_Dict_String__String__LlT_Signed (self_1,length_1) {
    var v636,v637;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v637 = ll_newlist__List_Dict_String__String__LlT_Signed_0 ( undefined,length_1 );
            v636 = v637;
            block = 1;
            break;
            case 1:
            return ( v636 );
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

function show_crash () {
    var v645,v646,v647,v648,v649,v650,v651,v652;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__74;
            v648 = __consts_0.Document;
            v649 = v648.getElementById(__consts_0.const_str__38);
            v650 = v649.childNodes;
            v651 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v650,0 );
            v651.nodeValue = __consts_0.const_str__75;
            block = 1;
            break;
            case 1:
            return ( v645 );
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

function scroll_down_if_needed (mbox_2) {
    var v638,v639,v640,v641,v642,v643,v644;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v639 = __consts_0.py____test_rsession_webjs_Options.oscroll;
            v640 = v639;
            if (v640 == true)
            {
                v641 = mbox_2;
                block = 2;
                break;
            }
            else{
                block = 1;
                break;
            }
            case 1:
            return ( v638 );
            case 2:
            v642 = v641.parentNode;
            v643 = v642;
            v643.scrollIntoView();
            block = 1;
            break;
        }
    }
}

function ll_append__List_Dict_String__String___Dict_String_ (l_9,newitem_0) {
    var v661,v662,v663,v664,v665,v666,v667,v668;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v662 = l_9;
            v663 = v662.length;
            v664 = l_9;
            v665 = (v663+1);
            v664.length = v665;
            v667 = l_9;
            v667[v663]=newitem_0;
            block = 1;
            break;
            case 1:
            return ( v661 );
        }
    }
}

function make_module_box (msg_30) {
    var v838,v839,v840,v841,v842,v843,v844,v845,v846,v847,v848,v849,v850,v851,v852,v853,v854,v855,v856,v857,v858,v859,v860,v861,v862,v863,v864,v865,v866,v867,v868,v869,v870,v871,v872,v873,v874,v875,v876,v877,v878,v879,v880,v881,v882,v883,v884,v885,v886,v887,v888,v889,v890,v891,v892,v893,v894,v895,v896,v897;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v839 = create_elem ( __consts_0.const_str__13 );
            v840 = create_elem ( __consts_0.const_str__14 );
            v841 = v839;
            v841.appendChild(v840);
            v843 = v840;
            v844 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__76 );
            v845 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__77 );
            v846 = new Object();
            v846.item0 = v844;
            v846.item1 = v845;
            v849 = v846.item0;
            v850 = v846.item1;
            v851 = new StringBuilder();
            v852 = ll_str__StringR_StringConst_String ( undefined,v849 );
            v851.ll_append(v852);
            v851.ll_append(__consts_0.const_str__78);
            v855 = ll_str__StringR_StringConst_String ( undefined,v850 );
            v851.ll_append(v855);
            v851.ll_append(__consts_0.const_str__41);
            v858 = v851.ll_build();
            v859 = create_text_elem ( v858 );
            v843.appendChild(v859);
            v861 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__77 );
            v862 = ll_int__String_Signed ( v861,10 );
            v863 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__79[v863]=v862;
            v865 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__76 );
            v866 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__80[v866]=v865;
            v868 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v869 = ll_strconcat__String_String ( __consts_0.const_str__81,v868 );
            v840.id = v869;
            v871 = v840;
            v872 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v873 = new Object();
            v873.item0 = v872;
            v875 = v873.item0;
            v876 = new StringBuilder();
            v876.ll_append(__consts_0.const_str__82);
            v878 = ll_str__StringR_StringConst_String ( undefined,v875 );
            v876.ll_append(v878);
            v876.ll_append(__consts_0.const_str__34);
            v881 = v876.ll_build();
            v871.setAttribute(__consts_0.const_str__35,v881);
            v883 = v840;
            v883.setAttribute(__consts_0.const_str__36,__consts_0.const_str__83);
            v885 = create_elem ( __consts_0.const_str__14 );
            v886 = v839;
            v886.appendChild(v885);
            v888 = create_elem ( __consts_0.const_str__84 );
            v889 = v885;
            v889.appendChild(v888);
            v891 = create_elem ( __consts_0.const_str__12 );
            v892 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            v891.id = v892;
            v894 = v888;
            v894.appendChild(v891);
            v896 = ll_dict_getitem__Dict_String__String__String ( msg_30,__consts_0.const_str__56 );
            __consts_0.const_tuple__85[v896]=0;
            v838 = v839;
            block = 1;
            break;
            case 1:
            return ( v838 );
        }
    }
}

function show_interrupt () {
    var v653,v654,v655,v656,v657,v658,v659,v660;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            __consts_0.py____test_rsession_webjs_Globals.ofinished = true;
            __consts_0.Document.title = __consts_0.const_str__86;
            v656 = __consts_0.Document;
            v657 = v656.getElementById(__consts_0.const_str__38);
            v658 = v657.childNodes;
            v659 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v658,0 );
            v659.nodeValue = __consts_0.const_str__87;
            block = 1;
            break;
            case 1:
            return ( v653 );
        }
    }
}

function add_received_item_outcome (msg_20,module_part_2) {
    var v669,v670,v671,v672,msg_21,module_part_3,v673,v674,v675,v676,v677,v678,v679,v680,v681,v682,v683,v684,v685,v686,v687,v688,v689,v690,v691,msg_22,module_part_4,item_name_6,td_0,v692,v693,v694,v695,msg_23,module_part_5,item_name_7,td_1,v696,v697,v698,v699,v700,v701,v702,v703,v704,v705,v706,v707,v708,v709,v710,v711,v712,v713,v714,v715,msg_24,module_part_6,td_2,v716,v717,v718,v719,v720,module_part_7,td_3,v721,v722,v723,v724,v725,v726,v727,v728,v729,v730,v731,v732,v733,v734,v735,v736,v737,v738,v739,v740,v741,v742,v743,v744,v745,v746,v747,v748,v749,v750,v751,v752,v753,v754,v755,msg_25,module_part_8,td_4,v756,v757,v758,msg_26,module_part_9,item_name_8,td_5,v759,v760,v761,v762,msg_27,module_part_10,item_name_9,td_6,v763,v764,v765,v766,v767,v768,v769,v770,v771,v772,v773,v774,v775,v776,v777,v778,v779,v780,v781,v782,msg_28,module_part_11,td_7,v783,v784,v785,msg_29,module_part_12,v786,v787,v788,v789,v790,v791,v792,v793,v794,v795,v796,v797,v798,v799,v800,v801,v802,v803,v804,v805,v806,v807,v808,v809,v810,v811,v812,v813,v814,v815,v816;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v670 = ll_dict_getitem__Dict_String__String__String ( msg_20,__consts_0.const_str__70 );
            v671 = ll_strlen__String ( v670 );
            v672 = !!v671;
            if (v672 == true)
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
            v673 = create_elem ( __consts_0.const_str__14 );
            v674 = v673;
            v675 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__56 );
            v676 = new Object();
            v676.item0 = v675;
            v678 = v676.item0;
            v679 = new StringBuilder();
            v679.ll_append(__consts_0.const_str__82);
            v681 = ll_str__StringR_StringConst_String ( undefined,v678 );
            v679.ll_append(v681);
            v679.ll_append(__consts_0.const_str__34);
            v684 = v679.ll_build();
            v674.setAttribute(__consts_0.const_str__35,v684);
            v686 = v673;
            v686.setAttribute(__consts_0.const_str__36,__consts_0.const_str__83);
            v688 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__56 );
            v689 = ll_dict_getitem__Dict_String__String__String ( msg_21,__consts_0.const_str__88 );
            v690 = ll_streq__String_String ( v689,__consts_0.const_str__30 );
            v691 = v690;
            if (v691 == true)
            {
                msg_28 = msg_21;
                module_part_11 = module_part_3;
                td_7 = v673;
                block = 10;
                break;
            }
            else{
                msg_22 = msg_21;
                module_part_4 = module_part_3;
                item_name_6 = v688;
                td_0 = v673;
                block = 2;
                break;
            }
            case 2:
            v692 = ll_dict_getitem__Dict_String__String__String ( msg_22,__consts_0.const_str__89 );
            v693 = ll_streq__String_String ( v692,__consts_0.const_str__90 );
            v694 = !v693;
            v695 = v694;
            if (v695 == true)
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
            v696 = create_elem ( __consts_0.const_str__91 );
            v697 = v696;
            v698 = ll_dict_getitem__Dict_String__String__String ( msg_23,__consts_0.const_str__56 );
            v699 = new Object();
            v699.item0 = v698;
            v701 = v699.item0;
            v702 = new StringBuilder();
            v702.ll_append(__consts_0.const_str__92);
            v704 = ll_str__StringR_StringConst_String ( undefined,v701 );
            v702.ll_append(v704);
            v702.ll_append(__consts_0.const_str__34);
            v707 = v702.ll_build();
            v697.setAttribute(__consts_0.const_str__93,v707);
            v709 = create_text_elem ( __consts_0.const_str__94 );
            v710 = v696;
            v710.appendChild(v709);
            v712 = td_1;
            v712.appendChild(v696);
            v714 = __consts_0.ExportedMethods;
            v715 = v714.show_fail(item_name_7,fail_come_back);
            msg_24 = msg_23;
            module_part_6 = module_part_5;
            td_2 = td_1;
            block = 4;
            break;
            case 4:
            v716 = ll_dict_getitem__Dict_String__String__String ( msg_24,__consts_0.const_str__69 );
            v717 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__85,v716 );
            v718 = (v717%50);
            v719 = (v718==0);
            v720 = v719;
            if (v720 == true)
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
                v721 = msg_24;
                block = 5;
                break;
            }
            case 5:
            v722 = ll_dict_getitem__Dict_String__String__String ( v721,__consts_0.const_str__69 );
            v723 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__85,v722 );
            v724 = (v723+1);
            __consts_0.const_tuple__85[v722]=v724;
            v726 = ll_strconcat__String_String ( __consts_0.const_str__81,v722 );
            v727 = get_elem ( v726 );
            v728 = ll_dict_getitem__Dict_String__String__String ( __consts_0.const_tuple__80,v722 );
            v729 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__85,v722 );
            v730 = ll_dict_getitem__Dict_String__Signed__String ( __consts_0.const_tuple__79,v722 );
            v731 = new Object();
            v731.item0 = v728;
            v731.item1 = v729;
            v731.item2 = v730;
            v735 = v731.item0;
            v736 = v731.item1;
            v737 = v731.item2;
            v738 = new StringBuilder();
            v739 = ll_str__StringR_StringConst_String ( undefined,v735 );
            v738.ll_append(v739);
            v738.ll_append(__consts_0.const_str__73);
            v742 = v736.toString();
            v738.ll_append(v742);
            v738.ll_append(__consts_0.const_str__95);
            v745 = v737.toString();
            v738.ll_append(v745);
            v738.ll_append(__consts_0.const_str__41);
            v748 = v738.ll_build();
            v749 = v727.childNodes;
            v750 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v749,0 );
            v750.nodeValue = v748;
            v752 = module_part_7.childNodes;
            v753 = ll_getitem__dum_nocheckConst_List_ExternalType__Si ( undefined,v752,-1 );
            v754 = v753;
            v754.appendChild(td_3);
            block = 6;
            break;
            case 6:
            return ( v669 );
            case 7:
            v756 = create_elem ( __consts_0.const_str__13 );
            v757 = module_part_8;
            v757.appendChild(v756);
            module_part_7 = module_part_8;
            td_3 = td_4;
            v721 = msg_25;
            block = 5;
            break;
            case 8:
            v759 = ll_dict_getitem__Dict_String__String__String ( msg_26,__consts_0.const_str__89 );
            v760 = ll_streq__String_String ( v759,__consts_0.const_str__96 );
            v761 = !v760;
            v762 = v761;
            if (v762 == true)
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
            v763 = __consts_0.ExportedMethods;
            v764 = v763.show_skip(item_name_9,skip_come_back);
            v765 = create_elem ( __consts_0.const_str__91 );
            v766 = v765;
            v767 = ll_dict_getitem__Dict_String__String__String ( msg_27,__consts_0.const_str__56 );
            v768 = new Object();
            v768.item0 = v767;
            v770 = v768.item0;
            v771 = new StringBuilder();
            v771.ll_append(__consts_0.const_str__97);
            v773 = ll_str__StringR_StringConst_String ( undefined,v770 );
            v771.ll_append(v773);
            v771.ll_append(__consts_0.const_str__34);
            v776 = v771.ll_build();
            v766.setAttribute(__consts_0.const_str__93,v776);
            v778 = create_text_elem ( __consts_0.const_str__98 );
            v779 = v765;
            v779.appendChild(v778);
            v781 = td_6;
            v781.appendChild(v765);
            msg_24 = msg_27;
            module_part_6 = module_part_10;
            td_2 = td_6;
            block = 4;
            break;
            case 10:
            v783 = create_text_elem ( __consts_0.const_str__99 );
            v784 = td_7;
            v784.appendChild(v783);
            msg_24 = msg_28;
            module_part_6 = module_part_11;
            td_2 = td_7;
            block = 4;
            break;
            case 11:
            v786 = __consts_0.Document;
            v787 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v788 = v786.getElementById(v787);
            v789 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v790 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v791 = ll_dict_getitem__Dict_String__List_String___String ( v789,v790 );
            v792 = v791;
            v793 = ll_pop_default__dum_nocheckConst_List_String_ ( undefined,v792 );
            v794 = __consts_0.py____test_rsession_webjs_Globals.ohost_pending;
            v795 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v796 = ll_dict_getitem__Dict_String__List_String___String ( v794,v795 );
            v797 = ll_len__List_String_ ( v796 );
            v798 = __consts_0.py____test_rsession_webjs_Globals.ohost_dict;
            v799 = ll_dict_getitem__Dict_String__String__String ( msg_29,__consts_0.const_str__70 );
            v800 = ll_dict_getitem__Dict_String__String__String ( v798,v799 );
            v801 = new Object();
            v801.item0 = v800;
            v801.item1 = v797;
            v804 = v801.item0;
            v805 = v801.item1;
            v806 = new StringBuilder();
            v807 = ll_str__StringR_StringConst_String ( undefined,v804 );
            v806.ll_append(v807);
            v806.ll_append(__consts_0.const_str__73);
            v810 = ll_int_str__IntegerR_SignedConst_Signed ( undefined,v805 );
            v806.ll_append(v810);
            v806.ll_append(__consts_0.const_str__41);
            v813 = v806.ll_build();
            v814 = v788.childNodes;
            v815 = ll_getitem_nonneg__dum_nocheckConst_List_ExternalT ( undefined,v814,0 );
            v815.nodeValue = v813;
            msg_21 = msg_29;
            module_part_3 = module_part_12;
            block = 1;
            break;
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

function ll_int__String_Signed (s_2,base_0) {
    var v904,v905,v906,v907,v908,v909,etype_5,evalue_5,s_3,base_1,v910,s_4,base_2,v911,v912,s_5,base_3,v913,v914,s_6,base_4,i_8,strlen_0,v915,v916,s_7,base_5,i_9,strlen_1,v917,v918,v919,v920,v921,s_8,base_6,i_10,strlen_2,v922,v923,v924,v925,s_9,base_7,i_11,strlen_3,v926,v927,v928,v929,s_10,base_8,val_0,i_12,sign_0,strlen_4,v930,v931,s_11,val_1,i_13,sign_1,strlen_5,v932,v933,val_2,sign_2,v934,v935,v936,v937,v938,v939,v940,v941,v942,v943,s_12,val_3,i_14,sign_3,strlen_6,v944,v945,v946,v947,s_13,val_4,sign_4,strlen_7,v948,v949,s_14,base_9,val_5,i_15,sign_5,strlen_8,v950,v951,v952,v953,v954,s_15,base_10,c_0,val_6,i_16,sign_6,strlen_9,v955,v956,s_16,base_11,c_1,val_7,i_17,sign_7,strlen_10,v957,v958,s_17,base_12,c_2,val_8,i_18,sign_8,strlen_11,v959,s_18,base_13,c_3,val_9,i_19,sign_9,strlen_12,v960,v961,s_19,base_14,val_10,i_20,sign_10,strlen_13,v962,v963,s_20,base_15,val_11,i_21,digit_0,sign_11,strlen_14,v964,v965,s_21,base_16,i_22,digit_1,sign_12,strlen_15,v966,v967,v968,v969,s_22,base_17,c_4,val_12,i_23,sign_13,strlen_16,v970,s_23,base_18,c_5,val_13,i_24,sign_14,strlen_17,v971,v972,s_24,base_19,val_14,i_25,sign_15,strlen_18,v973,v974,v975,s_25,base_20,c_6,val_15,i_26,sign_16,strlen_19,v976,s_26,base_21,c_7,val_16,i_27,sign_17,strlen_20,v977,v978,s_27,base_22,val_17,i_28,sign_18,strlen_21,v979,v980,v981,s_28,base_23,strlen_22,v982,v983,s_29,base_24,strlen_23,v984,v985,s_30,base_25,i_29,strlen_24,v986,v987,v988,v989,s_31,base_26,strlen_25,v990,v991;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v905 = (2<=base_0);
            v906 = v905;
            if (v906 == true)
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
            v907 = __consts_0.exceptions_ValueError;
            v908 = v907.meta;
            v909 = v907;
            etype_5 = v908;
            evalue_5 = v909;
            block = 2;
            break;
            case 2:
            throw(evalue_5);
            case 3:
            v910 = (base_1<=36);
            s_4 = s_3;
            base_2 = base_1;
            v911 = v910;
            block = 4;
            break;
            case 4:
            v912 = v911;
            if (v912 == true)
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
            v913 = s_5;
            v914 = v913.length;
            s_6 = s_5;
            base_4 = base_3;
            i_8 = 0;
            strlen_0 = v914;
            block = 6;
            break;
            case 6:
            v915 = (i_8<strlen_0);
            v916 = v915;
            if (v916 == true)
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
            v917 = (i_9<strlen_1);
            v918 = v917;
            if (v918 == true)
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
            v919 = __consts_0.exceptions_ValueError;
            v920 = v919.meta;
            v921 = v919;
            etype_5 = v920;
            evalue_5 = v921;
            block = 2;
            break;
            case 9:
            v922 = s_8;
            v923 = v922[i_10];
            v924 = (v923=='-');
            v925 = v924;
            if (v925 == true)
            {
                s_29 = s_8;
                base_24 = base_6;
                strlen_23 = strlen_2;
                v984 = i_10;
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
            v926 = s_9;
            v927 = v926[i_11];
            v928 = (v927=='+');
            v929 = v928;
            if (v929 == true)
            {
                s_28 = s_9;
                base_23 = base_7;
                strlen_22 = strlen_3;
                v982 = i_11;
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
            v930 = (i_12<strlen_4);
            v931 = v930;
            if (v931 == true)
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
            v932 = (i_13<strlen_5);
            v933 = v932;
            if (v933 == true)
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
                v934 = i_13;
                v935 = strlen_5;
                block = 13;
                break;
            }
            case 13:
            v936 = (v934==v935);
            v937 = v936;
            if (v937 == true)
            {
                v941 = sign_2;
                v942 = val_2;
                block = 15;
                break;
            }
            else{
                block = 14;
                break;
            }
            case 14:
            v938 = __consts_0.exceptions_ValueError;
            v939 = v938.meta;
            v940 = v938;
            etype_5 = v939;
            evalue_5 = v940;
            block = 2;
            break;
            case 15:
            v943 = (v941*v942);
            v904 = v943;
            block = 16;
            break;
            case 16:
            return ( v904 );
            case 17:
            v944 = s_12;
            v945 = v944[i_14];
            v946 = (v945==' ');
            v947 = v946;
            if (v947 == true)
            {
                s_13 = s_12;
                val_4 = val_3;
                sign_4 = sign_3;
                strlen_7 = strlen_6;
                v948 = i_14;
                block = 18;
                break;
            }
            else{
                val_2 = val_3;
                sign_2 = sign_3;
                v934 = i_14;
                v935 = strlen_6;
                block = 13;
                break;
            }
            case 18:
            v949 = (v948+1);
            s_11 = s_13;
            val_1 = val_4;
            i_13 = v949;
            sign_1 = sign_4;
            strlen_5 = strlen_7;
            block = 12;
            break;
            case 19:
            v950 = s_14;
            v951 = v950[i_15];
            v952 = v951.charCodeAt(0);
            v953 = (97<=v952);
            v954 = v953;
            if (v954 == true)
            {
                s_25 = s_14;
                base_20 = base_9;
                c_6 = v952;
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
                c_0 = v952;
                val_6 = val_5;
                i_16 = i_15;
                sign_6 = sign_5;
                strlen_9 = strlen_8;
                block = 20;
                break;
            }
            case 20:
            v955 = (65<=c_0);
            v956 = v955;
            if (v956 == true)
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
            v957 = (48<=c_1);
            v958 = v957;
            if (v958 == true)
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
            v959 = (c_2<=57);
            s_18 = s_17;
            base_13 = base_12;
            c_3 = c_2;
            val_9 = val_8;
            i_19 = i_18;
            sign_9 = sign_8;
            strlen_12 = strlen_11;
            v960 = v959;
            block = 23;
            break;
            case 23:
            v961 = v960;
            if (v961 == true)
            {
                s_19 = s_18;
                base_14 = base_13;
                val_10 = val_9;
                i_20 = i_19;
                sign_10 = sign_9;
                strlen_13 = strlen_12;
                v962 = c_3;
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
            v963 = (v962-48);
            s_20 = s_19;
            base_15 = base_14;
            val_11 = val_10;
            i_21 = i_20;
            digit_0 = v963;
            sign_11 = sign_10;
            strlen_14 = strlen_13;
            block = 25;
            break;
            case 25:
            v964 = (digit_0>=base_15);
            v965 = v964;
            if (v965 == true)
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
                v966 = val_11;
                block = 26;
                break;
            }
            case 26:
            v967 = (v966*base_16);
            v968 = (v967+digit_1);
            v969 = (i_22+1);
            s_10 = s_21;
            base_8 = base_16;
            val_0 = v968;
            i_12 = v969;
            sign_0 = sign_12;
            strlen_4 = strlen_15;
            block = 11;
            break;
            case 27:
            v970 = (c_4<=90);
            s_23 = s_22;
            base_18 = base_17;
            c_5 = c_4;
            val_13 = val_12;
            i_24 = i_23;
            sign_14 = sign_13;
            strlen_17 = strlen_16;
            v971 = v970;
            block = 28;
            break;
            case 28:
            v972 = v971;
            if (v972 == true)
            {
                s_24 = s_23;
                base_19 = base_18;
                val_14 = val_13;
                i_25 = i_24;
                sign_15 = sign_14;
                strlen_18 = strlen_17;
                v973 = c_5;
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
            v974 = (v973-65);
            v975 = (v974+10);
            s_20 = s_24;
            base_15 = base_19;
            val_11 = val_14;
            i_21 = i_25;
            digit_0 = v975;
            sign_11 = sign_15;
            strlen_14 = strlen_18;
            block = 25;
            break;
            case 30:
            v976 = (c_6<=122);
            s_26 = s_25;
            base_21 = base_20;
            c_7 = c_6;
            val_16 = val_15;
            i_27 = i_26;
            sign_17 = sign_16;
            strlen_20 = strlen_19;
            v977 = v976;
            block = 31;
            break;
            case 31:
            v978 = v977;
            if (v978 == true)
            {
                s_27 = s_26;
                base_22 = base_21;
                val_17 = val_16;
                i_28 = i_27;
                sign_18 = sign_17;
                strlen_21 = strlen_20;
                v979 = c_7;
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
            v980 = (v979-97);
            v981 = (v980+10);
            s_20 = s_27;
            base_15 = base_22;
            val_11 = val_17;
            i_21 = i_28;
            digit_0 = v981;
            sign_11 = sign_18;
            strlen_14 = strlen_21;
            block = 25;
            break;
            case 33:
            v983 = (v982+1);
            s_10 = s_28;
            base_8 = base_23;
            val_0 = 0;
            i_12 = v983;
            sign_0 = 1;
            strlen_4 = strlen_22;
            block = 11;
            break;
            case 34:
            v985 = (v984+1);
            s_10 = s_29;
            base_8 = base_24;
            val_0 = 0;
            i_12 = v985;
            sign_0 = -1;
            strlen_4 = strlen_23;
            block = 11;
            break;
            case 35:
            v986 = s_30;
            v987 = v986[i_29];
            v988 = (v987==' ');
            v989 = v988;
            if (v989 == true)
            {
                s_31 = s_30;
                base_26 = base_25;
                strlen_25 = strlen_24;
                v990 = i_29;
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
            v991 = (v990+1);
            s_6 = s_31;
            base_4 = base_26;
            i_8 = v991;
            strlen_0 = strlen_25;
            block = 6;
            break;
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

function fail_come_back (msg_31) {
    var v995,v996,v997,v998,v999,v1000,v1001,v1002,v1003,v1004;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v996 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__101 );
            v997 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__102 );
            v998 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__103 );
            v999 = new Object();
            v999.item0 = v996;
            v999.item1 = v997;
            v999.item2 = v998;
            v1003 = ll_dict_getitem__Dict_String__String__String ( msg_31,__consts_0.const_str__104 );
            __consts_0.const_tuple__23[v1003]=v999;
            block = 1;
            break;
            case 1:
            return ( v995 );
        }
    }
}

function skip_come_back (msg_32) {
    var v1029,v1030,v1031,v1032;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            v1030 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__57 );
            v1031 = ll_dict_getitem__Dict_String__String__String ( msg_32,__consts_0.const_str__104 );
            __consts_0.const_tuple__15[v1031]=v1030;
            block = 1;
            break;
            case 1:
            return ( v1029 );
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

function exceptions_ValueError () {
}

exceptions_ValueError.prototype.toString = function (){
    return ( '<exceptions_ValueError instance>' );
}

inherits(exceptions_ValueError,exceptions_StandardError);
function ll_null_item__List_String_ (lst_2) {
    var v1045,v1046;
    var block = 0;
    for(;;){
        switch(block){
            case 0:
            undefined;
            block = 1;
            break;
            case 1:
            return ( v1045 );
        }
    }
}

function Object_meta () {
    this.class_ = __consts_0.None;
}

Object_meta.prototype.toString = function (){
    return ( '<Object_meta instance>' );
}

function py____test_rsession_webjs_Globals_meta () {
}

py____test_rsession_webjs_Globals_meta.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Globals_meta instance>' );
}

inherits(py____test_rsession_webjs_Globals_meta,Object_meta);
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
function py____test_rsession_webjs_Options_meta () {
}

py____test_rsession_webjs_Options_meta.prototype.toString = function (){
    return ( '<py____test_rsession_webjs_Options_meta instance>' );
}

inherits(py____test_rsession_webjs_Options_meta,Object_meta);
__consts_0 = {};
__consts_0.const_str__66 = ' failures, ';
__consts_0.const_str__33 = "show_host('";
__consts_0.const_str__81 = '_txt_';
__consts_0.const_str__91 = 'a';
__consts_0.const_str__41 = ']';
__consts_0.const_list__114 = [];
__consts_0.const_str__49 = 'ReceivedItemOutcome';
__consts_0.const_str__82 = "show_info('";
__consts_0.const_str__58 = '- skipped (';
__consts_0.const_tuple = undefined;
__consts_0.const_str__37 = 'hide_host()';
__consts_0.const_str__83 = 'hide_info()';
__consts_0.const_str__20 = '#message';
__consts_0.ExportedMethods = new ExportedMethods();
__consts_0.const_str__12 = 'tbody';
__consts_0.const_tuple__79 = {};
__consts_0.exceptions_KeyError__108 = exceptions_KeyError;
__consts_0.exceptions_KeyError_meta = new exceptions_KeyError_meta();
__consts_0.const_str__59 = ')';
__consts_0.const_str__44 = 'main_table';
__consts_0.const_str__87 = 'Tests [interrupted]';
__consts_0.const_str__34 = "')";
__consts_0.const_str__53 = 'RsyncFinished';
__consts_0.const_str__65 = ' run, ';
__consts_0.exceptions_KeyError = new exceptions_KeyError();
__consts_0.const_str__102 = 'stdout';
__consts_0.const_str = 'aa';
__consts_0.const_str__67 = ' skipped';
__consts_0.const_str__74 = 'Py.test [crashed]';
__consts_0.const_str__48 = 'HostReady';
__consts_0.const_str__64 = 'FINISHED ';
__consts_0.const_str__39 = 'Rsyncing';
__consts_0.const_str__9 = 'info';
__consts_0.const_str__14 = 'td';
__consts_0.const_str__42 = 'true';
__consts_0.exceptions_ValueError__106 = exceptions_ValueError;
__consts_0.exceptions_StopIteration__110 = exceptions_StopIteration;
__consts_0.exceptions_StopIteration_meta = new exceptions_StopIteration_meta();
__consts_0.exceptions_StopIteration = new exceptions_StopIteration();
__consts_0.const_tuple__85 = {};
__consts_0.const_str__94 = 'F';
__consts_0.const_str__36 = 'onmouseout';
__consts_0.const_str__45 = 'type';
__consts_0.const_str__88 = 'passed';
__consts_0.const_str__99 = '.';
__consts_0.const_str__51 = 'FailedTryiter';
__consts_0.py____test_rsession_webjs_Options__112 = py____test_rsession_webjs_Options;
__consts_0.py____test_rsession_webjs_Options_meta = new py____test_rsession_webjs_Options_meta();
__consts_0.const_str__32 = '#ff0000';
__consts_0.const_str__29 = 'checked';
__consts_0.const_str__17 = 'messagebox';
__consts_0.const_str__56 = 'fullitemname';
__consts_0.const_str__84 = 'table';
__consts_0.const_str__68 = 'Py.test ';
__consts_0.const_str__63 = 'skips';
__consts_0.const_str__55 = 'CrashedExecution';
__consts_0.const_str__19 = '\n';
__consts_0.py____test_rsession_webjs_Options = new py____test_rsession_webjs_Options();
__consts_0.const_str__18 = 'pre';
__consts_0.const_str__86 = 'Py.test [interrupted]';
__consts_0.const_str__25 = '\n======== Stdout: ========\n';
__consts_0.const_str__71 = '#00ff00';
__consts_0.const_tuple__8 = undefined;
__consts_0.const_str__11 = 'beige';
__consts_0.const_str__77 = 'length';
__consts_0.const_tuple__80 = {};
__consts_0.const_str__101 = 'traceback';
__consts_0.const_str__43 = 'testmain';
__consts_0.const_str__97 = "javascript:show_skip('";
__consts_0.const_str__73 = '[';
__consts_0.const_str__75 = 'Tests [crashed]';
__consts_0.const_str__57 = 'reason';
__consts_0.const_str__92 = "javascript:show_traceback('";
__consts_0.const_str__38 = 'Tests';
__consts_0.const_tuple__23 = {};
__consts_0.const_str__98 = 's';
__consts_0.const_str__61 = 'run';
__consts_0.const_str__52 = 'SkippedTryiter';
__consts_0.const_str__90 = 'None';
__consts_0.const_str__30 = 'True';
__consts_0.const_str__95 = '/';
__consts_0.const_str__70 = 'hostkey';
__consts_0.const_str__62 = 'fails';
__consts_0.const_str__46 = 'ItemStart';
__consts_0.const_str__76 = 'itemname';
__consts_0.const_str__50 = 'TestFinished';
__consts_0.const_str__2 = 'jobs';
__consts_0.const_str__26 = '\n========== Stderr: ==========\n';
__consts_0.const_tuple__15 = {};
__consts_0.const_str__103 = 'stderr';
__consts_0.const_str__93 = 'href';
__consts_0.exceptions_ValueError_meta = new exceptions_ValueError_meta();
__consts_0.const_str__10 = 'visible';
__consts_0.const_str__96 = 'False';
__consts_0.const_str__35 = 'onmouseover';
__consts_0.const_str__60 = '- FAILED TO LOAD MODULE';
__consts_0.const_str__78 = '[0/';
__consts_0.const_list = undefined;
__consts_0.const_str__47 = 'SendItem';
__consts_0.const_str__69 = 'fullmodulename';
__consts_0.const_str__89 = 'skipped';
__consts_0.const_str__31 = 'hostsbody';
__consts_0.const_str__72 = '[0]';
__consts_0.const_str__3 = 'hidden';
__consts_0.const_str__24 = '====== Traceback: =========\n';
__consts_0.const_str__13 = 'tr';
__consts_0.const_str__104 = 'item_name';
__consts_0.const_str__40 = 'Tests [';
__consts_0.py____test_rsession_webjs_Globals__115 = py____test_rsession_webjs_Globals;
__consts_0.Document = document;
__consts_0.exceptions_ValueError = new exceptions_ValueError();
__consts_0.py____test_rsession_webjs_Globals_meta = new py____test_rsession_webjs_Globals_meta();
__consts_0.const_str__5 = '';
__consts_0.py____test_rsession_webjs_Globals = new py____test_rsession_webjs_Globals();
__consts_0.const_str__54 = 'InterruptedExecution';
__consts_0.const_str__28 = 'opt_scroll';
__consts_0.exceptions_KeyError_meta.class_ = __consts_0.exceptions_KeyError__108;
__consts_0.exceptions_KeyError.meta = __consts_0.exceptions_KeyError_meta;
__consts_0.exceptions_StopIteration_meta.class_ = __consts_0.exceptions_StopIteration__110;
__consts_0.exceptions_StopIteration.meta = __consts_0.exceptions_StopIteration_meta;
__consts_0.py____test_rsession_webjs_Options_meta.class_ = __consts_0.py____test_rsession_webjs_Options__112;
__consts_0.py____test_rsession_webjs_Options.meta = __consts_0.py____test_rsession_webjs_Options_meta;
__consts_0.py____test_rsession_webjs_Options.oscroll = true;
__consts_0.exceptions_ValueError_meta.class_ = __consts_0.exceptions_ValueError__106;
__consts_0.exceptions_ValueError.meta = __consts_0.exceptions_ValueError_meta;
__consts_0.py____test_rsession_webjs_Globals_meta.class_ = __consts_0.py____test_rsession_webjs_Globals__115;
__consts_0.py____test_rsession_webjs_Globals.odata_empty = true;
__consts_0.py____test_rsession_webjs_Globals.osessid = __consts_0.const_str__5;
__consts_0.py____test_rsession_webjs_Globals.ohost = __consts_0.const_str__5;
__consts_0.py____test_rsession_webjs_Globals.orsync_dots = 0;
__consts_0.py____test_rsession_webjs_Globals.ofinished = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_dict = __consts_0.const_tuple;
__consts_0.py____test_rsession_webjs_Globals.meta = __consts_0.py____test_rsession_webjs_Globals_meta;
__consts_0.py____test_rsession_webjs_Globals.opending = __consts_0.const_list__114;
__consts_0.py____test_rsession_webjs_Globals.orsync_done = false;
__consts_0.py____test_rsession_webjs_Globals.ohost_pending = __consts_0.const_tuple__8;
