import numpy as np
import json
from PIL import Image
import os


def estGridSize(num_cards: int):
    """ Estimate the size of the game grid based on the number of cards available.
    This is the square root of the number of cards, if this is an integer, else
    one row and num_cards columns.

    :param num_cards: The number of square tiles to be arranged
    :return: list of two integers [number of rows, number of columns]
    """
    root = int(np.sqrt(num_cards))
    if root * root == num_cards:
        return [root, root]
    return [1, num_cards]


def findDistinctSymbols(card_list):
    """ Find the unique symbols from the list of cards given and return them as a list.

    :param card_list: list of lists of strings (symbol names by card)
    :return: list of strings (symbol names)
    """
    return np.unique(np.array(card_list))


def isRotation(grid_size, solution):
    """Determine whether solution is a complete rotation of an earlier solution by checking the
    indices of the corner cards. If any is lower than the top left card, it is a rotation.

    This implementation is specific to the algorithm in use here, i.e. all possible solutions with the
    card with index 0 in position 0 are tested before moving on to putting the card with index 1 in
    position 0, etc. Therefore any possible solution in which card 0 appears in another corner,
    must represent a rotation of a solution that has already been seen.

    :param grid_size: list of two ints. [num rows, num cols]. Must be a square (TODO, extend to rectangles)
    :param solution: a particular layout of cards.
    """
    ref_idx = solution[0][0]
    if ref_idx > solution[grid_size[1]-1][0]:
        return True
    if ref_idx > solution[-1][0]:
        return True
    if ref_idx > solution[-grid_size[1]][0]:
        return True
    return False


def rotateCard(card, orientation):
    """Return the symbols on the card, rotated by orientation steps.

    :param card: list of 4 integers representing the symbols on the card, ordered clockwise from the top
    :param orientation: integer between 0 and 3, the number of 90 degree turns to make (clockwise)
    :returns: list of integers representing the new positions of the symbols.
    """
    ns = len(card)
    return [card[(i + orientation) % ns] for i in range(ns)]


def compareCards(card, card2):
    """Return 1 if card > card2, 0 if the same, and -1 if card < card2 where the ordering
    is defined by the value of the symbols from first to last, e.g. [0, 1, 2, 3] < [1, 2, 3, 0] and
    [0, 0, 10, 7] < [0, 1, 1, 1].

    To test whether two cards are functionally the same they should both be first put into their
    'first' rotation, see firstRotation(card).

    :param card, card2: Lists of 4 integers representing the symbols on the cards to be compared.
    :returns: -1 if card < card2, 0 if the same symbols in the same order, +1 if card > card2.
    """

    for pos in range(len(card)):
        if card[pos] > card2[pos]:
            return 1
        if card[pos] < card2[pos]:
            return -1
    return 0


def firstRotation(card):
    """Return the card symbols rotated such that the first one in numerical order is in the first position.

    This is useful for checking whether two cards are the same.

    :param card: list of ints. Ordered list of the symbols on the card (which depends on rotation)
    :returns: the same list of ints, with the beginning moved to the lowest position as described
    """
    ret_rot = card[:]  # best rotation found so far
    for o in range(1, len(card)):
        test_rot = rotateCard(card, o)
        comparison = compareCards(test_rot, ret_rot)
        if comparison < 0:
            ret_rot = test_rot[:]

    return ret_rot


def excludeRotatedSolutions(grid_size, solutions):
    """Exclude any solutions which represent the entire solution being rotated.

    Since solutions are found by attempting to place cards in numerical order,
    starting from the top left corner, any solution in which the index of a card
    in one of the other corners is lower than that in the top left must have already
    been identified with that card in the top left.
    """
    pruned_solutions = []
    for sol in solutions:
        if not isRotation(grid_size, sol):
            pruned_solutions.append(sol)
    return pruned_solutions

def excludePairSolutions(cards_numerical, solutions):
    """Exclude any solutions which are identical to a previous solution
    except in the swapping of two identical cards and/or the in-place rotation of any card
    (e.g. if all symbols on a card are the same)."""
    fwd_dict = {idx: tuple(firstRotation(c)) for idx, c in enumerate(cards_numerical)}
    bwd_dict = {}
    for idx, card in fwd_dict.items():
        if bwd_dict.get(card) is not None:
            bwd_dict[card].append(idx)
        else:
            bwd_dict[card] = [idx]

    # Now bwd_dict has a list of ids for each distinct card.
    canonical_sols = []
    pruned_sols = []
    for sol in solutions:
        canonical_sol = [bwd_dict[fwd_dict[card[0]]][0] for card in sol]
        for got in canonical_sols:
            if got == canonical_sol:
                break
        else:
            # If we didn't break out of the for loop then we found a new solution
            canonical_sols.append(canonical_sol)
            pruned_sols.append(sol)

    return pruned_sols


def showSolution(grid_size, solution, image_dir, image_name_pattern):
    """Given a puzzle solution, display the images in the given positions, defined row-wise from top left of grid.

    :param grid_size: List of two ints [num rows, num cols]
    :param solution: List of tuples. Each tuple gives the index and orientation of the card in that position
    :param image_dir: Directory in which to find images of the tiles
    :param image_name_pattern: String to be formatted with the tile index to give the filename for the image
    """
    idx = 0
    out_image = None
    for _ in range(grid_size[0]):
        row = None
        for _ in range(grid_size[1]):
            path = os.path.join(image_dir, image_name_pattern.format(solution[idx][0]))
            try:
                tile = Image.open(path).resize((200, 200))
            except FileNotFoundError as e:
                print(f"Could not find the image for card {idx}, {path}")
                tile = Image.new(mode='RGB', size=(200, 200))
            tile = np.array(tile.rotate(90*solution[idx][1]))
            if row is None:
                row = tile
            else:
                row = np.hstack((row, tile))
            idx += 1
        if out_image is None:
            out_image = row
        else:
            out_image = np.vstack((out_image, row))
    out_image = Image.fromarray(out_image)
    out_image.show()


