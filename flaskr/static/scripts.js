//function for blue team hint button that makes the button invisible after click and the hint visible
function toggleText(str) {
    var text = document.getElementById(str);
    if (text.style.display === "none") {
      text.style.display = "inline";
      bluehint.style.display = "none";
      sessionStorage.setItem(str,"bluebutton");
    } 
}
//function for red team hint button that makes the button invisible after click and the hint visible
function toggleText2(str){
    var text = document.getElementById(str);
    if (text.style.display === "none") {
      text.style.display = "inline";
      redhint.style.display = "none";
      sessionStorage.setItem(str,"redbutton");
    } 
}
//function to reveal all player names after completition
function revealText(){
    for (let i = 1; i < 11; i++) {
        let num = i.toString();
        var text = document.getElementById(num);
        text.style.display = "inline";
    }
    
}
//function to check if the user has completed a run for the particular id, if not it removes the localstorage as ids can be evenutally repeated and sets the value to the current id so the user
//cannout refresh to play again that day
function checkcomplete(str){
  const done = localStorage.getItem('done');
  if (done != str){
    localStorage.removeItem('done');
    localStorage.removeItem('completed');
    localStorage.setItem('done',str)
  }
}

