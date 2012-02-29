/*Common javascript function*/
String.prototype.toHtmlChar = function(){
  c = {'<':'&lt;', '>':'&gt;', '&':'&amp;', '"':'&quot;', "'":'&#039;',
       '#':'&#035;' };
  return this.replace( /[<&>'"#]/g, function(s) { return c[s]; } );
}

/**************************/
