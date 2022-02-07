import requests
import os
import math
from dotenv import load_dotenv
from summarizer import generate_summary
from auth import attempt_authorization

#TODO rework auth.py flow, properly print to file, properly format summary tweet(s)

load_dotenv()

bearer_token = os.getenv("BEARER_TOKEN")
user_id = os.getenv("USER_ID")
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")


def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2UserMentionsPython"
    return r


def connect_and_send_request(verb, url, params):
    response = requests.request(verb, url, auth=bearer_oauth, params=params)
    if response.status_code != 200:
        print(response.status_code)
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


def get_mentions():
    url = "https://api.twitter.com/2/users/{}/mentions".format(user_id)
    return connect_and_send_request("GET", url, {"tweet.fields": "conversation_id,referenced_tweets,author_id"})

def get_tweet(tweet_id):
    url = "https://api.twitter.com/2/tweets/{}".format(tweet_id)
    return connect_and_send_request("GET", url, {"tweet.fields": "conversation_id,referenced_tweets,author_id"})

def search_tweets(tweet_id, author_id):
    url = "https://api.twitter.com/2/tweets/search/recent?query=conversation_id:{} and from:{}".format(tweet_id, author_id)
    return connect_and_send_request("GET", url, {})

def get_user_name(user_id):
    url = "https://api.twitter.com/2/users/{}".format(user_id)
    response = connect_and_send_request("GET", url, {})
    return response["data"]["username"]

def reply_to_tweet(parent_tweet_id, status):
    url = "https://api.twitter.com/2/tweets"
    oauth = attempt_authorization(consumer_key, consumer_secret)
    response = oauth.post(url, json = { "text": status, "reply": {"in_reply_to_tweet_id": parent_tweet_id}})
    if response.status_code != 201:
        print(response.status_code)
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )


def find_thread_recursive(tweet, thread):
    thread.append(tweet["text"])
    if "referenced_tweets" in tweet:
        for reference in tweet["referenced_tweets"]:
            if reference["type"] == "replied_to":
                nextTweet = get_tweet(reference["id"])
                return find_thread_recursive(nextTweet["data"], thread)
    else:
        return thread


def write_summary_to_file(summary, conv_id, username):
    if summary != None:
        f = open(conv_id + ".txt", "w", encoding="utf-8")
        for element in summary:
            f.write(element + "\n")
        f.close()

def is_top_of_thread(tweet):
    print(tweet)
    for reference in tweet["referenced_tweets"]:
        if reference["type"] == "replied_to":
            return reference["id"] == tweet["conversation_id"]


def main():
    json_response = get_mentions()
    for tweet in json_response["data"]:
        if "referenced_tweets" in tweet and is_top_of_thread(tweet) == False:
            thread = find_thread_recursive(tweet, [])
            if thread != None:                
                summary = generate_summary(thread[::-1], math.floor(len(thread) / 2))
                username = get_user_name(tweet["author_id"])
                summary[0] = "@" + username + " " + summary[0]

                write_summary_to_file(summary, tweet["conversation_id"], username)
                # reply_to_tweet(tweet["id"], "".join(summary[0]))


if __name__ == "__main__":
    main()