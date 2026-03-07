// CREATE MAP

var map = L.map('map').setView([31.5204, 74.3587], 13);


// MAP TILES

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
maxZoom: 19
}).addTo(map);


// BUS ICON

var busIcon = L.icon({
iconUrl: "https://cdn-icons-png.flaticon.com/512/3448/3448339.png",
iconSize: [35,35],
iconAnchor: [17,35]
});


// ROUTES FOR BUSES

var routes = [

[[31.5204,74.3587],[31.5220,74.3600],[31.5240,74.3620],[31.5260,74.3650]],

[[31.5150,74.3500],[31.5170,74.3520],[31.5190,74.3550],[31.5210,74.3580]],

[[31.5250,74.3700],[31.5270,74.3720],[31.5290,74.3740],[31.5310,74.3760]],

[[31.5100,74.3600],[31.5120,74.3620],[31.5140,74.3640],[31.5160,74.3660]],

[[31.5300,74.3500],[31.5320,74.3520],[31.5340,74.3540],[31.5360,74.3560]],

[[31.5180,74.3720],[31.5200,74.3740],[31.5220,74.3760],[31.5240,74.3780]],

[[31.5350,74.3650],[31.5370,74.3670],[31.5390,74.3690],[31.5410,74.3710]],

[[31.5050,74.3550],[31.5070,74.3570],[31.5090,74.3590],[31.5110,74.3610]],

[[31.5280,74.3400],[31.5300,74.3420],[31.5320,74.3440],[31.5340,74.3460]],

[[31.5400,74.3500],[31.5420,74.3520],[31.5440,74.3540],[31.5460,74.3560]],

[[31.5000,74.3650],[31.5020,74.3670],[31.5040,74.3690],[31.5060,74.3710]],

[[31.5450,74.3600],[31.5470,74.3620],[31.5490,74.3640],[31.5510,74.3660]]

];


// ARRAY FOR BUSES

var buses = [];


// CREATE ROUTES AND BUSES

routes.forEach(function(route,index){

// DRAW ROUTE

L.polyline(route,{
color:"blue",
weight:4,
opacity:0.6
}).addTo(map);


// CREATE BUS

var bus = L.marker(route[0],{icon:busIcon})
.addTo(map)
.bindPopup("Bus #" + (index+1));

buses.push({
marker:bus,
route:route,
position:0
});

});


// MOVE BUSES

setInterval(function(){

buses.forEach(function(busObj){

if(busObj.position < busObj.route.length-1){

busObj.position++;

busObj.marker.setLatLng(busObj.route[busObj.position]);

}

});

},2000);