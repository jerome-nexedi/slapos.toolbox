/**
 * Free Web File Manager is free software released under MIT License.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
 * TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 * CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 *
 * George Sarafov
 * http://freewebfilemanager.com
 */

var gsItem = function (type, name, path, size, id, exta, lastMod) {
    this.path = path;
    this.type = type;
    this.name = name;
    this.size = size;
    this.id = id;
    this.exta = exta.toLowerCase();
    this.lastMod = lastMod;

    this.getSize = function () {
        if (this.size < 1000000) {
            return Math.ceil(this.size / 1000) + ' KB';
        } else {
            return Math.ceil(this.size / 1000000) + ' MB';
        }
    };

    this.getExt = function () {
        return this.exta;
    };

    this.getLastMod = function () {
        return this.lastMod;
    };

    this.isEditable = function(){
        return !this.isPicture() && !this.isArchive();
    };

    this.isPicture = function(){
        return typeof(gs_ext_pictures[this.exta]) != 'undefined';
    };

    this.isArchive = function(){
        return typeof(gs_ext_arhives[this.exta]) != 'undefined';
    };

    this.getType = function(){
        type = 'unknown';
        if (this.isPicture()) {
            type = 'picture';
        } else if (this.isEditable()) {
            type = 'editable';
        } else if (this.isArchive()) {
            type = 'archive';
        }
        return type;
    };
};
var editor,
    modelist = modelist = require("ace/ext/modelist");
function setupEditor(){
    editor = ace.edit("editor");
    editor.setTheme("ace/theme/crimson_editor");

    editor.getSession().setMode("ace/mode/text");
    editor.getSession().setTabSize(2);
    editor.getSession().setUseSoftTabs(true);
    editor.renderer.setHScrollBarAlwaysVisible(false);
    editor.setReadOnly(true);
}

function updateCoords(c){
    jQuery('#gs_jcrop_x').val(c.x);
    jQuery('#gs_jcrop_y').val(c.y);
    jQuery('#gs_jcrop_w').val(c.w);
    jQuery('#gs_jcrop_h').val(c.h);
}

function gs_get_cur_item(id){
    result = null;
    if (typeof(gs_cur_items[id]) != 'undefined') {
        result = gs_cur_items[id];
    }
    return result;
}

function gs_show_loading() {
    jQuery("#gs_dir_content").html('<div class="loadingDiv">&nbsp;</div>');
}

function gsGetSelectedItemsPath() {
    var arr = new Array();
    for (var x in gs_clipboard) {
        arr.push(gs_clipboard[x].path);
    }
    if (arr.length > 0) {
        return arr.join(',,,');
    }
    return null;
}

function gsGetSelectedItems(){
    var arr = new Array();
    jQuery("#gs_content_table div.rowSelected").each(function(){
        var id = jQuery(this).attr('rel');
        if (typeof(gs_cur_items[id]) != 'undefined') {
            arr.push(gs_cur_items[id].name);
        }
    });
    if (arr.length > 0) {
        return arr.join(',,,');
    }
    return null;
}

function gsCheckResponce (data) {
    if (typeof(data) == 'undefined') {
        return;
    }
    if (data.substr(0 , 9) == '{result: ') {
        eval('var my_responce = ' + data + ';');
        if (typeof(my_responce.result != 'undefined')) {
            if (my_responce.result == '1') {
            //alert('OK');
            } else if (typeof(my_responce.gserror) != 'undefined') {
                alert(my_responce.gserror);
            } else {
                alert('Error');
            }
        }
        delete my_responce;
    }
}

function gs_storeSelectedItems(){
    gs_clipboard = new Array();
    jQuery("#gs_content_table div.rowSelected").each(function(){
        var id = jQuery(this).attr('rel');
        if (typeof(gs_cur_items[id]) != 'undefined') {
            gs_clipboard.push(gs_cur_items[id]);
        } else {
            alert('Uknown item selected');
        }
    });
}

function gs_showClipboardContent(){
    var diva = jQuery('#gsclipboardContent');
    var divaHtml = '';
    for (var xx in gs_clipboard) {
        var clasa = 'file';
        if (gs_clipboard[xx].getExt() == 'dir') {
            clasa = 'directory';
        }
        divaHtml += '<div class="'+ clasa +'">&nbsp;&nbsp;&nbsp;' + gs_clipboard[xx].path + '<div>';
    }
    diva.html(divaHtml);
    diva.dialog({
        title: 'Clipboard',
        modal: true,
        buttons: {
            "Clear": function() {
                gs_clipboard = new Array();
                jQuery('#gsclipboardContent').html('');
                jQuery("#gsClipBoard").html('0 items');
                jQuery(this).dialog('close');
            }
        }
    });
    return false;
}

function gs_makeUrl(root, params){
    if (root.indexOf('?') !=-1) {
        return root + '&' + params;
    } else {
        return root + '?' + params;
    }
}

