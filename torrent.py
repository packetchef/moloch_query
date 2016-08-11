#!/usr/bin/python
import urllib
import urllib2
import os
import sys
import time
import socket
import struct
import json
import ConfigParser


def int2ip(addr):
	# thank you stackoverflow
	return socket.inet_ntoa(struct.pack("!I", addr))


def main(argv):
	# ref. https://github.com/aol/moloch/wiki/API
	configFile = sys.argv[1]

	# Need to validate config values are set and valid
	# eg. values are sensible, directory is writeable
	config = ConfigParser.RawConfigParser()
	config.read(configFile)
	runIntervalSeconds = config.getint('Config', 'runIntervalSeconds')
	node_name = config.get('Config', 'node_name')
	node_url = config.get('Config', 'node_url')
	node_user = config.get('Config', 'node_user')
	node_password = config.get('Config', 'node_password')
	query = config.get('Config', 'query')
	logfile = config.get('Config', 'logfile')

	# print("runIntervalSeconds: %s" % runIntervalSeconds)
	# print("node_url: %s" % node_url)
	# print("node_password: %s" % node_password)
	# print('query: %s' % query)


	# Output files will be named after runtime
	now = time.time()
	runtime = int(now)
	startTime = str(runtime - runIntervalSeconds)
	runtime = str(runtime)

	# skeleton to build a password manager to handle HTTP Basic Auth
	password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
	password_mgr.add_password(None, node_url, node_user, node_password)
	handler = urllib2.HTTPBasicAuthHandler(password_mgr)
	opener = urllib2.build_opener(handler)
	urllib2.install_opener(opener)

	# the expression= syntax is what you see in the URL bar in your browser, so modify as you see fit
	# add iDisplayLength=## to limit number of sessions to retrieve
	# Field names: https://github.com/aol/moloch/blob/master/db/db.pl
	# eg. a1 = ip.src
	api = 'spiview.json'
	spi_fields = 'spi=a1'
	expr = '?startTime=' + startTime + '&stopTime=' + runtime + '&' + spi_fields + '&expression=' + urllib.quote_plus(query)

	fullUrl = node_url + '/' + api + expr
	# print('fullUrl: %s' % fullUrl)

	req = urllib2.urlopen(fullUrl)
	reqjson = req.read()
	jdata = json.loads(reqjson)

	# Tester:
	# import json
	# with open('file.json') as file:
	#     j = json.load(file)
	# print(j['spi']['a1'])

	# Assumes we have results, need to handle for zero results
	logoutput = ''
	for result in jdata['spi']['a1']['terms']:
		# timestamp = time(jdata['health']['_timeStamp'] / 1000))
		ip = int2ip(result['term'])
		sessionCount = result['count']
		detectionTime = time.strftime('%Y-%m-%d %H:%M:%S %z', time.gmtime(now))
		print('Found IP: %s' % ip)
		print('Session count: %s' % sessionCount)
		print('Found during runtime: %s' % detectionTime)
		logoutput += 'BitTorrent detection: node=%s time=%s src=%s count=%s\n' % (node_name, detectionTime, ip, sessionCount)

	outFile = logfile + '.' + runtime
	print('Outfile: %s' % outFile)
	print('Logger: %s' % logoutput)

	with open(os.path.abspath(outFile), "wb") as local_file:
		#local_file.write(reqjson)
		local_file.write(logoutput)


if __name__ == '__main__':
    main(sys.argv[1:])


