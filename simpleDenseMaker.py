import csv
import random
import copy
import sys
from pyrebase import pyrebase
import pygtrie
import string
import pickle

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

EMPTY_CHAR = "•"

# 8 x 8 empty board template
M_TEMPLATE = [
  "        "
  "#       ",
  " #    ##",
  "  #     ",
  "   #    ",
  "        ",
  "###  #  ",
  "      # "]

# 5 x 5 templates
TEMPLATE_SMALL = [
"#   #",
"     ",
"     ",
"     ",
"#   #"]

TEMPLATE_SMALL_2 = [
"  #  ",
"     ",
"#   #",
"     ",
"  #  "]

TEMPLATE_MEDIUM = [
  "        ",
  "   #    ",
  "#   ####",
  "        ",
  "        ",
  "####   #",
  "    #   ",
  "        "]

# 15 x 15 empty board
TEMPLATE_LARGE = [
  "   #      #    ",
  "   #      #    ",
  "      #   #    ",
  "    #   ##     ",
  "##            #",
  "#     ##   ####",
  "     #    #    ",
  "               ",
  "    #    #     ",
  "####   ##     #",
  "#            ##",
  "     ##   #    ",
  "    #          ",
  "    #      #   ",
  "    #      #   "]

TEMPLATE_VIRUS = [
  "   #TONSIL#V  M",
  "   #      #I  A",
  "      #   #R  S",
  "    #   ## U  K",
  "##         S  #",
  "#     ##   ####",
  "     #    #    ",
  "EPIDEMIOLOGISTS",
  "    #    #     ",
  "####   ##     #",
  "#            ##",
  "WUHAN##   #   S",
  "    #         O",
  "    #      #  A",
  "    #UNWELL#  P"]

TEMPLATE_MUSIC = [
"#######        #",
"P      #####    ",
"L##   #MUSIC#   ",
"A##   #     #   ",
"Y##   #     #   ",
"L#   ##    ##   ",
"I   ###   ###   ",
"S   ###   ###   ",
"T    ##    ##   ",
"####         ####"]

TEMPLATE_LARGE = [
  "       #    #       ",
  "       #    #       ",
  "##   #       #   ###",
  "    #    #     #    ",
  "        #       #   ",
  "      #       #     ",
  "####       ##       ",
  "    #        #      ",
  "     #   ##    #    ",
  "       ##       ####",
  "####       ##       ",
  "    #    ##   #     ",
  "      #        #    ",
  "       ##       ####",
  "     #       #      ",
  "   #       #        ",
  "    #     #    #    ",
  "###   #       #   ##",
  "       #    #       ",
  "       #    #       ",
  ]

TEMPLATE = TEMPLATE_MUSIC

def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

def getAllPartialWords(word):
  if len(word) == 1:
    return [word, ' ']

  partial_words = getAllPartialWords(word[1:len(word)])
  new_words = []
  for partial_word in partial_words:
    new_words.append(' ' + partial_word)
    new_words.append(word[0:1] + partial_word)
  return new_words

# Creates a mapping of partial words to words. For example, for the word 'wow',
# we get the entries wow -> wow, *ow -> wow, **w -> wow, w*w -> wow, **w -> wow
# and *** -> wow.
def createPartialWordMap(clue_dict):
  print("Loading partial word mapping")
  foundSaved = True
  try :
    partialWordMap = load_obj('partial_word_map')
  except:
    foundSaved = False
  # print("mapping " + partial_word + " to " + word)
  print("found saved? " + str(foundSaved))
  # Save this to file if we just generated it.
  if not foundSaved:
    for word in clue_dict.keys():
      for partial_word in getAllPartialWords(word):
        if partial_word not in partialWordMap:
          partialWordMap[partial_word] = word
    "saving partial word map"
    save_obj(partialWordMap, 'partial_word_map')
  return partialWordMap


def wordLength(board, x, y, dir):
  x_add = 0
  y_add = 1
  if dir == 'across':
    x_add = 1
    y_add = 0

  length = 0
  while (board[x][y]['char'] != EMPTY):
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



