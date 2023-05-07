# StudentID:	p2128496
# Name:	        Jerald Yeo
# Class:		DISM/FT/1B/03
# Assessment:	CA2
# 
# Script name:	admin.py
# 
# Purpose:	Connect to server to edit quiz settings and questions
#
# Usage syntax:	Press Fn + F5
# 
# Input file:	NIL
# 
# Output file:	NIL
# 
# Python ver:	Python 3.10.0
#
# Modules: from getpass import getpass
#          import socket
#          import sys
#          import pickle
#
#
# ****************************** User-defined functions ***************************
from getpass import getpass
import socket
import sys
import pickle
import time

# functions to validate input
def checkAnsValid(allowP_N,qnNumber=1):
    while True:
        try:
            answer = (input('>>>> ')).lower()
            inputs = 'abcdpn'
            if answer in inputs and answer != '':
                if qnNumber == 1 and answer == 'p' and allowP_N:
                    raise Exception
                if allowP_N:
                    break
                elif answer == 'p' or answer == 'n':
                    print('\nError! Please enter a, b, c or d')
                else:
                    break
            else:
                raise Exception
        except:
            if qnNumber == 1 and answer == 'p' and allowP_N:
                print("\nError! You are on the first question")
            else:
                print('\nError! Please enter a, b, c or d')

    return answer

def checkNewAnsValid(option):
    while True:
        print(f'{option})',end=" ")
        newAns = input()
        if newAns == "":
            print("Please enter a new answer!")
        else:
            return newAns

def checkQnNumValid(maxQuestionNo,action):
    print(f'\nEnter a question number to {action} (0 to exit):')
    while True:
        questionNo = input('>>>> ')
        try:
            questionNo = int(questionNo)
            if questionNo >= 0 and questionNo <= maxQuestionNo:
                break
            else:
                raise Exception
        except:
            print(f'\nInvalid question number! Please enter a question number from 1 to {maxQuestionNo}')
    return questionNo

def checkNewAnsValid(option):
    while True:
        print(f'{option})',end=" ")
        newAns = input()
        if newAns == "":
            print("Please enter a new answer!")
        else:
            return newAns

def checkYorN(Input):
    while True:
        try:
            YorN = input(Input)
            YorN = YorN.lower()
            if YorN == 'y':
                bool = True
                break
            elif YorN == 'n':
                bool = False
                break
            else:
                raise Exception
        except:
            print("\nPlease enter y or n!")
            
    return bool

def checkOption(num,allowZero=False):
    while True:
        option = (input('>>>> '))
        try:
            option = int(option)
            if option >= 1 and option <= num:
                break
            elif allowZero:
                if option >= 0 and option <= num:
                    break
                else:
                    raise Exception
            else:
                raise Exception
        except:
            print(f'\nError! Please enter option 1 to {num}')
    return option

# function to login
def c_adminlogin(soc):
    while True:
        inAdmin_ID = input("Enter Admin ID (0 to exit): ")
        if inAdmin_ID == '':
            print('Please enter an admin ID!')
        elif inAdmin_ID == '0':
            soc.send(b'--exit--')   #send 1
            return False, ''
        else:
            while True:
                inPasswd = getpass("Enter password: ")
                if inPasswd == '':
                    print('Please enter a password!')
                else:
                    soc.send(bytes(inAdmin_ID + ';' + inPasswd,'utf-8'))
                    loginstatus = soc.recv(1024).decode('utf-8')
                    if loginstatus == '--success--':
                        print('Login success!')
                        return True, inAdmin_ID
                    elif loginstatus == '--fail--':
                        print('Invalid login!')
                        return False, ''

# function to logout
def c_adminlogout(soc,currentAdminID):
    logout = checkYorN('Are you sure you want to logout? (y/n): ')
    if logout:
        soc.send(b'--logout--') #send 1
        soc.send(bytes(currentAdminID,'utf-8'))
        print("Logged out.")
        return True
    else:
        soc.send(b'--nologout--')
        soc.send(b'null')
        return False

