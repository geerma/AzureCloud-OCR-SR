# INSTALLATION REQUIREMENTS
# pip install --upgrade azure-cognitiveservices-vision-computervision
# pip install azure-cognitiveservices-speech
# pip install pysimplegui
# pip install pillow

# Computer Vision
import textwrap
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

# Speech
import azure.cognitiveservices.speech as speech

# PySimpleGUI
import PySimpleGUI as sg

# ETC
import os.path
import time

# VARIABLES
AUDIO_API_KEY = "INSERT-SPEECH-API-KEY-HERE" 
AUDIO_REGION = "westus2" 
OCR_ENDPOINT = "https://cognitive-services-azure-cloud.cognitiveservices.azure.com"
OCR_API_KEY = "INSERT-OCR-API-KEY-HERE"

# Create the PySimpleGUI
def GUI():
    sg.theme('LightBlue')

    # Left Column. For pressing the record button, or choosing the file
    file_list_column = [
        [
            sg.Text("Record from Mic"),
            sg.Button('Record', button_color=('white', 'firebrick2'), size=(10,2)),
            sg.Button('Stop', button_color=('white', 'firebrick3'), size=(10,2)),
        ],
        [
            sg.Text("File Folder"),
            sg.In(size=(20,1), enable_events=True, key="-FOLDER-"),
            sg.FolderBrowse(size=(8,2)),
        ],
        [
            sg.Listbox(
                values=[], enable_events=True, size=(40,15),
                key="-FILE LIST-"
            )
        ],
    ]

    # Right Column. For viewing the image or text
    viewer_column = [
        [sg.Text("Choose an Image OR Record:", key="-CHOOSE-")],
        [sg.Text(size=(100,1), key="-OUTPUT-")],
        [sg.Image(key="-IMAGE-")],
    ]

    # Layout for PySimpleGUI
    layout = [
        [
            sg.Column(file_list_column), # Left Column
            sg.VSeparator(), # Seperator
            sg.Column(viewer_column), # Right Column
        ]
    ]

    # Initialize Window with specified layout
    window = sg.Window("Blue Sky", layout)

    while True:
        event, values = window.read()

        # IMAGE EVENTS
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "-FOLDER-": # After browsing and choosing a folder
            folder=values["-FOLDER-"]
            try:
                file_list = os.listdir(folder)
            except:
                file_list = []

            window["-FILE LIST-"].update(file_list)
        elif event == "-FILE LIST-": # After choosing an image
            try:
                filename = os.path.join(
                    values["-FOLDER-"], values["-FILE LIST-"][0]
                )
                window["-CHOOSE-"].update("File Chosen: " + values["-FILE LIST-"][0])
                window["-IMAGE-"].update(filename=filename)
                print("") # New Line
                optical_character_recognition(window, filename) # Call OCR function
            except:
                pass

        # AUDIO EVENTS
        if event == "Record":
            try:
                window["-IMAGE-"].update()
                time.sleep(0.5)
                audio_from_mic(window) # Call cognitive services speech function
                event="Stop"
                print("End of Recording")
            except:
                pass
        elif event == "Stop":
            try:
                window["-CHOOSE-"].update("Choose an Image OR Record:")
                print('Stopped Recording')
            except:
                pass

    window.close()

# Function to retrieve audio from microphone, then display speech to the user
def audio_from_mic(window):
    speech_config = speech.SpeechConfig (
        subscription=AUDIO_API_KEY, 
        region=AUDIO_REGION
        )
    speech_config.speech_recognition_language="en-US" 

    audio_config = speech.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speech.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("\nPlease speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speech.ResultReason.RecognizedSpeech:
        window["-CHOOSE-"].update("Recognized Speech:")
        window["-OUTPUT-"].update(speech_recognition_result.text)
        print("Recognized Speech: {}".format(speech_recognition_result.text))
    elif speech_recognition_result.reason == speech.ResultReason.NoMatch:
        window["-CHOOSE-"].update("No Speech Recognized. Please try again.")
        print("No Speech Recognized. Please try again.")

# Function to retrieve text from an image, then display text to the user. Can be used for multiple languages
def optical_character_recognition(window, filename):

    cv_client = ComputerVisionClient(
        OCR_ENDPOINT, 
        CognitiveServicesCredentials(OCR_API_KEY)
        )

    local_file = filename

    # Langauges: https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/language-support#optical-character-recognition-ocr
    response = cv_client.read_in_stream(open(local_file, 'rb'), language='zh-Hans', raw=True)

    operationLocation = response.headers["Operation-Location"]
    operation_id = operationLocation.split('/')[-1] # Grabs last element

    # Function to continuously call get_read_result until a response is received
    while True:
        read_result = cv_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    text_string = ""

    # Print out each line of the analyzed text
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                text_string += " " + line.text # Append to text string, used in GUI
                print(line.text) # Prints line by line to the console

    window["-OUTPUT-"].update(text_string)

def main():
    GUI()

main()