# StudentID:	p2128496
# Name:	        Jerald Yeo
# Class:		DISM/FT/1B/03
# Assessment:	CA2
# 
# Script name:	user.py
# 
# Purpose:	Connect to server to download the quiz questions, and take the quiz
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
#          import time
#          import pickle
#
#
# ****************************** User-defined functions ***************************
from getpass import getpass
import socket
import sys
import time
import pickle

# functions to validate input
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

def checkOption(num):
    while True:
        option = (input('>>>> '))
        try:
            option = int(option)
            if option >= 1 and option <= num:
                break
            else:
                raise Exception
        except:
            print(f'\nError! Please enter option 1 to {num}')
    return option

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

# function to login
def c_userlogin(soc):
    while True:
        inUser_ID = input("Enter User ID (0 to exit): ")
        if inUser_ID == '':
            print('Please enter a user ID!')
        elif inUser_ID == '0':
            soc.send(b'--exit--')   #send 1
            return False, ''
        else:
            while True:
                inPasswd = getpass("Enter password: ")
                if inPasswd == '':
                    print('Please enter a password!')
                else:
                    soc.send(bytes(inUser_ID + ';' + inPasswd,'utf-8')) #send 1
                    loginstatus = soc.recv(1024).decode('utf-8')    #recv 2
                    if loginstatus == '--success--':
                        print('Login success!')
                        return True, inUser_ID
                    elif loginstatus == '--fail--':
                        print('Invalid login!')
                        return False, ''

# function to register user
def c_register(soc):
    while True:
        inNewUser_ID = input('Enter a new user ID to register (0 to exit): ')
        if inNewUser_ID == '':
            print('Please enter a new user ID!')
        elif inNewUser_ID == '0':
            soc.send(b'--exit--')   #send 1   
            return
        else:
            soc.send(bytes(inNewUser_ID,'utf-8'))   #send 1
            registerstatus1 = soc.recv(1024).decode('utf-8') #recv 2
            if registerstatus1 == '--fail--':
                print("This user ID is already in use!")
            elif registerstatus1 == '--success--':
                print('''
****************************************************************
* The password should fulfill these conditions:                *
* - Contain at least one number                                *
* - Contain at least one uppercase and one lowercase character *
* - Contain at least one of these special symbols: !@#$%       *
* - 4 to 20 characters long                                    *
****************************************************************''')
                while True:
                    inNewPasswd = getpass("Enter new password for user: ")
                    if inNewPasswd == '':
                        print("Please enter a password!")
                    else:
                        soc.send(bytes(inNewPasswd,'utf-8'))    #send 3
                        registerstatus2 = soc.recv(1024).decode('utf-8')    #recv 4
                        if registerstatus2 == '--success--':
                            print('Register Success!')
                            return
                        elif registerstatus2 == '--fail--':
                            print('Your password does not follow all of the requirements!')

# function to reset password
def c_resetpasswd(soc):
    while True:
        inUser_ID = input("Please enter your user ID (0 to exit): ")
        if inUser_ID == "":
            print("Please enter your user ID!")
        elif inUser_ID == "0":
            soc.send(b'--exit--')   #send 1
            return
        else:
            soc.send(bytes(inUser_ID,'utf-8'))  #send 1
            resetpasswdstatus = soc.recv(1024).decode('utf-8')  #recv 2
            if resetpasswdstatus == '--success--':
                print('An email has been sent to you. Please click the link in the email to reset your password.')
                time.sleep(2)
                return
            elif resetpasswdstatus == '--fail--':
                print('This user ID does not exist!')

