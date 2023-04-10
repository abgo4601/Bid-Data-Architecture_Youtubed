import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from dotenv import load_dotenv
import openai
from datetime import datetime,timedelta

load_dotenv()

openai.api_key=os.getenv("OPEN_AI")

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = 'client_secrets.json'

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_local_server()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    now=datetime.utcnow()
    start_time=(now-timedelta(30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time=now.strftime("%Y-%m-%dT%H:%M:%SZ")


    results = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        myRating='like', maxResults=25
    )

    response = results.execute()

    video_tags = []

    for item in response["items"]:
        if 'tags' in item["snippet"].keys():
            for t in item["snippet"]["tags"]:
                if t not in video_tags:
                    video_tags.append(t)

    model_engine = "text-davinci-003"
    prompt = f"Recommend me names of top 15 TV shows, movies that are listed on IMDB and songs listed on Spotify based on the following tags: {video_tags}."

    response = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.8,
    )


    sections=response.choices[0].text.split("\n\n")
    sections=[section.strip() for section in sections]

    shows=[]
    movies=[]
    songs=[]

    for section in sections:
        lines = section.split('\n')
        category = lines.pop(0).replace(':', '')
        for line in lines:
            if category == 'TV Shows':
                shows.append(line.strip().split('. ')[1].split(' (')[0])
            elif category == 'Movies':
                movies.append(line.strip().split('. ')[1].split(' (')[0])
            elif category == 'Songs':
                songs.append(line.strip().split('. ')[1].split(' - ')[0].split(' (')[0])

    print('TV Shows:', shows)
    print('Movies:', movies)
    print('Songs:', songs)
    return response.choices[0].text

if __name__ == "__main__":
    main()