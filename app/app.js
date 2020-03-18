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
  var db = firebase.database();

  var ref = db.ref().child("puzzles").child("1").child("game-4");

  // var ref = firebase.database().ref().child("boards").child("game1");
  // download the data into a local object
  var syncObject = $firebaseObject(ref);

  // synchronize the object with a three-way data binding
  // click on `index.html` above to see it used in the DOM!
  syncObject.$bindTo($scope, "game");
  //var board_length = $scope.game.board.length;
  //$scope.cell_width = 100/board_length + '%';

  $scope.GenerateGame = function(difficulty) {
    // Fetch random game of specified max_difficulty
    var game_num = Math.floor(Math.random() * Math.floor(4)) + 1;
    // Fetch the puzzle data
    var puzzle_ref = db.ref().child("puzzles")
      .child(difficulty).child("game-" + game_num).once("value").then(function(snapshot) {
        var puzzle = snapshot.val();
        if (puzzle == null) {
          console.log("Could not generate puzzle");
        } else {
          console.log("got puzzle. Now loading it into game")
          // Generate game / generate gamecode.
          $scope.gamecode =  Math.random().toString(36).substring(2, 15)
            + Math.random().toString(36).substring(2, 15);
          // Create a new game ref and copy the puzzle data there.
          db.ref().child("games").child($scope.gamecode).set(puzzle);
          var gameSyncObject =  $firebaseObject(
            db.ref().child("games").child($scope.gamecode));
          gameSyncObject.$bindTo($scope, "game");
        }
      });
  };

  $scope.GoToGame = function(gamecode)  {
    db.ref().child("games").child(gamecode).once("value").then(function(snapshot){
      if (snapshot.val() == null){
        console.log ("no puzzle found for gamecode");
      } else {
        console.log("found puzzle, loading it.");
      }
    });
    var gameSyncObject = $firebaseObject(db.ref().child("games").child(gamecode));
    gameSyncObject.$bindTo($scope, "game");
  };

});
