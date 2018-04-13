# TFTP

Trivial File Transfer Protocol 

## Information

This project was made during Computer Networks course. 
Its goal was to implement TFTP compliant with RFC 1350, RFC 2347, RFC 2348 and RFC 7440.

## Description

Project consists of two files: client.py and server.py meaning respectively source code of client and
server TFTP. Both files was written to handle write request (RRQ) and accept windowsize option (which allow to
establish number of data blocks in one transfer window).

Both client and server were implemented in similar way.

Client manages all received packets in map. After each transfer window he sends ACK to server with
minimal index of packet he didn't get yet. To test correctness, from data blocks is calculated md5 hash.

Server listens for upcoming requests and for each RRQ he starts a new thread which at first reads whole file and
saves all data blocks in map. Then, in transfer windows of size equal to windowsize (set by client) he sends that data.
In case of timeout while waiting for ACK, server repeats sending last transfer window.

Except for that, both files contain a couple of supplementary functions whose main goal is to parse packets
and check correctness of input.


### Running

To run client, type './client.py server_name filename' (default number of port is 6969).
Analogously, to run server type './server.py port_nr dir_path'.

### Tests

Project was tested by my tutor via checking domain satori.tcs.uj.edu.pl and of course by me.
Tests' aim was to detect errors connected with lost packets and overall wrong functioning of program.