# function to edit question pool
def c_editqnpool(soc):
    while True:
        qnPool = pickle.loads(soc.recv(5000))   #recv 1
        no_of_questions = len(qnPool)
        print(f'''
Here are the list of questions:
*****************************************************''')
        for i in range(no_of_questions):
            print(f'{i+1}) {qnPool[i][0]}')
        print(
f'''*****************************************************
1) Edit question
2) Add question
3) Delete question
4) Exit''')
        adminOption = checkOption(4)
        match adminOption:
            case 1:
                soc.send(b'--editqn--') #send 2
                c_editqn(soc,no_of_questions)
            case 2:
                soc.send(b'--addqn--') #send 2
                c_addqn(soc)
            case 3:
                soc.send(b'--deleteqn--') #send 2
                c_deleteqn(soc,no_of_questions)
            case 4:
                soc.send(b'--exit--')   #send 2
                return

# function to edit question information
def c_editqn(soc,no_of_questions):
    while True:
        question_no = checkQnNumValid(no_of_questions,'edit')
        if question_no == 0:
            soc.send(b'--exit--')   #send 1
            return
        else:
            soc.send(bytes(str(question_no),'utf-8'))   #send 1
            while True:
                topic = soc.recv(1024).decode('utf-8')  #recv 1.5
                question = pickle.loads(soc.recv(1024)) #recv 2
                print(f'''
=====================================================
Topic: {topic}
Question {question_no}:
{question[0]}
a) {question[1]}
b) {question[2]}
c) {question[3]}
d) {question[4]}
Correct answer: {question[5]}
=====================================================
1) Edit question topic
2) Edit question description
3) Edit question answers
4) Exit''')
                adminOption = checkOption(4)
                match adminOption:
                    case 1:
                        soc.send(b'--editqntopic--')
                        c_editqntopic(soc)
                    case 2:
                        soc.send(b'--editqndesc--') #send 3
                        c_editqndesc(soc)
                    case 3:
                        soc.send(b'--editqnans--')  #send 3
                        c_editqnans(soc)
                    case 4:
                        soc.send(b'--exit--')   #send 3
                        return

# function to edit question information - topic                     
def c_editqntopic(soc):
    present_topics = pickle.loads(soc.recv(1024))   #recv 1
    print('\nExisting topics:')
    for topic in present_topics:
        print(f'-> {topic}')
    print('Enter the topic name (0 to exit)')
    while True:
        topic = input('>>>> ')
        if topic == '0':
            soc.send(b'--exit--')   #send 2
            return
        elif topic == '' or topic not in present_topics:
            print('Please enter an existing topic!')
        else:
            break
    soc.send(bytes(topic,'utf-8'))  #send 2
    return

# function to edit question information - description
def c_editqndesc(soc):
    print('Enter new question:')
    while True:
        newQnDesc = input('>>>> ')
        if newQnDesc == "":
            print('Please enter a question description!')
        else:
            break
    soc.send(bytes(newQnDesc,'utf-8'))  #send 1
    return

# function to edit question information - answers
def c_editqnans(soc):
    print('Enter new answers:')
    newAnswerA = checkNewAnsValid('a')
    newAnswerB = checkNewAnsValid('b')
    newAnswerC = checkNewAnsValid('c')
    newAnswerD = checkNewAnsValid('d')
    print('Correct answer (a/b/c/d): ')
    newAnswerCorr = checkAnsValid(False)
    answers = [newAnswerA,newAnswerB,newAnswerC,newAnswerD,newAnswerCorr]
    soc.send(pickle.dumps(answers)) #send 1
    return

# function to add question to question pool
def c_addqn(soc):
    print('Enter new question to add (0 to exit):')
    while True:
        newQnDesc = input(">>>> ")
        if newQnDesc == "":
            print("Please enter a question description!")
        elif newQnDesc == '0':
            soc.send(b'--exit--')   #send 1
            return
        else:
            soc.send(b'--continue--')   #send 1
            break
    print('Enter answers:')
    newAnswerA = checkNewAnsValid('a')
    newAnswerB = checkNewAnsValid('b')
    newAnswerC = checkNewAnsValid('c')
    newAnswerD = checkNewAnsValid('d')
    print('Correct answer (a/b/c/d): ')
    newAnswerCorr = checkAnsValid(False)
    present_topics = pickle.loads(soc.recv(1024))   #recv 2
    print('Existing topics:')
    for topic in present_topics:
        print(f'-> {topic}')
    print('Enter the topic name')
    while True:
        topic = input('>>>> ')
        if topic == '' or topic not in present_topics:
            print('Please enter an existing topic!')
        else:
            break
    newQn = [topic,newQnDesc,newAnswerA,newAnswerB,newAnswerC,newAnswerD,newAnswerCorr]
    soc.send(pickle.dumps(newQn))   #send 3
    return

