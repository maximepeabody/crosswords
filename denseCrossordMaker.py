import csv
import random
import copy
import sys
from pyrebase import pyrebase
import pygtrie

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
OPEN = " "

# 8 x 8 empty board template
TEMPLATE = [
  ["        "],
  ["   #    "],
  ["     ###"],
  ["    #   "],
  ["   #    "],
  ["###    "],
  ["    #   "],
  ["        "]]


# 15 x 15 empty board
DENSE_BOARD_TEMPLATE = [
  ["     ##        "],
  ["#    #     #   "],
  [" #    #    #   "],
  ["  #    ########"],
  ["   #   #   #   "],
  ["    ####       "],
  ["      #   #    "],
  ["##     ######  "],
  ["   #    #    # "],
  ["   #    #    # "],
  ["   #    #    # "],
  ["   #    ##   # "],
  ["#      #      #"],
  ["   ####    ##  "],
  ["     #    #    "]]


def getAllPartialWords(word):
  if len(word) == 1:
    return [word, '*']

  partial_words = getAllPartialWords(word[1:len(word)])
  new_words = []
  for partial_word in partial_words:
    new_words.append('*' + partial_word)
    new_words.append(word[0:1] + partial_word)
  return new_words

# Creates a mapping of partial words to words. For example, for the word 'wow',
# we get the entries wow -> wow, *ow -> wow, **w -> wow, w*w -> wow, **w -> wow
# and *** -> wow.
def createWordTemplateMap(clue_dict):
  partialWordMap = {}
  for word in clue_dict.keys():
    for partial_word in getAllPartialWords(word):
      if partial_word not in partialWordMap:
        partialWordMap[partial_word] = word


def wordLength(board, x, y, dir):
  x_add = dir == "across" ? 1 : 0
  y_add = dird == "down" ? 1 : 0
  length = 0
  while (board[x][y] != EMPTY):
    x += x_add
    y += y_add
    length += 1
  return length

def validPosition(board, x, y, dir):
  if x < 1 or x > MAX or y < 1 or y > MAX:
    print("pos out of bounds")
    return False

  if dir == "across":
    if(board[x][y-1]['char'] != EMPTY and board[x][y]['char'] == EMPTY):
      return False
    if(board[x][y+1]['char'] != EMPTY and board[x][y]['char'] == EMPTY):
      return False
  if dir == "down":
    if(board[x-1][y]['char'] != EMPTY and board[x][y]['char'] == EMPTY):
      return False
    if(board[x+1][y]['char'] != EMPTY and board[x][y]['char'] == EMPTY):
      return False
  return True

# return coords of overlap
def fitsAcross(board, x, y, word):
  fits = False
  adjacent_coords = []
  for pos in range(len(word)):
    cell_letter = board[x+pos][y]['char']

    # return false if the word runs into an empty cell
    if cell_letter == EMPTY:
      return False

    # return false if the word runs into a char that doesn't fit with the word
    if cell_letter != " " and cell_letter != word[pos]:
      return False
    else if cell_letter != " " and cell_letter == word[pos]:
      return True []
    # otherwise cell_letter is equal to " ".

    # find any adjacent coords that you need to check if there is overlap.
    # this shouldn't happen if the cell is already filled.
    up_cell_letter = board[x+pos][y-1]['char']
    if up_cell_letter != " " and up_cell_letter != EMPTY:
      adjacent_coords.add({'x': x+pos, 'y': y - 1})

    down_cell_letter = board[x+pos][y+1]['char']
    if down_cell_letter != " " and down_cell_letter != EMPTY:
      adjacent_coords.add({'x': x+pos, 'y': y + 1})

  return True, adjacent_coords


def fitsDown(board, x, y, word):
  fits = False
  adjacent_coords = []
  for pos in range(len(word)):
    cell_letter = board[x][y+pos]['char']

    # return false if the word runs into an empty cell
    if cell_letter == EMPTY:
      return False

    # return false if the word runs into a char that doesn't fit with the word
    if cell_letter != " " and cell_letter != word[pos]:
      return False
    else if cell_letter != " " and cell_letter == word[pos]:
      return True []
    # otherwise cell_letter is equal to " ".

    # find any adjacent coords that you need to check if there is overlap.
    # this shouldn't happen if the cell is already filled.
    left_cell_letter = board[x-1][y+pos]['char']
    if left_cell_letter != " " and left_cell_letter != EMPTY:
      adjacent_coords.add({'x': x-1, 'y': y + pos})

    right_cell_letter = board[x+1][y+pos]['char']
    if right_cell_letter != " " and right_cell_letter != EMPTY:
      adjacent_coords.add({'x': x+1, 'y': y + pos})

  return True, adjacent_coords