var gs_filemanager_languages = new Array();
gs_filemanager_languages['en'] = new Array();
gs_filemanager_languages['en'][1] = 'Current Dir';
gs_filemanager_languages['en'][2] = 'Clipboard';
gs_filemanager_languages['en'][3] = 'Upload';
gs_filemanager_languages['en'][4] = 'New File';
gs_filemanager_languages['en'][5] = 'New Directory';
gs_filemanager_languages['en'][6] = 'Paste';
gs_filemanager_languages['en'][7] = 'Name';
gs_filemanager_languages['en'][8] = 'Type';
gs_filemanager_languages['en'][9] = 'Size';
gs_filemanager_languages['en'][10] = 'Last Modified';
gs_filemanager_languages['en'][11] = 'Open with';
gs_filemanager_languages['en'][12] = 'View file';
gs_filemanager_languages['en'][13] = 'Open in editor';
gs_filemanager_languages['en'][14] = 'Copy';
gs_filemanager_languages['en'][15] = 'Cut';
gs_filemanager_languages['en'][16] = 'Rename';
gs_filemanager_languages['en'][17] = 'Copy AS';
gs_filemanager_languages['en'][18] = 'Download';
gs_filemanager_languages['en'][19] = 'Delete';
gs_filemanager_languages['en'][20] = 'Open';
gs_filemanager_languages['en'][21] = 'CKeditor';
gs_filemanager_languages['en'][22] = 'JCrop';
gs_filemanager_languages['en'][23] = 'Select all';
gs_filemanager_languages['en'][24] = 'Deselect all';
gs_filemanager_languages['en'][25] = 'Invert selection';
gs_filemanager_languages['en'][26] = 'Width';
gs_filemanager_languages['en'][27] = 'Height';
gs_filemanager_languages['en'][28] = 'Cancel';
gs_filemanager_languages['en'][29] = 'Upload File';
gs_filemanager_languages['en'][30] = 'Items';
gs_filemanager_languages['en'][31] = 'Save';
gs_filemanager_languages['en'][32] = 'Resize';
gs_filemanager_languages['en'][33] = 'Crop';
gs_filemanager_languages['en'][34] = 'As name';
gs_filemanager_languages['en'][35] = 'New name';
gs_filemanager_languages['en'][36] = 'File name';
gs_filemanager_languages['en'][37] = 'Directory name';
gs_filemanager_languages['en'][38] = 'Are you sure that you want to deleted selected items?';
gs_filemanager_languages['en'][39] = 'Zip directory';
gs_filemanager_languages['en'][40] = 'Zip file';
gs_filemanager_languages['en'][41] = 'Zip archive name';
gs_filemanager_languages['en'][42] = 'UnZip';
gs_filemanager_languages['en'][43] = 'UnZip Name';
gs_filemanager_languages['en'][44] = 'Lock sizes';

function gs_getTranslation(lg, code){
    result = null;
    if (typeof(gs_filemanager_languages[lg]) != 'undefined') {
        if (typeof(gs_filemanager_languages[lg][code]) != 'undefined') {
            result = gs_filemanager_languages[lg][code];
        }
    }
    return result;
}

var gs_cur_items =  new Array();

var gs_clipboard = new Array();

var gs_ext_pictures = new Array();
gs_ext_pictures['png'] = '1';
gs_ext_pictures['jpg'] = '1';
gs_ext_pictures['jpeg'] = '1';
gs_ext_pictures['gif'] = '1';
gs_ext_pictures['pdf'] = '1';
gs_ext_pictures['ico'] = '1';

var gs_ext_arhives = new Array();
gs_ext_arhives['zip'] = '1';

var gs_forbitten_ext_mapping = new Array();
gs_forbitten_ext_mapping['editable'] = '16,17,23';
gs_forbitten_ext_mapping['picture'] = '12,18,23';
gs_forbitten_ext_mapping['unknown'] = '12,15,16,17,18,23';
gs_forbitten_ext_mapping['archive'] = '12,15,16,17,18,19';

