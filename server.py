# StudentID:	p2128496
# Name:	        Jerald Yeo
# Class:		DISM/FT/1B/03
# Assessment:	CA2
# 
# Script name:	server.py
# 
# Purpose:	Accept incoming requests from admin and user, replies with necessary data
#           Read and overwrite data files (such as settings and  question pool)
#
# Usage syntax:	Press Fn + F5
# 
# Input file:	C:/PSEC-CA2/adminid_pswd.txt
#               C:/PSEC-CA2/attempt_log.txt
#               C:/PSEC-CA2/question_pool.csv
#               C:/PSEC-CA2/quiz_settings.txt
#               C:/PSEC-CA2/quiz1_topics.txt
#               C:/PSEC-CA2/quiz2_topics.txt
#               C:/PSEC-CA2/userid_pswd.txt
# 
# Output file:	C:/PSEC-CA2/management_report.csv
#               C:/PSEC-CA2/quiz_results.csv
# 
# Python ver:	Python 3.10.0
#
# Modules: from copy import deepcopy
#          import random
#          import socket
#          from threading import Thread
#          import sys
#          from operator import itemgetter
#          import traceback
#          import re
#          import pickle
#          from datetime import date
#          import time
#          import csv
#
# Known issues: Report generator not fully complete
#
# ****************************** User-defined functions ***************************
from copy import deepcopy
import random
import socket
from threading import Thread
import sys
from operator import itemgetter
import traceback
import re
import pickle
from datetime import date
import time
import csv

############# USER ##############

# function to decrypt passwords
def s_decryptPassword(password):
    decryptedPasswd = password[:len(password)-2:]
    return decryptedPasswd

# function to encrypt passwords
def s_encryptPassword(password):
    encryptedPasswd = password + "**"
    return encryptedPasswd

# function to validate user login
def s_userlogin(c):
    inUserInfo = c.recv(1024).decode('utf-8')   #recv 1
    if inUserInfo == '--exit--':
        return
    inUserInfo = inUserInfo.split(';')
    userInfo = s_readUserInfo()
    for i in range(len(userInfo)):
        userInfo[i][1] = s_decryptPassword(userInfo[i][1])
        if inUserInfo[0] == userInfo[i][0] and inUserInfo[1] == userInfo[i][1]:
            print(f'User \'{inUserInfo[0]}\' log in success')
            c.send(b"--success--")  #send 2
            return
    else:
        print(f'User \'{inUserInfo[0]}\' log in fail')
        c.send(b"--fail--") #send 2
        return

# function to read data files
def s_readUserInfo():
    userInfo = []
    f = open("userid_pswd.txt" , "r")
    for line in f:
        y = line.strip().split(';')
        userInfo.append(y)
    f.close()
    return userInfo

