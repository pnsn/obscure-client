# obscure-client
For Eric and company

# Requirements
- python3
- pip install stomp.py
- pip install xmltodict

# Usage
- Set environment variable DM_USER to be your User Display user name
- Set environment variabl DM_WP to be your User Display pw

```
usage: amq_listener.py [-h] amq_broker

Connects to ActiveMQ broker of specified ShakeAlert host. Listens for
ShakeAlert DMMessages and GMMessages, prints some header info to stdout and
the full xml messages to a file named messages.xml. Requires environment
variables STOMP_PORT, DM_USER, and DM_PW to be set.

positional arguments:
  amq_broker  provide one of the ShakeAlert DNS names

optional arguments:
  -h, --help  show this help message and exit
```