def fillDenseBoard(clue_dict):
  # Preprocess words into dictionary by word length.
  len_dict = {}
  for word in clue_dict.keys():
    if if len(word) in len_dict:
      len_dict[len(word)].append(word)
    else:
      len_dict[len(word)] = [word]

  across_filled = [[0 for x in range(0, MAX+2)] for y in range(0, MAX+2)]
  down_filled = [[0 for x in range(0, MAX+2)] for y in range(0, MAX+2)]

  # Create a board, 2 cells bigger than the template
  board = [[{"char": EMPTY} for x in range(0, MAX+2)] for y in range(0, MAX+2)]

  # 1. preprocessing
  # 1.1 set the char of each cell to the template, with 1 cell of padding
  for x in range(1, MAX +1):
    for y in range(1, MAX + 1):
      board[x][y]["char"] = DENSE_BOARD_TEMPLATE[y][x]

  # find all indexes (first empty cell after a non-empty cell in the
  # x or y direction)
  index = 0
  for y in range(1, MAX +1):
    for x in range(1, MAX + 1):
      if board[x][y] != EMPTY:
        is_index = false
        if board[x-1][y] == EMPTY:
          word_length = wordLength(board, x, y, 'across')
          if word_length > 2:
            # this should be an across index
            is_index = True
            board[x][y]["across_index"] = index
            # set the word word length for across
            board[x][y]["across_word_length"] = word_length
        if board[x][y-1] == EMPTY:
          word_length = wordLength(board, x, y, 'down')
          if word_length > 2:
            is_index = True
            board[x][y]["down_index"] = index
            # set the word word length for down
            board[x][y]["down_word_length"] = word_length

        if is_index:
          board[x][y]["index"] = index
          index += 1

  # 2. Now we have a board with the indexes, and the length of word we need.
  #    Let's fill it with words.
  across_placed = {}
  down_placed = {}
  dictionary = clue_dict.keys()

  for y in range(1, MAX +1):
    for x in range(1, MAX + 1):
      # Try to fit a word.
      index = board[x][y]["index"]
      # if !index then the current cell is not an index, and we should not try
      # to place a word here.
      if !index:
        continue

      # try to place a word down if it's a down index
      if board[x][y]["down_index"] and !down_placed[index]:
        word_length = board[x][y]['down_word_length']
        placed = False
        while (!placed):
          # find word of correct length
          word = random.choice(len_dict[word_length])
          fits, overlap_coords = fitsDown(board, x, y, word)
          if !fits:
            continue
          if overlap_coords == None:
            placed = True
            placeWord(board, x, y, word)
          # for each overlapped coordinate, try to place a word.
        else:


      # try to place a word across if it's an across index
      if board[x][y]["across_index"] and !across_placed[index]:


# Tries to place a word on a board, given a current board state, a list of
# words, and an index. Returns the new board state, or false if error.
#
# board: the board state prior to placing this word.
# len_dic: a mapping of word->lengths to words.
# x: the x pos of the word to try to place
# y: the y pos of ''
# a hash set of all {x, y} pairs that have already been placed.
tryToPlaceWord(board, len_dict, x, y, down_placed, across_placed, max_iter = 1000 ):
  # try to place a word down if it's a down index
  new_board = copy.deepcopy(board)
  if board[x][y]["down_index"] and !down_placed[index]:
    word_length = board[x][y]['down_word_length']
    placed = False
    iter = 0
    while (!placed and iter < max_iter):
      iter += 1
      # find word of correct length
      word = random.choice(len_dict[word_length])
      fits, overlap_coords = fitsDown(board, x, y, word)
      # if it doesn't fit, continue the while loop to try a new word.
      if !fits:
        continue
      # if there are no overlapping letters, then we're set! Place the word
      # in the new board and return it.
      if overlap_coords == None:
        placed = True
        placeWord(new_board, x, y, word)
        return True, new_board
      # for each overlapped coordinate, try to place a word.
      else:
        for coord in overlap_coords:
          tryToPlaceWord


  # try to place a word across if it's an across index
  if board[x][y]["across_index"] and !across_placed[index]:

