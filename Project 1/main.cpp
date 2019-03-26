//William Chen
//Professor Mevawala
//ECE-303 Communication Networks
//Project 1
//In retrospect, Python would've been much faster
#include <iostream>
#include <sstream>
#include <vector>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <map>
#include <netdb.h>

using namespace std;

map <int, string> default_ports = {{25, "SMTP"}, {80, "HTTP"}, {443, "HTTPS"}, {20, "FTP"}, {21, "FTP"}, {23, "TELNET"}, {143, "IMAP"}, {22, "SSH"}, {53, "DNS"}};

struct range {
  int start_range, end_range;
};
int checkDefault(int port);
range parseRange(string string_range, range ports);
void scanPorts(string host_name, range ports);

int main(int argc, char *argv[]) {
  int c = 0;
  range ports; ports.start_range = 0; ports.end_range = 65535;
  string host_name = argv[optind++];
  while ((c = getopt(argc, argv, "p:")) != -1) //checks the -p flag
          switch (c) {
          case 'p':
                  ports = parseRange(optarg, ports);
                  break;
          case '?':
                  return -1;
                  break;
          }
  scanPorts(host_name, ports);
}
//Checks to see if the input port number is a default ports
int checkDefault(int port) {
  if (default_ports[port] != "")
    return 1;
  else
    return 0;
}
//Divides the given range into workable numbers
range parseRange(string string_range, range ports) {
  string alt_range;
  stringstream ss(string_range);
  vector<string> result;
  while(ss.good()) {
    string substr;
    getline(ss, substr, ':');
    result.push_back(substr);
  }
  ports.start_range = stoi(result[0]); ports.end_range = stoi(result[1]);
  if (ports.start_range > ports.end_range || ports.start_range < 0 || ports.end_range > 65535) {
    printf("Please enter a valid range:\n");
    cin >> alt_range;
    ports = parseRange(alt_range, ports);
  }
  return ports;
}
//Scans all of the ports in the given range.
void scanPorts(string host_name, range ports) {
  int socketfd; //socket descriptor
  struct sockaddr_in sockaddr; //socket address
  const char* addr = host_name.c_str();

  for (int port = ports.start_range; port <= ports.end_range; port++) {
    socketfd = socket(AF_INET, SOCK_STREAM, 0); //AF_LOCAL

    sockaddr.sin_family = AF_INET;
    sockaddr.sin_addr.s_addr = inet_addr(addr);
    sockaddr.sin_port = htons(port); //set the port number
    checkDefault(port);

    if (connect(socketfd, (struct sockaddr *)&sockaddr, sizeof(sockaddr)) == 0 && checkDefault(port))
      cout << default_ports[port] << " is open" << endl;
    else if (connect(socketfd, (struct sockaddr *)&sockaddr, sizeof(sockaddr)) == 0)
      cout << "Port " << port << " is open" << endl;

    close(socketfd);
  }
}