def solvePuzzle(grid_size, cards_list, symbols_list=None):
    """Given a list of tiles and the four symbols on them, and a grid size, arrange the tiles into a grid such that
    neighbouring symbols match.

    :param grid_size: List of ints [rows, columns]. What shape the solution should be.
    :param cards_list: List of lists of strings. For each card, an ordered list of the symbols that appear on that card.
    :param symbols_list: list of strings. What symbols are there in the puzzle? If none, this is inferred.
    """
    if symbols_list is None:
        symbols_list = findDistinctSymbols(cards_list)

    # Convert symbols from strings to integers for speed.
    symbols_dict = {s: i for i, s in enumerate(symbols_list)}
    cards_numerical = []
    try:
        for c in cards_list:
            if len(c) != 4:
                print(f"Non-square tiles are not supported. Card has {len(c)} symbols: {c}")
                return
            cards_numerical.append([symbols_dict[c[i]] for i in range(len(c))])
    except KeyError as ke:
        print(f"Symbol found on card is not included in list: {ke}")
        return

    solutions = placeRemainingCards(grid_size, cards_numerical, [])
    if len(solutions) > 0:
        print(f"Found {len(solutions)} solutions.")

        solutions = excludePairSolutions(cards_numerical, solutions)
        solutions = excludeRotatedSolutions(grid_size, solutions)
        print(f"Pruned to {len(solutions)} solutions, given row-wise from top left (card_idx, rotation).")

        for idx, solution in enumerate(solutions):
            print(solution)
            showSolution(grid_size, solution, "images", "tile_{0:02d}.jpg")


def neighbourSymbols(grid_size, cards_numerical, placed):
    """Determine the symbols above and to the left of the next open position.

    Given the cards that have already been placed, row-wise from left, into a grid
    of size grid_size, identify what symbols need to be matched on the top and left
    of the next card to be placed.

    :param grid_size: list of ints [num_rows, num_cols]
    :param cards_numerical: list of lists of ints. For each card, gives an ordered list of its symbols represented
    numerically
    :param placed: list of tuples. For each card already placed, gives the index and rotation of the card (row-wise
    from top left)
    :returns: (top, left) tuple of symbol indices.
    """
    num_placed = len(placed)
    top = None
    left = None

    if num_placed >= grid_size[1]:
        # There is a card above. Find its bottom symbol.
        card_and_orient = placed[num_placed - grid_size[1]]
        card_above = cards_numerical[card_and_orient[0]]
        top = card_above[(card_and_orient[1] + 2) % 4]

    if num_placed % grid_size[1] > 0:
        # There is a card to the left. Find its right symbol.
        card_and_orient = placed[num_placed - 1]
        card_left = cards_numerical[card_and_orient[0]]
        left = card_left[(card_and_orient[1] + 1) % 4]

    return top, left


def placeRemainingCards(grid_size, cards_numerical, placed):
    """Recursive function to complete the grid from the given position.

    :param grid_size: list of two integers [rows, columns]
    :param cards_numerical: list of all cards that are in the game
    :param placed: list of tuples. Card index and rotation for each already-placed card
    :returns: list of tuples. All placed card indices with their orientations
    """
    if len(placed) == grid_size[0] * grid_size[1]:
        return [placed]

    solutions = []
    # Determine which symbols need to be matched based on the grid size and number of cards placed
    top, left = neighbourSymbols(grid_size, cards_numerical, placed)

    # Loop through all the cards and orientations that can go in the next position
    used_cards = [idx for (idx, orientation) in placed]
    for idx in range(len(cards_numerical)):
        if idx not in used_cards:
            for orient in cardFits(cards_numerical[idx], top, left):
                final_positions = placeRemainingCards(grid_size, cards_numerical, [*placed, (idx, orient)])
                if len(final_positions) > 0:
                    solutions.extend(final_positions)
    return solutions


def cardFits(card, top=None, left=None):
    """Return list of orientations for which the given card fits with the given top and left symbols.
    """
    matches = []
    for o in range(4):
        if left is not None:
            if card[(o+3) % 4] != left:
                continue
        if top is not None:
            if card[o] != top:
                continue
        matches.append(o)
    return matches


if __name__ == '__main__':
    # Read the game spec
    setup_file = "./card_list.json"
    with open(setup_file) as f:
        try:
            game_spec = dict(json.load(f))
        except FileNotFoundError:
            print(f"Game specification file not found at {setup_file}")
            exit(-1)

    # Fill in any gaps
    game_name = game_spec.get('name') or 'Unnamed'
    game_maker = game_spec.get('manufacturer') or 'Unknown'
    print(f"Attempting to solve {game_name} by {game_maker}")
    grid_size = game_spec.get('grid_size') or estGridSize(len(game_spec['cards']))
    print("Game has grid size: [" + " ".join(map(str, grid_size)) + "]")
    cards = game_spec.get('cards')
    if cards is None:
        print("Description of cards not found in game specification.")
        exit(-1)

    symbols = game_spec.get('symbols') or findDistinctSymbols(cards)
    print(f"Game has {len(symbols)} symbols on {len(cards)} cards")

    # Search for solutions
    solvePuzzle(grid_size, cards, symbols)
