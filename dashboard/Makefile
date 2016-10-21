all: containers wait provision

clean:
	./destroy.sh

clean_hard: clean
	./delete_volumes.sh

containers:
	./boot.sh

wait:
	sleep 10

provision:
	./provision.sh	
