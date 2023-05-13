from flask import Flask, render_template, request
import requests
#import nltk
#nltk.download('punkt')
from newspaper import Article
#import textblob
#from textblob import TextBlob
from selenium import webdriver
from selenium.webdriver.common.by import By
from textblob import TextBlob
import time
import os
from negation_words import negation_words
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from collections import defaultdict
from heapq import nlargest


app = Flask(__name__)


corpa_path = os.path.join(os.path.dirname(__file__), 'corpa.txt')
with open(corpa_path, 'r') as f:
    corpa = dict(map(str.strip, line.split('\t')) for line in f)


with open("english_stopwords.txt", "r") as f:
    stop_words = f.read().split()

def calculate_sentiment(text):
    from negation_words import negation_words
    words = text.lower().split()
    new_words = []
    negate = False
    for word in words:
        if word.lower() in negation_words:
            negate = True
        elif negate:
            word = "not " + word
            negate = False
        new_words.append(word)
    new_words = [word for word in new_words if word not in negation_words]
    words = new_words
    words = [word for word in words if word not in stop_words]
    sentiment_score = 0
    for i, word in enumerate(words):
        sentiment_score += int(corpa.get(word, 0))
    num_words = len(words)
    if num_words == 0:
        return 0
    else:
        sentiment = round(sentiment_score/num_words, 2)
        return sentiment
    

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def sentiment_or_reviews():
    if request.method == 'POST':
        radio_value = request.form['radio_button']
        url = request.form['url']

        if radio_value == 'Website blog':
            article = Article(url)
            article.download()
            article.parse()
            text = article.text

            #summarizing starts           
            # Text rank algorithm starts for summarizing
            sentences = sent_tokenize(text)

            # Tokenize the sentences into words
            words = [word_tokenize(sentence.lower()) for sentence in sentences]

            # Remove stop words
            stop_words = set(stopwords.words('english'))
            filtered_words = []
            for sentence in words:
                filtered_words.append([word for word in sentence if word.casefold() not in stop_words])

            # Calculate the word frequency
            word_freq = FreqDist([word for sentence in filtered_words for word in sentence])

            # Calculate the sentence scores using the TextRank algorithm
            rankings = defaultdict(int)
            for i, sentence in enumerate(filtered_words):
                for word in sentence:
                    rankings[i] += word_freq[word]

            # Get the top n sentences as the summary
            n = 3
            summary_text = nlargest(n, rankings, key=rankings.get)
            summary = ' '.join([sentences[i] for i in summary_text])
            # call the function to get the sentiment of the summary
            sentiment = calculate_sentiment(summary)

          
            if sentiment>0:
                overall_sentiment = "Positive Blog"
                print(overall_sentiment)      
            elif sentiment<0:
                overall_sentiment = "Negative Blog"
                print(overall_sentiment)
            else:
                overall_sentiment = "Neutral"
                print(overall_sentiment)      
            return render_template('blog.html', text=text, summary=summary, sentiment=sentiment, overall_sentiment=overall_sentiment)  


        elif radio_value == 'Amazon':
            driver = webdriver.Firefox()
            url= request.form['url']
            
            # Navigate to the Amazon product page
            driver.get(url)

            # Scroll to the bottom of the page repeatedly until all reviews are loaded
            while True:
                # Get the current page height
                current_height = driver.execute_script("return document.body.scrollHeight")

                # Scroll to the bottom of the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait for the page to load
                time.sleep(2)

                # Get the new page height
                new_height = driver.execute_script("return document.body.scrollHeight")

                # If the page height has not increased, all reviews have been loaded
                if new_height == current_height:
                    break

                # Extract all the review elements
                reviews = []
                while True:
                    review_elements = driver.find_elements(By.XPATH, '//div[@data-hook="review"]')

                    # Extract the text of each review element and determine the sentiment                      
                    for review_element in review_elements:
                        review_text = review_element.find_element(By.XPATH, './/span[@data-hook="review-body"]').text
                        
                        review_sentiment = calculate_sentiment(review_text)
                        sentiment_label = "Positive Review" if review_sentiment > 0 else "Negative Review" if review_sentiment < 0 else "Neutral Review"
                        reviews.append((review_text, review_sentiment, sentiment_label))
                    # Click the "Next page" button
                    try:
                        next_button = driver.find_element(By.XPATH, '//a[contains(text(),"Next page")]')
                        next_button.click()

                        # Wait for the page to load
                        time.sleep(2)

                    except:
                        break

                # Close the web driver
                driver.quit()

                # Render the reviews template with the extracted reviews
                return render_template('reviews_amazon.html', reviews=reviews)



        elif radio_value == 'Flipkart':

            driver = webdriver.Firefox()
            url= request.form['url']
            driver.get(url)    

            try:
                close_button = driver.find_element(By.XPATH, '//button[@class="_2KpZ6l _2doB4z"]')
                close_button.click()
                time.sleep(2)
            except:
                pass

    # Scroll to the bottom of the page repeatedly until all reviews are loaded
            while True:
        # Get the current page height
                current_height = driver.execute_script("return document.body.scrollHeight")

        # Scroll to the bottom of the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for the page to load
                time.sleep(2)

        # Get the new page height
                new_height = driver.execute_script("return document.body.scrollHeight")

        # If the page height has not increased, all reviews have been loaded
                if new_height == current_height:
                    break

    # Extract all the review elements
            reviews = []
            while True:
                review_elements = driver.find_elements(By.XPATH, '//div[@class="_1AtVbE col-12-12"]')

        # Extract the text of each review element and determine the sentiment
                for review_element in review_elements:
                    try:
                        review_text = review_element.find_element(By.XPATH, './/div[contains(@class,"t-ZTKy")][1]').text
                        review_sentiment = calculate_sentiment(review_text)
                        sentiment_label = "positive" if review_sentiment > 0 else "negative" if review_sentiment < 0 else "neutral"
                        reviews.append((review_text, review_sentiment, sentiment_label))
                    except:
                        pass

        # Click the "Next page" button
                try:
                    next_button = driver.find_element(By.XPATH, '//span[normalize-space()="Next"]')
                    next_button.click()

            # Wait for the page to load
                    time.sleep(2)

                except:
                    break

    # Close the web driver
            driver.quit()

    # Render the reviews template with the extracted reviews
            return render_template('reviews_flipkart.html', reviews=reviews)
        

    return render_template('form.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True)