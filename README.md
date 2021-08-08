# VoiceEmoji
Speech based emoji entry 👄🗣

This is the code repo for the CHI 2021 paper [Voicemoji: Emoji Entry Using Voice for Visually Impaired People](https://drustz.com/assets/pdfs/voicemoji.pdf)

![teaser](https://user-images.githubusercontent.com/8768646/110891967-00889600-82a8-11eb-9221-7670f1db0668.png)

[Demo video](https://www.bilibili.com/video/BV1My4y1J7oN)

## Prerequisites
Please refer to the file `requirements.txt`

## Code Structure
The `*.py` files are for the backend server. The project uses [Tornado](http://www.tornadoweb.org/) to host the website as well as to process the speech requests.
```
project
│   server.py (the main server entry)
|   Recognizer.py (speech recognition with Google api)
│   TextProcessor.py (search emojis realted to the spoken content using google search api)
│   CHNTextProcessor.py (same as TextProcessor.py, but for Chinese)
```

The `main.js` contains the webinterface logic. It uses websocket to communicate with the backend for the chat feature. Other features are commented in the file.

## Deploy
### Apply for your own Google Cloud API for speech recognition and translation (optional)
Voicemoji uses google api for [speech recognition](https://cloud.google.com/speech-to-text) and [translation](https://cloud.google.com/translate) for Chinese. 
You may apply for your own api key and store the api json file in the folder.

### Apply for Google Search API
To search emojis based on the spoken content, you need to apply for a [google custom search api](https://developers.google.com/custom-search/v1/overview) and 
replace the corresponding url (`gsearchURL`) in `TextProcessor.py`.

### Create a HTTPS certificate for the website
If you want to deploy the website, you must apply for a HTTPS cert, as voice data transfer is restricted only in HTTPS mode. You can use services such as [Let's Encrypt](https://letsencrypt.org/)
to get a free certificate. Once done, create a folder `certs` and put the necessary cert files `.crt` and `.key`, which are used in `server.py`.

#Commands to run
Use `python -W ignore server.py` to run the server. Then you can navigate to `https://localhost:443` to see if the website is up.

## Citation
If you use the code in your paper, then please cite it as:

```
@inbook{10.1145/3411764.3445338,
author = {Zhang, Mingrui Ray and Wang, Ruolin and Xu, Xuhai and Li, Qisheng and Sharif, Ather and Wobbrock, Jacob O.},
title = {Voicemoji: Emoji Entry Using Voice for Visually Impaired People},
year = {2021},
isbn = {9781450380966},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3411764.3445338},
booktitle = {Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems},
articleno = {37},
numpages = {18}
}
```
