# async-await-crawler
Web crawler implementation using Python 3.5+ async/await

## Requirements
- Python 3.5+
- `pip install -r requirements.txt`

## Usage
```
$ python crawl.py www.example.com
```

## Options
- --out/-o : sitemap output file name
- --verbose/-v: verbosity level


## Docker usage

### Build the Docker image:
```
$ docker build -t async-await-crawler:latest .
```

### Run the crawler
```
$ docker run -it async-await-crawler http://me.syrex.com
```