# function to delete question from question pool
def c_deleteqn(soc,no_of_questions):
    while True:
        question_no = checkQnNumValid(no_of_questions,'delete')
        if question_no == 0:
            soc.send(b'--exit--')   #send 1
            return
        else:
            confirm = f'Are you sure you want to delete question {question_no}? (y/n): '
            if checkYorN(confirm):
                soc.send(bytes(str(question_no),'utf-8'))   #send 1
                return
            else:
                pass

# function to edit settings / topics for quiz
def c_editsettings(soc):
    while True:
        print(f'''
*******************
*  Settings Menu  *
*******************
1) Set up quiz settings
2) Set up quiz topics
3) Exit''')
        adminOption = checkOption(3)
        match adminOption:
            case 1:
                soc.send(b'--quizsettings--')
                c_quizsettings(soc)
            case 2:
                soc.send(b'--quiztopics--')
                c_quiztopics(soc)
            case 3:
                soc.send(b'--exit--')
                return

# function to edit quiz settings
def c_quizsettings(soc):
    while True:
        settings = pickle.loads(soc.recv(1024)) #recv 1
        assessmentcomponent,randomize,attempts,timelimit,marks = settings.items()
        assessmentcomponent = assessmentcomponent[1]
        randomize = randomize[1]
        attempts = attempts[1]
        timelimit = timelimit[1]
        marks = marks[1]
        print('''
Here are the settings for the quizzes:
------------------------------------------------------''')
        i = 1
        for setting,value in settings.items():
            print(f'{i}) {setting}: {value}')
            i += 1
        print(
'''------------------------------------------------------
Enter a setting number to change (0 to exit)''')
        adminOption = checkOption(5,True)
        if adminOption != 0:
            print('''
Current setting
-----------------''')
        match adminOption:
            case 1:
                soc.send(b'--assessmentcomponent--')
                c_assessmentcomponent(assessmentcomponent,soc)
            case 2:
                soc.send(b'--randomize--')
                c_randomize(randomize,soc)
            case 3:
                soc.send(b'--attempts--')
                c_attempts(attempts,soc)
            case 4:
                soc.send(b'--timelimit--')
                c_timelimit(timelimit,soc)
            case 5:
                soc.send(b'--marks--')
                c_marks(marks,soc)
            case 0:
                soc.send(b'--exit--')
                return

# function to edit quiz settings - assessment
def c_assessmentcomponent(assessmentcomponent,soc):
    print(f'Assessment Component: {assessmentcomponent}')
    print('''
1) Quiz-1
2) Quiz-2

Enter the quiz you would like to set to''')
    newsetting = checkOption(2)
    if newsetting == 1:
        soc.send(b'Quiz-1')   #send 1
    elif newsetting == 2:
        soc.send(b'Quiz-2')   #send 1
    return

# function to edit quiz settings - randomize
def c_randomize(randomize,soc):
    print(f'Randomize questions: {randomize}\n')
    newsetting = 'Randomize questions? (y/n): '
    if checkYorN(newsetting):
        soc.send(b'True')   #send 1
    else:
        soc.send(b'False')  #send 1
    return

# function to edit quiz settings - attempts
def c_attempts(attempts,soc):
    print(f'Number of attempts: {attempts}\n')
    print('Enter new number of attempts:')
    while True:
        newsetting = input('>>>> ')
        try: 
            newsetting = int(newsetting)
            if newsetting >= 1:
                soc.send(bytes(str(newsetting),'utf-8')) #send 1
                return
            else:
                raise Exception 
        except:
            print("\nInvalid input! Please enter a number greater than 0")

# function to edit quiz settings - time limit
def c_timelimit(timelimit,soc):
    print(f'Time limit (mins): {timelimit}\n')
    print('Please enter the new time limit (in minutes)')
    while True:
        newsetting = input('>>>> ')
        try: 
            newsetting = int(newsetting)
            if newsetting >= 1:
                soc.send(bytes(str(newsetting),'utf-8')) #send 1
                return
            else:
                raise Exception
        except:
            print("\nInvalid input! Please enter a time limit of more than 0 minutes")

