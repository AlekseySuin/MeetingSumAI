import base64
import os
import requests
import uuid
import json
import streamlit as st
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError

client_id = st.secrets['client_id']

secret = st.secrets['secret']

auth = st.secrets['auth']


def get_token(auth_token, scope='GIGACHAT_API_PERS'):
    rq_uid = str(uuid.uuid4())

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rq_uid,
        'Authorization': f'Basic {auth_token}'
    }

    payload = {
        'scope': scope
    }

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response
    except requests.RequestException as e:
        print(f"Ошибка: {str(e)}")
        return -1

response = get_token(auth)
if response != 1:
  print(response.text)
  giga_token = response.json()['access_token']


url = "https://gigachat.devices.sberbank.ru/api/v1/models"

payload={}
headers = {
  'Accept': 'application/json',
  'Authorization': f'Bearer {giga_token}'
}

response = requests.request("GET", url, headers=headers, data=payload, verify=False)

print(response.text)

def get_chat_completion(auth_token, user_message):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat",  # Используемая модель
        "messages": [
            {
                "role": "user",  # Роль отправителя (пользователь)
                "content": user_message  # Содержание сообщения
            }
        ],
        "temperature": 1,  # Температура генерации
        "top_p": 0.1,  # Параметр top_p для контроля разнообразия ответов
        "n": 1,  # Количество возвращаемых ответов
        "stream": False,  # Потоковая ли передача ответов
        "max_tokens": 512,  # Максимальное количество токенов в ответе
        "repetition_penalty": 1,  # Штраф за повторения
        "update_interval": 0  # Интервал обновления (для потоковой передачи)
    })

    # Заголовки запроса
    headers = {
        'Content-Type': 'application/json',  # Тип содержимого - JSON
        'Accept': 'application/json',  # Принимаем ответ в формате JSON
        'Authorization': f'Bearer {auth_token}'  # Токен авторизации
    }

    # Выполнение POST-запроса и возвращение ответа
    try:
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        return response
    except requests.RequestException as e:
        # Обработка исключения в случае ошибки запроса
        print(f"Произошла ошибка: {str(e)}")
        return -1

def ourTranscribe(PATH_TO_FILE):
    with BatchClient(settings) as client:
        try:
            job_id = client.submit_job(
                audio=PATH_TO_FILE,
                transcription_config=conf,
            )
            print(f'job {job_id} submitted successfully, waiting for transcript')

            # Note that in production, you should set up notifications instead of polling.
            # Notifications are described here: https://docs.speechmatics.com/features-other/notifications
            transcript = client.wait_for_completion(job_id, transcription_format='txt')
            # To see the full output, try setting transcription_format='json-v2'.
            print(transcript)
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                print('Invalid API key - Check your API_KEY at the top of the code!')
            elif e.response.status_code == 400:
                print(e.response.json()['detail'])
            else:
                raise e


    credentials = f"{client_id}:{secret}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    encoded_credentials == auth

    answer = get_chat_completion(giga_token, 'Объясни какую задачу должен выполнить каждый участник этой реальной встречи: ' + transcript)

    answer.json()

    st.write(answer.json()['choices'][0]['message']['content'])


API_KEY = st.secrets['API_KEY']
LANGUAGE = "ru"

settings = ConnectionSettings(
    url="https://asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

# Define transcription parameters
conf = {
    "type": "transcription",
    "transcription_config": {
        "language": LANGUAGE
    }
}

st.title(":green[Meeting Summarization App]")

st.write("Вы можете выбрать свой файл или заготовку")
selectedOption = st.selectbox("Выберите ваш вариант", ('Свой файл', 'Заготовленные'))

if selectedOption == "Свой файл":
    audio_file_extensions = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "flac"]
    uploaded_file = st.file_uploader(":green[Загрузите файл]",
                                  type=audio_file_extensions)
    if uploaded_file is not None:
        with open(os.path.join("audio", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        audio_bytes = uploaded_file.read()
        st.audio(audio_bytes, format='audio/mp3')
        PATH_TO_FILE = "audio/" + uploaded_file.name

        ourTranscribe(PATH_TO_FILE)
else:
    st.write("Вариант 1:")
    if st.button("Собеседование"):
        PATH_TO_FILE = "audio/Собеседование — аудиозапись 1 (www.lightaudio.ru).mp3"
        st.write("Вы выбрали файл: Собеседование - аудиозапись")
        ourTranscribe(PATH_TO_FILE)

    st.write("Вариант 2:")
    if st.button("Совещание"):
        PATH_TO_FILE = "audio/Sovecshanie_po_ekonomicheskim_voprosam_-_V_sovecshanii_prinyali_uchastie_pomocshnik_Prezidenta_Andrej_Belouso_(Zvyki.com).mp3"
        st.write("Вы выбрали файл: Совещание - аудиозапись")
        ourTranscribe(PATH_TO_FILE)