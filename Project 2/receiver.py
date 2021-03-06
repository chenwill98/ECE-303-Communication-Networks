# Written by S. Mevawala, modified by D. Gitzel

# Credit to Leart for helping me

import logging

import channelsimulator
import utils
import sys
import socket

MAX_SEQUENCE = 200


class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def receive(self):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


# class BogoReceiver(Receiver):
#     ACK_DATA = bytes(123)
#
#     def __init__(self):
#         super(BogoReceiver, self).__init__()
#
#     def receive(self):
#         self.logger.info(
#             "Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
#         while True:
#             try:
#                 data = self.simulator.u_receive()  # receive data
#                 self.logger.info("Got data from socket: {}".format(
#                     data.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
#                 sys.stdout.write(data)
#                 self.simulator.u_send(BogoReceiver.ACK_DATA)  # send ACK
#             except socket.timeout:
#                 sys.exit()


class ReliableReceiver(Receiver):

    def __init__(self, timeout):
        super(ReliableReceiver, self).__init__()
        self.timeout = timeout
        self.simulator.rcvr_socket.settimeout(self.timeout)
        self.data_packet = bytearray([0, 0, 0])
        self.corrupted = bytearray([1, 0])
        self.ack_resend = 0
        self.final_ack = -1
        self.seq = 0

    def receive(self):
        self.logger.info(
            "Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))

        while True:
            try:
                data_packet = self.simulator.u_receive()  # receive data

                checksum = data_packet[0]
                seq_num = data_packet[1]
                data = data_packet[2:]
                self.logger.info(
                    "Receiving packet checksum: {} seq_num:{}".format(checksum, seq_num))

                # Compares the received checksum to the generated checksum
                if self._checksum(data_packet):
                    self.seq = (seq_num + 1) % MAX_SEQUENCE
                    if self.final_ack == -1 or seq_num == self.final_ack:
                        sys.stdout.write("{}".format(data.decode('ascii')))
                        sys.stdout.flush()
                    self.final_ack = self.seq
                else:
                    # self._error_resend(self.corrupted)
                    self.logger.info(
                        "Sending corrupt corrupt ACK checksum: {} seq_num:{}".format(self.corrupted[0],
                                                                                     self.corrupted[1]))
                if self.seq < 0:
                    self.seq = 0
                self._send_ack(self.seq)

            # If timeout, respond the same way as a corrupted packet
            except socket.timeout:
                self._error_resend(self.corrupted) # Send a "corrupted" ACK that has a checksum and ACK mismatch
                self.logger.info(
                    "Sending corrupt timeout ACK checksum: {} seq_num:{}".format(self.corrupted[0], self.corrupted[1]))

    def _error_resend(self, ack_pkt):
        self.simulator.u_send(ack_pkt)
        self.ack_resend += 1
        if self.ack_resend >= 3:
            self.timeout *= 5
            self.simulator.rcvr_socket.settimeout(self.timeout)
            self.ack_resend = 0
            # If there's too long timeouts, it quits
            if self.timeout >= 3:
                sys.exit()

    def _send_ack(self, seq_num):
        # Generates the ACK packet and sends the payload in the correct format
        ack = Packet(ack_num=seq_num)
        ack_pkt = bytearray([ack.check_sum, ack.ack_num])
        self.simulator.u_send(ack_pkt)
        self.logger.info(
            "Sending ACK checksum: {} seq_num:{}".format(ack_pkt[0], ack_pkt[1]))

    # Credit to Rayhan for this
    @staticmethod
    def _checksum(data):
        checksum = ~ data[0]           # covert to two's complement
        for i in xrange(2, len(data)):
            checksum ^= data[i]        # XOR bitwise
        if checksum == - 1:
            return True
        return False


# Packet format: [Checksum, ACK]
class Packet(object):

    def __init__(self, ack_num=0):
        self.check_sum = self._checksum(ack_num)
        self.ack_num = ack_num

    # The checksum can just be itself, because what are the odds they get corrupted to the same thing?
    @staticmethod
    def _checksum(ack_num):
        return ack_num


if __name__ == "__main__":
    # test out BogoReceiver
    # rcvr = BogoReceiver()
    # rcvr.receive()

    rcvr = ReliableReceiver(0.1)
    rcvr.receive()
