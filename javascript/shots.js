// Handles clicking on an shot...
function shot_click()
{
 var dest = $(this).parent().find('a').attr('href');
 window.location = dest;
}


// Handles clicking on a rating...
function rating_click()
{
 if ($(this).hasClass('r0')) rating = 0;
 if ($(this).hasClass('r1')) rating = 1;
 if ($(this).hasClass('r2')) rating = 2;
 if ($(this).hasClass('r3')) rating = 3;
 if ($(this).hasClass('r4')) rating = 4;
 if ($(this).hasClass('r5')) rating = 5;
 
 var parent = $(this).parent()
 
 var callback = function(response)
 {
  if (rating<1) parent.find('.r1').removeClass('on').addClass('off');
           else parent.find('.r1').removeClass('off').addClass('on');
  if (rating<2) parent.find('.r2').removeClass('on').addClass('off');
           else parent.find('.r2').removeClass('off').addClass('on');
  if (rating<3) parent.find('.r3').removeClass('on').addClass('off');
           else parent.find('.r3').removeClass('off').addClass('on');
  if (rating<4) parent.find('.r4').removeClass('on').addClass('off');
           else parent.find('.r4').removeClass('off').addClass('on');
  if (rating<5) parent.find('.r5').removeClass('on').addClass('off');
           else parent.find('.r5').removeClass('off').addClass('on');
 };
 
 path = parent.parent().parent().attr('data-path');
 $.getJSON('/store/asset/' + path, {'key':'rating', 'value':rating}, callback);
}



function pipeline_record(pipeline)
{
 var callback = function(response)
 {
  if (response)
  {
   pipeline.find('.state_sync').attr('class', 'state_ok'); 
   pipeline.find('.state_error').attr('class', 'state_ok');
  }
  else
  {
   pipeline.find('.state_ok').attr('class', 'state_error'); 
   pipeline.find('.state_sync').attr('class', 'state_error'); 
  }
 };
 
 path = pipeline.parent().attr('data-path');
 $.getJSON('/store/asset/' + path, {'key':'pipeline', 'value':$(pipeline).find('select').val()}, callback);
}



function pipeline_change()
{
 // Update class of select so it has the right colour...
  $(this).attr('class', $(this).children(':selected').val())
  
 // Swap the icon to indicate we are synching...
  $(this).parent().find('.state_ok').attr('class', 'state_sync');
  $(this).parent().find('.state_error').attr('class', 'state_sync');
    
 // Arrange for the update to happen only after a timeout, so it doesn't do it with every keypress...
  var pipeline = $(this).parent();
  clearTimeout($(this).data('timeout'));
  $(this).data('timeout', setTimeout(function(){pipeline_record(pipeline)}, 500)); 
}



// Setup all the handlers...
$(function() {
 // Clicking a shot should load its asset link...
  $('.shot .name').click(shot_click);
  
 // Make sure the shot update controls all chat with the server...
  $('.shot').each(function()
  {
   var id = $(this).attr('id');
   var path = $(this).attr('data-path');
   
   tie_input('#' + id + ' .owner', 'asset/' + path, 'owner');
  });
  
 // Make the ratings work...
  $('.rating div').click(rating_click);
  
 // Correct which is selected for pipeline selector...
  $('.pipeline select').each(function()
  {
   $(this).val($(this).attr('class'));
  });
 
 // Make the pipeline selector work...
  $('.pipeline select').data('timeout', null)
                       .change(pipeline_change)
                       .keyup(pipeline_change)
                       .keydown(pipeline_change);
});
