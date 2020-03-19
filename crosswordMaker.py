import csv
import random
import copy
import sys
from pyrebase import pyrebase

config = {
    "apiKey": "AIzaSyC1xwRC3Ww0rFGUcRhO_WWuckLPPzcuNB4",
    "authDomain": "crosswords-502c3.firebaseapp.com",
    "databaseURL": "https://crosswords-502c3.firebaseio.com",
    "storageBucket": "crosswords-502c3.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
b = {"id": "1", "board": {"length": "5"}}

## The keys to the cvs file
keys = ["id","thekey","key","source","file","date","day","difficulty","direction",
  "number","instruction","flag","groupid","question","answer"]

MAX = 15
EMPTY = "#"
OPEN = "O"

class Board:
  words_down = []
  words_across = []

  def __init__(self, size):
    self.size = size
    for x in range(0, max + 1):
      for y in range(0, max + 1):
        self.squares[Coord(x,y)] = EMPTY

  def open_at(coord):
    return self.squares[coord].is_empty()

  def letter_at(coord):
    return self.squares[coord].letter




class Word:
  def __init__(self, word, coord, hint, direction):
    self.word = word
    self.coord = coord
    self.hint = hint
    self.direction = direction

class Coord:
  def __init__(self, x, y):
    self.x = x
    self.y = y

class Square:
  def __init__(self, coord, letter, number, word):
    self.coord = coord
    self.letter = letter
    self.number = number
    self.word = word

  def is_empty(self):
    return self.letter == EMPTY

# Load the clues
#
# Returns: a list of clue objects, containing the key-value pairs from the cvs file.
def load_clues():
  print("Loading clues from csv file")
  clues = []
  with open('nyt-crossword-master/clues.csv', 'r') as csvfile:
    clue_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in clue_reader:
      index = 0
      clue = {}
      for string in row:
        clue[keys[index]] = string
        index += 1
      clues.append(clue)
  return clues

# Gets a map of word -> {hint, difficulty}
# TODO: set difficulty
def get_clue_map(clues, max_difficulty = 6, num_clues = 50):
  print("Creating clue set")
  clue_map= {}
  for clue in clues:
    try:
      diff = int(clue["difficulty"])
      q = clue["question"]
      new_clue = {"difficulty": diff, "hint": q}
    except:
      print("clue could not be parsed")
      continue
    # validate the question
    question = clue["question"]
    question.lower()
    if question == "":
      print("empty question.")
      continue
    if "across" in question or "down" in question or "Across" in question or "Down" in question:
      print("question contains 'across' or 'down' reference.")

    # validate the answer
    if len(clue["answer"]) < 2 :
      print("invalid one char answer: " + clue["answer"])
      continue
    if new_clue["difficulty"] <= max_difficulty :
      clue_map[clue["answer"]] = new_clue
    #  num_clues -= 1
  #    if num_clues <= 0:
  #      break
  return clue_map

# given a clue map, creates a list of all the words that appear in it.
def create_dictionary(clue_map):
  set = []
  for word, clue in clue_map.items():
    set.append(word)
  return set

# place a word on a board (i.e, write it down)
def place_word(word, board, pos_x, pos_y, dir):
  if dir == "across":
    for x in range(len(word)):
      board[pos_x + x][pos_y] = word[x]
  # place down
  else:
    for y in range(len(word)):
      board[pos_x][pos_y + y] = word[y]
  return board

## Create board:
# This tries to place words on the board randomly for num_iterations iterations.
def create_board(board, num_iterations, dictionary, clue_map):
  new_set = []
  across_set = []
  down_set = []
  word_set = {}
  count = 0
  for i in range(num_iterations):
    word = random.choice(dictionary)
    if len(word) >= MAX or word in word_set: continue
    across = random.randint(0,1)
    if across == 1:
      pos_x = random.randint(1, MAX - len(word))
      pos_y = random.randint(1, MAX - 1)
      if fits_across(board, pos_x, pos_y,  word):
        print("placing word: " + word + " at (" + str(pos_x) + ", " + str(pos_y) + ")")
        board = place_word(word, board, pos_x, pos_y, "across")
        print_board(board)
        word_data = {"word": word, "index": -1, "x": pos_x, "y": pos_y,
                          "hint": clue_map[word]["hint"], "dir": "across"}
        word_set[word] = word_data
    else:
      pos_x = random.randint(1, MAX - 1)
      pos_y = random.randint(1, MAX - len(word))
      if fits_down(board, pos_x, pos_y, word):
        print("placing word: " + word + " at (" + str(pos_x) + ", " + str(pos_y) + ")")
        board = place_word(word, board, pos_x, pos_y, "down")
        print_board(board)
        word_data = {"word": word, "index": -1, "x": pos_x, "y": pos_y,
                        "hint": clue_map[word]["hint"], "dir": "down"}
        word_set[word] = word_data

  # set the correct indexes: map each word to a [x][y] map, and then sort.
  index_map = [[None for _ in range(0, MAX+1)] for _ in range(0, MAX+1)];
  for word, data in word_set.items():
    pos_x = data["x"]
    pos_y = data["y"]
    if index_map[pos_x][pos_y] == None:
        index_map[pos_x][pos_y] = [word]
    else:
      (index_map[pos_x][pos_y]).append(word);

  count = 0;
  for x in range(1, MAX):
    for y in range(1, MAX):
      if index_map[x][y] != None:
        for word in index_map[x][y]:
          word_set[word]["index"] = count
        count += 1

  down_set = []
  across_set = []
  for word, data in word_set.items():
    if data["index"] == -1:
      print("abort!! what?")
    if data["dir"] == "down":
      down_set.append(data)
    else:
      across_set.append(data)

  return board, down_set, across_set


###
# How to represent the board?
#
# data structure containing {word, hint, position (of first letter), direction (down or across)}
# board data structure containing 2d array, each value can be letter and/or number
# board gets filled by going through the list of words
#
# can have 'solved board', hidden, and 'current board', empty.





# init board
# board goes from 1 to max
def init_board(board):
  for x in range(0, max + 1):
    for y in range(0, max + 1):
      board[x][y] = EMPTY

def valid_position(board, x, y, dir):
  if x < 1 or x > MAX or y < 1 or y > MAX:
    print("pos out of bounds")
    return False

  if dir == "across":
    if(board[x][y-1] != EMPTY and board[x][y] == EMPTY):
      return False
    if(board[x][y+1] != EMPTY and board[x][y] == EMPTY):
      return False
  if dir == "down":
    if(board[x-1][y] != EMPTY and board[x][y] == EMPTY):
      return False
    if(board[x+1][y] != EMPTY and board[x][y] == EMPTY):
      return False
  return True

def fits_across(board, x, y, word):
  fits = False
  for pos in range(len(word)):
    if (pos == 0 and board[x-1][y] != EMPTY ) or (pos == (len(word) - 1) and board[x + len(word)][y] != EMPTY):
      return False
    if (valid_position(board, x+pos, y, "across")) and (board[x+pos][y] == word[pos] or board[x+pos][y] == EMPTY):
      fits = True
    else :
      return False
  return fits

def fits_down(board, x, y, word):
  fits = False
  for pos in range(len(word)):
    if (pos == 0 and board[x][y-1] != EMPTY ) or (pos == (len(word) - 1) and board[x][y + len(word)] != EMPTY):
      return False
    if (valid_position(board, x, y+pos, "down")) and (board[x][y+pos] == word[pos] or board[x][y+pos] == EMPTY):
      fits = True
    else:
      return False
  return fits

def print_board(board):
  for y in range(len(board[0])):
    for x in range(len(board)):
      print (board[x][y] + " ", end=" ")
    print ("\n")



def fill_board_data(board, down, across):
  new_board = copy.deepcopy(board)
  for y in range(len(board[0])):
    for x in range(len(board)):
      new_board[x][y] = {
        "letter": board[x][y],
        "guess": "",
        "empty": board[x][y] == EMPTY,
        "index": ""}
  for word in down:
    new_board[word["x"]][word["y"]]["index"] = str(word["index"])
  for word in across:
    new_board[word["x"]][word["y"]]["index"] = str(word["index"])
  return new_board

# Creates a random puzzle of specified difficulty.
def create_puzzle(clues, difficulty):
  board = [[EMPTY for x in range(0, MAX+2)] for y in range(0, MAX+2)]
  new_set = []
  num_iterations = 1000000
  random.shuffle(clues)
  clue_map = get_clue_map(clues, difficulty, 100000)
  dictionary = create_dictionary(clue_map)
  board_view, down, across = create_board(board, num_iterations, dictionary, clue_map)
  new_board = fill_board_data(board_view, down, across)
  return board_view, new_board, down, across

def main():
  games_per_difficulty = 5;
  # load clues from CSV file
  clues = load_clues()
  for difficulty in range(1,6):
    for game_num in range(1, games_per_difficulty):
      board_view, board, down, across = create_puzzle(clues, difficulty)
      print_board(board_view)
      db.child("puzzles").child(difficulty).child("game-"+str(game_num)).set({"board": board, "down": down, "across": across})


# new idea. rank words from longest to shortest.
# randomly place word in grid for x iterations, and check if it fits.
# iterate x times.
#
# How does it fit? It can't modify any existing word.
def old_main():
  board = [[EMPTY for x in range(0, MAX+2)] for y in range(0, MAX+2)]
  n = 0
  new_set = []
  num_iterations = 1000000
  clues = load_clues()
  random.shuffle(clues)
  clue_map = get_clue_map(clues, 1, 100000)
  dictionary = create_dictionary(clue_map)
  board, down, across = create_board(board, num_iterations, dictionary, clue_map)
  # create a new board object to store letter and guess
  new_board = copy.deepcopy(board)
  for y in range(len(board[0])):
    for x in range(len(board)):
      new_board[x][y] = {
        "letter": board[x][y],
        "guess": "",
        "empty": board[x][y] == EMPTY,
        "index": ""}
  for word in down:
    new_board[word["x"]][word["y"]]["index"] = str(word["index"])
  for word in across:
    new_board[word["x"]][word["y"]]["index"] = str(word["index"])

  # db.child("boards").child("game1").set({"board": new_board, "down": down, "across": across})


  #print(board)
  #print(len(words))
  print ("")
  empty_board = copy.deepcopy(board)
  for y in range(len(board[0])):
    for x in range(len(board)):
      if board[x][y] == EMPTY : board[x][y] = '#'
      if (empty_board[x][y] != EMPTY) :
        empty_board[x][y] = "[ ]"


  for word in down:
    empty_board[word["x"]][word["y"]] = str(word["index"])
    for x in range(3 - len(str(word["index"]))):
      empty_board[word["x"]][word["y"]] += " "
  for word in across:
    empty_board[word["x"]][word["y"]] = str(word["index"])
    for x in range(3 - len(str(word["index"]))):
      empty_board[word["x"]][word["y"]] += " "


  print_board(board)
  print_board(empty_board)
  print ("-- Down. --")
  for word in down:
    #print (str(word["index"]) + ". " + word["word"] + " , hint: " + clue_map[word["word"]]["hint"])
    print (str(word["index"]) + ". " + clue_map[word["word"]]["hint"])
  print ("-- Across. --")
  for word in across:
    #print (str(word["index"]) + ". " + word["word"] + " , hint: " + clue_map[word["word"]]["hint"])
    print (str(word["index"]) + ". " + clue_map[word["word"]]["hint"])


main()

# TODO:
#
# figure out game logic
#  - have server create board, assign an id, and store it.
#  - client goes to a page with the board id.
#  - use firebase to sync the game state across players
#  - have color per player
#
# index across/down set of words better.
# (x,y) maps to {down: word, across: word}, use that to map indexes.
#
# make better data structures
