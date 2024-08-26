function toggleText(str) {
    var text = document.getElementById(str);
    if (text.style.display === "none") {
      text.style.display = "inline";
      bluehint.style.display = "none";
      redhint.style.display = "inline";
      sessionStorage.setItem(str,"bluebutton");
    } 
}
function toggleText2(str){
    var text = document.getElementById(str);
    if (text.style.display === "none") {
      text.style.display = "inline";
      redhint.style.display = "none";
      sessionStorage.setItem(str,"redbutton");
    } 
}
function revealText(){
    for (let i = 1; i < 11; i++) {
        let num = i.toString();
        var text = document.getElementById(num);
        text.style.display = "inline";
    }
    
}
function higherLower(str){
  if (str=="higher"){
    document.getElementById("higher").style.display == "inline";
  }
  else if ("int==lower"){
    document.getElementById("lower").style.display == "inline";
  }
  }
function checkcomplete(str){
  const done = localStorage.getItem('done');
  if (done != str){
    localStorage.removeItem('done');
    localStorage.removeItem('completed');
    localStorage.setItem('done',str)
  }
}

