Start:
	cp Makefile ~ && cd ~
	sudo apt-get install mininet
	git clone http://github.com/noxrepo/pox
	git clone https://github.com/mininet/mininet
	mininet/util/install.sh -w
	mv ~/networksMininetStuff/pox ~
	mv ~/networksMininetStuff/mininet ~
	cp ~/networksMininetStuff/theThing.py ~/pox/ext
	clear
	echo "Let's a go!"

refresh:
	cd ~/networksMininetStuff
	git pull
	cd ~
	cp ~/networksMininetStuff/theThing.py ~/pox/ext


startpox: 
	cd ~ && cd pox && python pox.py openflow.of_01 --port=6633 log.level --DEBUG theThing &
	clear

stoppox:
	sudo fuser -k 6633/tcp
	clear

startmini: 
	sudo mn --topo single,6 --mac --controller remote,ip=127.0.0.1,port=6633 --switch ovsk,protocols=OpenFlow10

wireshark:
	sudo wireshark &