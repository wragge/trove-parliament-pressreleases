# Harvesting Parliamentary press releases via Trove Australia

This is an example of harvesting useful data using the Trove API.

Trove includes more than 300,000 press releases and interview transcripts issued by federal politicians and saved by the Parliamentary Library. You can view them all in Trove by [searching for `nuc:"APAR:PR"` in the journals zone](http://trove.nla.gov.au/article/result?q=nuc%3A%22APAR%3APR%22).

This repository includes code to:

* harvest press release records from Trove and save them to a MongoDB database
* save the harvested metadata as a CSV file
* retrieve the full text of each press release from the ParlInfo database and save it as a Markdown-flavoured text file (complete with YAML front matter)

## Example dataset -- politicians talking about refugees

I've used the code to create an example dataset relating to refugees. It's been created by searching for the terms 'immigrant', 'asylum seeker', 'boat people', 'illegal arrivals', and 'boat arrivals' amongst the press releases. The exact query used is:

```
nuc:"APAR:PR" AND ("illegal arrival" OR text:"immigrant" OR text:"immigrants" OR "asylum seeker" OR "boat people" OR refugee OR "boat arrivals")
```

You can view the [results of this query on Trove](http://trove.nla.gov.au/article/result?q=nuc%3A%22APAR%3APR%22+AND+%28%22illegal+arrival%22+OR+text%3A%22immigrant%22+OR+text%3A%22immigrants%22+OR+%22asylum+seeker%22+OR+%22boat+people%22+OR+refugee+OR+%22boat+arrivals%22%29).

Here's the results:

* Metadata for each record saved as a [a CSV file](results-20171202.csv).
* Browse the full text of each article in the [texts](texts/) folder. Metadata is included in each file as YAML front matter.

## Some warnings

There are multiple versions of some press releases. For example, sometimes the office of a Minister and the Minister's department both issue a copy of the same press release or transcript. In many cases Trove has grouped these versions together as a work, however, that doesn't mean that the versions are identical. I've decided to harvest each individual version -- this means more duplicates, but it also means you can explore how the versions might differ.

It looks like the earlier documents have been OCRd and the results are quite variable. If you follow the `source_url` link you should be able to view a PDF version for comparison.

It also seems that some documents only have a PDF version and not any OCRd text. These documents will be ignored by the `save_texts()` function, so you might end up with fewer texts than records.

The copyright statement attached to each record in Trove reads:

> Copyright remains with the copyright holder. Contact the Australian Copyright Council for further information on your rights and responsibilities.

I'm providing these harvested records to support research. Depending on what you want to do with them, you might need to contact individual copyright holders for permission.

## Generate your own dataset

Requirements:

* A [Trove API key](http://help.nla.gov.au/trove/building-with-trove/api)
* Python 2.7.* (not tested with Python 3)
* a MongoDB database (either local or in the cloud)
* Git

### Setting things up

* Make sure you have [Python, Pip, and Virtualenv installed](http://timsherratt.org/digital-heritage-handbook/docs/python-pip-virtualenv/).
* Create a new virtual environment -- you can call it whatever you want.
``` shell
virtualenv trove-pressreleases
```
* Move to and then activate your virtual environment.
``` shell
cd trove-pressreleases
source/bin activate
```
* Clone this repository, and then move into the new folder that has been created.
``` shell
git clone ....
cd ....
```
* Install all the necessary Python packages listed in `requirements.txt`.
``` shell
pip install -r requirements.text
```
* Either [install MongoDB locally](https://docs.mongodb.com/manual/administration/install-community/) or create a new database on MongoDB hosting service like [MLab](https://mlab.com/) (you'll can probably make do with one of their free Sandbox databases).
* If you use a hosted database you'll need to copy the MongoDB URI, It looks like a url, but starts with `mongodb://`.
* Make a copy of the `credentials_blank.py` file and save it as `credentials.py`.
``` shell
cp credentials_blank.py credentials.py
```
* Open the new `credentials.py` file in your preferred text editor. Paste in your Trove API key where indicated. If your using a hosted MongoDB database, paste in the URI. If you've installed MongoDB locally, the default setting should work.

### Starting a harvest

* Make sure your virtual environment is activated and your inside the cloned repository folder.
* Type `python` to start up Python, the command prompt will change to `>>>`.
``` shell
python
```
* Import the `harvest.py` module and then run the `harvest()` function.
``` python
import harvest
harvest.harvest()
```

### Using your own search query

By default `harvest()` will launch the example search for terms relating to refugees. You can feed in your own query as a parameter to `harvest()` function.
``` python
import harvest
harvest.harvest('cats OR dogs')
```

Note that if you're doing multiple searches and you want to keep the results separate, you might want to change the database name in the `credentials.py` file.

### Saving as CSV

Once your harvest is complete, you can save the results to a CSV file.

* Make sure your virtual environment is activated and your inside the cloned repository folder.
* Type `python` to start up Python, the command prompt will change to `>>>`.
``` shell
python
```
* Import the `harvest.py` module and then run the `save_csv()` function.
``` python
import harvest
harvest.save_csv()
```

### Save full text versions of documents

Once your harvest is complete, you can download the texts of all the available documents.

* Make sure your virtual environment is activated and your inside the cloned repository folder.
* Type `python` to start up Python, the command prompt will change to `>>>`.
``` shell
python
```
* Import the `harvest.py` module and then run the `save_texts()` function.
``` python
import harvest
harvest.save_csv()
```

Note that this function will only download documents that have OCRd text in ParlInfo. So you might notice a difference between the number of records in your dataset and the number of texts downloaded.
