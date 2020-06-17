from abc import ABC, abstractmethod

from fuzzywuzzy import process

class BaseClassifier(ABC):
    @abstractmethod
    def classifier(self, query, questions):
        pass

class FuzzyMatchingClassifier(BaseClassifier):
    def classifier(self, query, questions):
        closest_match, confidence = process.extractOne(query, questions)

        return closest_match, confidence