import requests
import time
from requests.exceptions import HTTPError
from pymongo import MongoClient
from bs4 import BeautifulSoup
from utilities import retry
from slugify import slugify
import csv
from datetime import datetime
import os

from credentials import API_KEY, MONGO_URL

DEFAULT_QUERY = '"illegal arrival" OR text:"immigrant" OR text:"immigrants" OR "asylum seeker" OR "boat people" OR refugee OR "boat arrivals"'

@retry(HTTPError, tries=10, delay=1)
def get_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def harvest(keywords=DEFAULT_QUERY):
    '''
    Harvest Parliamentary press releases using the Trove API and save them to a Mongo DB.
    This function saves the 'version' level records individually (these are grouped under 'works').
    You could easily adapt this to harvest other types of records.
    '''
    # Connect to Mongo database
    dbclient = MongoClient(MONGO_URL)
    db = dbclient.get_default_database()
    # Define parameters for the search -- you could change this of course
    # The nuc:"APAR:PR" limits the results to the Parliamentary Press Releases
    query = 'nuc:"APAR:PR" AND ({})'.format(keywords)
    zone = 'article'
    # Number of results to include per request
    # The count value is also used to check when the harvest has got to the end of the results set
    count = 100
    n = count
    # Start at the beginning!
    s = 0
    # n is set below to the number of results returned by the most recent request, so if n is not equal to count then we must have got to the end.
    while n == count:
        url = 'http://api.trove.nla.gov.au/result?q={}&zone=article&encoding=json&include=workVersions&n={}&s={}&key={}'.format(query, n, s, API_KEY)
        print url
        data = get_data(url)
        # Set n to number of results delivered by the current request.
        n = int(data['response']['zone'][0]['records']['n'])
        # Increment s to get the next set of results
        s = int(data['response']['zone'][0]['records']['s']) + count
        # Loop through all the works
        for work in data['response']['zone'][0]['records']['work']:
            # We're going to harvest version details. Multiple version ids are stored in a single field.
            # We need to split the ids so we can attach them to individual records below.
            ids = work['version'][0]['id'].split()
            # Loop through the versions.
            for index, version in enumerate(work['version'][0]['record']):
                # Add the id to the version record
                version['_id'] = ids[index]
                # Save the version record to Mongo
                db.versions.replace_one({'_id': ids[index]}, version, upsert=True)
                print version['title']
            # Try to avoid hitting the API request limit
            time.sleep(0.5)


def clean_metadata(version):
    '''
    Standardises, cleans, and encodes record metadata.
    '''
    record = {}
    record['_id'] = version['_id']
    record['title'] = version['title'].strip().encode('utf-8')
    record['date'] = version['date']
    # Make sure creators is a list
    creators = version.get('creator', [])
    if isinstance(creators, basestring):
        creators = [creators]
    record['creators'] = [c.strip().encode('utf-8') for c in creators]
    record['source'] = version.get('source', '').encode('utf-8')
    # Make sure subjects is a list
    subjects = version.get('subject', [])
    if isinstance(subjects, basestring):
        subjects = [subjects]
    record['subjects'] = [unicode(s).strip().encode('utf-8') for s in subjects]
    # Loop through identifiers to get fulltext url
    for link in version['identifier']:
        if link['linktype'] == 'fulltext':
            record['source_url'] = link['value']
            break
    record['trove_url'] = 'http://trove.nla.gov.au/version/{}'.format(version['_id'])
    return record


def save_csv():
    '''
    Save the harvested records as a CSV file, flattening lists as required.
    This function saves the following fields:
        'title', 'date', 'creators', 'source', 'subjects', 'source_url', 'trove_url'
    '''
    # Connect to db
    dbclient = MongoClient(MONGO_URL)
    db = dbclient.get_default_database()
    versions = db.versions.find()
    # Open a CSV file for writing.
    # Filename of CSV file includes a datastamp so as not to overwrite previous datasets.
    with open('results-{}.csv'.format(datetime.now().strftime('%Y%m%d')), 'wb') as csv_file:
        # The fields we're going to save
        fieldnames = ['title', 'date', 'creators', 'source', 'subjects', 'source_url', 'trove_url']
        # Create a CSV DictWriter and add a header row
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        # Loop through versions
        for version in versions:
            # Add values to a dictionary
            record = clean_metadata(version)
            record['creators'] = '; '.join(record['creators'])
            record['subjects'] = '; '.join(record['subjects'])
            # Write dictionary to the CSV file
            writer.writerow(record)


def save_texts():
    '''
    Get the text of press releases in the ParlInfo db.
    This function uses urls harvested from Trove to request press releases from Parlinfo.
    The text of each release is saved as a markdown file with YAML front matter to document basic metadata.
    '''
    # Connect to Mongo
    dbclient = MongoClient(MONGO_URL)
    db = dbclient.get_default_database()
    # Loop through all the previously harvested records
    for version in db.versions.find().batch_size(50):
        # Format record metadata
        record = clean_metadata(version)
        print record['source_url']
        # filename based on date, creator name/s, and version id
        creator_name = slugify('-'.join(record['creators']))
        filename = '{}-{}-{}.md'.format(version['date'], creator_name, version['_id'])
        # Only save files we haven't saved before
        if not os.path.exists('texts/{}'.format(filename)):
            # Get the Parlinfo web page
            response = requests.get(record['source_url'])
            # Parse web page in Beautiful Soup
            soup = BeautifulSoup(response.content, 'lxml')
            content = soup.find('div', class_='box')
            # If we find some text on the web page then save it.
            if content:
                # Open file
                print 'Saving file...'
                with open('texts/{}'.format(filename), 'wb') as text_file:
                    # Write YAML front matter
                    text_file.write('---\n')
                    text_file.write('title: "{}"\n'.format(record['title']))
                    text_file.write('date: "{}"\n'.format(record['date']))
                    text_file.write('creators:\n')
                    for creator in record['creators']:
                        text_file.write('  - "{}"\n'.format(creator))
                    text_file.write('source: "{}"\n'.format(record['source']))
                    text_file.write('subjects:\n')
                    for subject in record['subjects']:
                        text_file.write('  - "{}"\n'.format(subject))
                    text_file.write('trove_url: {}\n'.format(record['trove_url']))
                    text_file.write('source_url: {}\n'.format(record['source_url']))
                    text_file.write('---\n\n')
                    # Write release content to the file
                    for para in content.find_all('p'):
                        text_file.write('{}\n\n'.format(para.get_text().encode('utf-8')))
            time.sleep(0.5)