def fillDenseBoard(partial_word_map, size):
  if (size == 'small') :
    TEMPLATE = TEMPLATE_SMALL
  elif (size == 'medium'):
    TEMPLATE = TEMPLATE_MEDIUM
  elif (size == 'large'):
    TEMPLATE = TEMPLATE_LARGE
  else:
    print("invalid template size")
    return
  width = len(TEMPLATE[0])
  height = len(TEMPLATE)
  #size = len(TEMPLATE)
  print("width:" + str(width))
  print("height:" + str(height))

  # Create a board, 2 cells bigger than the template
  board = [[{"char": EMPTY} for x in range(0, height+2)] for y in range(0, width+2)]

  print("Preprocessing.")
  # 1. preprocessing
  # 1.1 set the char of each cell to the template, with 1 cell of padding
  for x in range(1, width + 1):
    for y in range(1, height + 1):
      print("x is" + str(x) + "y is " + str(y))
      board[x][y]["char"] = TEMPLATE[y-1][x-1]
      if (board[x][y]["char"] != " " and board[x][y]["char"] != EMPTY):
        board[x][y]["fixed_char"] = True
      else:
        board[x][y]["fixed_char"] = False


  # find all indexes (first empty cell after a non-empty cell in the
  # x or y direction)
  index = 0
  for y in range(1, height + 1):
    for x in range(1, width + 1):
      if board[x][y]["char"] != EMPTY and not board[x][y]["fixed_char"]:
        is_index = False
        # Is across index if prev cell is # and word is > 2
        if board[x-1][y]['char'] == EMPTY:
          word_length = wordLength(board, x, y, 'across')
          if word_length > 2:
            # this should be an across index
            is_index = True
            for i in range(word_length):
              board[x+i][y]["across_index"] = index
              # set the word word length for across
              board[x+i][y]["across_word_length"] = word_length

        # Is down index if prev cell is # and word is > 2
        if board[x][y-1]['char'] == EMPTY:
          word_length = wordLength(board, x, y, 'down')
          if word_length > 2:
            is_index = True
            for i in range(word_length):
              board[x][y+i]["down_index"] = index
              # set the word word length for down
              board[x][y+i]["down_word_length"] = word_length

        if is_index:
          board[x][y]["index"] = index
          index += 1

  letters = list(string.ascii_uppercase)

  needs_fitted = []
  for x in range(1, width + 1):
    for y in range(1, height + 1):
      if board[x][y]['char'] == EMPTY or board[x][y]["fixed_char"]:
        continue
      needs_fitted.append([x, y])

  iteration = 0
  total_iterations = 0

  last_coord = None
  while (len(needs_fitted) > 0):
    total_iterations += 1
    iteration += 1
    coord = needs_fitted.pop(0)
    x = coord[0]
    y = coord[1]
    fits = False
    random.shuffle(letters)
    alph_index = 0
    while (not fits and alph_index < 26):
      letter = letters[alph_index]
      alph_index+=1
      board[x][y]["char"] = letter
      down_word = ""
      if ("down_index" in board[x][y]):
        down_word, start_y = getDownWord(x, y, board)
      if down_word != "":
        if down_word not in partial_word_map:
          # this letter doens't fit - try a different one.
          board[x][y]["char"] = " "
          continue
      across_word = ""
      if ("across_index" in board[x][y]):
        across_word, start_x = getAcrossWord(x, y, board)
      if across_word != "":
        if across_word not in partial_word_map:
          # this letter doens't fit - try a different one.
          board[x][y]["char"] = " "
          continue
      if (down_word == "" and across_word == ""):
        print("this shouldn't happen")
      # the letter fits, continue.
      fits = True

    # try to replace a letter in the across direction.
    if not fits:
      if coord not in needs_fitted:
        needs_fitted.append(coord)

      if len(needs_fitted) > 50 or iteration < 2000:
        #  this removes a random letter from both the across and down words.
        if ("across_index" in board[x][y]):
          word, start_x = getAcrossWord(x, y, board)
          if (len(word)) > 2:
            new_x = getRandomNumberExcept(start_x, start_x + len(word) - 1, x)
            if ([new_x, y] not in needs_fitted and not board[new_x][y]["fixed_char"]):
              board[new_x][y]['char'] = " "
              needs_fitted.append([new_x, y])
        if ("down_index" in board[x][y]):
          word, start_y = getDownWord(x, y, board)
          if (len(word)) > 2:
            new_y = getRandomNumberExcept(start_y, start_y + len(word) - 1, y)
            if ([x, new_y] not in needs_fitted and not board[x][new_y]["fixed_char"]):
              board[x][new_y]['char'] = " "
              needs_fitted.append([x, new_y])

      # this removes the whole word and places it in the queue in random order
      else:
        iteration = 0
        coords_to_add = []
        if ("across_index" in board[x][y]):
          word, start_x = getAcrossWord(x, y, board)
          if (len(word)) > 2:
            for new_x in range(start_x, start_x + len(word)):
              if not board[new_x][y]["fixed_char"]:
                board[new_x][y]['char'] = " "
                coords_to_add.append([new_x, y])
        if ("down_index" in board[x][y]):
          word, start_y = getDownWord(x, y, board)
          if (len(word)) > 2:
            for new_y in range(start_y, start_y + len(word)):
              if not board[x][new_y]["fixed_char"]:
                board[x][new_y]['char'] = " "
                coords_to_add.append([x, new_y])
        random.shuffle(coords_to_add)
        for new_coord in coords_to_add:
          if new_coord not in needs_fitted:
            needs_fitted.append(new_coord)

  print_board(board)
  print("after " + str(total_iterations) + " iterations")
  return board

