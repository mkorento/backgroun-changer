#Wallpaper changer for Windows 10

The program downloads the top-25 images from the subreddits in subreddits.txt
once a day. Default download starting time is 16:00.  Add time.txt file to
config directory containing seconds since midnight to set a different starting
time.

Build and runtime dependencies:
===============================
        $ pip install pyinstaller
        $ pip install requests
        $ pip install pypiwin32
        $ .\build.ps1

Start the program by running Start.py in dist/client/

Icons made by [Amit Jakhu](http://www.flaticon.com/authors/amit-jakhu) from [http://www.flaticon.com](www.flaticon.com) are licensed by [CC BY 3.0](http://creativecommons.org/licenses/by/3.0/)

#License
MIT
