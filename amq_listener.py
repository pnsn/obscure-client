import datetime
import os
import time
import signal
import sys

from collections import OrderedDict

from pprint import pprint
import stomp
import xmltodict


global db
global amq_broker

def get_utc_datetime(iso_format_string):
    """
    """
    # "2016-09-02T01:57:53.172Z"
    dt_time_string = iso_format_string[0:19]
    msecs = int( iso_format_string[20:-1] )
    dt = datetime.datetime.strptime(dt_time_string,"%Y-%m-%dT%H:%M:%S") + datetime.timedelta(milliseconds=msecs)
    return dt

def process(sa_message):
    """
        write trigger params message to datafile
    """
    datafile = "messages.xml"
    with open(datafile,"a") as fp:
        fp.write(sa_message)
    return

def process2(dm_message):
    """
        convert xml message to dict and then stores it into mongodb, adding a lddate
    """
    now = datetime.datetime.utcnow()
    d = xmltodict.parse(dm_message)
    d['lddate'] = now
    d['amq_broker'] = amq_broker
    #d['event_message']['core_info']['orig_time']['#text'] = get_utc_datetime(d['event_message']['core_info']['orig_time']['#text'])
    pprint(d)
    #try:
    #    result = db.messages.insert_one(d)
    #except Exception as e:
    #    print "Unable to write to MongoDB: {}".format(e)
    return
    
class GracefulShutdown:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

class MyListener(stomp.ConnectionListener):
    def on_connected(self, headers, body):
        print('Connected: "%s"' % headers)
    def on_error(self, headers, message):
        print('received an error "%s"' % message)
    def on_message(self, headers, message):
        print('received a message "%s", headers: %s' % (type(message),headers))
        process((message))
        

# user that subscribes to eew.sys.dm.data topic, to see DM output
DM_USER = os.environ.get('DM_USER')
DM_PW = os.environ.get('DM_PW')
STOMP_PORT = os.environ.get('STOMP_PORT')

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Connects to ActiveMQ broker of \
            specified ShakeAlert host. Listens for ShakeAlert DMMessages and GMMessages, \
            prints some header info to stdout and the full xml messages to a file named \
            messages.xml. \
            Requires environment variables STOMP_PORT, DM_USER, and DM_PW to be set.")

    parser.add_argument("amq_broker",help="provide one of the ShakeAlert DNS names")

    args = parser.parse_args()
    #non-optional arguments
    amq_broker = args.amq_broker
     
    shutdown_manager = GracefulShutdown() # catches SIGINT and SIGTERM

    # start listening to algorithm topic
    sa_conn = stomp.Connection([(amq_broker,STOMP_PORT)],auto_decode=True)
    sa_conn.set_listener('', MyListener())
    sa_conn.start()
    sa_conn.connect(DM_USER, DM_PW, wait=True)

    core_info_topic = "/topic/eew.sys.dm.data"
    gmcontour_topic = "/topic/eew.sys.gm-contour.data"
    gmmap_topic = "/topic/eew.sys.gm-map.data"
    heartbeat_topic = "/topic/eew.sys.ha.data"
    try:
        sa_conn.subscribe(destination=heartbeat_topic, id=1, ack='auto')
        sa_conn.subscribe(destination=core_info_topic, id=2, ack='auto')
        sa_conn.subscribe(destination=gmcontour_topic, id=3, ack='auto')
        sa_conn.subscribe(destination=gmmap_topic, id=4, ack='auto')
    except Exception as e:
        "Error subscribing to topic {}: {}".format(topic,e)
        sa_conn.disconnect()
        sys.exit()

    while True:
        time.sleep(1)
        if shutdown_manager.kill_now:
            # stop, disconnect from ActiveMQ broker
            print("Disconnecting from ShakeAlert ActiveMQ broker.\n")
            sa_conn.disconnect()
            break