# bounds are inclusive
def getRandomNumberExcept(min, max, e):
  if max - min == 0:
    return 0
  r = random.randint(min, max)
  while (r == e):
    r = random.randint(min, max)
  return r

def getWordIndex(x, y, board, dir):
  if dir == 'down':
    # go up until you find the index.
    y_index = y
    word = ""
    while (board[x][y_index]['char'] != EMPTY):
      y_index -= 1
    return x, y_index

  else:
    x_index = x
    word = ""
    while (board[x_index][y]['char'] != EMPTY):
      x_index -= 1
    return x_index, y

# find the down word that the position is part of
def getDownWord(x, y, board):
  start_y = y
  # go up until you find the index.
  curr_y = y
  word = ""
  while (board[x][curr_y]['char'] != EMPTY):
    curr_y -= 1
  curr_y += 1
  start_y = curr_y
  # move forward to the beginning of the word.
  while (board[x][curr_y]['char'] != EMPTY):
    word = word + board[x][curr_y]['char']
    curr_y += 1
  if (len(word) <= 1):
    return ""
  return word, start_y

def getAcrossWord(x, y, board):
  start_x = x
  # go back until you find the index.
  curr_x = x
  word = ""
  while (board[curr_x][y]['char'] != EMPTY):
    curr_x -= 1
  curr_x += 1
  start_x = curr_x
  # move forward to the beginning of the word.
  while (board[curr_x][y]['char'] != EMPTY):
    word = word + board[curr_x][y]['char']
    curr_x += 1
  if (len(word) <= 1):
    return ""
  return word, start_x

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
# TODO preprocess clue map?
# difficulty is 1 hardest, 6 easiest
def get_clue_dict(clues, max_difficulty = 6, num_clues = 1000000):
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


def print_board(board, with_index = False):
  for y in range(len(board[0])):
    for x in range(len(board)):
      if (with_index and "index" in board[x][y]):
        print(str(board[x][y]['index']) + " ", end=" ")
      else:
        if (board[x][y]['char'] == "#"):
          print (EMPTY_CHAR + " ", end=" ")
        else:
          print (board[x][y]['char'] + " ", end=" ")
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

# Creates a random puzzle of specified difficulty.
# def create_puzzle(clues, clue_dict):
#   board = [[EMPTY for x in range(0, MAX+2)] for y in range(0, MAX+2)]
#   new_set = []
#   num_iterations = 1000000
#   random.shuffle(clues)
#   dictionary = create_dictionary(clue_dict)
#   board_view, down, across = create_board(board, num_iterations, dictionary, clue_dict)
#   board = fill_board_data(board_view, down, across)
#   puzzle_score = calculate_puzzle_score(board_view)
#   print ('puzzle score: ' + str(puzzle_score))
#   return board_view, board, down, across, puzzle_score

def main():
  clue_dict = load_obj('clues_by_difficulty')
  # Preprocess words into dictionary by word length.
  partial_word_map = createPartialWordMap(clue_dict)

  for i in range(0, 100):
    board = fillDenseBoard(partial_word_map, 'small')
    # print_board(board)
# def main():
#   games_per_difficulty = 25
#   # load clues from CSV file
#   clues = load_clues()
#   clue_dict = []
#   for difficulty in range(1, 7):
#     clue_dict.append(get_clue_dict(clues, difficulty))
#   print("saving ")
#   save_obj(clue_dict, 'clues_by_difficulty')
#   # fillDenseBoard(clue_dict)

main()
