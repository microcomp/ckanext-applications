var rows = document.getElementsByTagName('td')
var x = "<a href='#' onclick='hide()' alt='hide content'>hide</a><br />"
text = ""
var ii = 0
for(var i=0; i < rows.length; i++){
	var text = rows[i].innerHTML
	if(text.substring(0,34)=='{"type": "Polygon", "coordinates":'){
		x += text
		ii = i
		rows[i].innerHTML = "<a href='#' onclick='show()' alt='show text'>show</a>"
	}
}

function show(){
	rows[ii].innerHTML = x
}
function hide(){
	rows[ii].innerHTML = "<a href='#' onclick='show()' alt='show text'>show</a>"
}