# function to edit quiz settings - marks
def c_marks(marks,soc):
    print(f'Marks for each question: {marks}\n')
    print('Please enter the new marks for each question:')
    while True:
        newsetting = input('>>>> ')
        try: 
            newsetting = int(newsetting)
            if newsetting >= 1:
                soc.send(bytes(str(newsetting),'utf-8')) #send 1
                return
            else:
                raise Exception
        except:
            print("\nInvalid input! Please enter a mark of 1 or more")

# function to edit quiz topics (quiz 1 / 2)
def c_quiztopics(soc):
    while True:
        print('''
Topics Menu
==============
1) Edit Quiz 1 Topics
2) Edit Quiz 2 Topics

Select the quiz you want to edit (0 to exit)''')
        adminOption = checkOption(2,True)
        match adminOption:
            case 1:
                soc.send(b'--quiz1topics--')    #send 1
                c_quizchangetopics(soc,'--quiz1--')
            case 2:
                soc.send(b'--quiz2topics--')    #send 1
                c_quizchangetopics(soc,'--quiz2--')
            case 0:
                soc.send(b'--exit--')   #send 1
                return

# function to change number of questions from topics for individual quiz
def c_quizchangetopics(soc,quiz):
    while True:
        topics = pickle.loads(soc.recv(1024))   #recv 1
        if quiz == '--quiz1--':
            print('''
--------Quiz 1 Topics--------''')
        elif quiz == '--quiz2--':
            print('''
--------Quiz 2 Topics--------''')
        i = 1
        for topic,num_of_questions in topics.items():
            print(
    f'''{i}) No. of \'{topic}\' questions: {num_of_questions}''')
            i += 1
        
        print('\nSelect the topic you want to change number of questions for (0 to exit):')
        topicno = checkOption(i-1,True)
        if topicno == 0:
            soc.send(b'--exit--')   #send 2
            return
        else:
            soc.send(b'--continue--')   #send 2
            list_topics = list(topics)
            selectedtopic = list_topics[topicno-1]
            print(f'Enter no. of \'{selectedtopic}\' questions you would like')
            soc.send(bytes(selectedtopic,'utf-8')) #send 3
            while True:
                while True:
                    try:
                        newnum = int(input('>>>> '))
                        if newnum < 0:
                            raise Exception
                        break
                    except:
                        print('Please enter a valid number of questions!')
                noofqnsundertopic = int(soc.recv(1024).decode('utf-8')) #recv 4
                if newnum > noofqnsundertopic:
                    soc.send(b'--nobreak--')    #send 5
                    print(f'Error! There are only {noofqnsundertopic} \'{selectedtopic}\' questions in the question pool')
                else:
                    soc.send(b'--break--')  #send 5
                    newnum = str(newnum)
                    break
            soc.send(bytes(newnum,'utf-8')) #send 6

# function to generate management report
def c_report():
    print('Generating Report...')
    time.sleep(2)
    print('Report generated!')
    return

# function to run the program
def adminMainProg(soc):
    while True:
        print('''
==============================
*  Welcome to Admin Program  *
==============================
1) Login
2) Exit program''')
        adminOption = checkOption(2)
        match adminOption:
            case 1:
                soc.send(b'adminlogin')
                cont,currentAdminID = c_adminlogin(soc)
                if cont:
                    while True:
                        print(f'''
Welcome, {currentAdminID}.

Admin Menu
------------
1) Set up question pool
2) Set up settings
3) Management report
4) Logout''')
                        adminOption = checkOption(4)
                        match adminOption:
                            case 1:
                                soc.send(b'editqnpool')
                                c_editqnpool(soc)
                            case 2:
                                soc.send(b'editsettings')
                                c_editsettings(soc)
                            case 3:
                                soc.send(b'report')
                                c_report()
                            case 4:
                                soc.send(b'logout')
                                logout = c_adminlogout(soc,currentAdminID)
                                if logout:
                                    break
            case 2:
                print('OK, Goodbye')
                return

# function to connect to the server
def connectServer():
    host = "127.0.0.1"
    port = 9090
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        soc.connect((host, port))
    except:
        print("Connection Error")
        sys.exit()
    adminMainProg(soc)
    soc.send(b'--quit--')

    

# ******************************* Main program ***********************************
connectServer()