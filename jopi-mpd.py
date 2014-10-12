#!/usr/bin/python

from time import sleep, localtime, strftime
import Adafruit_CharLCD as LCD
from cleaner import cleanString
import sys
import subprocess
import threading
import os
import re
import logging

welcomeText = "Welcome on jopi-mpd!"
musicAbsPath = "/var/lib/mpd/music/"
playlistRelPath = "WEBRADIO/"
stopFile = "/var/lock/stop-jopi-mpd"

class TextScroller:
	text = ''
	position = 0
	textLength = 0
	step = 0

	playPos = -1
	playAnimPos = 0

	def scroll(self):
		nextPos = self.position + self.step
		if nextPos < 0 or nextPos >= self.textLength - 16:
			self.step *= -1
		else:
			self.position = nextPos

		if self.playAnimPos + 1 >= self.playPos:
			self.playAnimPos = 0
		else:
			self.playAnimPos = self.playAnimPos + 1

		self.display()

	def setText(self, newText):
		self.text = newText
		self.textLength = len(newText)
		self.position = 0
		if self.textLength <= 16:
			# Text is small enough => deactivate scrolling
			self.step = 0
		else:
			# 1 means left to right
			self.step = 1

	def setPlayPos(self, newPos):
		self.playPos = newPos
		if self.playAnimPos >= newPos:
			self.playAnimPos = newPos - 1
			if self.playAnimPos < 0:
				self.playAnimPos = 0

	def display(self):
		global lcd
		topStart = self.position
		topEnd = topStart + 16
		top = cleanString(self.text[topStart:topEnd])
		fullArt = "~~~~~~~~~~~~~~~~"
		bottom = "                "

		if self.playPos < 0:
			bottom = fullArt
		else:
			bottom = bottom[:self.playAnimPos] + fullArt[self.playAnimPos] + bottom[self.playAnimPos+1:]
			bottom = bottom[:self.playPos] + ">" + bottom[self.playPos+1:]

		fmtText = top + "\n" + bottom
		lcd.clear()
		lcd.message(fmtText)

scroller = TextScroller()

# Initialize the LCD plate. Should auto-detect correct I2C bus. If not,
# pass '0' for early 256 MB Model B boards or '1' for all later versions
lcd = LCD.Adafruit_CharLCDPlate()

def display(text):
	fmtText = cleanString(text[:16] + "\n" + text[16:])
	lcd.clear()
	lcd.message(fmtText)

# Clear display and show greeting, pause 1 sec
display(welcomeText)
sleep(3)

state = "play"

# Use subprocess.check_output to get list of playlists (mpc lsplaylists)
lists = ["no-list"]
currentList = 0
fileListIdx = -1
previousSong = ""

# Buttons
buttons = (LCD.SELECT, LCD.LEFT, LCD.UP, LCD.DOWN, LCD.RIGHT)
curPressed = -1

# Colors
colors = ((1,0,0) , (1,1,0), (0,1,0), (0,0,1))
curColor = 0

showingTime = False

def fetchLists():
	global lists, fileListIdx, musicAbsPath, playlistRelPath
	lists = subprocess.check_output(["mpc", "lsplaylists"]).splitlines()
	fileListIdx = len(lists)
	lists.extend(os.listdir(musicAbsPath + playlistRelPath))

fetchLists()

def buttonPressed(i):
	global state
	if state == "menu":
		buttonPressedMenu(i)
	else:
		buttonPressedPlayback(i)

def changeColor():
	global curColor
	curColor += 1
	curColor %= len(colors)
	lcd.set_backlight(colors[curColor])

def buttonPressedMenu(i):
	global state, currentList, lists, showingTime
	if i == 0:
		state = "play"
		refreshModePlaying(True)
	elif i == 1:
		# prev list
                if currentList == 0:
                        currentList = len(lists) - 1
                else:
                        currentList -= 1
                refreshModeList()
	elif i == 2:
		showingTime = not showingTime
		if not showingTime:
			refreshModeList()
	elif i == 3:
		# play list
                subprocess.call(["mpc", "clear"])
		if currentList < fileListIdx:
	                subprocess.call(["mpc", "load", lists[currentList]])
		else:
			subprocess.call(["mpc", "load", playlistRelPath + lists[currentList]])
                subprocess.call(["mpc", "play"])
                state = "play"
		refreshModePlaying(True)
	elif i == 4:
		# next list
                currentList += 1
                if currentList == len(lists):
                        currentList = 0
                refreshModeList()

def buttonPressedPlayback(i):
	global state, showingTime
	if i == 0:
		fetchLists()
		refreshModeList()
		state = "menu"
	elif i == 1:
		subprocess.call(["mpc", "prev"])
	elif i == 2:
		showingTime = not showingTime
		refreshModePlaying(True)
	elif i == 3:
		subprocess.call(["mpc", "toggle"])
	elif i == 4:
		subprocess.call(["mpc", "next"])


def refreshModeList():
	global lists, currentList, scroller
	scroller.setText(lists[currentList])


def refreshModePlaying(forceSetText=False):
	global previousSong, scroller
	statusLines = subprocess.check_output(["mpc"]).split('\n')
	curSong = statusLines[0]
	pct = -1
	if len(statusLines) > 2:
		search = re.search('\\((\\d+)%', statusLines[1])
		if search:
			pct = int(0.16 * int(search.group(1)))
	scroller.setPlayPos(pct)
	if previousSong != curSong:
		previousSong = curSong
		changeColor()
		if curSong == "":
			scroller.setText("No song selected")
		else:
			scroller.setText(curSong)
	elif forceSetText:
		scroller.setText(curSong)


def refreshModeTime():
	scroller.setText(strftime("%a, %d %b %Y %H:%M:%S", localtime()))

def checkRun():
	global stopFile
	try:
		with open(stopFile):
			return False
	except IOError:
		return True

class DisplayThread(threading.Thread):
	def run (self):
		dispError = False
		while True:
			try:
				global state, showingTime, scroller
				if checkRun() == False:
					break
				if showingTime:
					refreshModeTime()
				elif state == "play":
					refreshModePlaying()
				scroller.scroll()
				sleep(.9)
				dispError = False
		        except Exception, err:
				if dispError == False:
					logging.exception('')
					dispError = True
				else:
					sleep(1)

print "To stop jopi-mpd from outside just do a"
print "'touch %s', without quotes." % stopFile
if os.path.exists(stopFile):
	os.remove(stopFile)

DisplayThread().start()

globError = False
while True:
	try:
		if checkRun() == False:
			break
		sleep(.1)
		nothingPressed = True
		for i in range(5):
			if lcd.is_pressed(buttons[i]):
				nothingPressed = False
				if i != curPressed:
					buttonPressed(i)
					curPressed = i
					break
		if nothingPressed:
			curPressed = -1
		globError = False
	except Exception, err:
		if globError == False:
			logging.exception('')
			globError = True
		else:
			sleep(1)

display("Goodbye!")

print "Goodbye"
sleep(5)
lcd.set_backlight(0)

