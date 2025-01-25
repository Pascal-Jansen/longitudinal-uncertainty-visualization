from flask import Flask, request
import csv
import re
import os
import datetime
import pytz

app = Flask(__name__)

# Halte die Links zu den Fragebögen bereit
survey_links = [
    "<a href='https://surveys.informatik.uni-ulm.de/index.php/499768?lang=en'>Click this to access the questionnaire for Morning Day 1</a>",
    "<a href='https://surveys.informatik.uni-ulm.de/index.php/239245?lang=en'>Click this to access the questionnaire for Evening Day 1</a>",
    "<a href='https://surveys.informatik.uni-ulm.de/index.php/288366?lang=en'>Click this to access the questionnaire for Morning Day 2</a>",
    "<a href='https://surveys.informatik.uni-ulm.de/index.php/773433?lang=en'>Click this to access the questionnaire for Evening Day 2</a>",
    "<a href='https://surveys.informatik.uni-ulm.de/index.php/143491?lang=en'>Click this to access the questionnaire for Morning Day 3</a>",
    "<a href='https://surveys.informatik.uni-ulm.de/index.php/934454?lang=en'>Click this to access the questionnaire for Evening Day 3</a>",
    "<a href='https://app.prolific.co/submissions/complete?cc=C18N9GKR'>Click this to return to Prolific</a>",
]

# Funktionen, um Benutzerdaten zu lesen und zu schreiben
def read_data(user_id):
    filename = os.path.join('/var/www/feedback-vis-server/database', f'{user_id}_data.csv')
    if not os.path.isfile(filename):
        return []
    with open(filename, 'r') as f:
        return list(csv.reader(f))

def write_data(user_id, data):
    filename = os.path.join('/var/www/feedback-vis-server/database', f'{user_id}_data.csv')
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)


# Funktion, um die UserID zu prüfen
def check_user_id(user_id, local_time):
    # Öffne die CSV-Datei und finde den letzten Eintrag des Benutzers
    last_participation = read_data(user_id)
    last_participation = last_participation[-1] if last_participation else None

    # Wenn der Benutzer noch nicht existiert, logge die Teilnahme und leite ihn zum ersten Fragebogen
    if last_participation is None:
        if check_survey_time(last_participation, True, local_time): # only morning time window is allowed for first time participants
            log_participation(user_id, local_time, 0, "Running")
            return {'questionnaire': survey_links[0], 'progress': {'cell': 0, 'content': 'Running'}} 
        else:
            return {'error': 'Please wait until the next morning between 7 am and 12 pm to start with the questionnaires.', 'progress': {'cell': 0, 'content': 'Waiting'}} 

    # Kann der nächste Fragebogen angezeigt werden? -> wenn nicht, dann return
    time_check_results = check_survey_time(last_participation, False, local_time)
    if time_check_results is not None:
        return time_check_results

    # Leite den Benutzer zum nächsten Fragebogen weiter
    next_survey = int(last_participation[2]) + 1

    # Beende die Studie, falls alle Fragebögen erfolgreich beantwortet wurden
    if next_survey >= len(survey_links) - 1:
        return {'error': 'Thank you for participating. You have completed all surveys. ' + survey_links[6], 'progress': {'cell': 6, 'content': 'Done'}}

    # Logge die Teilnahme
    log_participation(user_id, local_time, next_survey, "Running")

    # Gebe den nächsten Questionnaire zurück
    return {'questionnaire': survey_links[next_survey], 'progress': {'cell': str(next_survey), 'content': 'Running'}}


# Funktion, um die Teilnahme des Benutzers zu protokollieren
def log_participation(user_id, participant_local_time, survey_number, status):
    # Protokolliere die aktuelle Uhrzeit und das Datum
    now = datetime.datetime.now()
    # Öffne die CSV-Datei und füge die Teilnahme hinzu
    participation_data = read_data(user_id)
    participation_data.append([user_id, participant_local_time, survey_number, status, now.strftime("%Y-%m-%d %H:%M:%S")])
    write_data(user_id, participation_data)


