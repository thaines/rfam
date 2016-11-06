// Code for when a user clicks a project...
function select_project()
{
 // Update the selection...
  $('#selected_project').removeAttr('id');
  $(this).attr('id', 'selected_project');
  var project = $(this).attr('data-ident');
  
 // Arrange for the correct users to be visible...
  $('.user').each(function(i, elem)
  {
   var projects = $.parseJSON($(this).attr('data-projects'));
   
   var found = false;
   for (var i=0; i<projects.length; i++)
   {
    if (projects[i]==project)
    {
     found = true;
     break;
    }
   }
   
   if (found) $(this).show();
         else $(this).hide();
  });
  
 // If the selected user is no longer visible deselect them and hide the login button...
  if ($('#selected_user').is(':hidden'))
  {
   $('#selected_user').removeAttr('id');
   $('#login').hide(); 
  }
}



// Code for when a user clicks a, erm, user...
function select_user()
{
 // Update the selection...
  $('#selected_user').removeAttr('id');
  $(this).attr('id', 'selected_user');
  
 // Make the login button visible - by construction we must have a valid login setup by now...
  $('#login').show();
}



// Code that arranges for a login...
function login()
{
 // Get the project and username...
  var project = $('#selected_project').attr('data-ident');
  var user = $('#selected_user').attr('data-ident');
 
 // Callback to handle the login result...
  var callback = function(response)
  {
   window.location.reload();
  }
  
 // Call through to the server with the information...
  $.getJSON('login', {'project':project, 'user':user}, callback);
}



// Register handlers for clicking the various things...
$(function() {
$('.project').click(select_project);
$('.user').click(select_user);
$('#login').click(login);
});
