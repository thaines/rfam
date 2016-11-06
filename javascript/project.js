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



// Functions for adding and removing roles...
function add_role()
{
 // Callback function...
  var callback = function(response)
  {
   if (response)
   {
    window.location.reload(); 
   }
   else
   {
    alert('Error adding role'); 
   }
  }
  
 // Extract needed parameters...
  var role = $('#add_role input').val();
  var user = $('#add_role select').val();
 
 // Do the call...
  $.getJSON('/add/role', {'role':role, 'user':user}, callback);
}

function remove_role()
{
 // Callback function...
  var callback = function(response)
  {
   if (response)
   {
    window.location.reload(); 
   }
   else
   {
    alert('Error removing role'); 
   }
  }
  
 // Figure out the ident...
  var ident = $(this).parent().parent().attr('id');
  
 // Send the request...
  $.getJSON('/remove/role', {'ident':ident}, callback);
}


// Functions to move a role...
function role_up()
{
 // Callback function...
  var callback = function(response)
  {
   if (response)
   {
    window.location.reload(); 
   }
   else
   {
    alert('Error moving a role up'); 
   }
  }
 
 // Figure out the ident...
  var ident = $(this).parent().parent().attr('id');
  
 // Send the request...
  $.getJSON('/store/role/'+ident, {'key':'up'}, callback);
}

function role_down()
{
 // Callback function...
  var callback = function(response)
  {
   if (response)
   {
    window.location.reload(); 
   }
   else
   {
    alert('Error moving a role down'); 
   }
  }
 
 // Figure out the ident...
  var ident = $(this).parent().parent().attr('id');
  
 // Send the request...
  $.getJSON('/store/role/'+ident, {'key':'down'}, callback);
}



// Functions for adding adn removing assets...
function add_ext_asset()
{
 // Callback function...
  var callback = function(response)
  {
   if (response)
   {
    window.location.reload(); 
   }
   else
   {
    alert('Error adding external asset'); 
   }
  }
  
 // Extract needed parameters...
  var description = $('#add_ext_asset .asset_description input').val();
  var license = $('#add_ext_asset .asset_license input').val();
  var origin = $('#add_ext_asset .asset_origin input').val();
 
 // Do the call...
  $.getJSON('/add/ext_asset', {'description' : description, 'license' : license, 'origin' : origin}, callback);
}

function remove_ext_asset()
{
 // Callback function...
  var callback = function(response)
  {
   if (response)
   {
    window.location.reload(); 
   }
   else
   {
    alert('Error removing external asset'); 
   }
  }
  
 // Figure out the ident...
  var ident = $(this).parent().parent().attr('id');
  
 // Send the request...
  $.getJSON('/remove/ext_asset', {'ident':ident}, callback);
}



// Setup all the handlers...
$(function() {
 // The basic ones...
  tie_input('#title', 'project', 'title');
  tie_input('#description', 'project', 'description');
  tie_input('#width', 'project', 'width');
  tie_input('#height', 'project', 'height');
  tie_input('#fps', 'project', 'fps');
  tie_input('#license', 'project', 'license');
 
 // The role stuff...
  $('#add_role button').click(add_role);
  $('.role_row button').click(remove_role);
  
  $('.role_row .up').click(role_up);
  $('.role_row .down').click(role_down);
  
  $('.role_row').each(function()
  {
   var ident = $(this).attr('id');
   
   tie_input('#' + ident + ' .role_role', 'role/' + ident, 'role');
   tie_input('#' + ident + ' .role_user', 'role/' + ident, 'user');
  });
  
 // The external asset stuff...
  $('#add_ext_asset button').click(add_ext_asset);
  $('.ext_asset button').click(remove_ext_asset);
  
  $('.ext_asset').each(function()
  {
   var ident = $(this).attr('id');
   
   tie_input('#' + ident + ' .asset_description', 'ext_asset/' + ident, 'description');
   tie_input('#' + ident + ' .asset_license', 'ext_asset/' + ident, 'license');
   tie_input('#' + ident + ' .asset_origin', 'ext_asset/' + ident, 'origin');
  });
});
