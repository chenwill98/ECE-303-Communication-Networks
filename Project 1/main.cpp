//William Chen
//Professor Mevawala
//ECE-303 Communication Networks
//Project 1
//In retrospect, Python would've been much faster
#include <iostream>
#include <sstream>
#include <vector>
#include <unistd.h>
#include <winsock2.h>

using namespace std;
struct range {
  int start_range, end_range;
};
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
  SOCKET socketfd; //socket descriptor
  SOCKADDR_IN sockaddr; //socket address
  for (int port = ports.start_range; port <= ports.end_range; port++) {
    socketfd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP); //AF_LOCAL

    sockaddr.sin_family = AF_INET;
    sockaddr.sin_port = htons(port); //set the port number

    if (connect(socketfd, (struct sockaddr *)&sockaddr, sizeof(sockaddr)))
      printf("Port %i is open\n", port);

    closesocket(socketfd);
  }
}