if (jQuery) (function(jQuery){

    jQuery.extend(jQuery.fn, {
        gsFileManager: function(o) {
            if( !o ) var o = {};
            if( o.root == undefined ) o.root = '/';
            if( o.language == undefined ) o.language = 'en';
            if( o.script == undefined ) o.script = 'jqueryFileTree.php';
            if( o.expandSpeed == undefined ) o.expandSpeed= 500;
            if( o.collapseSpeed == undefined ) o.collapseSpeed= 500;
            if( o.expandEasing == undefined ) o.expandEasing = null;
            if( o.collapseEasing == undefined ) o.collapseEasing = null;
            if( o.loadMessage == undefined ) o.loadMessage = 'Loading...';

            var menuHtml = '<div class="gs_title"><span class=\'gsHeadText\'> ' + gs_getTranslation(o.language, 1)+ ': </span><span id=\'curDir\'></span></div>';
            menuHtml += '<div class="gs_head"><a id="gs_uploadbutton" class=\'lshare no-right-border\'>&nbsp;' + gs_getTranslation(o.language, 3)+ '&nbsp;</a>';
            menuHtml += '<a id="gs_newfilebutton" class=\'lshare no-right-border\'>&nbsp;' + gs_getTranslation(o.language, 4)+ '&nbsp;</a>';
            menuHtml += '<a id="gs_newdirbutton" class=\'lshare no-right-border\'>&nbsp;' + gs_getTranslation(o.language, 5)+ '&nbsp;</a>';
            menuHtml += '<a id="gs_pastebutton" class=\'lshare no-right-border\'>&nbsp;' + gs_getTranslation(o.language, 6)+ '&nbsp;</a>';
            menuHtml += '<a id="gs_selectallbutton" class=\'lshare no-right-border\'>&nbsp;' + gs_getTranslation(o.language, 23)+ '&nbsp;</a>';
            menuHtml += '<a id="gs_deselectbutton" class=\'lshare\'>&nbsp;' + gs_getTranslation(o.language, 24)+ '&nbsp;</a></div>';
            menuHtml += '<span id=\'gsClipBoard\'>0 items</span>';
            var wrapperHtml = '<div id=\'gs_dir_list\' class=\'gs_dir_list\' onClick="jQuery(this).doGSAction({action: 21})"></div>';
            wrapperHtml    += '<div class=\'gs_dir_content\' onClick="jQuery(this).doGSAction({action: 21})">'
            + '<div class=\'gs_dir_content_menu\'>';
            wrapperHtml += menuHtml;
            wrapperHtml    += '     </div>';
            wrapperHtml    += '<div id=\'gs_dir_content\' class=\'gs_dir_content_files\'></div>';
            wrapperHtml    += '</div></div>';

            var contexMenus = '<ul id="gsFileMenu" class="contextMenu">';
            contexMenus += '<li class="edit"><a href="#edit">' + gs_getTranslation(o.language, 11)+ '</a>';
            contexMenus += '   <ul class="contextMenu subContextMenu">';
            contexMenus += '     <li class="picture"><a href="#notepad" rel="12">' + gs_getTranslation(o.language, 12)+ '</a></li>';
            contexMenus += '     <li class="notepad separator"><a href="#imageviewer" rel="15">' + gs_getTranslation(o.language, 13)+ '</a></li>';
            contexMenus += '   </ul>';
            contexMenus += '</li>';
            contexMenus += '<li class="copy separator"><a href="#Copy" rel="7">' + gs_getTranslation(o.language, 14)+ '</a></li>';
            contexMenus += '<li class="cut"><a href="#Cut" rel="8">' + gs_getTranslation(o.language, 15)+ '</a></li>';
            contexMenus += '<li class="rename"><a href="#Rename" rel="10">' + gs_getTranslation(o.language, 16)+ '</a></li>';
            contexMenus += '<li class="rename"><a href="#Copy As" rel="13">' + gs_getTranslation(o.language, 17)+ '</a></li>';
            contexMenus += '<li class="zip"><a href="#zip" rel="19">' + gs_getTranslation(o.language, 40)+ '</a></li>';
            contexMenus += '<li class="zip"><a href="#zip" rel="23">' + gs_getTranslation(o.language, 42)+ '</a></li>';
            contexMenus += '<li class="download separator"><a href="#Download" rel="11">' + gs_getTranslation(o.language, 18)+ '</a></li>';
            contexMenus += '<li class="delete"><a href="#Delete" rel="6">' + gs_getTranslation(o.language, 19)+ '</a></li>';
            contexMenus += '</ul>';

            contexMenus += '<ul id="gsDirMenu" class="contextMenu">';
            contexMenus += '<li class="directorymenu"><a href="#Open" rel="5">' + gs_getTranslation(o.language, 20)+ '</a></li>';
            contexMenus += '<li class="copy separator"><a href="#Copy" rel="7">' + gs_getTranslation(o.language, 14)+ '</a></li>';
            contexMenus += '<li class="cut"><a href="#Cut" rel="8">' + gs_getTranslation(o.language, 15)+ '</a></li>';
            contexMenus += '<li class="rename"><a href="#Rename" rel="10">' + gs_getTranslation(o.language, 16)+ '</a></li>';
            contexMenus += '<li class="zip"><a href="#zip" rel="19">' + gs_getTranslation(o.language, 39)+ '</a></li>';
            contexMenus += '<li class="zip"><a href="#zip" rel="23">' + gs_getTranslation(o.language, 42)+ '</a></li>';
            contexMenus += '<li class="delete"><a href="#Delete" rel="4">' + gs_getTranslation(o.language, 19)+ '</a></li>';
            contexMenus += '</ul>';

            contexMenus += '<ul id="gsContentMenu" class="contextMenu">';
            contexMenus += '<li class="paste separator"><a href="#Paste" rel="9">' + gs_getTranslation(o.language, 6)+ '</a></li>';
            contexMenus += '<li class="newfile separator"><a href="#New File" rel="2">' + gs_getTranslation(o.language, 4)+ '</a></li>';
            contexMenus += '<li class="newdir"><a href="#New Directory" rel="3">' + gs_getTranslation(o.language, 5)+ '</a></li>';
            contexMenus += '<li class="uploadfolder separator"><a href="#Upload" rel="14">' + gs_getTranslation(o.language, 3)+ '</a></li>';
            contexMenus += '<li class="selection separator"><a href="#Select All" rel="20">' + gs_getTranslation(o.language, 23)+ '</a></li>';
            contexMenus += '<li class="selection"><a href="#>Deselect all" rel="21">' + gs_getTranslation(o.language, 24)+ '</a></li>';
            contexMenus += '<li class="selection"><a href="#Invert selection" rel="22">' + gs_getTranslation(o.language, 25)+ '</a></li>';
            contexMenus += '</ul>';

            wrapperHtml    += contexMenus;

            var hiddenElements = '<div id=\'gsclipboardContent\' style=\'display: none\'></div>';
            hiddenElements += '<a id="showfile" style="display:none" href="#sfile_content">File content</a>';
            hiddenElements += '<div style="display:none">';
            hiddenElements += '<div id="sfile_content" style="padding:10px; background:#fff;"></div></div>';
            hiddenElements += '<a class="inline" style="display:none" href="#inline_content">Inline HTML</a>';
            hiddenElements += '<div style="display:none">';
            hiddenElements += '<div id="inline_content" style="padding:10px; background:#fff;"><h2 style="color: #4c6172; font: 18px \'Helvetica Neue\', Helvetica, Arial, sans-serif;">';
            hiddenElements += 'Upload Files</h2><p id="xmllog" class="message"><br/></p>';
            hiddenElements += '<form action="' + o.script +'" id="gsUploadForm" enctype="multipart/form-data"><input type="hidden" name="opt" value="11"><input type="hidden" name="dir" value="">';
            hiddenElements += '<div class="fileinputs"><input type="file" name="filename" size="30" id="gsUploadButton">';
            hiddenElements += '<br/><input type=submit value="Load" id="submit_inline" class="button"></div></form></div></div>';
            wrapperHtml += hiddenElements;
            jQuery(this).html(wrapperHtml);

            jQuery('#gs_dir_content').contextMenu({
                menu: 'gsContentMenu',
                addSelectedClass: false
            },
            function(action, el, pos) {
                jQuery(el).doGSAction({
                    action: action,
                    script: o.script,
                    type: 'context',
                    lg: o.language
                    });
            });

            jQuery('#gs_uploadbutton').click(function (e){
                e.stopPropagation();
                jQuery(this).doGSAction({
                    action: 14,
                    script:  o.script,
                    type: 'file',
                    lg: o.language
                    });
            });

            jQuery('#gs_newfilebutton').click(function (e){
                e.stopPropagation();
                jQuery(this).doGSAction({
                    action: 2,
                    script: o.script,
                    type: 'file',
                    lg: o.language
                    });
            });

            jQuery('#gs_newdirbutton').click(function (e){
                e.stopPropagation();
                jQuery(this).doGSAction({
                    action: 3,
                    script: o.script,
                    type: 'dir',
                    lg: o.language
                    });
            });

            jQuery('#gs_pastebutton').click(function (e){
                e.stopPropagation();
                jQuery(this).doGSAction({
                    script: o.script,
                    action: 9,
                    lg: o.language
                    });
            });

            jQuery('#gs_selectallbutton').click(function (e){
                e.stopPropagation();
                jQuery(this).doGSAction({
                    action: 20,
                    script: o.script,
                    type: 'context',
                    lg: o.language
                    });
            });

            jQuery('#gs_deselectbutton').click(function (e){
                e.stopPropagation();
                jQuery(this).doGSAction({
                    action: 21,
                    script: o.script,
                    type: 'context',
                    lg: o.language
                    });
            });

            jQuery('#gs_invertselectbutton').click(function (e){
                e.stopPropagation();
                return jQuery(this).doGSAction({
                    action: 22,
                    script: o.script,
                    type: 'context',
                    lg: o.language
                    });
            });

            jQuery('#gsUploadForm').ajaxForm({
                beforeSubmit: function () {
                    jQuery('#gsuploadfiles').append('<div class="loadingDiv">&nbsp;</div>');
                },
                success: function (responseText, statusText, xhr, $form) {
                    gsCheckResponce(responseText);
                    jQuery('#'+jQuery("#curDir").attr('rel')).trigger('click');
                    jQuery('#gsuploadfiles').find('div.loadingDiv').remove();
                },
                dataType: 'script'
            });

            function showFiles (gsfiless) {
                var fileshtml = '';
                if (gsfiless.length > 0) {
                    for (var num in gsfiless) {
                        var curItem = gsfiless[num];
                        gs_cur_items[curItem.id] = curItem;
                        fileshtml += "<tr><td class='first'><div class='file gsItem directory_info ext_" + curItem.getExt() + "' rel=\'" + curItem.id + "\'>" + curItem.name + "</div></td><td align='center'><span class=\'file_ext_name\'>" + curItem.getExt() + "</span></td><td align='center'>" + curItem.getSize() + "</td><td align='center'>"+curItem.getLastMod()+"</td></tr>";
                    }
                }
                return fileshtml;
            }

            function manageGsMenu (srcElement, menu){
                if (srcElement.attr('rel') == 'up') {
                    return false;
                }
                gs_item = gs_cur_items[srcElement.attr('rel')];
                type = gs_item.getType();
                if (typeof(gs_forbitten_ext_mapping[type]) != 'undefined') {
                    menu.disableContextMenuItems(gs_forbitten_ext_mapping[type]);
                }
                return true;
            }

            function showDirs (gsfiless) {
                var fileshtml = '';
                var gs_lastparent = jQuery('#' + jQuery("#curDir").attr('rel')).parent().parent().parent().children('a');
                if (gs_lastparent.length > 0) {
                    fileshtml += "<tr><td class='first'><div class='directory directory_info gsItem' rel=\'up\'><a href='javascript:void(0)' onclick=\"jQuery('#" + jQuery("#curDir").attr('rel')+ "').parent().parent().parent().children('a').trigger('click'); return false\"> ..</a></div></td align='center'><td align='center'>Folder</td><td align='center'>-</td><td align='center'>-</td></tr>";
                }
                if (gsfiless.length > 0) {
                    for (var numf in gsfiless) {
                        var curItem = gsfiless[numf];
                        gs_cur_items[curItem.id] = curItem;
                        fileshtml += "<tr><td class='first'><div class='directory directory_info gsItem' rel=\'" + curItem.id + "\'><a href='javascript:void(0)' onclick=\"jQuery('#"+curItem.id+"').trigger('click'); return false\">" + curItem.name + "</a></div></td><td align='center'>Folder</td><td align='center'>-</td><td align='center'>"+curItem.getLastMod()+"</td></tr>";
                    }
                }
                return fileshtml;
            }

            function showContent (gsdirss, gsfiless) {
                var dirshtml = showDirs (gsdirss);
                var fileshtml = showFiles (gsfiless);
                var tableheader = '<table class=\'dirs_files_table\' cellpadding=0 cellspacing=2 id="gs_content_table"><tr><th>' + gs_getTranslation(o.language, 7)+ '</th><th width=\'10%\'>' + gs_getTranslation(o.language, 8)+ '</th><th width=\'10%\'>' + gs_getTranslation(o.language, 9)+ '</th><th width=\'20%\'>' + gs_getTranslation(o.language, 10)+ '</th></tr>';
                jQuery('#gs_dir_content').html(tableheader + dirshtml + fileshtml + "</table>");

                jQuery('div.file').contextMenu({
                    menu: 'gsFileMenu'
                },
                function(action, el, pos) {
                    jQuery(el).doGSAction({
                        action: action,
                        script: o.script,
                        type: 'file',
                        lg: o.language
                        });
                },
                manageGsMenu);

                jQuery('table.dirs_files_table tr').find('div.gsItem').bind('click', function(e){
                    var cur_element = jQuery(this);
                    var rel = jQuery(this).attr('rel');
                    if (rel != 'up') {
                        if (cur_element.hasClass('rowSelected')) {
                            cur_element.removeClass('rowSelected');
                        } else {
                            cur_element.addClass('rowSelected');
                        }
                    }
                    jQuery(".contextMenu").hide();
                    return false;
                });

                jQuery('div.directory').contextMenu({
                    menu: 'gsDirMenu'
                },
                function(action, el, pos) {
                    jQuery(el).doGSAction({
                        action: action,
                        script: o.script,
                        type: 'dir',
                        lg: o.language
                        });
                },
                manageGsMenu);

            }

            function splitPath(path) {
                var list = path.split('/'),
                    html = "";
                for (var i=0; i<list.length; i++){
                    var subList = new Array();
                    if (list[i] !== '') {
                        for (var j=0; j<=i; j++){
                            subList.push(list[j]);
                        }
                        html += "<a class='pathlink' rel='"+subList.join('/')+"/'>"+list[i]+"</a>/";
                    }
                }
                return html;
            }

            function showTree(c, t) {
                var cObject = jQuery(c);
                cObject.addClass('wait');
                gs_show_loading();
                jQuery(".jqueryFileTree.start").remove();
                jQuery.ajax({
                    type: 'POST',
                    url: o.script,
                    data: {
                        dir: t
                    },
                    dataType: 'script',
                    contentType : 'application/x-www-form-urlencoded; charset=utf-8',
                    success: function(data) {

                        //remember current dir id
                        jQuery("#curDir").html(splitPath(unescape(t)));
  											jQuery("#curDir").attr('val', unescape(t));
                        jQuery("#curDir").attr('rel', jQuery('a', cObject).attr('id'));

                        gs_cur_items = new Array();

                        var dirhtml = '';
                        if (typeof(gsdirs) != 'undefined' && gsdirs.length > 0) {
                            dirhtml += "<ul class=\"jqueryFileTree\" style=\"display: none;\">";
                            for (var num in gsdirs) {
                                var curItem = gsdirs[num];
                                dirhtml += "<li class=\"directoryMeny collapsed\"><span class='dir_index toggleplus'>&nbsp;&nbsp;&nbsp;&nbsp;</span><a href=\"#\" rel=\"" + curItem.path + "/\" id=\"" + curItem.id + "\">" + curItem.name + "</a></li>";
                            }
                            dirhtml += "</ul>";
                        } else {
                            gsdirs = new Array();
                        }
                        if (typeof(gsfiles) == 'undefined') {
                            gsfiles = new Array();
                        }

                        cObject.find('.start').html('');

                        cObject.find('UL').remove();

                        cObject.removeClass('wait').append(dirhtml);

                        showContent(gsdirs, gsfiles, unescape(t));

                        if( o.root == t ) {
                            cObject.find('UL:hidden').show();
                        } else {
                            cObject.find('UL:hidden').slideDown({
                                duration: o.expandSpeed,
                                easing: o.expandEasing
                            });
                        }
                        setHandlers(cObject);
                    }
                });
        }

        function setHandlers(t) {
            //jQuery(t).find('LI').droppable();
            jQuery(t).find('LI > A').bind('click', function () {
                showTree (jQuery(this).parent(), encodeURIComponent(jQuery(this).attr('rel').match( /.*\// )));
            });
						jQuery('a.pathlink').bind('click', function () {
								showTree( jQuery('#gs_dir_list'), jQuery(this).attr('rel'));
						});
        }

        function showRoot(){
            showTree( jQuery('#gs_dir_list'), escape(o.root));
        }

        var cusElement = jQuery('#gs_dir_list');
        // Loading message
        cusElement.html('<ul class="jqueryFileTree start"><li class="wait">' + o.loadMessage + '<li></ul>');
        // Get the initial file list
        cusElement.prepend('<a href="#" id="rootLink">root</a>');
        cusElement.find('#rootLink').bind('click', showRoot);

        showRoot();
    },

    doGSAction: function(o) {
        if (o.action == '20') { // select
            jQuery("#gs_content_table div.gsItem").each(function(){
                if (jQuery(this).attr('rel') != 'up') {
                    jQuery(this).addClass('rowSelected');
                }
            });
            return false;
        }
        if (o.action == '21') { // deselect
            jQuery("#gs_content_table div.gsItem").each(function(){
                jQuery(this).removeClass('rowSelected');
            });
            return false;
        }
        if (o.action == '22') { // invert select
            jQuery("#gs_content_table div.gsItem").each(function(){
                if (jQuery(this).attr('rel') != 'up') {
                    if (jQuery(this).hasClass('rowSelected')) {
                        jQuery(this).removeClass('rowSelected');
                    } else {
                        jQuery(this).addClass('rowSelected');
                    }
                }
            });
            return false;
        }
        var curDir = jQuery("#curDir").attr('val');
        var dataForSend = null;
        var gsitem = gs_get_cur_item(jQuery(this).attr('rel'));

        if (gsitem == null) {
        //alert('no gsitem');
        }

        if (o.action == '23') { // zip
            unZipItem(o, curDir, gsitem);
            return;
        }

        if (o.action == '12') { // show notepad
            showNotePad(o, curDir, gsitem);
            return;
        }

        if (o.action == '13') { // copy as
            copyAs(o, curDir, gsitem);
            return;
        }

        if (o.action == '14') { // show upload
          $.colorbox.remove();
          $(".inline").colorbox({inline:true, width: "480px", height: "200px", onComplete:function(){
            //nothing
        	}});
          $(".inline").click();
          $("#submit_inline").click(function(){
            jQuery("#inline_content").find("input[name=dir]").val(curDir);
            jQuery('#gsUploadForm').submit();
            $("#cboxClose").click();
            return false;
          });
        }

        if (o.action == '15') { // Edit file in nex windows
            var url = $SCRIPT_ROOT+"/editFile?profile="+encodeURIComponent(curDir+"/"+gsitem.name)+"&filename="+encodeURIComponent(gsitem.name);
            window.open(url, '_blank');
            window.focus();
            return;
        }
        if (o.action == '19') { // zip
            zipItem(o, curDir, gsitem);
            return;
        }
        if (o.action == '7') { // copy
            var clipBoard = jQuery("#gsClipBoard");
            gs_storeSelectedItems();
            clipBoard.html('(Copy) ' + gs_clipboard.length + ' ' + gs_getTranslation(o.lg, 30));
            clipBoard.attr('rel', o.action);
            return;
        }
        if (o.action == '8') { // cut
            var clipBoard = jQuery("#gsClipBoard");
            gs_storeSelectedItems();
            clipBoard.html('(Cut) ' + gs_clipboard.length + ' ' + gs_getTranslation(o.lg, 30));
            clipBoard.attr('rel', o.action);
            return;
        }
        if (o.action == '9') { //paste
            pasteItems(o, curDir, gsitem);
            return;
        }
        if (o.action == '10') { //rename
            renameItem(o, curDir, gsitem);
            return;
        }
        if (o.action == '11') { //download
            dataForSend = {
                opt: 8,
                filename: gsitem.name,
                dir: curDir
            };
            location.href= gs_makeUrl(o.script, jQuery.param(dataForSend));
            return;
        }
        if (o.action == '2') { //new file
            newFile(o, curDir, gsitem);
            return;
        }
        if (o.action == '3') { //new dir
            newDir(o, curDir, gsitem);
            return;
        }
        if (o.action == '4' || o.action == '6') { //delete item
            deleteItem(o, curDir, gsitem);
            return;
        }
        if (o.action == '5') { //open dir
            jQuery('#' + gsitem.id).trigger('click');
            return;
        }

        function showNotePad(o, curDir, gsitem){
            $.colorbox.remove();
            $("#sfile_content").empty();
          	$("#sfile_content").append('<br/><br/><br/><div class="loadingDiv">&nbsp;</div>');
            dataForSend = {
                opt: 9,
                filename: encodeURIComponent(gsitem.name),
                dir: curDir
            };
            sendAndRefresh(o, dataForSend, false, function(data) {
                $("#sfile_content").empty();
          			$("#sfile_content").append('<div class="main_content"><pre id="editor"></pre></div>');
                setupEditor();
                var mode = modelist.getModeForPath(gsitem.name);
                editor.getSession().modeName = mode.name;
                editor.getSession().setMode(mode.mode);
          			$("#showfile").colorbox({inline:true, width: "847px", onComplete:function(){
          				editor.getSession().setValue(data);
          			}, title: "Content of file: " + gsitem.name});
    			      $("#showfile").click();
            });
        }

        function pasteItems(o, curDir, gsitem){
            var clipBoard = jQuery("#gsClipBoard");
            var opt = null;
            var selectedFiles = gsGetSelectedItemsPath();
            if (clipBoard.attr('rel') == '7') { //copy
                opt = 5;
            } else if (clipBoard.attr('rel') == '8') { // paste
                gs_clipboard = new Array();
                clipBoard.html('0 items');
                jQuery('#gsclipboardContent').html('');
                clipBoard.attr('rel', '');
                opt = 7;
            } else {
                return;
            }
            if (selectedFiles != null) {
                dataForSend = {
                    opt: opt,
                    files: selectedFiles,
                    dir: curDir
                };
                sendAndRefresh(o, dataForSend, true);
            }
            if (opt == 7) {
                for (var xx in gs_clipboard) {
                    if (gs_clipboard[xx].getExt() == 'dir') {
                        jQuery("#" + gs_clipboard[xx].id).parent().remove();
                    }
                }
            }
        }

        function copyAs(o, curDir, gsitem){
            var newName = window.prompt(gs_getTranslation(o.lg, 34) + ': ', gsitem.name);
            if (newName == null) {
                return;
            }
            dataForSend = {
                opt: 14,
                filename: gsitem.name,
                dir: curDir,
                newfilename: newName
            };
            sendAndRefresh(o, dataForSend, true);
        }

        function unZipItem(o, curDir, gsitem){
            var newName = window.prompt(gs_getTranslation(o.lg, 43) + ': ', 'unzipped_' + gsitem.name);
            if (newName == null) {
                return;
            }
            dataForSend = {
                opt: 17,
                filename: gsitem.name,
                dir: curDir,
                newfilename: newName
            };
            sendAndRefresh(o, dataForSend, true);
        }

        function zipItem(o, curDir, gsitem){
            var newName = window.prompt(gs_getTranslation(o.lg, 41) + ': ', gsitem.name + '.zip');
            if (newName == null) {
                return;
            }
            dataForSend = {
                opt: 16,
                filename: gsitem.name,
                dir: curDir,
                newfilename: newName
            };
            sendAndRefresh(o, dataForSend, true);
        }

        function renameItem(o, curDir, gsitem){
            var newName = window.prompt(gs_getTranslation(o.lg, 35) + ': ', gsitem.name);
            if (newName == null) {
                return;
            }
            dataForSend = {
                opt: 6,
                filename: curDir+gsitem.name,
                dir: curDir,
                newfilename: newName
            };
            sendAndRefresh(o, dataForSend, true);
        }

        function newFile(o, curDir, gsitem){
            var newName = window.prompt(gs_getTranslation(o.lg, 36) + ': ');
            if (newName == null || newName.length < 1) {
                return;
            }
            dataForSend = {
                opt: 2,
                filename: newName,
                dir: curDir
            };
            sendAndRefresh(o, dataForSend, true);
        }

        function newDir(o, curDir, gsitem){
            var newName = window.prompt(gs_getTranslation(o.lg, 37) + ': ');
            if (newName == null || newName.length < 1) {
                return;
            }
            dataForSend = {
                opt: 3,
                filename: newName,
                dir: curDir
            };
            sendAndRefresh(o, dataForSend, true);
        }

        function deleteItem(o, curDir, gsitem){
            if(!window.confirm(gs_getTranslation(o.lg, 38))){
                return;
            }
            var selectedFiles = gsGetSelectedItems();
            //alert('sel ' + selectedFiles);
            if (selectedFiles != null) {
                dataForSend = {
                    opt: 4,
                    files: encodeURIComponent(selectedFiles),
                    dir: curDir
                };
            }
            sendAndRefresh(o, dataForSend, true);
        }

        function sendAndRefresh(o, dataForSend, refresh, callback, type) {
            if (refresh) {
                gs_show_loading();
            }
            if (typeof(type) == 'undefined') {
                type = 'text';
            }
            dataForSend.dir = encodeURIComponent(dataForSend.dir);
            jQuery.ajax({
                type: 'POST',
                url: o.script,
                data: jQuery.param(dataForSend) + '&time='+ new Date().getTime(),
                dataType: type,
                contentType : 'application/x-www-form-urlencoded; charset=utf-8',
                success: function(data) {
                    gsCheckResponce(data);
                    if (refresh) {
                        jQuery('#'+jQuery("#curDir").attr('rel')).trigger('click');
                    }
                    if (callback) {
                        callback(data);
                    }
                }
            });
    }
    }
});

})(jQuery);

//jQuery Context Menu Plugin
//
// Version 1.01
//
// Cory S.N. LaViska
// A Beautiful Site (http://abeautifulsite.net/)
//
// More info: http://abeautifulsite.net/2008/09/jquery-context-menu-plugin/
//
// Terms of Use
//
// This plugin is dual-licensed under the GNU General Public License
//   and the MIT License and is copyright A Beautiful Site, LLC.
//
if(jQuery)( function() {

  /* Check browser version, since $.browser was removed in jQuery 1.9 */
  function _checkBrowser(){
		var matched, browser;
		function uaMatch( ua ) {
			ua = ua.toLowerCase();
			var match = /(chrome)[ \/]([\w.]+)/.exec( ua ) ||
				 /(webkit)[ \/]([\w.]+)/.exec( ua ) ||
				 /(opera)(?:.*version|)[ \/]([\w.]+)/.exec( ua ) ||
				 /(msie) ([\w.]+)/.exec( ua ) ||
				 ua.indexOf("compatible") < 0 && /(mozilla)(?:.*? rv:([\w.]+)|)/.exec( ua ) ||
				 [];
			return {
				browser: match[ 1 ] || "",
				version: match[ 2 ] || "0"
			};
		}
		matched = uaMatch( navigator.userAgent );
		browser = {};
		 if ( matched.browser ) {
			 browser[ matched.browser ] = true;
			 browser.version = matched.version;
		 }
		 if ( browser.chrome ) {
			 browser.webkit = true;
		 } else if ( browser.webkit ) {
			 browser.safari = true;
		 }
		 return browser;
	}
	var BROWSER = jQuery.browser || _checkBrowser();

  jQuery.extend(jQuery.fn, {

      contextMenu: function(o, callback, onShowMenu) {
          // Defaults
          if( o.menu == undefined ) return false;
          if( o.inSpeed == undefined ) o.inSpeed = 150;
          if( o.addSelectedClass == undefined ) o.addSelectedClass = true;
          if( o.outSpeed == undefined ) o.outSpeed = 75;
          // 0 needs to be -1 for expected results (no fade)
          if( o.inSpeed == 0 ) o.inSpeed = -1;
          if( o.outSpeed == 0 ) o.outSpeed = -1;
          // Loop each context menu
          jQuery(this).each( function() {
              var el = jQuery(this);
              var offset = jQuery(el).offset();
              // Add contextMenu class
              jQuery('#' + o.menu).addClass('contextMenu');
              // Simulate a true right click
              jQuery(this).mousedown( function(e) {
                  var evt = e;
                  evt.stopPropagation();
                  jQuery(this).mouseup( function(e) {
                      e.stopPropagation();
                      var srcElement = jQuery(this);
                      srcElement.unbind('mouseup');
                      if( evt.button == 2 ) {
                          // Hide context menus that may be showing
                          jQuery(".contextMenu").hide();
                          // Get this context menu
                          var menu = jQuery('#' + o.menu);
                          menu.enableContextMenuItems();
                          if (onShowMenu) {
                              if (!onShowMenu( srcElement, menu )) {
                                  return false;
                              }
                          }
                          if (!srcElement.hasClass('rowSelected')){
                              jQuery("#gs_content_table div.gsItem").each(function(){
                                  jQuery(this).removeClass('rowSelected');
                              });
                              if (o.addSelectedClass) {
                                  srcElement.addClass('rowSelected');
                              }
                          }

                          var jmenu = jQuery(menu);
                          if( jQuery(el).hasClass('disabled')) {
                              return false;
                          }
                          // Detect mouse position
                          var d = {}, x, y;
                          if( self.innerHeight ) {
                              d.pageYOffset = self.pageYOffset;
                              d.pageXOffset = self.pageXOffset;
                              d.innerHeight = self.innerHeight;
                              d.innerWidth = self.innerWidth;
                          } else if( document.documentElement &&
                              document.documentElement.clientHeight ) {
                              d.pageYOffset = document.documentElement.scrollTop;
                              d.pageXOffset = document.documentElement.scrollLeft;
                              d.innerHeight = document.documentElement.clientHeight;
                              d.innerWidth = document.documentElement.clientWidth;
                          } else if( document.body ) {
                              d.pageYOffset = document.body.scrollTop;
                              d.pageXOffset = document.body.scrollLeft;
                              d.innerHeight = document.body.clientHeight;
                              d.innerWidth = document.body.clientWidth;
                          }
                          (e.pageX) ? x = e.pageX : x = e.clientX + d.scrollLeft;
                          (e.pageY) ? y = e.pageY : y = e.clientY + d.scrollTop;

                          // Show the menu
                          jQuery(document).unbind('click');
                          jmenu.css({
                              top: y,
                              left: x
                          }).fadeIn(o.inSpeed);

                          // Hover events
                          jmenu.find('A').mouseover( function() {
                              jmenu.find('LI.hover').removeClass('hover');
                              if (!jQuery(this).parent().parent().hasClass('subContextMenu')) {
                                  jmenu.find('UL.subContextMenu').hide();
                              }
                              jQuery(this).parent().addClass('hover');
                              jQuery(this).parent().find('UL').css({
                                  top: 0,
                                  left: 120
                              }).fadeIn(o.inSpeed);
                          }).mouseout( function() {
                              jmenu.find('LI.hover').removeClass('hover');
                          });

                          // When items are selected
                          menu.find('A').unbind('click');
                          menu.find('A').bind('click', function() {
                              if(jQuery(this).parent().hasClass('disabled')){
                                  return false;
                              }
                              jQuery(".contextMenu").hide();
                              // Callback
                              if (callback) {
                                  callback( jQuery(this).attr('rel'), jQuery(srcElement), {
                                      x: x - offset.left,
                                      y: y - offset.top,
                                      docX: x,
                                      docY: y
                                  } );
                              }
                              return false;
                          });

                          // Hide bindings
                          setTimeout( function() { // Delay for Mozilla
                              jQuery(document).click( function() {
                                  jQuery(menu).fadeOut(o.outSpeed);
                              });
                          }, 0);
                      }
                  });
              });

              // Disable text selection
              if( BROWSER.mozilla ) {
                  jQuery('#' + o.menu).each( function() {
                      jQuery(this).css({
                          'MozUserSelect' : 'none'
                      });
                  });
              } else if( BROWSER.msie ) {
                  jQuery('#' + o.menu).each( function() {
                      jQuery(this).bind('selectstart.disableTextSelect', function() {
                          return false;
                      });
                  });
              } else {
                  jQuery('#' + o.menu).each(function() {
                      jQuery(this).bind('mousedown.disableTextSelect', function() {
                          return false;
                      });
                  });
              }
              // Disable browser context menu (requires both selectors to work in IE/Safari + FF/Chrome)
              jQuery(el).add(jQuery('UL.contextMenu')).bind('contextmenu', function() {
                  return false;
              });

          });
          return jQuery(this);
      },

      // Disable context menu items on the fly
      disableContextMenuItems: function(o) {
          if( o == undefined ) {
              // Disable all
              jQuery(this).find('LI').addClass('disabled');
              return( jQuery(this) );
          }
          jQuery(this).each( function() {
              if( o != undefined ) {
                  var d = o.split(',');
                  for( var i = 0; i < d.length; i++ ) {
                      //alert(d[i]);
                      jQuery(this).find('A[rel="' + d[i] + '"]').parent().addClass('disabled');
                  }
              }
          });
          return( jQuery(this) );
      },

      // Enable context menu items on the fly
      enableContextMenuItems: function(o) {
          if( o == undefined ) {
              // Enable all
              jQuery(this).find('LI.disabled').removeClass('disabled');
              return( jQuery(this) );
          }
          jQuery(this).each( function() {
              if( o != undefined ) {
                  var d = o.split(',');
                  for( var i = 0; i < d.length; i++ ) {
                      jQuery(this).find('A[rel="' + d[i] + '"]').parent().removeClass('disabled');

                  }
              }
          });
          return( jQuery(this) );
      },

      // Disable context menu(s)
      disableContextMenu: function() {
          jQuery(this).each( function() {
              jQuery(this).addClass('disabled');
          });
          return( jQuery(this) );
      },

      // Enable context menu(s)
      enableContextMenu: function() {
          jQuery(this).each( function() {
              jQuery(this).removeClass('disabled');
          });
          return( jQuery(this) );
      },

      // Destroy context menu(s)
      destroyContextMenu: function() {
          // Destroy specified context menus
          jQuery(this).each( function() {
              // Disable action
              jQuery(this).unbind('mousedown').unbind('mouseup');
          });
          return( jQuery(this) );
      }

  });
})(jQuery);