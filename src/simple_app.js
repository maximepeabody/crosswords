// import _ from 'lodash';
// import Keyboard from '../node_modules/simple-keyboard/build/index.js';
//import 'simple-keyboard/build/css/index.css';



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
var game_ref;


// global game state
var state = {
  username: "anon" + Math.floor(Math.random() * Math.floor(10000)) + 1,
  current_cell: {},
  dir: 'across',
  current_index: 0,
  game: {},
  gamecode: "",
  loaded: false,
  mobile: false
};

var detectMob = function() {
  return ( ( window.innerWidth <= 800 ) && ( window.innerHeight <= 600 ) );
}

var onVirtualKeyPress = function(button) {
  console.log(button);
  ProcessKey(button);
}

// On page load, init game.
window.onload = function () {
  if (detectMob) {
    //document.getElementById('simple-keyboard');
    state.mobile = true;
    let Keyboard = window.SimpleKeyboard.default;
    console.log('on mobile.');

    let keyboard = new Keyboard({
      onKeyPress: button => onVirtualKeyPress(button),
      mergeDisplay: true,
      layoutName: "default",
      layout: {
        default: [
          "Q W E R T Y U I O P",
          " A S D F G H J K L ",
          " Z X C V B N M {backspace}",
        ],
      },
      display: {
        "{backspace}": "<=",
      }
    });
  }

  // get gamecode from url if represent
  var urlVars = GetUrlVars();
  console.log(urlVars);
  if (urlVars["gamecode"]) {
    console.log("found gamecode, going to load it now.");
    state.gamecode = urlVars["gamecode"];
    LoadGame(state.gamecode);
    window.scrollTo(0,document.body.scrollHeight);
  } else {
    // Go back to main.
  }

}

// Event listeners:
/*
window.addEventListener('unload', function(event) {
  console.log('Loggin off.');
  if (state.username && state.game && state.game.users) {
    // remove the username from users list:
    var updated_users = RemoveUser(state.username);
    state.game.users = updated_users;
    db.ref().child("games").child(state.gamecode).child("users").set(
      state.game.users, function(error) {
        console.log(error);
      }
    );
  }
});
*/

// Click listener for the Board
var ProcessClick = function(x, y) {
  // if the click is on the same cell that is in focus, then change the direction
  if (state.current_cell.x == x && state.current_cell.y == y) {
    state.dir = state.dir == 'across' ? 'down' : 'across';
  }
  // maybe update direction:
  // if direction = across, and there are no cells across, update to down
  if (state.dir == 'across') {
    if (state.game.board[x-1][y].empty && state.game.board[x+1][y].empty) {
      state.dir = 'down';
    }
  } else if (state.game.board[x][y+1].empty && state.game.board[x][y-1].empty) {
    state.dir = 'across';
  }

  state.current_index = state.dir == 'across' ? state.game.board[x][y].across_index : state.game.board[x][y].down_index;
  SetCurrentCell(x, y);
  UpdateView();
};

// Keyboard listener for the board.
var ProcessInput = function(event) {
  console.log('test');
  var key = event.key;
  console.log(key);
  console.log(event.keyCode);
  if (key == 'Backspace' || (event.keyCode > 64 && event.keyCode < 91)) {
    ProcessKey(key);
  }
}

var ProcessKey = function(key) {
  console.log(key);
  var x = state.current_cell.x;
  var y = state.current_cell.y;
  if (key == 	'Backspace' || key == "{backspace}") {
    // if cell was already empty, go to prevCell. Otherwise, stay in current cell.
    if(state.game.board[x][y]["guess"] == "") {
      GoToPrevCell();
    } else {
      state.game.board[x][y]["guess"] = "";
    }
  } else {
    state.game.board[x][y]["guess"] = key;
    GoToNextCell();
  }
  UpdateView();
  Save();
}

// Util methods
var SortedWords = function(words) {
  return words.sort((a, b) => (parseInt(a.index) > parseInt(b.index)) ? 1 : -1);
}

// update the game view based on a snapshot from the server.
var UpdateGame = function(snapshot) {
    state.game = snapshot.val();
    console.log(state.game);
    console.log("loaded game");
    if(!state.loaded) {
      state.loaded = true;
      console.log('sorting list');
      DrawBoard();
      DrawHints();
      // element which needs to be scrolled to
      document.querySelector("#board-container").scrollIntoView();

    }
    UpdateView();
}

// Fetches the firebase game object, and attaches the UpdateGame event
// listener to it. This makes it so that every time the game get's updated
// on the server, the UpdateGame function gets called, which updates the game
// state.
var LoadGame = function(gamecode)  {
  state.game = null;
  state.gamecode = gamecode;
  console.log("fetching game session");
  game_ref = db.ref().child("games").child(gamecode);
  game_ref.on('value', UpdateGame);
};

