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



// This is called each time the filename needs to be recalculated...
function update_filename()
{
 // Check that the fields are filled in - if not set the filename to an empty string...
  if (($('#name input').val()=='')||($('#type select').val()==''))
  {
   $('#filename input').val('');
   return; 
  }
  
 // Get the details and calculate the default filename...
  var type = $('#type select').val();
  var dir = $('#type option[value=' + type + ']').attr('data-dir');
  var ext = $('#type option[value=' + type + ']').attr('data-ext');
  var name = $('#name input').val().toLowerCase().replace(/[\s?*]/g, '_');
  
  var fn = dir + '/' + name + ext;
  
 // Record it in the filename field...
  $('#filename input').val(fn);
}



// To actually create the asset...
function create()
{
 // Extract needed parameters...
  var name = $('#name input').val();
  var type = $('#type select').val();
  var filename = $('#filename input').val();
  var description = $('#description textarea').val();
  
 // Callback function...
  var callback = function(response)
  {
   if (response)
   {
    window.location = "/asset/" + filename;
   }
   else
   {
    alert('Error adding asset'); 
   }
  }

 // Do the call...
  $.getJSON('/add/asset', {'name':name, 'type':type, 'filename':filename, 'description':description}, callback);
}



// Setup all the handlers...
$(function() {
 // Make the filename field change as the others are updated...
  $('#name input').keyup(update_filename);
  $('#type select').change(update_filename);
  
 // Create button needs to do something...
  $('#create').click(create);
});
