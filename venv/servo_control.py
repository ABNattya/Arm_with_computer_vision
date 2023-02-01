#4444aref  pass for sajed laptob
import cv2
import numpy as np
import pyfirmata
from cvzone.HandTrackingModule import HandDetector

cap = cv2.VideoCapture(0)

ws, hs = 1920,1080

cap.set(3, ws)
cap.set(4, hs)



detector = HandDetector(detectionCon=0.8, maxHands=2)

port = "COM12"
board = pyfirmata.Arduino(port)
base = board.get_pin('d:9:s') #pin 9 Arduino base
shoulder = board.get_pin('d:10:s') #pin 10 Arduino shoulder
elbow = board.get_pin('d:11:s') #pin 11 Arduino elbow
gripper = board.get_pin('d:12:s') #pin 12 Arduino gripper  // 75 open  0 close
pot = board.get_pin('a:0:i') #pin a0 for pot




base.write(90)
shoulder.write(90)
elbow.write(70)
gripper.write(90);

it = pyfirmata.util.Iterator(board)
it.start()

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img,flipType=False)  # With Draw

    potd = pot.read()
    pp = int(np.interp(potd, [0, 1], [1000, 0]))
    p = int(np.interp(pp, [0, 1000], [180, 0]))



    print(p)

    # hands = detector.findHands(img, draw=False)  # No Drawx

    if hands:
        # Hand 1
        hand1 = hands[0]
        lmList1 = hand1["lmList"]  # List of 21 Landmarks points
        bbox1 = hand1["bbox"]  # Bounding Box info x,y,w,h
        centerPoint1 = hand1["center"]  # center of the hand cx,cy
        handType1 = hand1["type"]  # Hand Type Left or Right


        fingers1 = detector.fingersUp(hand1)
        if (fingers1[0]==1 and fingers1[1]==1 and  fingers1[2]==0 and fingers1[3]==0 and fingers1[4]==0 ):#gripper is closed and move shoulder with x-axis and elbow with y-axis by point 0,0

            gripper.write(0) #close gripper
            point=lmList1[8]
            pxshoulder=point[0]
            pyelbow = point[1]
            shoulderD = int(np.interp(pxshoulder, [0, ws-180], [180, 40]))
            elbowD = int(np.interp(pyelbow, [100, hs-300], [180,40]))
            cv2.rectangle(img, (40, 20), (350, 110), (0, 255, 255), cv2.FILLED)
            cv2.putText(img, f'shoulder X: {shoulderD} deg', (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            cv2.putText(img, f'elbow Y: {elbowD} deg', (50, 120), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            shoulder.write(shoulderD)
            elbow.write(elbowD)
            # base.write(p)
            base.write(p)

            print('elbow Motor-angle', elbowD)


        elif(fingers1[0]==0 and fingers1[1]==1 and fingers1[2]==0 and fingers1[3]==0 and fingers1[4]==0):
            gripper.write(75) #open gripper
            point2 = lmList1[8]
            pxshoulder2=point2[0]
            pyelbow2 = point2[1]
            shoulderD2 = int(np.interp(pxshoulder2, [0, ws-180], [180, 40]))
            elbowD2 = int(np.interp(pyelbow2, [100, hs-300], [180,40]))
            cv2.rectangle(img, (40, 20), (350, 110), (0, 255, 255), cv2.FILLED)
            cv2.putText(img, f'shoulder X: {shoulderD2} deg', (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            cv2.putText(img, f'elbow Y: {elbowD2} deg', (100, 150), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            shoulder.write(shoulderD2)
            elbow.write(elbowD2)
            base.write(p)
            print('sholder Motor-angle', shoulderD2 )
            print('elbow Motor-angle', elbowD2)



        elif(fingers1[0]==1 and fingers1[1]==1 and fingers1[2]==1 and fingers1[3]==0 and fingers1[4]==0):
            gripper.write(0) #close gripper
            point3 = lmList1[12]
            pxBase  =point3[0]
            baseD = int(np.interp(pxBase, [0, ws-300], [0, 180]))
            cv2.rectangle(img, (40, 20), (350, 110), (0, 255, 255), cv2.FILLED)
            cv2.putText(img, f'base X: {baseD} deg', (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            base.write(baseD)



        elif(fingers1[0]==0 and fingers1[1]==1 and fingers1[2]==1 and fingers1[3]==0 and fingers1[4]==0):
            gripper.write(75) #open gripper
            point4 = lmList1[12]
            pxBase2 = point4[0]
            baseD = int(np.interp(pxBase2, [0, ws-300], [0, 180]))
            cv2.rectangle(img, (40, 20), (350, 110), (0, 255, 255), cv2.FILLED)
            cv2.putText(img, f'base X: {baseD} deg', (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            base.write(baseD)


        print(fingers1)


    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    if key == ord('q'):
        board.exit()
        it=None
        break