# function to take quiz
def c_takequiz(soc,currentUserID):
    while True:

    ## CHECK IF HAVE ATTEMPTS LEFT ##
        soc.send(bytes(currentUserID,'utf-8'))  #send 0\
        attemptInfo = soc.recv(1024).decode('utf-8') #recv 0.5
        attemptstatus,attemptsAllowed = attemptInfo.split(';')
        if attemptstatus == '--noattempts--':
            print('You have no attempts left for the quiz.')
            return False
        elif attemptstatus == '--continue--':
            pass
        attemptsAllowed = int(attemptsAllowed)
        
        ## DISPLAY QUIZ INFO ##
        settings = pickle.loads(soc.recv(1024)) #recv 1
        noofQuestions,timeLimit,marks = settings
        course_module_assessment = pickle.loads(soc.recv(1024))    #recv 1.5
        course,module,assessment = course_module_assessment
        print(f'''
Course: {course}
Module: {module}
Assessment: {assessment}
--------------------

No. of questions: {noofQuestions}
Marks for each question: {marks}
Total marks: {noofQuestions * marks}
Duration: {timeLimit} minutes

You have {attemptsAllowed} attempts left.''')
        while True:
            startquiz = input("Enter 0 to begin, or e to exit: ")
            if startquiz == 'e':
                soc.send(b'--exit--')   #send 2
                return False
            elif startquiz == '0':
                soc.send(b'--sendqns--')    #send 2
                break
        qnHolder = pickle.loads(soc.recv(5000))    #recv 3 (download question file from server)
        attemptsAllowed -= 1
        questionNo = 1
        ansHolder = []
        ansindexHolder = []
        i = 0
        for j in range(noofQuestions):
            ansHolder.append('')
            ansindexHolder.append('no_ans')

        while True:
            if i != noofQuestions:
                print(f'''
Question {questionNo}:
{qnHolder[i][0]}
a) {qnHolder[i][1]}
b) {qnHolder[i][2]}
c) {qnHolder[i][3]}
d) {qnHolder[i][4]}''')
                text = "Enter N for next question"
                if questionNo != 1:
                    text += ", P for previous question"
                print(text)

                if ansHolder[i] != '':
                        print(f'Saved answer: {ansHolder[i]}')
                answer = checkAnsValid(True,questionNo)

                match answer:
                    case 'a': ansindexHolder[i] = 1
                    case 'b': ansindexHolder[i] = 2
                    case 'c': ansindexHolder[i] = 3
                    case 'd': ansindexHolder[i] = 4

                if ansindexHolder[i] == '':
                    ansindexHolder[i] = 'no_ans'

                if answer == 'p':
                    print('\n')
                    i -= 1
                    questionNo -= 1
                elif answer == 'n':
                    print('\n')
                    i += 1
                    questionNo += 1
                else:
                    ansHolder[i] = answer
                    print('\n')
                    questionNo += 1
                    i += 1
            else:
                break
                

        ## CHANGE ANSWER ##
        printqns = True
        while printqns:
            showanswers = "\nYour answers:\n"
            for i in range(1,noofQuestions+1):
                if ansindexHolder[i-1] != 'no_ans':
                    showanswers += f'''
Question {i}:
{qnHolder[i-1][0]}
Saved answer: {qnHolder[i-1][ansindexHolder[i-1]]}
'''
                else:
                    showanswers += f'''
Question {i}
{qnHolder[i-1][0]}
No saved answer!
'''

            print(showanswers)
            print(f'Enter 0 to submit your answers or [1 to {noofQuestions}] to change your answer')
            while True:
                try:
                    questionNoChanged = int(input('>>>> '))
                    if questionNoChanged < 0 or questionNoChanged > noofQuestions:
                        raise Exception
                    break
                except:
                    print('Error! Question does not exist.')
            if questionNoChanged != 0:
                index_questionNoChanged = questionNoChanged - 1
                print(f'''
Question {questionNoChanged}:
{qnHolder[index_questionNoChanged][0]}
a) {qnHolder[index_questionNoChanged][1]}
b) {qnHolder[index_questionNoChanged][2]}
c) {qnHolder[index_questionNoChanged][3]}
d) {qnHolder[index_questionNoChanged][4]}''')
                if ansHolder[index_questionNoChanged] != '':
                    print(f'Saved answer: {ansHolder[index_questionNoChanged]}')
                else:
                    print('No saved answer!')
                
                answer = checkAnsValid(False,questionNoChanged)
                ansHolder[index_questionNoChanged] = answer

                match answer:
                    case 'a': ansindexHolder[index_questionNoChanged] = 1
                    case 'b': ansindexHolder[index_questionNoChanged] = 2
                    case 'c': ansindexHolder[index_questionNoChanged] = 3
                    case 'd': ansindexHolder[index_questionNoChanged] = 4
                    case '': ansindexHolder[index_questionNoChanged] = 'no_ans'

            elif questionNoChanged == 0 and '' in ansHolder:
                unanswered_qns = ""
                start = 0
                for elem in ansHolder:
                    if elem == '':
                        unanswered_qns += str(ansHolder.index(elem,start) + 1)
                        unanswered_qns += ", "
                    start += 1
                unanswered_qns = unanswered_qns[:-2:]
                msg = f'\nWARNING! You have not answered question(s): {unanswered_qns}\nAre you sure you want to submit? (y/n): '
                submitanswers = checkYorN(msg)
                if submitanswers:
                    printqns = False
                    break
            elif questionNoChanged == 0:
                printqns = False
                break

        ## SEND TO SERVER TO CALCULATE SCORE ##
        soc.send(pickle.dumps(ansHolder))  #send 4
        results = soc.recv(1024).decode('utf-8')    #recv 5
        results = results.split(';')
        score, maxscore, percentage = results
        score = int(score)
        maxscore = int(maxscore)
        percentage = float(percentage)
        print(f'\nYour score is {score}/{maxscore} ({percentage}%).')
        if percentage <= 40:
            print('Poor. You need to work harder')
        elif percentage > 40 and percentage < 80:
            print('Fair. You can do better with more effort')
        elif percentage >= 80:
            print('Good. Well done!')
        
        if attemptsAllowed != 0:
            print(f'\nYou have {attemptsAllowed} attempts left, and you can retake the quiz anytime you want.')
            msg = 'Would you like to retake the quiz? (y/n): '
            if checkYorN(msg):
                soc.send(b'--retakequiz--') #send 5
            else:
                soc.send(b'--exit--')   #send 5
                return
        elif attemptsAllowed == 0:
            print('You have no more attempts for the quiz.')
            soc.send(b'--exit--')   #send 5
            return

