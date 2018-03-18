var app = angular.module('myApp', ["firebase"]);


app.controller('myCtrl', function($scope, $firebaseObject) {
  // Initialize the Firebase SDK
  var config = {
    apiKey: 'AIzaSyC1xwRC3Ww0rFGUcRhO_WWuckLPPzcuNB4',
    authDomain: 'crosswords-502c3.firebaseapp.com',
    databaseURL: 'https://crosswords-502c3.firebaseio.com',
    storageBucket: 'crosswords-502c3.appspot.com'
  };
  firebase.initializeApp(config);
  
  var ref = firebase.database().ref().child("boards").child("game1");
  // download the data into a local object
  var syncObject = $firebaseObject(ref);
  // synchronize the object with a three-way data binding
  // click on `index.html` above to see it used in the DOM!
  syncObject.$bindTo($scope, "game");
  //var board_length = $scope.game.board.length;
  //$scope.cell_width = 100/board_length + '%';
  
  
  });


