import re

def extraction_fn_3(note_string, context_words=10):
    """
    Expected format: "Note: X" where X is an integer.
    
    
    Extracts the note number and returns a small snippet
    with a few words before and after the matched number.
    """

    if not isinstance(note_string, str):
        return "ERROR_COULD_NOT_EXTRACT"

    # Same flexible regex as before
    pattern = re.compile(r'\bnote\s*:\s*(\d+)\b', re.IGNORECASE)
    match = pattern.search(note_string)
    if not match:
        return "ERROR_COULD_NOT_EXTRACT"

    note_value = int(match.group(1))

    # Validate note_value is within valid range (0-18)
    if not (0 <= note_value <= 18):
        return "ERROR_COULD_NOT_EXTRACT"

    # Get the span of the number itself
    num_start, num_end = match.span(1)

    # Tokenize into "words" with their positions
    word_pattern = re.compile(r'\S+')
    words = []
    index_of_number_word = None

    for i, wmatch in enumerate(word_pattern.finditer(note_string)):
        w_start, w_end = wmatch.span()
        words.append((wmatch.group(), w_start, w_end))

        # Check if this word overlaps with the number span
        if not (w_end <= num_start or w_start >= num_end):
            index_of_number_word = i

    # Fallback in weird edge cases
    if index_of_number_word is None:
        context_snippet = note_string[max(0, num_start-30): num_end+30]
        return note_value

    # Choose some words before and after
    start_idx = max(0, index_of_number_word - context_words)
    end_idx = min(len(words), index_of_number_word + context_words + 1)

    snippet_words = [w[0] for w in words[start_idx:end_idx]]
    context_snippet = " ".join(snippet_words)

    return note_value