# function to view past attempts
def c_viewattempts(soc,currentUserID):
    soc.send(bytes(currentUserID,'utf-8'))  #send 1
    pickleornot = soc.recv(1024).decode('utf-8')   #recv 1.5: determine if pickle/notpickle
    if pickleornot == 'notpickle':
        past_attempts = soc.recv(1024).decode('utf-8')  #recv 2
        if past_attempts == '--exit--':
            print('\nYou have not attempted the quiz yet.')
            return
    elif pickleornot == 'pickle':
        past_attempts = pickle.loads(soc.recv(5000))    #recv 2
    noOfQuestions = float(soc.recv(1024).decode('utf-8'))  #recv 3
    noOfQuestions = int(noOfQuestions)
    i = 1
    print('Listing all past attempts...\n')
    for attempt in past_attempts:
        questionNumber = 1
        print(f'''
-------------------
 Attempt {i}
-------------------''')
        print(f'Date of quiz: {attempt[-1]}')
        attempttxt = ""
        for j in range(noOfQuestions):
            attempttxt += f'''
Question {questionNumber}:
{attempt[0]}
Your answer: {attempt[1]}
'''
            attempt = attempt[2:]
            questionNumber += 1
        print(attempttxt)
        i += 1
        print(f'Total score: {attempt[0]}')
    while True:
        cont = input('Press Enter to continue...')
        if cont == '':
            return

# function to logout
def c_userlogout(soc,currentUserID):
    logout = checkYorN('Are you sure you want to logout? (y/n): ')
    if logout:
        soc.send(b'--logout--') #send 1
        soc.send(bytes(currentUserID,'utf-8'))  #send 2
        print("Logged out.")
        return True
    else:
        soc.send(b'--nologout--')
        soc.send(b'null')
        return False

# function to run the program
def userMainProg(soc):
    while True:
        print('''
************************************
*   Welcome to BetterTutors Quiz   *
************************************
1) Login
2) Register
3) Reset Password
4) Exit program''')
        userOption = checkOption(4)
        match userOption:
            case 1:
                soc.send(b'userlogin')
                cont, currentUserID = c_userlogin(soc) #cont is True or False / login success or fail
                if cont:
                    while True:
                        print(f'''
Welcome, {currentUserID}!

User Menu
-----------
1) Take quiz
2) View attempts
3) Log out''')
                        userOption = checkOption(3)
                        match userOption:
                            case 1:
                                soc.send(b'takequiz')
                                c_takequiz(soc,currentUserID)
                            case 2:
                                soc.send(b'viewattempts')
                                c_viewattempts(soc,currentUserID)
                            case 3:
                                soc.send(b'userlogout')
                                logout = c_userlogout(soc,currentUserID)
                                if logout:
                                    break
                                
            case 2:
                soc.send(b'register')
                c_register(soc)
            case 3:
                soc.send(b'resetpasswd')
                c_resetpasswd(soc)
            case 4:
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
    userMainProg(soc)
    soc.send(b'--quit--')

    

# ******************************* Main program ***********************************
connectServer()