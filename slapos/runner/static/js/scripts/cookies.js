/*Cookies Management*/
function setCookie(name,value,expires,path,domain,secure){
  if (!expires){
    var today = new Date();
    expires = new Date(today.getTime() + 365 * 24 * 60 * 60 * 1000);
  }
  document.cookie = name + "=" + escape(value) +
    "; expires=" + expires.toGMTString() +
    ((path) ? "; path=" + path : "/") +
    ((domain) ? "; domain=" + domain : "") +
    ((secure) ? "; secure" : "");
}
function deleteCookie(name,path,domain) {
  if (getCookie(name)) {
    document.cookie = name + "=" +
    ((path) ? "; path=" + path : "/") +
    ((domain) ? "; domain=" + domain : "") +
    "; expires=Thu, 01-Jan-70 00:00:01 GMT";
  }
}
function getCookie(name) {
  var i,x,y,ARRcookies=document.cookie.split(";");
  for (i=0;i<ARRcookies.length;i++){
    x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
    y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
    x=x.replace(/^\s+|\s+$/g,"");
    if (x==name){
      var result = unescape(y);
      if (result != "" && result != null){
        return result;
      }
      return null;
    }
  }
  return null;
}
/**************************/
