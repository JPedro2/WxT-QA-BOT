from pyadaptivecards.card import AdaptiveCard
from pyadaptivecards.container import FactSet
from pyadaptivecards.components import TextBlock, Choice, Image, Fact
from pyadaptivecards.inputs import Text, Number, Choices
from pyadaptivecards.actions import Submit, OpenUrl

def make_card_payload(card):
    """Create a attachment payload from a adaptive card instance. 

    Args:
        card (AdaptiveCard): Instance of the adaptive card for this attachment. 

    Raises:
        Exception: If card is not a subclass of AdaptiveCard or an instance of
            AdaptiveCard.

    Returns:
        dict: A attachment payload containing the specified card. 
    """
    if not issubclass(type(card), AdaptiveCard) and not isinstance(card, AdaptiveCard):
        raise Exception('card must be either a subclass of AdaptiveCard or an instance of AdaptiveCard')
    
    attachment = {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": card.to_dict(),
    }

    return attachment

class ResponseCard(AdaptiveCard):
    def __init__(self, q_id, query, answer, corrected=False, file_attachment=None):
        self.q_id = q_id
        self.file_attachment = file_attachment

        body = []
        actions = []
        
        if corrected:
            corrected_label = TextBlock("Here is your answer from the Webex 🦸‍♀️Warriors🦸‍♂️")
            body.append(corrected_label)
        
        question_label = TextBlock(f"**Your question:**")
        body.append(question_label)

        question_block = TextBlock(f"{query}")
        body.append(question_block)

        answer_label = TextBlock(f"**Our answer:**")
        body.append(answer_label)

        answer_block = TextBlock(answer)
        body.append(answer_block)

        disclaimer_block = TextBlock("Was this not the answer that you looked for? Try rephrasing your question or click the button below for one of the Webex 🦸‍♀️Warriors🦸‍♂️ to take a look.")
        body.append(disclaimer_block)

        super().__init__(body=body, actions=actions)
    
    def to_dict(self):
        d = super().to_dict()
        d['actions'].append({'type': "Action.Submit", 'title': "Not the correct answer", 'data': {'type': 'response_card', 'q_id': self.q_id}})
        
        if self.file_attachment is not None:
            d['actions'].append({'type': "Action.OpenUrl", 'title': "Additional resources", 'url': self.file_attachment})
        
        return d

class CorrectAnswerCard(AdaptiveCard):
    def __init__(self, q_id, query, answer_provided, answer_options):
        self.q_id = q_id

        body = []
        actions = []

        intro = TextBlock("We received the following question that the requester deemed to be wrongly answered. If we have misclassified this please use the drop-down to choose the matching question. If the answer is not yet in our database use the response field to type the correct answer.")
        body.append(intro)

        question_label = TextBlock("**Query**")
        body.append(question_label)

        question = TextBlock(query)
        body.append(question)

        answer_label = TextBlock("**Our Answer**")
        body.append(answer_label)

        answer = TextBlock(answer_provided)
        body.append(answer)

        answer_options_label = TextBlock("If this was misclassified provide the matching question here and click 'Wrongly classified'")
        body.append(answer_options_label)

        answer_choices = []
        for q_id, text in answer_options.items():
            c = Choice(f"{q_id}:{text}", q_id)
            answer_choices.append(c)
        
        answer_option_choices = Choices(answer_choices, 'correct_question')
        body.append(answer_option_choices)

        answer_new_response_label = TextBlock("If this is a new question please provide a answer in the text field below and click 'New answer'")
        body.append(answer_new_response_label)

        new_answer = Text('new_answer')
        body.append(new_answer)


        super().__init__(body=body, actions=actions)

    def to_dict(self):
        d = super().to_dict()
        d['actions'].append({'type': "Action.Submit", 'title': "Wrongly classified", 'data': {'type': 'wrong_classification', 'q_id': self.q_id}})
        d['actions'].append({'type': "Action.Submit", 'title': "New answer", 'data': {'type': 'new_answer', 'q_id': self.q_id}})
        d['actions'].append({'type': "Action.OpenUrl", 'title': "View Knowledge Base", 'url'    : "http://35.242.181.193/update.html"})
        
        return d

