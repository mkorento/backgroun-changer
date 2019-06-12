If (Test-Path .\dist){
    rm .\dist -r -Force;
}
If (Test-Path .\build){
    rm .\build -r -Force;
}

pyinstaller --onedir client.py
mkdir .\dist\client\images;
mkdir .\dist\client\icons;
mkdir .\dist\client\config;
cp .\images\1d6e3da17be1d926443c4f5bd63d342c.jpg .\dist\client\images\;
cp .\config\last_completion.txt .\dist\client\config\;
cp .\config\subreddits.txt .\dist\client\config\;
cp .\config\minimum_width.txt .\dist\client\config\;
cp .\icons\icon_busy.ico .\dist\client\icons;
cp .\icons\icon_ready.ico .\dist\client\icons;
cp .\server.py .\dist\client;
cp .\Start.py .\dist\client;
