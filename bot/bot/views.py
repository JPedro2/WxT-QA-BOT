import json
import requests

from django.views import View
from django.views.decorators.csrf import csrf_exempt

import os

from django.http import JsonResponse

from django.shortcuts import render

from django.utils.decorators import method_decorator

from django.conf import settings

from webexteamssdk import WebexTeamsAPI, ApiError

from .classifier import FuzzyMatchingClassifier
from .models import Question, ClassifierVote
from .cards import make_card_payload, ResponseCard, CorrectAnswerCard

@method_decorator(csrf_exempt, name='dispatch')
class ReceiverView(View):
    def post(self, request):
        payload = json.loads(request.body)
        
        hook_id = str(payload['data']['id']).replace('/', '_bs_')
        path = os.path.join(settings.BASE_DIR, "hooks", f"{payload['data']['id']}.json")

        f = open(path, "w")
        f.writelines(str(payload))
        f.flush()
        f.close()
        print(f"- Saving {path}")
        return JsonResponse({'success': True})




# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class AttachmentActionWebhookView(View):
    def post(self, request):
        payload = json.loads(request.body)

        api = WebexTeamsAPI(access_token=settings.WEBEX_ACCESS_TOKEN)


        attachment = api.attachment_actions.get(payload['data']['id'])

        inputs = attachment.inputs

        if inputs['type'] == "response_card":
            q = Question.objects.get(pk=inputs['q_id'])
            q.suggestion_correct = False

            # Create response card

            # Retrieve answer options
            question_response = requests.get("http://35.242.181.193/api/getAll")
        
            items = question_response.json()['items']

            answer_options = {}

            for itm in items:
                answer_options[itm['id']] = itm['question']
            
            print(str(answer_options))
            card = CorrectAnswerCard(str(q.id), q.question_text, q.answer, answer_options)

            api.messages.create(roomId=settings.WARRIORS_ROOM, markdown="This is an adaptive card. Please view on your desktop device", attachments=[make_card_payload(card)])
        elif inputs['type'] == "wrong_classification":
            q = Question.objects.get(pk=inputs['q_id'])
            q.was_missclassified = True
            q.suggestion_correct = False
            
            # Fetch correct answer
            correct_question_id = inputs['correct_question']
            correct_resp = requests.get(f"http://35.242.181.193/api/getAnswer/{correct_question_id}").json()

            correct_answer = correct_resp['answer']
            q.answer = f"{correct_question_id}:{correct_answer}"
            q.save()

            # Send answer back and delete card
            file_attachment = correct_resp['location']
            card = ResponseCard(str(q.id), q.question_text, correct_answer, corrected=True, file_attachment=file_attachment)
            api.messages.create(roomId=q.room_id, markdown="This is an adaptive card. Please view on your desktop device", attachments=[make_card_payload(card)], parentId=q.message_id)
            api.messages.delete(payload['data']['messageId'])
        elif inputs['type'] == "new_answer":
            q = Question.objects.get(pk=inputs['q_id'])
            q.was_missclassified = False
            q.suggestion_correct = False
            
            # Fetch correct answer
            correct_answer = inputs['new_answer']
            q.answer = f"{correct_answer}"
            q.save()

            # Send answer back and delete card
            card = ResponseCard(str(q.id), q.question_text, correct_answer, corrected=True)
            api.messages.create(roomId=q.room_id, markdown="This is an adaptive card. Please view on your desktop device", attachments=[make_card_payload(card)], parentId=q.message_id)
            api.messages.delete(payload['data']['messageId'])
        return JsonResponse({'success': True})

@method_decorator(csrf_exempt, name='dispatch')
class MessageCreatedWebhookView(View):
    def post(self, request):
        payload = json.loads(request.body)
    
        if not payload['data']['personId'] == settings.BOT_ID:
            api = WebexTeamsAPI(access_token=settings.WEBEX_ACCESS_TOKEN)

            message = api.messages.get(payload['data']['id'])
            query = message.text

            if message.roomType == "group":
                split = query.split(" ")
                query = " ".join(split[1:])
            
            greeting_words = ["hi", "hi", "hello", "whats up", "whats up", "what’s up", "wassup", "yo", "heya", "good morning", "good afternoon", "good evening", "what is this?", "who are you", "help"]
            online_greeting_words = ["hi", "hello", "hey", "helloo", "hellooo", "g morning", "gmorning", "good morning", "morning", "good day", "good afternoon", "good evening", "greetings", "greeting", "good to see you", "its good seeing you", "how are you", "how're you", "how are you doing", "how ya doin'", "how ya doin", "how is everything", "how is everything going", "how's everything going", "how is you", "how's you", "how are things", "how're things", "how is it going", "how's it going", "how's it goin'", "how's it goin", "how is life been treating you", "how's life been treating you", "how have you been", "how've you been", "what is up", "what's up", "what is cracking", "what's cracking", "what is good", "what's good", "what is happening", "what's happening", "what is new", "what's new", "what is neww", "g’day", "howdy"]
            greeting_words.extend(online_greeting_words)
            greeting_words = list(set(greeting_words))

            words_with_april = []
            for greet in greeting_words:
                words_with_april.append(f"{greet} april")
            greeting_words.extend(words_with_april)

            if str(query).lower() in greeting_words:
                api.messages.create(toPersonId=message.personId, markdown=settings.HELP_TEXT)
            else:
                # This code statically uses the FuzzyMatching
                # If you want to use IBMs Watson check the 
                # watson.py file and see how to implement such a 
                # classifier based on Watson's NLU
                # 
                # You will need a lot of training data. Our recommendation is to use 
                # the fuzzy matching until you have enough training data and/or augment 
                # the data with amazon mechanical turk
                clf = FuzzyMatchingClassifier()

                question_response = requests.get("http://35.242.181.193/api/getAll")
        
                items = question_response.json()['items']

                # Find closest match 
                question_list = []
                question_reverse_mapping = {}
                question_answer_mapping = {}   
                location_mapping = {} 

                for itm in items:
                    question_list.append(itm['question'])
                    question_reverse_mapping[itm['question']] = itm['id']
                    question_answer_mapping[itm['id']] = itm['answer']
                    location_mapping[itm['id']] = itm['location']
                    
                closest, confidence = clf.classifier(query, question_list)

                # Get answer 
                q_id = question_reverse_mapping[closest]
                answer = question_answer_mapping[q_id]
                file_attachment = location_mapping[q_id]
                vote = ClassifierVote(classifier="FuzzyMatchingClassifier", vote_id=q_id)
                vote.save()

                # Save votes and return card
                q = Question(question_text=query, asker=payload['data']['personId'], answer=answer, message_id=payload['data']['id'], room_id=message.roomId)
                q.save()
                q.votes.add(vote)
                q.save()

                card = ResponseCard(str(q.id), query, answer, file_attachment=file_attachment)

                api.messages.create(roomId=message.roomId, markdown="This is an adaptive card. Please view on your desktop device", attachments=[make_card_payload(card)], parentId=q.message_id)

        return JsonResponse({'success': True})

