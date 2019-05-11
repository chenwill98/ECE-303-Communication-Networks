portscan: main.o
	g++ -o portscan main.o

main.o: main.cpp
	g++ -c main.cpp

clean:
	rm -f *.exe *.o *.stackdump *~

backup:
	test -d backups || mkdir backups
	cp *.cpp backups
	cp *.h backups
	cp Makefile backups
