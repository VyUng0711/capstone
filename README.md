# Capstone

To run this project, 

Step 1: 
- Download Google pre-trained word2vec model from `https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit`
- Look for the file `config.py` inside the repo and assign `MODEL = ` the path to the model you just downloaded.

Step 2:
- Get the set of English word from `https://drive.google.com/drive/u/1/my-drive?ogsrc=32`
- If you cannot access the file, you can also get this from the nltk library. Use the follow code to pickle the set.
`PATH_TO_ENGLISH_VOCAB` is the path to where you like to store this in your computer
    ```
    from nltk.corpus import words
    pickle.dump(set(words.words()), open(PATH_TO_ENGLISH_VOCAB, "wb"))
    ```
    
- Look for the file `config.py` and assign `ENGLISH_VOCAB = ` the path to english vocab. 

Step 3:
Open terminal, navigate to the repo, and run: `python3 app.py`