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



// Button click handlers...
function reset_stats()
{
 // Extract the path of the asset...
  var path = $('#page_tab').attr('data-path');
  
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error reseting render statistics');  
   }
  };
  
 // Send the request...
  $.getJSON('/action/reset_stats/' + path, {}, callback);
}


function checkpoint()
{
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    var d = new Date();
    $('#checkpoint_result').html('Checkpointed at ' + d.toTimeString());
   }
   else
   {
    $('#checkpoint_result').html('Error: Checkpoint not created');
   }
  };
  
 // Send the request...
  path = $('#page_tab').attr('data-path');
  $.getJSON('/action/checkpoint/' + path, {}, callback);
}

function delete_asset()
{
 if (confirm('Are you sure you want to delete this asset?'))
 {
  // Callback of response - refresh the page...
   var callback = function(response)
   {
    if (response)
    {
     window.location.pathname = '/assets';
    }
    else
    {
     alert('Failed to delete file');
    }
   };
  
  // Send the request...
   path = $('#page_tab').attr('data-path');
   $.getJSON('/action/delete/' + path, {}, callback);
 }
}



// Setup all the handlers...
$(function() {
 // Extract the path of the asset...
  var path = $('#page_tab').attr('data-path');
  
 // Do the many handlers...
  tie_input('#name', 'asset/' + path, 'name');
  tie_input('#description', 'asset/' + path, 'description');
  
  tie_input('#type', 'asset/' + path, 'type');
  tie_input('#state', 'asset/' + path, 'state');
  tie_input('#priority', 'asset/' + path, 'priority');
  tie_checkbox('#render', 'asset/' + path, 'render');
  tie_checkbox('#final', 'asset/' + path, 'final');
  
  tie_input('#owner', 'asset/' + path, 'owner');
  tie_checkbox('.supporter', 'asset/' + path, 'support');
  
 // Make the back button a little smarter...
  $('#back').click(function()
  {
   var split = window.location.href.split('?');
   if (split.length>1)
   {
    dest = split[1];
    if (dest=='home')
    {
     window.location.pathname = '/home';
     return false;
    }
    if (dest=='team')
    {
     window.location.pathname = '/team';
     return false;
    }
   }
  });
  
 // Setup button handlers...
  $('#reset_stats').click(reset_stats);
  $('#checkpoint').click(checkpoint);
  $('#delete').click(delete_asset);
});