var GoToNextCell = function() {
  var x = state.current_cell.x;
  var y = state.current_cell.y;
  if (state.dir == 'across') {
    if (!state.game.board[x + 1][y].empty) {
      SetCurrentCell(x + 1, y);
    }
  } else {
    if (!state.game.board[x][y + 1].empty) {
      SetCurrentCell(x, y + 1);
    }
  }
};

var GoToPrevCell = function() {
  var x = state.current_cell.x;
  var y = state.current_cell.y;
  if (state.dir == 'across') {
    if (!state.game.board[x - 1][y].empty) {
      SetCurrentCell(x - 1, y);
    }
  } else if (!state.game.board[x][y - 1].empty) {
        SetCurrentCell(x, y - 1);
  }
};

var SetCurrentCell = function(x,y) {
  state.current_cell = {"x": x, "y": y};
  console.log("updating current cell to (" + x + "," + y + ")");
};

// Updates the view to reflect the current state.
// This should be called on any state change. A keypress event, mouseclick
// or game object update from server.
var UpdateView = function () {
  if (state.current_cell == null) {
    return;
  }


  // 1. Update word list to select current word.
  for (var i = 0; i < state.game.across.length; i++) {
    var word = state.game.across[i];
    var listElement = document.getElementById('across-'+ word.index);

    // 1.1. Select Current Hint if across
    if (state.dir=='across' && parseInt(state.current_index) == parseInt(word.index)) {
      listElement.className = 'hint-list-hint-selected';
      var currentHintElement = document.getElementById('current-hint');
      currentHintElement.innerHTML = "<b> " + word.index + "-across: </b>" + word.hint;
    } else {
      listElement.className = 'hint-list-hint';
    }
  }
  for (var i = 0; i < state.game.down.length; i++) {
    var word = state.game.down[i];
    var listElement = document.getElementById('down-'+word.index);

    // 1.2 Select Current Hint if Down
    if (state.dir=='down' && state.current_index == word.index) {
      listElement.className = 'hint-list-hint-selected';
      var currentHintElement = document.getElementById('current-hint');
      currentHintElement.innerHTML = "<b> " + word.index + "-down: </b>" + word.hint;
    } else {
      listElement.className = 'hint-list-hint';
    }
  }


  // 3. Update board
  for (var x = 0; x < state.game.board.length; x++) {
    for (var y = 0; y < state.game.board[0].length; y++) {
      var element = document.getElementById(x + "-" + y);
      // Empty cells should never be updated.
      if (state.game.board[x][y].empty) {
        continue;
      }

      // Set the cells in focus
      var cell_in_focus = false;
      if (x == state.current_cell.x && y == state.current_cell.y) {
        element.className = "cell-selected-focus";
        var cell_in_focus = true;
      } else if (
        state.current_index != "" &&
        (state.dir == 'across' && state.game.board[x][y].across_index == state.current_index
        || state.dir == 'down' && state.game.board[x][y].down_index == state.current_index)) {
          // set the cell corresponding to the current word in focus
        element.className = "cell-selected";
      } else {
        element.className = "cell-input";
      }

      // Set the letter value
    //  var inputLetterElement = element.querySelector('.cell-input-letter');
      for (var i =0 ; i < element.childNodes.length; i++) {
        if (element.childNodes[i].className == 'cell-input-letter') {
          var input_element = element.childNodes[i];
          input_element.innerHTML = state.game.board[x][y].guess.toUpperCase();
          /*
          if (cell_in_focus) {
            input_element.focus();
          } else {
            input_element.blur();
          }
          */
        }
      }
    }
  }
};

// renders the words into the html
var DrawHints = function() {
  console.log("drawing words");

  // draw the down list
  var downContainer = document.getElementById('down-list');
  var downList = SortedWords(state.game.down);

  for (var i =0 ;i < downList.length; i++) {
    var word = downList[i];
    var downContainer = document.getElementById('down-list');
    var hintElement = document.createElement("div");
    hintElement.id = 'down-' + word.index;
    hintElement.className = 'hint-list-hint';
    hintElement.innerHTML = '<b>' + (word.index) +'. </b>' + word.hint;
    downContainer.appendChild(hintElement);
  }

  downContainer.addEventListener("click", function(e) {
    var id  = e.target.id;
    // if we didn't get a valid id, then try the parent id
    if (id == "") {
      id = e.target.parentElement.id
    }
    var tokens = id.split("-");
    if (tokens.length == 2 ) {
      var index = tokens[1];
      state.dir = 'down';
      state.current_index = index;
      state.current_cell = FindCellForIndex(index);
    }
    UpdateView();
  });

  // draw the across list
  var acrossContainer = document.getElementById('across-list');
  var acrossList = SortedWords(state.game.across);

  for (var i =0 ;i < acrossList.length; i++) {
    var word = acrossList[i];
    var acrossContainer = document.getElementById('across-list');
    var hintElement = document.createElement("div");
    hintElement.className = 'hint-list-hint';
    hintElement.id = 'across-' + word.index;
    hintElement.innerHTML = '<b>' + (word.index) +'. </b>' + word.hint;
    acrossContainer.appendChild(hintElement);
  }

  acrossContainer.addEventListener("click", function(e) {
    var id  = e.target.id;
    // if we didn't get a valid id, then try the parent id
    if (id == "") {
      id = e.target.parentElement.id
    }
    var tokens = id.split("-");
    if (tokens.length == 2 ) {
      var index = tokens[1];
      state.dir = 'across';
      state.current_index = index;
      state.current_cell = FindCellForIndex(index);
    }
  //  document.getElementById('board-container').focus();
    UpdateView();
  });
}

