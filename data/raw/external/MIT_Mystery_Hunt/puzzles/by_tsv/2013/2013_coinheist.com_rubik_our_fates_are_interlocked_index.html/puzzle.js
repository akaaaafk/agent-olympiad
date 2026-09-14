// This must include the trailing slash.
var ENDPOINT_PREFIX = 'http://puzzle.scripts.mit.edu/2013/special-snowflakes/puzzle_our_fates_are_interlocked/';

var sid;

function reset_puzzle()
{
  $('img').each(function(i, img) {
    var match = /^s([0-9]+[LR])$/.exec(img.id);
    if (match !== null) {
      set_graphic(match[1], 292);
    }
  });
  $.ajax({type: 'POST',
          url: ENDPOINT_PREFIX+'new-session',
          data: '',
          xhrFields: {withCredentials: true},
          success: function(data) {
            sid = data.sid;
            setup_levers(data.levers);
            update_lights(data.lights);
            $('#errormsg').text('');
          },
          dataType: 'json'});
}

function setup_levers(levers){
  var evenLevers = $('<tr class="even-levers"/>'), oddLevers = $('<tr class="odd-levers"/>'), labels = $('<tr/>');
  var lightsL = $('<tr class="L-lights"/>'), lightsR = $('<tr class="R-lights"/>');
  $('#levers tbody').html('');
  $('#levers tbody').append(oddLevers, labels, evenLevers, lightsL, lightsR);
  for(var lever = levers[0], i = 0; lever <= levers[levers.length - 1]; lever++){
    var missing = false;
    if(levers[i] != lever)
      missing = true;
    else
      i++;
    var cell = $('<td class="lever" />');
    var label = $('<td id="lever' + lever + '" class="N">' + lever + '</td>');
    if(parseInt(lever)%2 == 0){
      cell.addClass('even');
      label.addClass('even-label');
      evenLevers.append(cell);
      oddLevers.append('<td/>');
      lightsL.append('<td id="'+lever+'L-light" class="L-light"><span>L</span></td>');
      lightsR.append('<td id="'+lever+'R-light" class="R-light"><span>R</span></td>');
    }
    else {
      cell.addClass('odd');
      label.addClass('odd-label');
      oddLevers.append(cell);
      evenLevers.append('<td/>');
      lightsL.append('<td class="light off"/>');
      lightsR.append('<td id="'+lever+'-light" class="light"><span>' + lever + '</span></td>');
    }
    labels.append(label);
    if(!missing){
      cell.append('<table class="lever-row"><tbody><tr></tr></tbody></table>');
      var row = cell.find('tr');
      var i, state;
      $.each(['L', 'N', 'R'], function(i, state){
        var td = $('<td/>').addClass(state + '-lever').addClass('lever');
        row.append(td);
        var input = $('<input type="radio"/>')
          .prop('id', lever + state)
          .prop('name', lever)
          .prop('title', state)
          .addClass('leverButton')
          .click(
            (function(lever){
              return function(event){
                move_lever(lever, state);
                event.preventDefault();
              };
            })(lever));
        if(state == 'N')
          input[0].checked = true;
        td.append(input);
      });
    }
    else
      label.addClass('missing');
  };
}

function update_lights(lights){
  $('.leverButton').prop('disabled', true);
  $('.leverButton:checked, .even .leverButton[id$="N"]').prop('disabled', false);
  $('.light, .L-light, .R-light').addClass('off');
  $.each(lights, function(i, light){
    if(light == String(parseInt(light)))
      $('input.leverButton[name="' + light + '"]').prop('disabled', false);
    else
      $('#' + light).prop('disabled', false);
    $('#' + light + '-light').removeClass('off');
  });
}

function set_graphic(s, state)
{
  var img = document.getElementById('s'+s);
  var pathLength = img.src.lastIndexOf('/')+1;
  img.src = img.src.slice(0, pathLength) + state + img.src.slice(pathLength+3);
}

function move_lever(lever, state)
{
  $('#errormsg').text('');
  $.ajax({type: 'POST',
          url: ENDPOINT_PREFIX+'move-lever',
          data: {sid: sid, lever: lever, state: state},
          xhrFields: {withCredentials: true},
          success: function(data) {
            if (data.result === 'error') {
              $('#errormsg').text(data.errmsg);
            } else {
              //$('#errormsg').text('Moved '+lever+' to '+state+'.');
              $('#' + lever + state)[0].checked = true;
              $('#lever' + lever).removeClass('N L R')
                                 .addClass(state);
              $.each(data.changes, function(i, change) {
                set_graphic(change[0], change[1]);
              });
              update_lights(data.lights);
            }
          },
          dataType: 'json'});
}

$(function() {
  reset_puzzle();
});
