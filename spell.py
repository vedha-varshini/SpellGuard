import streamlit as st
import string
from collections import defaultdict
import metaphone

# Class Definitions (SpellGuard, Trie, etc.)
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

    def get_all_words(self):
        """Retrieve all words in the Trie."""
        return self._get_words_from_node(self.root, "")

    def _get_words_from_node(self, node, prefix):
        words = []
        if node.is_end_of_word:
            words.append(prefix)
        for char, child in node.children.items():
            words.extend(self._get_words_from_node(child, prefix + char))
        return words

class SpellGuard:
    def __init__(self):
        self.trie = Trie()
        self.word_frequencies = defaultdict(int)  # Frequency of words

    def load_dictionary(self, file_path):
        """Load words from a text file into the Trie."""
        with open(file_path, 'r') as file:
            for line in file:
                word = line.strip().lower()  # Clean up spaces and newlines
                if word:
                    self.trie.insert(word)
                    self.word_frequencies[word] += 1

    def check_word(self, word):
        """Check if the word is valid"""
        return self.trie.search(word.lower())

    def suggest_corrections(self, word, max_suggestions=5):
        """Suggest corrections using Levenshtein distance, phonetic matching, and word frequency"""
        dictionary_words = self.trie.get_all_words()
        suggestions = []

        # Calculate Levenshtein distance for each word in the dictionary
        for dict_word in dictionary_words:
            if len(suggestions) >= max_suggestions:
                break
            distance = self.levenshtein_distance(word.lower(), dict_word)
            if distance <= 2:  # Allow a max distance of 2
                confidence = 1 - (distance / len(dict_word))  # Confidence score based on distance
                suggestions.append((dict_word, confidence))

        # Add phonetic suggestions
        phonetic_suggestions = self.phonetic_suggestions(word, max_suggestions - len(suggestions))
        for suggestion in phonetic_suggestions:
            suggestions.append((suggestion, 1.0))  # Add with high confidence

        # Rank suggestions by confidence score (word frequency + Levenshtein distance)
        suggestions.sort(key=lambda x: (x[1], self.word_frequencies[x[0].lower()]), reverse=True)

        # Return only the words, not the confidence scores
        return [suggestion[0] for suggestion in suggestions]

    def levenshtein_distance(self, word1, word2):
        """Calculate Levenshtein distance between two words"""
        len_word1 = len(word1)
        len_word2 = len(word2)

        dp = [[0] * (len_word2 + 1) for _ in range(len_word1 + 1)]

        for i in range(len_word1 + 1):
            dp[i][0] = i
        for j in range(len_word2 + 1):
            dp[0][j] = j

        for i in range(1, len_word1 + 1):
            for j in range(1, len_word2 + 1):
                if word1[i - 1] == word2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(dp[i - 1][j - 1] + 1, dp[i][j - 1] + 1, dp[i - 1][j] + 1)

        return dp[len_word1][len_word2]

    def phonetic_suggestions(self, word, max_suggestions=5):
        """Suggest corrections based on phonetic similarity using Metaphone"""
        phonetic_word = metaphone.doublemetaphone(word)
        dictionary_words = self.trie.get_all_words()
        suggestions = []

        for dict_word in dictionary_words:
            if metaphone.doublemetaphone(dict_word) == phonetic_word:
                suggestions.append(dict_word)
                if len(suggestions) >= max_suggestions:
                    break

        return suggestions

    def auto_correct(self, word, max_suggestions=5):
        """Auto-correction with confidence score"""
        suggestions = self.suggest_corrections(word, max_suggestions)
        if suggestions:
            return suggestions[0]  # Return the most confident suggestion
        return word  # Return the original word if no suggestions

    def process_text(self, text):
        """Process the text and suggest corrections for each word"""
        words = text.split()
        corrected_words = []
        for word in words:
            clean_word = word.strip(string.punctuation).lower()

            # Auto-correction mode
            corrected_word = self.auto_correct(clean_word)
            corrected_words.append(corrected_word)

        return " ".join(corrected_words)


# Example of using SpellGuard for Streamlit
spell_checker = SpellGuard()

# Load words from a file (e.g., 'word.txt')
spell_checker.load_dictionary("word.txt")

# Streamlit interface
st.title("SpellGuard: Advanced Spell Checker")
st.markdown("### Enter a sentence to check spelling and get corrections:")

# Text input
input_text = st.text_area("Input text", height=150)

# Check if input is given
if input_text:
    corrected_text = spell_checker.process_text(input_text)
    
    # Display the result
    st.subheader("Corrected Text:")
    st.write(corrected_text)

    # Display suggestions for each word
    st.subheader("Suggestions for Misspelled Words:")

    words = input_text.split()
    for word in words:
        clean_word = word.strip(string.punctuation).lower()
        if not spell_checker.check_word(clean_word):
            st.write(f"Misspelled word: **{clean_word}**")
            suggestions = spell_checker.suggest_corrections(clean_word, max_suggestions=3)
            
            if suggestions:
                chosen_correction = st.radio(f"Choose a correction for: {clean_word}", suggestions)
                
                if chosen_correction:
                    corrected_text = corrected_text.replace(clean_word, chosen_correction)

    # Show the final corrected sentence after choosing corrections
    st.subheader("Final Corrected Sentence:")
    st.write(corrected_text)
