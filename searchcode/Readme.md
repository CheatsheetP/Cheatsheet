# Download Result Files From Searchcode Api

## Usage:

### Execute From Terminal

```python3 -m searchcode.searchcode [-h] [-n NUM] [-t THREAD] [-p PER_QUERY] [-o OUTPUT] Q [Q ...]```

Use ```python3 -m searchcode.searchcode -h``` for details.

Notice that Q is a list of keywords. You don't need to include 'Q' in.

Example:

#### Download all files with keywords list and defaultdict:
```
python3 -m searchcode.searchcode -n 0 -o path/to/out list defaultdict
```
#### Download the first 10 files with keywords list and map using 2 threads and 5 repositories per query.
```
python3 -m searchcode.searchcode -n 10 -t 2 -p 5 -o path/to/out list map
```

### Clone the whole drectory and get all files with given extension

Example:

Clone repos that uses "Qt", and get all files with extension "py".

```
python3 -m searchcode.searchcode -n 0 -o outputdir -c py Qt
```
