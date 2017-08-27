"""
Created by: Akash Agarwal
Institute of Engineering and Technology,Lucknow

This is a simple implementation of a Facebook Chatbot:
The language used is Python.
Resources used- we require several python libraries: 
Flask: This library is used to create a local host on the device.
Since the Facebook requires a SSL Webhook for verification of a safe site, we require certain modularities-
The facebook provides the Developer Account with "Access Token" (PAT), also makes use of Heroku and ngrok
for setting up secure server.
"""

import sys, json, traceback, requests
from flask import Flask, request

app = Flask(__name__)
PAT = 'EAABnOxb3Ck8BAH57uXZALlswSCKMuvmUZCTtZASfDMLmImyXrHgn2tBpQpIntR1eKeIczlgNZCitiShUOMNzGMoRpxyUGbW4CdWMJ1bFkjXm7us2PWZAwZBSxmwcQ5NDIAfUWdJKUKdkkZCj3DNWBFfr4v9DOS3MQLDPgqnPel6iQZDZD'
VERIFICATION_TOKEN = 'Akash.1996' # This is the verification code that we have to enter in the facebook account.

@app.route('/', methods=['GET'])
def webhookVerification():
    '''
        This function handles the verification process for the webhooks required to attach bot to the 
        facebook page.
    '''
    print "Handling Verification."
    if request.args.get('hub.verify_token', '') == VERIFICATION_TOKEN:  # If the verfication code entered at
                                                                        # at the FB Developers page matches to 
                                                                        # the above defined value.
        print "Webhook verified!"
        return request.args.get('hub.challenge', '')
    else:
        return "Wrong verification token!"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Functions defined that handle BOT Processing~~~~~~~~~~~~~~~~~~~~~~ #
def msgHandler():
    payload = request.get_data()    # request.get_data() requests for the data entered in the chat box

    # Handle messages
    for sender_id, message in messaging_events(payload):
        # Start processing valid requests
        try:
            response = processIncoming(sender_id, message)
            
            if response is not None:    # if response if not NUll, i.e. some message is received.
                send_message(PAT, sender_id, response) # then reply back the same message to the user.

            else:
                send_message(PAT, sender_id, "Sorry, I couldn't understand what you just said.")
        except Exception, e:
            print e
            traceback.print_exc()
    return "ok"

def processIncoming(user_id, message):
    ''' 
        This functions keep track of 3 types of input that the user can enter:
        1) Text
        2) Location
        3) Audio
        In case of text message, resend it.
        In case of location, write a simple message while sending the link to the location.
        In case of music, write a simple message while sending a link to the same audio.
    '''

    if message['type'] == 'text':
        message_text = message['data']
        return message_text

    elif message['type'] == 'location':
        response = "Received a location (%s,%s) (y)"%(message['data'][0],message['data'][1])
        return response

    elif message['type'] == 'audio':
        audio_url = message['data']
        return "Received an audio %s"%(audio_url)

    # If the data received is unrecognisable, remove the context and reset all data to start as new.
    else:
        return "*unrecognised data received!!*"


def send_message(token, user_id, text):
    """Send the message text to recipient with id recipient.
    """
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {"text": text.decode('unicode_escape')}
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

# Generate tuples of (sender_id, message_text) from the provided payload.
# This part technically clean up received data to pass only meaningful data to processIncoming() function
def messaging_events(payload):
    
    data = json.loads(payload) # json.loads() converts python dictionary to json object
    messaging_events = data["entry"][0]["messaging"]
    
    for event in messaging_events:
        sender_id = event["sender"]["id"]

        # If it is not a message, i.e. nothing is received
        if "message" not in event:
            yield sender_id, None

        # If the message is a simple text message
        if "message" in event and "text" in event["message"] and "quick_reply" not in event["message"]:
            data = event["message"]["text"].encode('unicode_escape')
            yield sender_id, {'type':'text', 'data': data, 'message_id': event['message']['mid']}

        # Message with attachment (location, audio, photo, file, etc)
        elif "attachments" in event["message"]:

            # If the attachment is a location 
            if "location" == event['message']['attachments'][0]["type"]:
                coordinates = event['message']['attachments'][
                    0]['payload']['coordinates']
                latitude = coordinates['lat']
                longitude = coordinates['long']

                yield sender_id, {'type':'location','data':[latitude, longitude],'message_id': event['message']['mid']}

            # If the attachment is an audio file
            elif "audio" == event['message']['attachments'][0]["type"]:
                audio_url = event['message'][
                    'attachments'][0]['payload']['url']
                yield sender_id, {'type':'audio','data': audio_url, 'message_id': event['message']['mid']}
            
            else:
                yield sender_id, {'type':'text','data':"I don't understand this", 'message_id': event['message']['mid']}
        
        # Quick reply message type
        elif "quick_reply" in event["message"]:
            data = event["message"]["quick_reply"]["payload"]
            yield sender_id, {'type':'quick_reply','data': data, 'message_id': event['message']['mid']}
        
        else:
            yield sender_id, {'type':'text','data':"I don't understand this", 'message_id': event['message']['mid']}


if __name__ == '__main__':  # If the file is the first file, treat as main() 
    if len(sys.argv) == 2: 
        app.run(port=int(sys.argv[1]))  
        # sys.argv is a list in Python, it contains the command-line arguments passed to the script
        # len(sys.argv) counts the number of such arguments.
    else:
        app.run() # Run Default port