# Load the clues
#
# Returns: a list of clue objects, containing the key-value pairs from the cvs file.
def load_clues():
  print("Loading clues from csv file")
  clues = []
  with open('nyt-crossword-master/clues.csv', 'r') as csvfile:
    clue_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in clue_reader:
      inde# = 0
      clue = {}
      for string in row:
        clue[keys[inde#]] = string
        inde# += 1
      clues.append(clue)
  return clues


# Gets a map of word -> {hint, difficulty}
# TODO preprocess clue map?
# difficulty is 1 hardest, 6 easiest
def get_clue_dict(clues, max_difficulty = 6, num_clues = 50):
  print("Creating clue set")
  clue_dict = pygtrie.CharTrie();
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
      continue
    if "across" in question or "down" in question or \
        "Across" in question or "Down" in question or \
        "this puzzle" in question:
      continue

    # validate the answer
    if len(clue["answer"]) < 2 :
      print("invalid one char answer: " + clue["answer"])
      continue
    if new_clue["difficulty"] >= max_difficulty :
      clue_dict[clue["answer"]] = new_clue
    #  num_clues -= 1
  #    if num_clues <= 0:
  #      break
  return clue_dict

# given a clue map, creates a list of all the words that appear in it.
def create_dictionary(clue_dict):
  set = []
  for word, clue in clue_dict.items():
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
###
# TODO:
# - remove any words that don't cross.
# - make a sparseness score
def create_board(board, num_iterations, dictionary, clue_dict):
  new_set = []
  # maps word to word data
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
                          "hint": clue_dict[word]["hint"], "dir": "across"}
        word_set[word] = word_data
    else:
      pos_x = random.randint(1, MAX - 1)
      pos_y = random.randint(1, MAX - len(word))
      if fits_down(board, pos_x, pos_y, word):
        print("placing word: " + word + " at (" + str(pos_x) + ", " + str(pos_y) + ")")
        board = place_word(word, board, pos_x, pos_y, "down")
        print_board(board)
        word_data = {"word": word, "index": -1, "x": pos_x, "y": pos_y,
                        "hint": clue_dict[word]["hint"], "dir": "down"}
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
  for y in range(1, MAX):
    for x in range(1, MAX):
      if index_map[x][y] != None:
        for word in index_map[x][y]:
          word_set[word]["index"] = str(count)
        count += 1

  # maps words index to word data
  down = []
  across = []
  # down = {}
  # across = {}
  for word, data in word_set.items():
    if data["dir"] == "down":
      down.append(data)
      # down[data["index"]] = data
    else:
      across.append(data)
    #  across[data["index"]] = data

  return board, down, across


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
        "index": "",
        "across_index": "",
        "down_index": ""
        }

  for word in down:
    # set the index to the cell corresponding to the first letter of the word
    new_board[word["x"]][word["y"]]["index"] = str(word["index"])
    # for each cell that the word is in, set a pointer to the down array
    char_count = 0;
    for char in word["word"]:
      new_board[word["x"]][word["y"] + char_count]["down_index"] = word["index"]
      char_count += 1

  for word in across:
    new_board[word["x"]][word["y"]]["index"] = str(word["index"])
    # for each cell that the word is in, set a pointer to the across data
    char_count = 0
    for char in word["word"]:
      new_board[word["x"] + char_count][word["y"]]["across_index"] = word["index"]
      char_count += 1
  return new_board

def calculate_puzzle_score(board_view):
  num_letters = 0
  for y in range(len(board_view[0])):
    for x in range(len(board_view)):
      if (board_view[x][y] != "#"):
        num_letters += 1
  return num_letters

# Creates a random puzzle of specified difficulty.
def create_puzzle(clues, clue_dict):
  board = [[EMPTY for x in range(0, MAX+2)] for y in range(0, MAX+2)]
  new_set = []
  num_iterations = 1000000
  random.shuffle(clues)
  dictionary = create_dictionary(clue_dict)
  board_view, down, across = create_board(board, num_iterations, dictionary, clue_dict)
  board = fill_board_data(board_view, down, across)
  puzzle_score = calculate_puzzle_score(board_view)
  print ('puzzle score: ' + str(puzzle_score))
  return board_view, board, down, across, puzzle_score

def main():
  games_per_difficulty = 25
  # load clues from CSV file
  clues = load_clues()

  # array containing objects of {'board': board, 'puzzle_score': puzzle_score}
  boards = [None for x in range(0, games_per_difficulty+1)]

  # create a bunch of games for each difficulty
  for difficulty in range(1,6):
    clue_dict = get_clue_dict(clues, difficulty, 100000)
    for game_num in range(1, games_per_difficulty):
      board_view, board, down, across, puzzle_score = create_puzzle(clues, clue_dict)
      if boards[difficulty]:
        boards[difficulty].append({'board': board,
         'puzzle_score': puzzle_score,
         'down': down,
         'across': across});
      else:
        boards[difficulty] = [{'board': board,
         'puzzle_score': puzzle_score,
         'down': down,
         'across': across}]

  # save the top n games of each difficulty
  top_games = 10
  for difficulty in range(1,6):
    boards[difficulty].sort(key=lambda x: x['puzzle_score'], reverse=True)
    for game_num in range(0, top_games-1):
      db.child("puzzles").child(difficulty).child("game-"+str(game_num)).set(boards[difficulty][game_num])


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
  clue_dict = get_clue_dict(clues, 1, 100000)
  dictionary = create_dictionary(clue_dict)
  board, down, across = create_board(board, num_iterations, dictionary, clue_dict)
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
    #print (str(word["index"]) + ". " + word["word"] + " , hint: " + clue_dict[word["word"]]["hint"])
    print (str(word["index"]) + ". " + clue_dict[word["word"]]["hint"])
  print ("-- Across. --")
  for word in across:
    #print (str(word["index"]) + ". " + word["word"] + " , hint: " + clue_dict[word["word"]]["hint"])
    print (str(word["index"]) + ". " + clue_dict[word["word"]]["hint"])


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