# function to validate user register
def s_register(c):
    while True:
        inNewUser_ID = c.recv(1024).decode('utf-8') #recv 1
        if inNewUser_ID == '--exit--':
            return
        userInfo = s_readUserInfo()
        for i in range(len(userInfo)):
            if inNewUser_ID == userInfo[i][0]:
                c.send(b'--fail--') #send 2
                break
            elif inNewUser_ID != userInfo[i][0] and i + 1 == len(userInfo):
                c.send(b'--success--') #send 2
                while True:
                    inNewPasswd = c.recv(1024).decode('utf-8')  #recv 3
                    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%])[A-Za-z\d@$!#%*?&]{6,20}$'
                    # Contain at least one uppercase character
                    # Contain at least one number
                    # Contain at least one of the symbols in '!@#$%'
                    # Consists of 4 to 20 characters which can be any of the characters mentioned above
                    is_valid = bool(re.match(pattern,inNewPasswd))
                    if is_valid:
                        inNewPasswd = s_encryptPassword(inNewPasswd)
                        f = open("userid_pswd.txt","a")
                        if len(userInfo) != 0:
                            f.write('\n')
                        f.write(f'{inNewUser_ID};{inNewPasswd}')
                        print('User register success')
                        c.send(b'--success--')  #send 4
                        return
                    else:
                        print('User register fail (Password does not meet requirements)')
                        c.send(b'--fail--') #send 4

# function to allow user reset password
def s_resetpasswd(c):
    while True:
        inUser_ID = c.recv(1024).decode('utf-8')    #recv 1
        if inUser_ID == '--exit--':
            return
        userInfo = s_readUserInfo()
        for i in range(len(userInfo)):
            if inUser_ID == userInfo[i][0]:
                print('Password reset success')
                c.send(b'--success--') #send 2
                return
            elif inUser_ID != userInfo[i][0] and i + 1 == len(userInfo):
                print('Password reset fail')
                c.send(b'--fail--') #send 2

# function to send quiz information and questions to user
def s_takequiz(c):
    while True:
        qnPool = s_readQuestionPool()
        quiz_settings = s_readQuizSettings()

        assessment = quiz_settings['Assessment Component']
        randomizeQuestions = quiz_settings['Randomize questions']
        noofAttempts = quiz_settings['Number of attempts']
        timeLimit = quiz_settings['Time limit (mins)']
        marks = quiz_settings['Marks for each question']

        if assessment == 'Quiz-1':
            topics = s_readQuiz1Topics()
        elif assessment == 'Quiz-2':
            topics = s_readQuiz2Topics()
        x = list(topics.values())

        noofQuestions = 0
        for elem in x:
            noofQuestions += int(elem)

        ## CHECK IF HAVE ATTEMPTS LEFT 
        accesslog = s_readAccessLog()
        currentUserID = c.recv(1024).decode('utf-8')   #recv 0
        try:
            for user in accesslog:
                if user == currentUserID:
                    attemptsAllowed = accesslog[user]
                    break
            if attemptsAllowed == 0:
                c.send(b'--noattempts--;0')   #send 0.5
                print('User has no more attempts')
                return
            else:
                c.send(bytes('--continue--' + ';' + str(attemptsAllowed),'utf-8')) #send 0.5
        except:
            accesslog[currentUserID] = noofAttempts
            s_overwriteAccessLog(accesslog)
            attemptsAllowed = noofAttempts
            c.send(bytes('--continue--' + ';' + str(attemptsAllowed),'utf-8')) #send 0.5
            user = currentUserID

        ## DISPLAY QUIZ INFO ##
        settings = [noofQuestions,timeLimit,marks]
        heading = qnPool.pop(0)
        course = qnPool[0][0]
        module = qnPool[0][1]
        course_module_assessment = [course,module,assessment]
        c.send(pickle.dumps(settings))  #send 1
        print('Settings sent')
        c.send(pickle.dumps(course_module_assessment)) #send 1.5
        print('Course and module info sent')
        startquiz = c.recv(1024).decode('utf-8')    #recv 2
        if startquiz == '--exit--':
            print('User exit quiz')
            return
        elif startquiz == '--sendqns--':
            print(f'User has {attemptsAllowed} attempts left')

        ## SEPARATING QUESTIONS INTO CATEGORIES (LISTS) 
            qnPool = sorted(qnPool,key=itemgetter(2))
            qnPool.insert(0,heading)
            s_overwriteQnPoolFile(qnPool)
            del(qnPool[0])

            qnsHolder = []
            qn_topicholder = []
            current_topic = ""
            copy = []
            for qn in qnPool:
                if qn[2] != current_topic or qn == qnPool[-1]:
                    if len(qn_topicholder) != 0:
                        if qn == qnPool[-1]:
                            qn_topicholder.append(qn)
                        copy = deepcopy(qn_topicholder)
                        qnsHolder.append(copy)
                    
                    qn_topicholder.clear()
                    qn_topicholder.append(qn[2])
                    qn_topicholder.append(qn)
                    current_topic = qn[2]
                else:
                    qn_topicholder.append(qn)

            temp_qnHolder = []
            qnHolder = []
  
            for topic in topics.keys():
                for i in range(len(qnsHolder)):
                    if topic == qnsHolder[i][0]:
                        del(qnsHolder[i][0])
                        if randomizeQuestions == 'True':
                            random.shuffle(qnsHolder[i])
                        for k in range(topics[topic]):
                            temp_qnHolder.append(qnsHolder[i][k])
            if randomizeQuestions == 'True':
                random.shuffle(temp_qnHolder)
            
            ## APPLY SETTINGS
            topicHolder = []
            for qn in temp_qnHolder:
                topicHolder.append(qn[2])
            ## SETTING UP QUESTIONS TO DISPLAY
            for i in range(noofQuestions):
                temp_qnHolder[i] = temp_qnHolder[i][3:]
                qnHolder.append(temp_qnHolder[i])

            today = date.today()
            quiz_date = today.strftime("%d/%m/%Y")
            quiz_time = time.strftime('%H:%M')
            c.send(pickle.dumps(qnHolder))   #send 3
            print('User taking quiz')
            correctansHolder = []
            for qn in qnHolder:
                correctansHolder.append(qn[5])
            accesslog[user] -= 1
            s_overwriteAccessLog(accesslog)

        ## CALCULATE SCORE ##
        ansHolder = pickle.loads(c.recv(1024))  #recv 4
        print('Answers sent to server')

        maxscore = noofQuestions * marks
        score = 0
        for i in range(noofQuestions):
            if ansHolder[i] == correctansHolder[i]:
                score += marks
        percentage = round((score/maxscore) * 100, 1)
        c.send(bytes(f'{str(score)};{str(maxscore)};{str(percentage)}','utf-8'))    #send 5
        print('Score sent to client')

        ## PUT QUIZ RESULTS IN CSV FILE
        quizResults = s_readQuizResultsFile()
        if len(quizResults) == 0:
            headings = []
            headings.append('User')
            headings.append('Course')
            headings.append('Module')
            headings.append('Assessment Component')
            for i in range(1,len(qnHolder)+1):
                headings.append('Topic')
                headings.append(f'Question {i}')
                headings.append('Answer')
                headings.append('User Answer')
            headings.append('User total score')
            headings.append('Quiz Date')
            headingstxt = ""
            for heading in headings:
                headingstxt += f"{heading},"
            headingstxt = headingstxt[:-1]
            f = open("quiz_results.csv","a")
            f.write(headingstxt)
            f.close()

        userResults = []
        userResults.append(currentUserID)
        userResults.append(course)
        userResults.append(module)
        userResults.append(assessment)
        for i in range(len(qnHolder)):
            userResults.append(topicHolder[i])
            userResults.append(qnHolder[i][0])
            userResults.append(correctansHolder[i])
            userResults.append(ansHolder[i])
        userResults.append(score)
        userResults.append(f'{quiz_date} {quiz_time}')

        s_overwriteQuizResultsFile(userResults)

        action = c.recv(1024).decode('utf-8')   #recv 5
        if action == '--retakequiz--':
            pass
        elif action == '--exit--':
            print('User exit quiz')
            return

# function to send past attempts to user
def s_viewattempts(c):
    currentUserID = c.recv(1024).decode('utf-8')    #recv 1
    quizResults = s_readQuizResultsFile()
    if len(quizResults) == 0:
        c.send(b'notpickle')#send 1.5
        c.send(b'--exit--') #send 2
        return
    else:
        del(quizResults[0])
        past_attempts = []
        user_not_found = True
        for userResults in quizResults:
            if userResults[0] == currentUserID:
                ## removing user, course, module, assessment component, score, date and time
                questions_userResults = userResults[4:-2]

                ## removing topics
                for i in range(0,len(questions_userResults),4):
                    questions_userResults[i] = 'topic'
                try:
                    while True:
                        questions_userResults.remove('topic')
                except ValueError:
                    pass

                ## removing correct answers
                for i in range(1,len(questions_userResults),3):
                    questions_userResults[i] = 'correctans'
                try:
                    while True:
                        questions_userResults.remove('correctans')
                except ValueError:
                    pass
                noOfQuestions = str(len(questions_userResults) / 2)
                questions_userResults.extend(userResults[-2:])

                ## questions_userResults consist of question, user answer, score and date/time
                past_attempts.append(questions_userResults)

                user_not_found = False
        if user_not_found:
            c.send(b'notpickle')#send 1.5
            c.send(b'--exit--') #send 2
            return
        else:
            c.send(b'pickle')#send 1.5
            c.send(pickle.dumps(past_attempts)) #send 2
            c.send(bytes(noOfQuestions,'utf-8'))    #send 3
        return

# function to allow user logout
def s_userlogout(soc):
    logout = soc.recv(1024).decode()    #recv 1
    currentUserID = soc.recv(1024).decode() #recv 2
    if logout == '--logout--':
        print(f'User \'{currentUserID}\' logged out')
    elif logout == '--nologout--':
        pass

############# ADMIN ##############

# function to validate admin login
def s_adminlogin(c):
    inAdminInfo = c.recv(1024).decode('utf-8')
    if inAdminInfo == '--exit--':
        return
    inAdminInfo = inAdminInfo.split(';')
    adminInfo = s_readAdminInfo()
    for i in range(len(adminInfo)):
        adminInfo[i][1] = s_decryptPassword(adminInfo[i][1])
        if inAdminInfo[0] == adminInfo[i][0] and inAdminInfo[1] == adminInfo[i][1]:
            print(f'Admin \'{inAdminInfo[0]}\' log in success')
            c.send(b"--success--")
            return
    else:
        print(f'Admin \'{inAdminInfo[0]}\' log in fail')
        c.send(b"--fail--")
        return

# functions to read data files
def s_readAdminInfo():
    adminInfo = []
    f = open("adminid_pswd.txt" , "r")
    for line in f:
        y = line.strip().split(';')
        adminInfo.append(y)
    f.close()
    return adminInfo

def s_readQuizSettings():
    settings = {}
    f = open('quiz_settings.txt','r')
    for line in f:
        key, value = line.strip().split(';')
        if value.isnumeric():
            value = int(value)
        settings[key] = value
    f.close()
    return settings

def s_readAccessLog():
    accessLog = {}
    f = open('attempt_log.txt','r')
    for line in f:
        key, value = line.strip().split(';')
        if value.isnumeric():
            value = int(value)
        accessLog[key] = value
    f.close()
    return accessLog

def s_readQuizResultsFile():
    quizResults = []
    f = open("quiz_results.csv" , "r")
    for line in f:
        y = line.strip().split(',')
        quizResults.append(y)
    f.close()
    return quizResults

def s_readQuestionPool():
    qnList = []
    f = open("question_pool.csv" , "r")
    for line in f:
        y = line.strip().split(',')
        qnList.append(y)
    f.close()
    return qnList

def s_readQuiz1Topics():
    topics = {}
    f = open('quiz1_topics.txt','r')
    for line in f:
        key, value = line.strip().split(';')
        if value.isnumeric():
            value = int(value)
        topics[key] = value
    f.close()
    topics = sorted(topics.items(),key=lambda x: x[1],reverse=True)
    topics = {key: value for key,value in topics}
    s_overwriteQuiz1TopicsFile(topics)
    return topics

def s_readQuiz2Topics():
    topics = {}
    f = open('quiz2_topics.txt','r')
    for line in f:
        key, value = line.strip().split(';')
        if value.isnumeric():
            value = int(value)
        topics[key] = value
    f.close()
    topics = sorted(topics.items(),key=lambda x: x[1],reverse=True)
    topics = {key: value for key,value in topics}
    s_overwriteQuiz2TopicsFile(topics)
    return topics

# function to overwrite data files
def s_overwriteSettingsFile(settings):
    settingstxt = ""
    for key,value in settings.items():  
        if settingstxt != "":
            settingstxt += '\n'
        settingstxt += f'{key};{value}'
    f = open('quiz_settings.txt','w')
    f.write(settingstxt)
    f.close()

def s_overwriteQnPoolFile(qnPool):
    questionstxt = ""
    for qn in qnPool:  
        if questionstxt != "":
            questionstxt += '\n'
        questionstxt += f'{qn[0]},{qn[1]},{qn[2]},{qn[3]},{qn[4]},{qn[5]},{qn[6]},{qn[7]},{qn[8]}'
    f = open("question_pool.csv","w")
    f.write(questionstxt)
    f.close()

def s_overwriteAccessLog(accessLog):
    accesslogtxt = ""
    for key,value in accessLog.items():  
        if accesslogtxt != "":
            accesslogtxt += '\n'
        accesslogtxt += f'{key};{value}'
    f = open('attempt_log.txt','w')
    f.write(accesslogtxt)
    f.close()

def s_overwriteQuizResultsFile(userResults):
    userresultstxt = "\n"
    for elem in userResults:
        userresultstxt += f"{elem},"
    userresultstxt = userresultstxt[:-1]
    f = open("quiz_results.csv","a")
    f.write(userresultstxt)
    f.close()

def s_overwriteQuiz1TopicsFile(topics):
    topicstxt = ""
    topics = sorted(topics.items(),key=lambda x: x[1],reverse=True)
    for topic in topics:  
        if topicstxt != "":
            topicstxt += '\n'
        topicstxt += f'{topic[0]};{topic[1]}'
    f = open('quiz1_topics.txt','w')
    f.write(topicstxt)
    f.close()

def s_overwriteQuiz2TopicsFile(topics):
    topicstxt = ""
    topics = sorted(topics.items(),key=lambda x: x[1],reverse=True)
    for topic in topics:  
        if topicstxt != "":
            topicstxt += '\n'
        topicstxt += f'{topic[0]};{topic[1]}'
    f = open('quiz2_topics.txt','w')
    f.write(topicstxt)
    f.close()

# function to edit question pool
def s_editqnpool(c):
    print('Admin editing question pool')
    while True:
        qnPool = s_readQuestionPool()
        del(qnPool[0])
        for qn in qnPool:
            for i in range(3):
                del(qn[0])
        c.send(pickle.dumps(qnPool))    #send 1
        adminOption = c.recv(1024).decode('utf-8')  #recv 2
        if adminOption == '--editqn--':
            s_editqn(c)
        elif adminOption == '--addqn--':
            s_addqn(c)
        elif adminOption == '--deleteqn--':
            s_deleteqn(c)
        elif adminOption == '--exit--':
            print('Admin exit question pool edit')
            return

# function to edit question information
def s_editqn(c):
    while True:
        question_no = c.recv(1024).decode('utf-8')  #recv 1
        if question_no == '--exit--':
            return
        else:
            question_no = int(question_no)
            while True:
                qnPool = s_readQuestionPool()
                topic = qnPool[question_no][2]
                c.send(bytes(topic,'utf-8'))    #send 1.5
                question = qnPool[question_no][3:]
                c.send(pickle.dumps(question))  #send 2

                adminOption = c.recv(1024).decode('utf-8')  #recv 3
                if adminOption == '--editqntopic--':
                    s_editqntopic(c,question_no,qnPool)
                if adminOption == '--editqndesc--':
                    s_editqndesc(c,question_no,qnPool)
                elif adminOption == '--editqnans--':
                    s_editqnans(c,question_no,qnPool)
                elif adminOption == '--exit--':
                    return

# function to edit question information - topic 
def s_editqntopic(c,question_no,qnPool):
    present_topics = []
    for qn in qnPool[1:]:
        if qn[2] not in present_topics:
            present_topics.append(qn[2])
    c.send(pickle.dumps(present_topics))    #send 1
    topic = c.recv(1024).decode('utf-8')    #recv 2
    if topic == '--exit--':
        return
    else:
        qnPool[question_no][2] = topic
        s_overwriteQnPoolFile(qnPool)
        
        print(f'Question {question_no} topic changed')
        return

# function to edit question information - description
def s_editqndesc(c,question_no,qnPool):
    newQnDesc = c.recv(1024).decode('utf-8')    #recv 1
    qnPool[question_no][3] = newQnDesc
    s_overwriteQnPoolFile(qnPool)
    print(f'Question {question_no} description changed')
    return

# function to edit question information - answers
def s_editqnans(c,question_no,qnPool):
    answers = pickle.loads(c.recv(1024))    #recv 1
    newAnswerA,newAnswerB,newAnswerC,newAnswerD,newAnswerCorr = answers
    qnPool[question_no][4] =  newAnswerA
    qnPool[question_no][5] =  newAnswerB
    qnPool[question_no][6] =  newAnswerC
    qnPool[question_no][7] =  newAnswerD
    qnPool[question_no][8] = newAnswerCorr
    s_overwriteQnPoolFile(qnPool)
    print(f'Question {question_no} answers changed')
    return

# function to add question to question pool
def s_addqn(c):
    action = c.recv(1024).decode('utf-8')   #recv 1
    if action == '--exit--':
        return
    elif action == '--continue--':
        pass
    qnPool = s_readQuestionPool()
    present_topics = []
    for qn in qnPool[1:]:
        if qn[2] not in present_topics:
            present_topics.append(qn[2])
    c.send(pickle.dumps(present_topics))    #send 2
    newQn = pickle.loads(c.recv(1024))  #recv 3
    question = ['DISM','PSEC']
    for elem in newQn:
        question.append(elem)
    qnPool.append(question)
    s_overwriteQnPoolFile(qnPool)


    print('Question added')
    return

# function to delete question from question pool
def s_deleteqn(c):
    qnPool = s_readQuestionPool()
    question_no = c.recv(1024).decode('utf-8')  #recv 1
    if question_no == '--exit--':
        return
    else:
        question_no = int(question_no)
        del qnPool[question_no]
        s_overwriteQnPoolFile(qnPool)
        print(f'Question {question_no} deleted')

# function to edit settings / topics for quiz
def s_editsettings(c):
    print('Admin editing settings')
    while True:
        adminOption = c.recv(1024).decode('utf-8')
        if adminOption == '--quizsettings--':
            s_quizsettings(c)
        elif adminOption == '--quiztopics--':
            s_quiztopics(c)
        elif adminOption == '--exit--':
            print('Admin exit settings edit')
            return

# function to edit quiz settings
def s_quizsettings(c):
    while True:
        settings = s_readQuizSettings()
        c.send(pickle.dumps(settings))  #send 1
        adminOption = c.recv(1024).decode('utf-8')
        if adminOption == '--assessmentcomponent--':
            s_assessmentcomponent(settings,c)
        elif adminOption == '--randomize--':
            s_randomize(settings,c)
        elif adminOption == '--attempts--':
            s_attempts(settings,c)
        elif adminOption == '--timelimit--':
            s_timelimit(settings,c)
        elif adminOption == '--marks--':
            s_marks(settings,c)
        elif adminOption == '--exit--':
            return
        s_overwriteSettingsFile(settings)

# function to edit quiz settings - assessment
def s_assessmentcomponent(settings,c):
    newsetting = c.recv(1024).decode('utf-8')   #recv 1
    settings['Assessment Component'] = newsetting
    return

# function to edit quiz settings - randomize
def s_randomize(settings,c):
    newsetting = c.recv(1024).decode('utf-8')   #recv 1
    if newsetting == "True":
        newsetting = True
    elif newsetting == "False":
        newsetting = False
    settings['Randomize questions'] = newsetting
    return

# function to edit quiz settings - attempts
def s_attempts(settings,c):
    newsetting = c.recv(1024).decode('utf-8')
    settings['Number of attempts'] = int(newsetting)

# function to edit quiz settings - time limit
def s_timelimit(settings,c):
    newsetting = c.recv(1024).decode('utf-8')
    settings['Time limit (mins)'] = int(newsetting)

# function to edit quiz settings - marks
def s_marks(settings,c):
    newsetting = c.recv(1024).decode('utf-8')
    settings['Marks for each question'] = int(newsetting)

# function to edit quiz topics (quiz 1 / 2)
def s_quiztopics(c):
    while True:
        adminOption = c.recv(1024).decode('utf-8')  #recv 1
        if adminOption == '--quiz1topics--':
            s_quiz1topics(c)
        elif adminOption == '--quiz2topics--':
            s_quiz2topics(c)
        elif adminOption == '--exit--':
            return

# functions to change number of questions from topics for individual quiz
def s_quiz1topics(c):
    while True:
        topics = s_readQuiz1Topics()
        c.send(pickle.dumps(topics))    #send 1
        action = c.recv(1024).decode('utf-8')   #recv 2
        if action == '--exit--':
            return
        elif action == '--continue--':
            pass
        qnPool = s_readQuestionPool()
        selectedtopic = c.recv(1024).decode('utf-8')  #recv 3
        while True:
            counter = 0
            for qn in qnPool:
                if qn[2] == selectedtopic:
                    counter += 1
            c.send(bytes(str(counter),'utf-8')) #send 4
            action = c.recv(1024).decode('utf-8')   #recv 5
            if action == '--break--':
                break
            else:
                pass
    
        newnum = c.recv(1024).decode('utf-8')   #recv 6
        newnum = int(newnum)
        topics[selectedtopic] = newnum
        s_overwriteQuiz1TopicsFile(topics)

def s_quiz2topics(c):
    while True:
        topics = s_readQuiz2Topics()
        c.send(pickle.dumps(topics))    #send 1
        action = c.recv(1024).decode('utf-8')   #recv 2
        if action == '--exit--':
            return
        elif action == '--continue--':
            pass
        qnPool = s_readQuestionPool()
        selectedtopic = c.recv(1024).decode('utf-8')  #recv 3
        while True:
            counter = 0
            for qn in qnPool:
                if qn[2] == selectedtopic:
                    counter += 1
            c.send(bytes(str(counter),'utf-8')) #send 4
            action = c.recv(1024).decode('utf-8')   #recv 5
            if action == '--break--':
                break
            else:
                pass
    
        newnum = c.recv(1024).decode('utf-8')   #recv 6
        newnum = int(newnum)
        topics[selectedtopic] = newnum
        s_overwriteQuiz2TopicsFile(topics)

# function to generate management report
def s_report():
    settings = s_readQuizSettings()
    qnPool = s_readQuestionPool()
    quizResults = s_readQuizResultsFile()
    del(qnPool[0])
    del(quizResults[0])
    assessment = settings['Assessment Component']
    if assessment == 'Quiz-1':
        topics = s_readQuiz1Topics()
    elif assessment == 'Quiz-2':
        topics = s_readQuiz2Topics()
    topicsinquiz = []
    for key in topics.keys():
        if topics[key] != 0:
            topicsinquiz.append(key)
    topicsinquiztxt = ""
    for topic in topicsinquiz:
        topicsinquiztxt += f'{topic}, '
    topicsinquiztxt = topicsinquiztxt[:-2]

    with open('management_report.csv','w',newline='') as f:
        blankrow = []
        writer = csv.writer(f)
        today = date.today()
        currentdate = today.strftime("%d/%m/%Y")
        writer.writerows(
[['','Quizzes','From: dd/mm/yy','','To: dd/mm/yy'],
['BetterTutors Pte Ltd','','','','','',f'Date: {currentdate}'],
['Course Name: DISM','','','','','','Module Name: PSEC']])
        writer.writerow(blankrow)
        writer.writerows(
[[f'Assessment: {assessment}','','','','','','Date of quiz: dd/mm/yyyy,hh:mm:ss'],
[f'Topics: {topicsinquiztxt}']])
        qnnum = 1
        for qn in qnPool:
            writer.writerows(
[[f'{qnnum}) {qn[3]}','a) '+qn[4],'','','b) '+qn[5]],
[f'Correct answer: {qn[8]}','c) '+qn[6],'','','d) '+qn[7]]])
            writer.writerow(blankrow)
            qnnum += 1
        
        questions = [n for n in range(1,len(qnPool)+1)]
        a = ['','','','','','','','Questions']
        a.extend(questions)
        a.append('Score')
        writer.writerow(a)

        quiz1_userResults = []
        for userResults in quizResults:
            if userResults[3] == assessment:
                quiz1_userResults.append(userResults)

        for i in range(len(quiz1_userResults)):
            username = quiz1_userResults[i][0]
            writer.writerow(['','','','','','',username,'','answer','answer','answer','answer','answer','answer','answer','answer','answer','answer','answer','answer','answer','answer','answer',quiz1_userResults[i][-2],f'Date of completion: {quiz1_userResults[i][-1]}'])

# function to start a thread for client connection
def clientThread(c, ip, port):
    loop = True
    while loop:
        receive = c.recv(1024).decode('utf-8')
        match receive:
            # USER MENU 1 #
            case 'userlogin': 
                s_userlogin(c)
            case 'register':
                s_register(c)
            case 'resetpasswd':
                s_resetpasswd(c)

            # USER MENU 2 #
            case 'takequiz':
                s_takequiz(c)
            case 'viewattempts':
                s_viewattempts(c)       

            # ADMIN MENU 1 #
            case 'adminlogin':
                s_adminlogin(c)

            # ADMIN MENU 2 #
            case 'editqnpool':
                s_editqnpool(c)      
            case 'editsettings':
                s_editsettings(c)       
            case 'report':
                s_report()             

            # USER + ADMIN LOGOUT / EXIT PROGRAM #
            case 'userlogout':
                s_userlogout(c)

            case '--quit--':
                c.close()
                print(f'Connection at port {port} closed')
                loop = False

# function to boot up the server
def start_server():
    host = "127.0.0.1"
    port = 9090
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created")
    try:
        serversocket.bind((host,port))
    except:
        print("Bind failed. Error: " + str(sys.exc_info()))
        sys.exit()

    serversocket.listen(5)
    print("Server is listening...")

    while True:
        c , address = serversocket.accept()
        ip, port = str(address[0]), str(address[1])
        print("Connected with " + ip + ":" + port)
        ##### after this point client is connected to server #####
        try:
            Thread(target=clientThread, args=(c, ip, port)).start()
        except:
            print("Thread did not start.")
            traceback.print_exc()
            serversocket.close()


# ******************************* Main program ***********************************
start_server()