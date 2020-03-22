var app = angular.module('myApp', ["firebase", "ngRoute"]);

// <div class="cell-black" ng-hide="!cell.empty"></div> \
//             <div ng-hide="cell.empty" class="cell-input" \
//                ng-click="processClick($parent.$index, $index)" \
//                id="{{$parent.$index + '-' + $index}}"> \
//             <p class="cell-letter"> \
//               {{cell.guess.toUpperCase()}} \
//             </p> \
//             <p class="cell-index"> \
//               {{cell.index}} \
//             </p> \
//           </div>'

app.directive("cellDir", function() {
  return {
    template : '<p class="cell-letter"> {{cell.guess.toUpperCase()}} <p> <p class="cell-index"> {{cell.index}} </p>',
    link: function(scope, element, attr) {
      if (!attr.x || !attr.y) {
        return;
      }
      if (scope.game.board[attr.x][attr.y].empty) {
        element.addClass("cell-black");
        return;
      }
      if (attr.x == scope.current_cell.x && scope.current_cell.y == attr.y) {
        console.log("making cell selected");
        console.log(attr.cell);
        element.addClass("cell-selected-focus");
      }
    },
  };
});

app.controller('myCtrl', function($scope, $firebaseObject, $location, $timeout) {
  //console.log($location.search());
  // Initialize the Firebase SDK
  var config = {
    apiKey: process.env.API_KEY,
    authDomain: 'crosswords-502c3.firebaseapp.com',
    databaseURL: 'https://crosswords-502c3.firebaseio.com',
    storageBucket: 'crosswords-502c3.appspot.com'
  };
  firebase.initializeApp(config);
  var db = firebase.database();
  var game_ref;

  // global state:
  $scope.username = "anon" + Math.floor(Math.random() * Math.floor(100)) + 1;
  $scope.current_cell = {};
  $scope.last_cell = {};
  $scope.dir = 'across';
  $scope.current_index = "";

  // update the game view based on a snapshot from the server.
  var UpdateGame = function(snapshot) {
    $timeout(function() {
      $scope.game = snapshot.val();
      console.log($scope.game);
      console.log("loaded game");
    }, 0).then(function(){
        $timeout(function(){
        console.log("updating view");
        updateView();
      });
    });
  }

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
          $scope.gamecode =  Math.random().toString(36).substring(2, 15)
            + Math.random().toString(36).substring(2, 15);

          // Create a new game reference, and save the puzzle data there.
          game_ref = db.ref().child("games").child($scope.gamecode);
          game_ref.set(puzzle);

          // Load the new game into the scope
          game_ref.on('value', UpdateGame);

          $scope.changeUrl($scope.gamecode);
        }
      });
  };

  $scope.GoToGame = function(gamecode)  {
    $scope.game = null;
    $scope.gamecode = gamecode;
    console.log("fetching game session");

    game_ref = db.ref().child("games").child(gamecode);
    game_ref.on('value', UpdateGame);;
    $scope.changeUrl(gamecode);
  };

  var goToNextCell = function() {
    var x = $scope.current_cell.x;
    var y = $scope.current_cell.y;
    if ($scope.dir == 'across') {
      if (!$scope.game.board[x + 1][y].empty) {
        $scope.SetCurrentCell(x + 1, y);
      }
    } else {
      if (!$scope.game.board[x][y + 1].empty) {
        $scope.SetCurrentCell(x, y + 1);
      }
    }
  }

  var goToPrevCell = function() {
    var x = $scope.current_cell.x;
    var y = $scope.current_cell.y;
    if ($scope.dir == 'across') {
      if (!$scope.game.board[x - 1][y].empty) {
        $scope.SetCurrentCell(x - 1, y);
      }
    } else {
      if (!$scope.game.board[x][y - 1].empty) {
        $scope.SetCurrentCell(x, y - 1);
      }
    }
  }

  $scope.SetCurrentCell = function(x,y) {
    var temp = $scope.current_cell;
    $scope.current_cell = {"x": x, "y": y};
    $scope.last_cell = temp;
    console.log("updating current cell from (" + $scope.last_cell.x + "," + $scope.last_cell.y +  ") to (" + x + "," + y + ")");
  }

  // Updates the view to reflect the current state.
  // This should be called on any state change. A keypress event, mouseclick
  // or game object update from server.
  updateView = function () {
    return;
    if ($scope.current_cell == null) {
      return;
    }
    for (var x = 0; x < $scope.game.board.length; x++) {
      for (var y = 0; y < $scope.game.board[0].length; y++) {
        element = document.querySelector("[id='" + x + "-" + y +"']");
        // Empty cells should never be updated.
        if ($scope.game.board[x][y].empty) {
          continue;
        }
        // set the current cell in focus
        if (x == $scope.current_cell.x && y == $scope.current_cell.y) {
          element.className = "cell-selected-focus";
        } else if ($scope.dir == 'across' && $scope.game.board[x][y].across_index == $scope.current_index
          || $scope.dir == 'down' && $scope.game.board[x][y].down_index == $scope.current_index) {
            // set the cell corresponding to the current word in focus
          element.className = "cell-selected";
        } else {
          element.className = "cell-input";
        }
      }
    }
  }

  $scope.IsCurrentCell = function(x, y) {
    console.log($scope.current_cell);
    return ($scope.current_cell.x == x) && ($scope.current_cell.y == y);
  }

 $scope.Save = function() {
   console.log("saving game");
   console.log(game_ref);
   console.log($scope.game);
   db.ref().child("games").child($scope.gamecode).set(
     angular.copy($scope.game), function(error) {
     if (error) {
       // The write failed...
       console.log("save failed");
     } else {
       console.log("game saved");
     }
   });
}

  $scope.changeUrl = function(gamecode) {
    //Change the URL gamecode parm
    $location.search('gamecode', gamecode);
  };

  // Event listeners:
  $scope.processClick = function(x, y) {
    console.log("processing click");
    // if the click is on the same cell that is in focus, then change the direction
    if ($scope.current_cell.x == x && $scope.current_cell.y == y) {
      $scope.dir = $scope.dir == 'across' ? 'down' : 'across';
    }
    // maybe update direction:
    // if direction = across, and there are no cells across, update to down
    if ($scope.dir == 'across') {
      if ($scope.game.board[x-1][y].empty && $scope.game.board[x+1][y].empty) {
        $scope.dir = 'down';
      }
    } else if ($scope.game.board[x][y+1].empty && $scope.game.board[x][y-1].empty) {
      $scope.dir = 'across';
    }
    $scope.SetCurrentCell(x, y);
    var index = $scope.dir == 'across' ? $scope.game.board[x][y].across_index
      : $scope.game.board[x][y].down_index;
    $scope.current_index = index;
    updateView();
  }

  $scope.processInput = function(event) {
    console.log('key pressed');
    var x = $scope.current_cell.x;
    var y = $scope.current_cell.y;
    if (event.key == 	'Backspace' /*backspace*/) {
      console.log("backspace");
      console.log($scope.game.board[x][y]['guess']);
      // if cell was already empty, go to prevCell. Otherwise, stay in current cell.
      if($scope.game.board[x][y]["guess"] == "") {
        goToPrevCell();
      } else {
        $scope.game.board[x][y]["guess"] = "";
      }
    } else {
      console.log('setting cell to' +event.key);
      $scope.game.board[x][y]["guess"] = event.key;
      goToNextCell();
    }
    $scope.Save();
    updateView();
  }

  $scope.indexFromWord = function(word){
    return parseInt(word.index);
  }


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
