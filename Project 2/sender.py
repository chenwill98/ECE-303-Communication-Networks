# Written by S. Mevawala, modified by D. Gitzel

# Credit to Leart for helping me

import logging
import socket

import channelsimulator
import utils
import sys
import math

MAX_SEQUENCE = 200


class Sender(object):

    def __init__(self, inbound_port=50006, outbound_port=50005, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)

    def send(self, data):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


# class BogoSender(Sender):
#
#     def __init__(self):
#         super(BogoSender, self).__init__()
#
#     def send(self, data):
#         self.logger.info(
#             "Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))
#         while True:
#             try:
#                 self.simulator.u_send(data)  # send data
#                 ack = self.simulator.u_receive()  # receive ACK
#                 self.logger.info("Got ACK from socket: {}".format(
#                     ack.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
#                 break
#             except socket.timeout:
#                 pass


class ReliableSender(Sender):

    global_timeout = 0

    def __init__(self, data, pkt_size, timeout):
        super(ReliableSender, self).__init__()
        self.pkt_size = pkt_size                                                  # Packet size
        self.pkt_count = int(math.ceil(len(data) // pkt_size)) + 1                # Total number of packets
        self.timeout = timeout
        self.global_timeout = timeout
        self.simulator.sndr_socket.settimeout(self.timeout)                       # Timeout interval
        self.seq_num = 0                                                          # Initializing sequence number
        self.pkt_resend = 0                                                       # Number of times it's been resent
        self.first = True

    def send(self, data):
        self.logger.info(
            "Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))

        # Split the data into many packets
        pkt_array = [data[i:i + self.pkt_size] for i in xrange(0, len(data), self.pkt_size)]

        for i in xrange(0, self.pkt_count):
            # self.first = True
            try:
                if self.first:
                    # Generates the packet and sends the payload in the correct format
                    pkt = Packet(i, data=pkt_array[i])
                    data_pkt = bytearray([pkt.check_sum, pkt.seq_num]) + pkt_array[i]
                    self.seq_num = pkt.seq_num
                    self.simulator.u_send(data_pkt)
                    self.logger.info(
                        "Sending first packet checksum: {} seq_num:{}".format(data_pkt[0], data_pkt[1]))

                # Waits for a response from the receiver
                while True:
                    ack_pkt = self.simulator.u_receive()
                    self.logger.info(
                        "Receiving ACK checksum: {} seq_num:{}".format(ack_pkt[0], ack_pkt[1]))
                    # If the checksum matches the ACK
                    if self._checksum(ack_pkt):
                        # If the sequence number matches the ACK, we don't need to do anything
                        if ack_pkt[1] == self.seq_num:
                            pass
                        # If the sequence number is less than the ACK, it means that the packet was also accepted and
                        # the ACK for that sequence number just got lost in the channel so we'll just accept packets
                        # that 1 ahead
                        elif ack_pkt[1] == (self.seq_num + 1) % MAX_SEQUENCE:
                            self.first = True
                            self.pkt_resend = 0
                            if self.timeout > self.global_timeout:
                                self.timeout -= self.global_timeout
                            self.simulator.sndr_socket.settimeout(self.timeout)
                            break

                        # If there was some other error, resend
                        else:
                            self.simulator.u_send(data_pkt)
                        self.logger.info(
                             "Sending other error packet checksum: {} seq_num:{}".format(data_pkt[0], data_pkt[1]))

                    # If the ACK is corrupted
                    else:
                        self._error_resend(data_pkt)
                        self.logger.info(
                             "Sending corrupted packet checksum: {} seq_num:{}".format(data_pkt[0], data_pkt[1]))

            # If it times out, simply send the data again
            except socket.timeout:
                self._error_resend(data_pkt)
                self.logger.info(
                     "Sending timeout packet checksum: {} seq_num:{}".format(data_pkt[0], data_pkt[1]))

    def _error_resend(self, data_pkt):
        self.first = False
        self.simulator.u_send(data_pkt)
        self.pkt_resend += 1
        if self.pkt_resend >= 3:
            self.timeout *= 2
            self.simulator.sndr_socket.settimeout(self.timeout)
            self.pkt_resend = 0
            # If there's too many timeouts, it quits
            if self.timeout >= 3:
                print("RIP")
                sys.exit()

    @staticmethod
    def _checksum(data):
        check_sum_val = ~ data[0]  # Invert all the bits in the first row of the data array (i.e. the checksum row)
        for i in xrange(1, len(data)):
            check_sum_val ^= data[i]  # XOR against all of the rows in the data
        if check_sum_val == - 1:
            return True  # If check_sum_val is all ones (i.e. -1 in twos complement), we good
        else:
            return False


# Packet format: [Checksum, Sequence number, Data]
class Packet(object):

    def __init__(self, seq_num=0, data=[]):
        self.seq_num = self._sequence_number(seq_num)
        self.check_sum = self._checksum(data)
        self.data = data

    # @staticmethod
    # def _checksum(data):
    #     check_sum = 0
    #     for bit in data:
    #         check_sum ^= bit
    #     return check_sum

    @staticmethod
    def _checksum(data):
        data_array = bytearray(data)
        check_sum = 0
        for i in xrange(len(data_array)):
            check_sum ^= data_array[i]
        return check_sum

    @staticmethod
    def _sequence_number(num):
        return num % MAX_SEQUENCE


if __name__ == "__main__":
    DATA = bytearray(sys.stdin.read())
    # test out BogoSender
    # sndr = BogoSender()
    # sndr.send(DATA)

    # ReliableSender(pkt_size, data, timeout)
    sndr = ReliableSender(DATA, 100, 0.1)
    sndr.send(DATA)
