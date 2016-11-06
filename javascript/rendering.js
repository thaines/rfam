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



// Function that handles selecting files in the file selector - it receives a path...
function on_file_select(path)
{
 // callback for when we have information about the selected file...
  var got_info = function(response)
  {
   $('#name').attr('data-path', path);
   
   $('#name input').val(response['name']);
   $('#start input').val(response['start']);
   $('#end input').val(response['end']);
   $('#final input').prop('checked', response['final']);
  };
 
 // Request further information about the file in question...
  $.get('/info/' + path, {}, got_info);
}



// Function that does the work when the user asks to render a job...
function render()
{
 // Get the parameters...
  var path = $('#name').attr('data-path');
  var name = $('#name input').val();
  var start = $('#start input').val();
  var end = $('#end input').val();
  var final = $('#final input').is(':checked');
  
 // Sanity check...
  if (path=='')
  {
   alert('You need to select a file to render');
   return; 
  }
  
  if (name=='')
  {
   alert('The job must have a name');
   return; 
  }
  
  if (parseInt(end) < parseInt(start))
  {
   alert('Your frame range is backwards');
   return;
  }
 
 // Callback to handle the job response...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error creating render job');  
   }
  };
 
 // Do the actual call...
  $.getJSON('/add/job/' + path, {'name' : name, 'start' : start, 'end' : end, 'final' : final}, callback);
}



// Four functions, one for each job button...
function job_pause()
{
 // Get the uuid of the job...
  var uuid = $(this).parent().parent().attr('id');
 
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error pausing job');  
   }
  };
  
 // Send the request...
  $.getJSON('/store/job/' + uuid, {'key' : 'pause', 'value' : 'true'}, callback);
}


function job_resume()
{
 // Get the uuid of the job...
  var uuid = $(this).parent().parent().attr('id');
 
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error resuming job');  
   }
  };
  
 // Send the request...
  $.getJSON('/store/job/' + uuid, {'key' : 'pause', 'value' : 'false'}, callback);
}


function job_cancel()
{
 if (confirm('Are you sure you want to terminate this job?'))
 {
  // Get the uuid of the job...
   var uuid = $(this).parent().parent().attr('id');
 
  // Callback of response - refresh the page...
   var callback = function(response)
   {
    if (response)
    {
     location.reload();
    }
    else
    {
     alert('Error removing job');  
    }
   };
  
  // Send the request...
   $.getJSON('/remove/job/' + uuid, {}, callback);
 }
}


function job_remove()
{
 // Get the uuid of the job...
  var uuid = $(this).parent().parent().attr('id');
 
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error removing job');  
   }
  };
  
 // Send the request...
  $.getJSON('/remove/job/' + uuid, {}, callback);
}



// Pause and unpause functions for the node buttons...
function node_pause()
{
 // Get the ident of the node...
  var ident = $(this).parent().parent().attr('id');
 
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error pausing node');  
   }
  };
  
 // Send the request...
  $.getJSON('/store/node/' + ident, {'key' : 'pause', 'value' : 'true'}, callback);
}


function node_resume()
{
 // Get the ident of the node...
  var ident = $(this).parent().parent().attr('id');
 
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error resuming node');  
   }
  };
  
 // Send the request...
  $.getJSON('/store/node/' + ident, {'key' : 'pause', 'value' : 'false'}, callback);
}



// Emergency controls...
function emergency_stop()
{
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error performing an emergency stop:-(');  
   }
  };
  
 // Send the request...
  $.getJSON('/action/emergency/stop', {}, callback);
}


function emergency_start()
{
 // Callback of response - refresh the page...
  var callback = function(response)
  {
   if (response)
   {
    location.reload();
   }
   else
   {
    alert('Error performing an emergency start:-(');  
   }
  };
  
 // Send the request...
  $.getJSON('/action/emergency/start', {}, callback);
}



// Setup all the handlers...
$(function() {
 // Make the file selector walk...
  selector_load('', on_file_select, false, true);
  
 // Make render job creation crawl...
  $('#render').click(render);
  
 // Make sure the jobs climb...
  $('.job').each(function()
  {
   var uuid = $(this).attr('id');
   
   tie_input('#' + uuid + ' .priority', 'job/' + uuid, 'priority');
   
   $('#' + uuid + ' .pause').click(job_pause);
   $('#' + uuid + ' .resume').click(job_resume);
   $('#' + uuid + ' .cancel').click(job_cancel);
   $('#' + uuid + ' .remove').click(job_remove);
  });
  
 // Make sure the nodes tango...
  $('.node').each(function()
  {
   var ident = $(this).attr('id');
   
   $('#' + ident + ' .pause').click(node_pause);
   $('#' + ident + ' .resume').click(node_resume);
  });
  
 // Make the emergency buttons jive...
  $('#emergency_stop').click(emergency_stop);
  $('#emergency_start').click(emergency_start);
});
