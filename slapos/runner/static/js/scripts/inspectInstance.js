$(document).ready(function() {
  var editor;
  setupFileTree();
  $($('#slappart li')[0]).find('input:radio').attr('checked', true);
  $('.menu-box-right>div').css('min-height', $('#slappart li').length * 26 + 20 + 'px');
  configRadio();
  var send = false;
  var lastli = null;
  var partitionAmount = $('input#partitionAmount').val();
  $('#slappart li').each(function() {
    lastli = $(this);
    $(this).find('input:radio').change(function() {
      configRadio();
    });
  });
  if (lastli) {lastli.css('border-bottom', 'none');}

  $('#parameterkw').slideBox('show');
  setupSlappart();
  $('#softwareType').slideBox();
  $('#reloadfiles').click(function() {
    setupFileTree();
  });
  $('#refresh').click(function() {
    if (send) return;
    $('#imgwaitting').fadeIn();
    $.ajax({
        type: 'GET',
      url: $SCRIPT_ROOT + '/supervisordStatus',
      data: '',
      success: function(data) {
            if (data.code == 1) {
                $('#supervisordcontent').empty();
                $('#supervisordcontent').append(data.result);
            }
            $('#imgwaitting').fadeOut();
      }
    });
    return false;
  });
  $('#add_attribute').click(function() {
    var size = Number($('#partitionParameter > tbody > tr').last().attr('id').split('_')[1]) + 1;
    var row = "<tr id='row_" + size + "'><td class='first'><input type='text' name='txt_" + size + "' id='txt_" + size + "'></td>" +
            "<td style='padding:6px'><textarea class='slap' id='value_" + size + "'></textarea>" +
            "</td><td valign='middle'><span style='margin-left: 10px;' id='btn_" + size + "' class='close'></span></td></tr>";
    $('#partitionParameter').append(row);
    setInput($('input#txt_' + size));
    setupTextarea($('textarea#value_' + size));
    $('#btn_' + size).click(function() {
      var index = $(this).attr('id').split('_')[1];
      $('tr#row_' + index).remove();
    });
    return false;
  });
  $('#updateParameters').click(function() {
    updateParameter();
    return false;
  });
  $('#xmlview').click(function() {
    var content = '<h2 style="color: #4c6172; font: 18px \'Helvetica Neue\', Helvetica, Arial, sans-serif;">' +
      'INSTANCE PARAMETERS: Load XML file</h2><p id="xmllog" class="message"><br/></p>';
    content += '<div class="main_content" style="height:230px"><pre id="editor"></pre></div>' +
      '<input type=submit value="Load" id="loadxml" class="button">';
    $.ajax({
    type: 'GET',
    url: $SCRIPT_ROOT + '/getParameterXml/xml',
    success: function(data) {
      if (data.code == 1) {
        $('#inline_content').html(content);
        setupEditor(true);
        $('.inline').colorbox({inline: true, width: '600px', height: '410px', onComplete: function() {
          editor.getSession().setValue(data.result);
        }});
        $('.inline').click();
        $('#loadxml').click(function() {
          //Parse XML file
          try {
            var xmlDoc = $.parseXML(editor.getSession().getValue()), $xml = $(xmlDoc);
            if ($xml.find('parsererror').length !== 0) {$('p#xmllog').html('Error: Invalid XML document!<br/>');return false;}
          } catch (err) {
            $('p#xmllog').html('Error: Invalid XML document!<br/>');return false;
          }
          $.ajax({
            type: 'POST',
            url: $SCRIPT_ROOT + '/saveParameterXml',
            data: {software_type: '', parameter: editor.getSession().getValue()},
            success: function(data) {
              if (data.code == 1) {
                location.href = $SCRIPT_ROOT + '/inspectInstance#tab3';
                location.reload();
              }
              else {$('p#xmllog').html(data.result);}
            }
          });
          return false;
        });
      }
      else {
        $('#error').Popup(data.result, {type: 'error', duration: 5000});
      }
    }
    });
  });
  //Load previous instance parameters
  loadParameter();
  $('a#parameterTab').click(function() {
    var size = $('#partitionParameter > tbody > tr').length;
    for (var i = 2; i <= size; i++) {
      $('textarea#value_' + i).keyup();
    }
  });

  function setupFileTree(path) {
    var root = $('input#root').val();
    if (root == '') return;
    if (path) {
      root += '/' + path;
      $('#tab4>h2').html('File content for <strong>' + path + '</strong>');
    }
    else {$('#tab4>h2').html('File content for all your partitions');}
    $('#fileTree').empty();
    $('#fileTree').fileTree({ root: root, script: $SCRIPT_ROOT + '/readFolder', folderEvent: 'click', expandSpeed: 750,
      collapseSpeed: 750, multiFolder: false, selectFolder: false }, function(file) {

      }, function(file) {
  //User have double click on file in to the fileTree
  viewFile(file);
    });
  }

  function viewFile(file) {
    //User have double click on file in to the fileTree
    loadFileContent(file);
  }
  $('#parameter').load($SCRIPT_ROOT + '/getParameterXml');
  $('#update').click(function() {
    if ($('#parameter').val() == '') {
        $('#error').Popup('Can not save empty value!', {type: 'alert', duration: 3000});
    }
    $.ajax({
        type: 'POST',
      url: $SCRIPT_ROOT + '/saveParameterXml',
      data: {parameter: $('#parameter').val().trim()},
      success: function(data) {
            if (data.code == 1) {
                $('#error').Popup('Instance parameters updated!', {type: 'info', duration: 3000});
            }
            else {
                $('#error').Popup(data.result, {type: 'error', duration: 5000});
            }
      }
    });
  });

  function loadFileContent(file) {
  $.ajax({
  type: 'POST',
  url: $SCRIPT_ROOT + '/checkFileType',
  data: 'path=' + file,
  success: function(data) {
    if (data.code == 1) {
      if (data.result == 'text') {
        $.ajax({
        type: 'POST',
        url: $SCRIPT_ROOT + '/getFileContent',
        data: {file: file, truncate: 1500},
        success: function(data) {
          if (data.code == 1) {
      $('#inline_content').empty();
      $('#inline_content').append('<h2 style="color: #4c6172; font: 18px \'Helvetica Neue\', Helvetica, Arial, sans-serif;">Inspect Instance Content: ' +
        file + '</h2>');
      $('#inline_content').append('<br/><div class="main_content"><pre id="editor"></pre></div>');
      setupEditor();
      $('.inline').colorbox({inline: true, width: '847px', onComplete: function() {
        editor.getSession().setValue(data.result);
      }});
      $('.inline').click();
          }
          else {
      $('#error').Popup('Can not load your file, please make sure that you have selected a Software Release', {type: 'alert', duration: 5000});
          }
      }
        });
      }
      else {
        //Can not displays binary file
        $('#error').Popup(data.result, {type: 'alert', duration: 5000});
      }
    }
    else {
      $('#error').Popup(data.result, {type: 'alert', duration: 5000});
    }
  }
    });
  }
  function updateParameter() {
    var xml = '<?xml version="1.0" encoding="utf-8"?>\n',
        software_type = '',
        software_type_input_value = $('input#software_type').val();
    if (software_type_input_value !== '' && software_type_input_value !== 'Software Type here...') {
      software_type = +software_type_input_value;
    }
    xml += '<instance>\n';
    var size = $('#partitionParameter > tbody > tr').length;
    if (size > 1) {
      for (var i = 2; i <= size; i++) {
        if ($('input#txt_' + i).val() != '') {
          xml += '<parameter id="' + $('input#txt_' + i).val() + '">' + $('textarea#value_' + i).val() + '</parameter>\n';
        }
      }
    }
    xml += '</instance>\n';
    $.ajax({
    type: 'POST',
    url: $SCRIPT_ROOT + '/saveParameterXml',
    data: {software_type: software_type, parameter: xml},
    success: function(data) {
      if (data.code == 1) {
        $('#error').Popup('Instance parameters has been updated, please run your instance now!', {type: 'confirm', duration: 5000});
      }
      else {
        $('#error').Popup(data.result, {type: 'error', duration: 5000});
      }
    }
    });
  }
  function setupTextarea($txt) {
    var size = Number($txt.attr('id').split('_')[1]);
    var hiddenDiv = $(document.createElement('div')),
    content = null;
    hiddenDiv.attr('id', 'div_' + size);
    hiddenDiv.addClass('hiddendiv');
    $('div#parameterkw').append(hiddenDiv);
    $txt.keyup(function() {
      content = $txt.val().replace(/\n/g, '<br>');
      hiddenDiv.html(content);
      if (hiddenDiv.height() > $txt.height() && hiddenDiv.height() > 120) {return}
      $txt.css('height', hiddenDiv.height() + 'px');
    });
  }
  function loadParameter() {
    $.ajax({
    type: 'GET',
    url: $SCRIPT_ROOT + '/getParameterXml/dict',
    success: function(data) {
      if (data.code == 1) {
        var dict = data.result['instance'];
        for (propertie in dict) {
          $('#add_attribute').click();
          var size = Number($('#partitionParameter > tbody > tr').last().attr('id').split('_')[1]);
          $('input#txt_' + size).val(propertie);
          $('textarea#value_' + size).val(dict[propertie]);
          $('textarea#value_' + size).keyup();
        }
      }
      else {
        $('#error').Popup(data.result, {type: 'error', duration: 5000});
      }
    }
    });
  }
  function configRadio() {
    $('#slappart li').each(function() {
      var $radio = $(this).find('input:radio');
      var boxselector = '#box' + $radio.attr('id');
      if ($(this).hasClass('checked')) {
        $(this).removeClass('checked');
        $(boxselector).slideUp('normal');
      }
      if ($radio.is(':checked')) {
        $(this).addClass('checked');
        //change content here
        $(boxselector).slideDown('normal');

      }
    });
  }
  function setupBox() {
    var state = $('#softwareType').css('display');
    if (state == 'none') {
      $('#softwareType').slideDown('normal');
      $('#softwareTypeHead').removeClass('hide');
      $('#softwareTypeHead').addClass('show');
    }
    else {
      $('#softwareType').slideUp('normal');
      $('#softwareTypeHead').removeClass('show');
      $('#softwareTypeHead').addClass('hide');
    }
  }
  function setupEditor(editable) {
    editor = ace.edit('editor');
    editor.setTheme('ace/theme/crimson_editor');

    var CurentMode = require('ace/mode/text').Mode;
    editor.getSession().setMode(new CurentMode());
    editor.getSession().setTabSize(2);
    editor.getSession().setUseSoftTabs(true);
    editor.renderer.setHScrollBarAlwaysVisible(false);
    if (!editable) {editor.setReadOnly(true);}
  }
  function setupSlappart() {
    for (var i = 0; i < partitionAmount; i++) {
      var elt = $('#slappart' + i + 'Parameter');
      var fileId = $('#slappart' + i + 'Files');
      if (elt && elt != undefined) elt.click(function() {
        alert($(this).html());
      });
      if (fileId && fileId != undefined) fileId.click(function() {
        $('#instancetabfiles').click();
        setupFileTree($(this).attr('rel'));
      });
    }
  }
});