def check_survey_time(last_participation, needs_init, local_time):
    # Überprüfe das Datum und die Uhrzeit der letzten Teilnahme
    #now = datetime.datetime.now() -> using local time of client instead

    # Check if the last participation falls into the morning or evening window
    is_morning = 7 <= local_time.hour < 12
    is_evening = 16 <= local_time.hour < 21

    # check if the first time participants is in the allowed time window
    if needs_init:
        return is_morning

    if last_participation[3] == "Running": # there must be an unanswered questionnaire
        if is_morning:
            if is_odd(last_participation[2]): # but it should be evening
                return {'error': 'You still have a questionnaire to answer but this is the wrong time slot. Please wait until the evening (4 pm - 9 pm).', 'progress': {'cell': last_participation[2], 'content': last_participation[3]}}
            else: # and it should be morning
                return {'error': 'You still have a questionnaire to answer: ' + survey_links[int(last_participation[2])], 'progress': {'cell': last_participation[2], 'content': last_participation[3]}}
        elif is_evening:
            if is_odd(last_participation[2]): # and it should be evening
                return {'error': 'You still have a questionnaire to answer: ' + survey_links[int(last_participation[2])], 'progress': {'cell': last_participation[2], 'content': last_participation[3]}}
            else: # but it should be morning
                return {'error': 'You still have a questionnaire to answer but this is the wrong time slot. Please wait until the morning (7 am - 12 pm).', 'progress': {'cell': last_participation[2], 'content': last_participation[3]}}
        else: # it is neither evening nor morning
            if is_odd(last_participation[2]): # but it should be evening
                return {'error': 'You still have a questionnaire to answer but this is the wrong time slot. Please wait until the evening (4 pm - 9 pm).', 'progress': {'cell': last_participation[2], 'content': last_participation[3]}}
            else: # but it should be morning
                return {'error': 'You still have a questionnaire to answer but this is the wrong time slot. Please wait until the morning (7 am - 12 pm).', 'progress': {'cell': last_participation[2], 'content': last_participation[3]}}
    else: # no active questionnaire -> check if the time slot is correct for the new one
        next_survey = int(last_participation[2]) + 1
        if next_survey >= len(survey_links) - 1:
            return None # all questionnaires were succesfully answered - just send through

        if is_odd(next_survey): # next questionnaire will be a evening one:
            if is_evening:
                return None # return everyting is fine and the website can provide the next questionnaire
            else:
                return {'error': 'Please wait until the evening (4 pm - 9 pm) to answer the next questionnare.', 'progress': {'cell': last_participation[2], 'content': last_participation[3]}}
        else: # next questionnaire will be a morning one:
            if is_morning:
                return None # return everyting is fine and the website can provide the next questionnaire
            else:
                return {'error': 'Please wait until the morning (7 am - 12 pm) to answer the next questionnaire.', 'progress': {'cell': last_participation[2], 'content': last_participation[3]}}



def is_valid_prolific_id(pid):
    # Der reguläre Ausdruck prüft, ob der String genau 24 hexadezimale Zeichen enthält
    match = re.fullmatch(r'[0-9a-fA-F]{24}', pid)
    return match is not None  # Gibt True zurück, wenn ein Match gefunden wurde, sonst False


def is_odd(number):
    if int(number) % 2 != 0:
        return True
    else:
        return False



@app.route('/')
def home():
    return open('/var/www/feedback-vis-server/index.html', encoding='UTF-8').read()

@app.route('/script.js')
def script():
    return open('/var/www/feedback-vis-server/script.js', encoding='UTF-8').read()

@app.route('/getQuestionnaire', methods=['POST'])
def get_questionnaire():
    user_id = request.json['userID']
    local_time = datetime.datetime.strptime(request.json['localTime'], "%d/%m/%Y, %H:%M:%S")
    if not is_valid_prolific_id(user_id):
        return {'error': 'Invalid ProlificID!'}
    return check_user_id(user_id, local_time)

@app.route('/returnQuestionnaire/<user_id>')
def return_questionnaire(user_id):
    filename = os.path.join('/var/www/feedback-vis-server/database', f'{user_id}_data.csv')
    if not os.path.isfile(filename):
        return "Invalid ProlificID!"
    with open(filename, 'r') as f:
        last_participation = list(csv.reader(f))
        last_participation = last_participation[-1] if last_participation else None # get last entry of the user to check current survey number
        
        if last_participation == None:
            return '<h2>We were unable to link your questionnaire return to an active entry in our database. Please contact the study supervisor.</h2>'

        #local_time = datetime.datetime.strptime(request.json['localTime'], "%d/%m/%Y, %H:%M:%S")
        #is_morning = (8, 8) <= (local_time.hour, local_time.minute) < (12, 8)
        #is_evening = (17, 8) <= (local_time.hour, local_time.minute) < (21, 8)
        #if (is_odd(last_participation[2]) and not is_evening) or (not is_odd(last_participation[2]) and not is_morning):
        #    return '<h2>Error: You did return the questionnaire at the wrong time slot or the time for the current slot is up.<b> You have 1 hour after the time slot ends to return the questionnaire. Please try again tomorrow.<b> If this problem persists, contact the study supervisor.</h2>'
       
        log_participation(user_id, last_participation[1], last_participation[2], "Done") # create new entry with the same survey number but updated status

    return '<h2>We have successfully tracked your progress. Please go back to the study home page by <a href="http://visualization-study.ddns.net/">clicking this link</a> to view your progress.</h2>'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
