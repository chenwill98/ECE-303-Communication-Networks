//William Chen
//Professor Mevawala
//ECE-303 Communication Networks
//Project 1
//In retrospect, Python would've been much faster
#include <iostream>
#include <sstream>
#include <vector>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
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
  struct sockaddr_in host_addr; //socket address

  socketfd = socket(AF_INET, SOCK_STREAM, 0);

  hostent* host_info = gethostbyname(host_name.c_str()); //converts host name to IP
  const char* host_ip = inet_ntoa(**(in_addr**)host_info->h_addr_list);

  for (int port = ports.start_range; port <= ports.end_range; port++) {

    host_addr.sin_family = AF_INET;
    inet_pton(AF_INET, host_ip, &host_addr.sin_addr);
    host_addr.sin_port = htons(port); //set the port number

    if (connect(socketfd, (struct sockaddr *)&host_addr, sizeof(host_addr)) > -1 && checkDefault(port))
      cout << default_ports[port] << " is open" << endl;
    if (connect(socketfd, (struct sockaddr *)&host_addr, sizeof(host_addr)) > -1)
      cout << "Port " << port << " is open" << endl;

    close(socketfd);
  }

}
