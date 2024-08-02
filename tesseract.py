import requests as r
import json
import threading
import streamlit as st

# Function to get the subjects dashboard
def dashbord(token):
    url = "https://api.tesseractonline.com/studentmaster/subjects/4/5"
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://tesseractonline.com/"
    }
    response = r.get(url=url, headers=headers).text
    response = json.loads(response)
    response = response['payload']
    subjects = {item['subject_id']: item['subject_name'] for item in response}
    return subjects

# Function to get the units of a subject
def get_units(token, subject_id):
    url = f"https://api.tesseractonline.com/studentmaster/get-subject-units/{subject_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://tesseractonline.com/"
    }
    response = r.get(url=url, headers=headers).text
    response = json.loads(response)
    response = response['payload']
    units = {item['unitId']: item['unitName'] for item in response}
    return units

# Function to get the topics of a unit
def get_topics(token, unit_id):
    url = f"https://api.tesseractonline.com/studentmaster/get-topics-unit/{unit_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://tesseractonline.com/"
    }
    response = r.get(url=url, headers=headers).text
    response = json.loads(response)
    response = response['payload']['topics']
    topics = {f"{item['id']}. {item['name']}  {item['learningFlag']}": {'pdf': f'"https://api.tesseractonline.com"{item["pdf"]}', 'video': item['videourl']} for item in response}
    return topics

# Function to get quiz details for a specific topic
def get_quiz(token, topic_id):
    url = f"https://api.tesseractonline.com/quizattempts/create-quiz/{topic_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://tesseractonline.com/"
    }
    response = r.get(url=url, headers=headers).text
    return json.loads(response)

# Function to save a user's answer to a quiz question
def save_answer(token, quiz_id, question_id, answer):
    url = "https://api.tesseractonline.com/quizquestionattempts/save-user-quiz-answer"
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://tesseractonline.com/"
    }
    payload = {
        "quizId": f'{quiz_id}',
        "questionId": f'{question_id}',
        "userAnswer": f'{answer}'
    }
    response = r.post(url=url, json=payload, headers=headers).text
    return response

# Function to submit the quiz attempt and get the score
def submit_quiz(token, quiz_id):
    url = "https://api.tesseractonline.com/quizattempts/submit-quiz"
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://tesseractonline.com/"
    }
    payload = {
        "branchCode": "CSE",
        "sectionName": "CSE-PS1",
        "quizId": f'{quiz_id}'
    }
    response = r.post(url=url, json=payload, headers=headers).text
    response = json.loads(response)
    return response

# Function to attempt to complete a quiz for a specific topic
def write_quiz(token, topic_id):
    try:
        quiz_details = get_quiz(token, topic_id)
        quiz_id = quiz_details["payload"]['quizId']
        questions = quiz_details["payload"]["questions"]
        options = ['a', 'b', 'c', 'd']
        previous_score = submit_quiz(token, quiz_id)["payload"]["score"]
        st.write(f"Working on quiz {topic_id}, please wait...")
        for question in questions:
            for option in options:
                save_answer(token, quiz_id, question['questionId'], option)
                current_score = submit_quiz(token, quiz_id)["payload"]["score"]
                if current_score == len(questions):
                    st.write(f'Test {topic_id} completed, refresh the page')
                    return
                if current_score > previous_score:
                    previous_score = current_score
                    break
    except KeyError:
        st.write(f'This subject or topic {topic_id} is inactive')

# Main program
def main():
    st.title("Tesseract Online Quiz Automation")
    
    token = st.text_input("Enter your token:")
    
    if token:
        sub = dashbord(token)
        subject_keys = list(sub.keys())
        subject_names = list(sub.values())
        subject_selected = st.selectbox('Select a subject:', subject_names)

        if subject_selected:
            subject_id = subject_keys[subject_names.index(subject_selected)]
            units_dict = get_units(token, subject_id)
            unit_keys = list(units_dict.keys())
            unit_names = list(units_dict.values())
            unit_selected = st.selectbox('Select a unit:', unit_names)

            if unit_selected:
                unit_id = unit_keys[unit_names.index(unit_selected)]
                topics_dict = get_topics(token, unit_id)
                topic_keys = list(topics_dict.keys())
                topic_names = list(topics_dict.keys())
                topics_selected = st.multiselect('Select topics:', topic_names)

                if st.button('Start Quizzes'):
                    topic_ids = [key.split('.')[0] for key in topics_selected]

                    # Using threading to process quizzes concurrently
                    threads = []
                    for topic_id in topic_ids:
                        t = threading.Thread(target=write_quiz, args=(token, topic_id))
                        threads.append(t)
                        t.start()

                    for t in threads:
                        t.join()

                    st.write("All topics completed.")

if __name__ == "__main__":
    main()