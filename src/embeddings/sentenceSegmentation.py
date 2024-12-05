import spacy
from typing import List
import os
import json
import re


class SentenceSegmentationService:
    def __init__(self, model: str = "en_core_web_sm"):
        """
        Initialize the sentence segmentation service with a SpaCy language model.
        
        Args:
            model (str): The SpaCy language model to use for segmentation.
        """
        self.nlp = spacy.load(model)

    def read_file(self, file_path: str) -> List[dict]:
        """
        Read the content of a JSON file containing an array of JSON objects.

        Args:
            file_path (str): The path to the JSON file.

        Returns:
            List[dict]: The parsed JSON content.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        if not file_path.endswith(".json"):
            raise ValueError("Only .json files are supported.")
        
        with open(file_path, "r", encoding="utf-8") as file:
            content = json.load(file)
        
        if not isinstance(content, list):
            raise ValueError("Expected a JSON array in the file.")
        
        return content

    def clean_sentence(self, sentence: str) -> str:
        """
        Clean an individual sentence by removing URLs, emails, mentions, stopwords, 
        punctuation, and applying lemmatization.
        
        Args:
            sentence (str): The input sentence to clean.
        
        Returns:
            str: The cleaned sentence.
        """
        # Remove URLs, emails, and mentions
        sentence = re.sub(r'http\S+|www\S+|https\S+', '', sentence)
        sentence = re.sub(r'\S+@\S+', '', sentence)
        sentence = re.sub(r'@[\w]+', '', sentence)  # Remove mentions (e.g., @user)

        # Apply SpaCy processing
        doc = self.nlp(sentence)
        
        # Tokenize and clean text by removing stopwords, punctuation, and lemmatization
        cleaned_tokens = [
            token.lemma_ for token in doc 
            if not token.is_stop and not token.is_punct and token.is_alpha
        ]
        
        return ' '.join(cleaned_tokens)

    def segment_text(self, text: str) -> List[str]:
        """
        Segment the given text into sentences using SpaCy's NLP model.
        
        Args:
            text (str): The input text to segment.
        
        Returns:
            List[str]: A list of sentences extracted from the text.
        """
        doc = self.nlp(text)
        return [sent.text.strip() for sent in doc.sents]

    def process_text(self, text: str) -> List[str]:
        """
        Segment the given text into sentences and clean each sentence.
        
        Args:
            text (str): The input text to process.
        
        Returns:
            List[str]: A list of cleaned sentences.
        """
        # Segment the text into sentences
        sentences = self.segment_text(text)
        print("Sentence Count:", len(sentences))
        # Clean each sentence
        processed_sentences = [self.clean_sentence(sentence) for sentence in sentences]
        print("Sentence Count:", len(processed_sentences))
        return processed_sentences

    def segment_content(self, file_path: str) -> List[List[str]]:
        """
        Read a JSON file, extract the "content" attribute from each JSON object,
        segment it into sentences, and clean each sentence.

        Args:
            file_path (str): The path to the JSON file.

        Returns:
            List[List[str]]: A list where each element is a list of cleaned sentences
                             from the "content" attribute of the corresponding JSON object.
        """
        content = self.read_file(file_path)
        
        processed_content = []
        for obj in content:
            if "content" not in obj:
                raise KeyError(f"Key 'content' not found in one of the JSON objects.")
            text = obj["content"]
            if not isinstance(text, str):
                raise ValueError(f"Expected a string for key 'content', got {type(text).__name__}.")
            
            # Segment and clean the "content" value
            processed_content.append(self.process_text(text))
        
        
        sentences = [item for sublist in processed_content for item in sublist]
        
        return sentences
