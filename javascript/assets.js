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



// Handles clicking on an asset...
function asset_click()
{
 var dest = $(this).parent().find('a').attr('href');
 window.location = dest;
}



// Handles toggling a types visibility...
function type_click()
{
 // Toggle the class of this...
  if ($(this).hasClass('type_on'))
  {
   $(this).removeClass('type_on');
   $(this).addClass('type_off');
  }
  else
  {
   $(this).removeClass('type_off');
   $(this).addClass('type_on');
  }
  
 // Call through and do the update...
  update_sort_filter();
}


// Makes a type the only one selected...
function type_dblclick()
{
 // Disable all other types...
  $('#type_box div').each(function(index, elem) {
    $(this).removeClass('type_on');
    $(this).addClass('type_off');
  });
 
 // Enable this type...
  $(this).removeClass('type_off');
  $(this).addClass('type_on');
  
 // Call through and do the update...
  update_sort_filter();
}



// Helper function for the below...
function key(mode, row)
{
 var m = mode.slice(0, mode.length-4);
 
 if (m=='name') return $(row).find('.name a').html();
 if (m=='type') return $(row).find('.type').html();
 if (m=='owner') return $(row).find('.owner select')[0].selectedIndex;
 if (m=='state') return $(row).find('.state select')[0].selectedIndex;
 if (m=='priority') return parseInt($(row).attr('data-priority'));
 
 alert('Sorting error!');
}



// Updates both the filter and sorting...
function update_sort_filter()
{
 // Determine which types are visible and which are not...
  var type_visible = {};
  $('#type_box div').each(function(index, toggle) {
    type_visible[$(toggle).attr('data-ident')] = $(toggle).hasClass('type_on');
  });
 
 // Get a list of assets...
  var rows = $('.asset').get();
  
 // Sort them by the current sort key...
  var mode = $('#tail select').val();
  
  rows.sort(function(lhs, rhs) {
    var lhk = key(mode, lhs);
    var rhk = key(mode, rhs);
    
    var ret = 0;
    if (lhk < rhk) ret = -1;
    if (lhk > rhk) ret = 1;
            
    if (ret==0)
    {
     var lhk = key('name_sec', lhs);
     var rhk = key('name_sec', rhs);
     
     if (lhk < rhk) ret = -1;
     if (lhk > rhk) ret = 1;
    }
            
    if (mode[mode.length-3]=='d') ret *= -1;

    return ret;
  });
  
 // Put them back, setting their visibility depending on the filter...
  var filter = $('#tail input').val().toLowerCase();
  $.each(rows, function(index, row) {
   // Put back...
    $('#assets').append(row);
    
   // Decide on visibility...
    var type_ident = $(row).find('.type').attr('data-ident');
    
    if (type_visible[type_ident]==false)
    {
     $(row).hide();
    }
    else
    {
     if (filter=='') $(row).show();
     else
     {
      var name = $(row).find('.name a').html().toLowerCase();
      if (name.indexOf(filter) > -1) $(row).show();
                                else $(row).hide();
     }
    }
  });
}



// Setup all the handlers...
$(function() {
 // Clicking an asset should load the link...
  $('.asset .name').click(asset_click);
  $('.asset .type').click(asset_click);
 
 // Make sure the asset update controls all chat with the server...
  $('.asset').each(function()
  {
   var id = $(this).attr('id');
   var path = $(this).attr('data-path');
   
   tie_input('#' + id + ' .owner', 'asset/' + path, 'owner');
   tie_input('#' + id + ' .state', 'asset/' + path, 'state');
   tie_input('#' + id + ' .priority', 'asset/' + path, 'priority');
  });
  
 // Setup handlers for the filter and sort function...
  $('#tail select').change(update_sort_filter);
  $('#tail input').keyup(update_sort_filter);

 // Arrange toggling support for the types bar...
  $('#type_box div').click(type_click);
  $('#type_box div').dblclick(type_dblclick);
  
 // Make sure they are up to date to start with (Ignore if not on assets page)...
  if ($('#page_tab').attr('data-tab')=='#goto_assets')
  {
   update_sort_filter();
  }
});
