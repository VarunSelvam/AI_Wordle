def wordle(word,guess):
    guess_list = []

    for i in range(0,len(guess)):
        if guess[i] == word[i]:
            guess_list.append(guess[i])
        elif guess[i] in word and (guess[i] != word[i]):
            guess_list.append(guess[i] + "*")
        elif guess[i] not in word:
            guess_list.append(guess[i] + "**")

    processed_letters = []
    for i in range(len(guess_list)):
        if len(guess_list[i]) == 2 and (guess.count(guess_list[i][0]) > word.count(guess_list[i][0])) and (guess_list[i] not in processed_letters):
            wrong_pos = guess_list.count(guess_list[i])
            correct_pos = guess_list.count(guess_list[i][0])
            total_letter_cnt = word.count(guess_list[i][0])
            processed_letters.append(guess_list[i])
            difference = total_letter_cnt - (correct_pos + wrong_pos)
            letter = guess_list[i]
            index_position = []
            abs_diff = abs(difference)
            # print("statement passed difference != 0")
            for location in range(0,len(guess_list)):
                if letter == guess_list[location]:
                    index_position.append(location)
                    # print("Appending Letter")
            index_position.sort(reverse=True) # Now, it'll label the letters that are last as Grey instead of the letters that are first.
            for letter_loc in range(0,abs_diff): # loc = location, iterator = letter location
                le = index_position[letter_loc] # le = letter
                guess_list[le] = guess_list[le][0] + "**"

    return guess_list