# iSpy_python

This code is for the [HiLT Lab's](http://hilt.cse.unt.edu) [I Spy Project](http://hilt.cse.unt.edu/ispy.html).

It simulates a game of I Spy between two players, who in this case are both simulated. We currently play using a set of 17 objects and hopefully we will be able to add new objects to the playspace soon. Imagine that player 1 selects the object to be guessed, and player 2 tries to guess the object. Player 2 learns about objects based on collected descriptions, player 1's answers to questions, and features extracted from images of the objects. As the system simulates games, player 2 should get better at asking questions to determine which object player 1 has selected. This will simultaneously increase accuracy and decrease the number of questions asked to identify the object.

A (very) rough description of how the simulation works can be found [here](http://hilt.cse.unt.edu/static/images/projects/ispy/SUREPoster2014.pdf). Another description is [here](http://www.aaai.org/ocs/index.php/WS/AAAIW15/paper/viewFile/10074/10210) if you feel like reading a conference paper. The version from the paper is not automated like the version in this repository and the formulas are different, but the concept and goals are similar.

If you intend to play the game with a NAO robot, you must install some custom modules. You can find the modules and the installation process in the repo: https://github.com/HiLT-ISpy/ispy_robot

Setup:

1. Create a database 'iSpy_features' and upload the dump.sql into it
2. Make sure the settings in the config section of main.py match your database credentials, or use the command line flags -u and -p for your username and password and change the config.py file that's created later. Also check the address for the robot, if you're using one.
3. Create a folder within the repo named 'SVM_model_777'. This is where the image models reside.
4. Make sure you use the -s flag to run setup the first time you run the program. If you're planning on using the image models at any point, either use -i now to set them up or run both -s and -i at a later point. The image models won't work without having prior run setup with them turned on.

Run:
- Execute 'python main.py' from within the ispy_python directory
- Use -h if you want to see all the options for running the program

Dependencies:
- Python Setup Tools
- MySQL server
- mysql-python or pymysql
- opencv
- sklearn
- matplotlib
- numpy
- naoqi (if using the robot)
- speech_recognition (if using the robot)
- SoX (command line tool, needed if using the robot)
