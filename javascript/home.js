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



// The checkpoint button...
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
  path = $('#current').attr('data-path');
  $.getJSON('/action/checkpoint/' + path, {}, callback);
}



// Setup all the handlers...
$(function() {
  // Handle the first asset...
   path = $('#current').attr('data-path');
   tie_input('#current_description', 'asset/' + path, 'description');
   tie_input('#current_owner', 'asset/' + path, 'owner', true);
   tie_input('#current_state', 'asset/' + path, 'state', true);
   tie_input('#current_priority', 'asset/' + path, 'priority', true);
   
  // Make checkpoint button dance...
   $('#checkpoint').click(checkpoint);
});
