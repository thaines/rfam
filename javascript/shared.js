// Copyright 2014 Tom SF Haines

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.



// Function to logout...
function logout()
{
 // Callback to handle the login result...
  var callback = function(response)
  {
   window.location.reload();
  }
  
 // Call through to the server with the information...
  $.getJSON('login', {'project':'', 'user':''}, callback);
}



// Register handler for the logout button...
$(function() {
 // Setup handlers...
  $('#logout').click(logout);
  
 // Make sure the right tab is selected...
  $('#page_tab').each(function() {
   var tab = $(this).attr('data-tab');
   $(tab).parent().attr('id', 'selected_tab');
  });
});



// Function that, on being given a dom search that contains all the relevant parts of an input mechanism and status indicator, plus the relevant data path, sets the object to behave correctly - this is used for every data entry box in the system...
function tie_input(search, path, key, refresh)
{
 refresh = (typeof refresh === 'undefined') ? false : refresh;
 
 // String that should match the relevant input, for several possibilities...
  var match = search + ' input, ' + search + ' textarea, ' + search + ' select';
 
 // Create the various handler functions for this situation...
  var do_update = function()
  {   
   // Create the callback handler...
    var callback = function(response)
    {
     if (response)
     {
      $(search + ' .state_sync').attr('class', 'state_ok'); 
      $(search + ' .state_error').attr('class', 'state_ok');
      if (refresh) location.reload();
     }
     else
     {
      $(search + ' .state_ok').attr('class', 'state_error'); 
      $(search + ' .state_sync').attr('class', 'state_error'); 
     }
    };
    
   // Send the request...
    var value = $(match).val();
    $.getJSON('/store/' + path, {'key':key, 'value':value}, callback);
  };
  
  var change = function()
  {
   // Swap the icon to indicate we are synching...
    $(search + ' .state_ok').attr('class', 'state_sync');
    $(search + ' .state_error').attr('class', 'state_sync');
    
   // Arrange for the update to happen only after a timeout, so it doesn't do it with every keypress...
    clearTimeout($(this).data('timeout'));
    $(this).data('timeout', setTimeout(do_update, 500));
  };
 
 // Setup the handlers on the relevant input boxes...
  $(match).data('timeout', null)
          .change(change)
          .keyup(change)
          .keydown(change);
}

// Same as above but for checkboxes - has to be a little different...
function tie_checkbox(search, path, key)
{
 // String that should match the relevant input, for several possibilities...
  var match = search + ' input';
 
 // Create the handler function for this situation...
  var do_update = function()
  {
   // Set the state to be updated...
    $(search + ' .state_ok').attr('class', 'state_sync');
    $(search + ' .state_error').attr('class', 'state_sync');
   
   // Create the callback handler...
    var callback = function(response)
    {
     if (response)
     {
      $(search + ' .state_sync').attr('class', 'state_ok'); 
      $(search + ' .state_error').attr('class', 'state_ok');
     }
     else
     {
      $(search + ' .state_ok').attr('class', 'state_error'); 
      $(search + ' .state_sync').attr('class', 'state_error'); 
     }
    };
   
   // Prepare the data, including extracting extra information from the html...
    var payload = $(this).parent().parent().data();    
    payload['key'] = key;
    payload['value'] = $(this).is(':checked');
    
   // Send the request...
    $.getJSON('/store/' + path, payload, callback);
  };
 
 // Setup the handler on the input boxes...
  $(match).change(do_update);
}



// Loads into a file selector the given path...
function selector_load(path, select_callback, show_all, inc_tail)
{
 // Callback for once we have the relevant data...
  var fill_selector = function(response)
  {
   // Replace the contents...
    $('#selector').html(response);
   
   // Handle toggling the show all...
    $('#selector input').change(function() {
      // Reload with the required state...
       var path = $('.selector_current').attr('data-path');
       selector_load(path, select_callback, $(this).is(':checked'), inc_tail);
    });
    
   // Setup handlers to manage clicking on current path...
    $('#selector .selector_part').click(function() {
      // Reload the interface with the new path...
       var path = $(this).attr('data-path');
       selector_load(path, select_callback, show_all, inc_tail);
    });
    
   // Setup handlers to manage clicking on directories...
    $('#selector .selector_directory').click(function() {
      // Reload the interface with the new path...
       var path = $(this).attr('data-path');
       selector_load(path, select_callback, show_all, inc_tail);
    });
    
   // Setup handlers to manage clicking on files...
    $('#selector .selector_file').click(function() {
      // Call the callback with the path...
       var path = $(this).attr('data-path');
       select_callback(path);
    });
    
  };
  
 // Request the path from the server...
  $.get('/selector/' + path, {'show_all' : show_all, 'inc_tail' : inc_tail}, fill_selector);
}
