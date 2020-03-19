var app = angular.module('myApp', ["firebase", "ngRoute"]);

app.controller('myCtrl', function($scope, $firebaseObject, $location) {
  //console.log($location.search());
  // Initialize the Firebase SDK
  var config = {
    apiKey: 'AIzaSyC1xwRC3Ww0rFGUcRhO_WWuckLPPzcuNB4',
    authDomain: 'crosswords-502c3.firebaseapp.com',
    databaseURL: 'https://crosswords-502c3.firebaseio.com',
    storageBucket: 'crosswords-502c3.appspot.com'
  };
  firebase.initializeApp(config);
  var db = firebase.database();

  $scope.GenerateGame = function(difficulty) {
    $scope.game = null;
    console.log("generating puzzle");
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
          gamecode =  Math.random().toString(36).substring(2, 15)
            + Math.random().toString(36).substring(2, 15);

          // Create a new game reference, and save the puzzle data there.
          db.ref().child("games").child(gamecode).set(puzzle);

          // Load the new game into the scope
          $scope.game =  $firebaseObject(
            db.ref().child("games").child(gamecode));

          $scope.game.$loaded().then(function(data) {
            console.log("loaded game"); // true
          })
          .catch(function(error) {
            console.error("Error:", error);
          });
          $scope.gamecode = gamecode;
          $scope.changeUrl(gamecode);
        }
      });
  };

  $scope.GoToGame = function(gamecode)  {
    $scope.game = null;
    console.log("fetching game session");
    db.ref().child("games").child(gamecode).once("value").then(function(snapshot){
      if (snapshot.val() == null){
        console.log ("no puzzle found for gamecode");
      } else {
        console.log("found puzzle, loading it.");
      }
    });
    $scope.game = $firebaseObject(db.ref().child("games").child(gamecode));
    $scope.game.$loaded().then(function(data) {
      console.log("loaded game"); // true
    })
    .catch(function(error) {
      console.error("Error:", error);
    });
    $scope.changeUrl(gamecode);
  };

  $scope.Save = function() {
    console.log("saving game");
    $scope.game.$save().then(function(ref) {
      ref.key === $scope.game.$id; // true
    }, function(error) {
      console.log("Error:", error);
    });
  }

  $scope.changeUrl = function(gamecode) {
    //Change the URL gamecode parm
    $location.search('gamecode', gamecode);
  };



  // get gamecode from url if represent
  var tokens = $location.url().split("gamecode=");
  console.log(tokens);
  if (tokens.length > 1) {
    console.log("gamecode token")
    $scope.GoToGame(tokens[1]);
  } else {
    console.log("no tokens");
  }

});
