var config = {
  apiKey: 'AIzaSyC1xwRC3Ww0rFGUcRhO_WWuckLPPzcuNB4',
  authDomain: 'crosswords-502c3.firebaseapp.com',
  databaseURL: 'https://crosswords-502c3.firebaseio.com',
  storageBucket: 'crosswords-502c3.appspot.com'
};
firebase.initializeApp(config);
var db = firebase.database();
var game_ref;

var GenerateGame = function(){
  document.getElementById('loader').className = 'loader';

  // Fetch random game of specified max_difficulty
  var difficulty = Math.floor(Math.random() * Math.floor(5)) + 1;
  var game_num = Math.floor(Math.random() * Math.floor(4)) + 1;
  var puzzle_ref = db.ref().child("puzzles")
    .child(difficulty).child("game-" + game_num).once("value").then(function(snapshot) {
      var puzzle = snapshot.val();
      if (puzzle == null) {
        console.log("Could not generate puzzle");
      } else {
        console.log("got puzzle. Now loading it into game");
        // Generate game / generate gamecode.
        gamecode =  Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

        // Create a new game reference, and save the puzzle data there.
        game_ref = db.ref().child("games").child(gamecode);
        game_ref.set(puzzle);

        // Load the new game into the scope
        game_ref.on('value', function() {
          setTimeout(function(){
            window.location.href = "./simple.html?gamecode=" + gamecode;
          }, 2000);
        });
      }
    });
}

var LoadGame = function() {
  var gamecode = document.getElementById('gamecode-input');
  window.location.href = "./simple.html?gamecode=" + gamecode.value;
}
