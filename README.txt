
** Cooperative Crossword Game **

Uses a bank of New York Times' word-hint pairs to automatically create a database of crossword games. 

** FrontEnd **

use AngularJs, connect with firebase, which lets multiple users work on the same crossword.

Display: 
- The board: consists of a grid, where you can input the letters when there's an empty space.
- List of word/hint pairs.

** Backend **

-Static GitHub page.
-Firebase database
-local python script which creates boards and stores them to firebase.

** Board Datastructure **
board consists of:
-2d array of : {char for letter/empty, char for winning letter, number for index of word}
-list of {word, hint, index(x,y), index} for both down and across.

active game board adds to the board data structure:
-for each word, we add "guessed_word", and correct(true/false)
-we can have a second board, the guessed_board.