var FindCellForIndex = function(index) {
  for (var x = 0; x < state.game.board.length; x++) {
    for (var y = 0; y < state.game.board[0].length; y++) {
      if (state.game.board[x][y].index == index) {
        return {'x':x, 'y':y};
      }
    }
  }
  return null;
}

var DrawBoard = function() {
  console.log("drawing board");
  // clear the board
  var container = document.getElementById('board-container');
  console.log(container);
  container.innerHtml = "";
  for (var x = 0; x < state.game.board.length; x++) {
    var columnElement = document.createElement("div");
    columnElement.className = "board-column";
    for (var y = 0; y < state.game.board[0].length; y++) {
      var cell = document.createElement("div");
      cell.className = "cell"
      // create black square
      if (state.game.board[x][y].empty) {
        var blackCell = document.createElement("div");
        blackCell.className = "cell-black";
        cell.appendChild(blackCell);
      } else {
        // create input cell div
        var inputCell = document.createElement("div");
        inputCell.className = "cell-input";
        inputCell.id = x + "-" + y;

        // maybe add index node
        if (state.game.board[x][y].index != "") {
          var index = document.createElement("div");
          index.innerHTML = (state.game.board[x][y].index);
          index.className = "cell-index";
          inputCell.appendChild(index);
        }

        // add letter node
        var inputCellLetter = document.createElement("div");
        inputCellLetter.innerHTML = state.game.board[x][y].guess;
        inputCellLetter.className = "cell-input-letter";
        inputCell.appendChild(inputCellLetter);

        cell.appendChild(inputCell);
      }
      columnElement.appendChild(cell);
    }
    container.appendChild(columnElement);
  }
  container.addEventListener("click", function(e) {
    console.log("clicked " + e.target.id);
    var id  = e.target.id;
    // if we didn't get a valid id, then
    if (id == "") {
      id = e.target.parentElement.id
    }
    var coord = id.split("-");
    if (coord.length == 2 ) {
      ProcessClick(parseInt(coord[0]), parseInt(coord[1]));
    }
  });
  container.addEventListener("keydown", ProcessInput);
}

var IsCurrentCell = function(x, y) {
  console.log(state.current_cell);
  return (state.current_cell.x == x) && (state.current_cell.y == y);
};

var Save = function() {
 console.log("saving game");
 console.log(game_ref);
 console.log(state.game);
 db.ref().child("games").child(state.gamecode).set(
   state.game, function(error) {
   if (error) {
     // The write failed...
     console.log("save failed");
   } else {
     console.log("game saved");
   }
 });
};

var SaveUserName = function() {
  console.log("saving user name");
  RemoveUser(state.username);
  state.username = document.getElementById('username').value;
  RemoveUser(state.username);
  console.log(state.username);
  state.game.users.push(state.username);
  db.ref().child("games").child(state.gamecode).child("users").set(
    state.game.users, function(error) {
      if (error) {console.log(error);}
    }
  );
}

var RemoveUser = function(username) {
  if (!state.game.users) {
    state.game.users = [];
    return;
  }
  var updated_users = [];
  for (var i = 0; i< state.game.users.length; i++) {
    if (state.game.users[i] != username) {
      updated_users.push(state.game.users[i]);
    }
  }
  state.game.users = updated_users;

}

var UpdateQueryString = function(key, value, url) {
  if (!url) url = window.location.href;
  var re = new RegExp("([?&])" + key + "=.*?(&|#|$)(.*)", "gi"),
      hash;

  if (re.test(url)) {
      if (typeof value !== 'undefined' && value !== null) {
          return url.replace(re, '$1' + key + "=" + value + '$2$3');
      }
      else {
          hash = url.split('#');
          url = hash[0].replace(re, '$1$3').replace(/(&|\?)$/, '');
          if (typeof hash[1] !== 'undefined' && hash[1] !== null) {
              url += '#' + hash[1];
          }
          return url;
      }
  }
  else {
      if (typeof value !== 'undefined' && value !== null) {
          var separator = url.indexOf('?') !== -1 ? '&' : '?';
          hash = url.split('#');
          url = hash[0] + separator + key + '=' + value;
          if (typeof hash[1] !== 'undefined' && hash[1] !== null) {
              url += '#' + hash[1];
          }
          return url;
      }
      else {
          return url;
      }
    }
  }


var ChangeUrl = function(gamecode) {
  //Change the URL gamecode parm
  UpdateQueryString("gamecode", gamecode);
};

var GetUrlVars = function() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}
