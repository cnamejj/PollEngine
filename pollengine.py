#!/usr/bin/env python
"""Routines to support implementation of a simple server"""

import socket
import select
import time
import inspect

# ---

ADMIN_PORT = 7778
ENGINE_PORT = 7777

SERVER_SPEC_LIST = ( ADMIN_PORT, ENGINE_PORT )

# ---

POLL_MAX_WAIT = 60
MAX_REQ_SIZE = 32768
STATUS_INTERVAL = 5

IS_LISTEN = 0
IS_SESSION = 1

NO_CLIENT = 'no-client'
NO_SOCK = 0
NO_PORT = -1
NO_EXT_IP = 'localhost'

DO_READ = 0
DO_WRITE = 1
DO_CLOSE = 2
DO_ACCEPT = 3
DO_TIMEOUT = 4

ACTION = dict()
ACTION[DO_READ] = 'Read'
ACTION[DO_WRITE] = 'Write'
ACTION[DO_CLOSE] = 'Close'
ACTION[DO_ACCEPT] = 'Accept'
ACTION[DO_TIMEOUT] = 'Timeout'

# ---

def displaymsg( line ):
    """Display timestamp'd message"""

    print '{now} {msg}'.format(now = time.strftime('%y/%m/%d-%H:%M:%S'),
            msg=line)

    return

# ---

def wait_for_sock_event( conn_list, handler ):
    """Block until some actionable network event is presented"""

    on_read = set()
    on_write = set()
    __event_list = set()

#    displaymsg( "dbg:: Start WFSE, conn's {clen} handlers {hlen}".format(
#            clen=len(conn_list), hlen=len(handler)) )

    for __conn in conn_list:

        if __conn.elist[DO_READ]:
            on_read.add( __conn.sock )
#            displaymsg( 'dbg:: Wait to read fd#{fd}'.format(
#                    fd=__conn.sock.fileno()) )

        if __conn.elist[DO_WRITE]:
            on_write.add( __conn.sock )
#            displaymsg( 'dbg:: Wait to write fd#{fd}'.format(
#                    fd=__conn.sock.fileno()) )

#    displaymsg( "dbg:: WFSE poll, read {rlen} write {wlen}".format(
#            rlen=len(on_read), wlen=len(on_write)) )
    __rlist, __wlist, __elist = select.select( on_read, on_write, [],
            POLL_MAX_WAIT )

    if len(__rlist) == 0 and len(__wlist) == 0:
        __event = EventData()
        __event.type = DO_TIMEOUT
        __event.sock = NO_SOCK
        __event_list.add( __event )
#        displaymsg( 'dbg:: Timeout on all sockets' )

    else:
        for __sock in __rlist:
            __event = EventData()
            __event.sock = __sock
            if handler[__sock].type == IS_LISTEN:
                __event.type = DO_ACCEPT
#                displaymsg( 'Ready to accept, fd={fno}'.format(
#                        fno=__sock.fileno()) )
            else:
                __event.type = DO_READ
#                displaymsg( 'Ready to read, fd={fno}'.format(
#                        fno=__sock.fileno()) )
            __event_list.add( __event )

        for __sock in __wlist:
            __event = EventData()
            __event.sock = __sock
            __event.type = DO_WRITE
            __event_list.add( __event )        
#            displaymsg( 'Ready to write, fd={fno}'.format(
#                    fno=__sock.fileno()) )

    return __event_list

# ---

def dummy_status( conn_list ):
    """Dummy routine used until the user overrides"""

    displaymsg( 'dbg:: Send status command, connect len {clen}'.format(
            clen=len(conn_list)) )
    return

# ---

class EventData:
    """Allocate data bundle describing a network event"""

    def __init__( self ):
#        displaymsg( 'dbg:: EventData init' )
        self.sock = NO_SOCK
        self.type = DO_READ
        return

# ---

class ShellNull:
    """Dummy class used until the user provides a data manager"""

    def __init__( self ):
        return

    def process_request( self, conn ):
        """Deal with the input queue"""

        conn.queue_response( 'Got {size} bytes\n'.format(
                size=len(conn.inp_queue)) )
        conn.inp_queue = ''
        return True

    def get_name( self ):
        """Identify this plugin data handler"""

        return 'ShellNull'

# ---

class SocketConn:
    """Manage a socket session."""

    def __init__( self, shell, status = dummy_status ):
#        displaymsg( 'dbg:: SocketConn init' )
        self.server_ip = NO_EXT_IP
        self.server_port = NO_PORT
        self.client = NO_CLIENT
        self.sock = NO_SOCK
        self.sock_open = False
        self.inp_queue = ''
        self.out_queue = ''
        self.type = IS_LISTEN
        self.elist = dict()
        self.elist[DO_READ] = True
        self.elist[DO_WRITE] = False
        if inspect.isclass( shell ):
            self.shell = shell()
        else:
            self.shell = shell
        self.req = ''
        self.status_callback = status

    def queue_response( self, response ):
        """Append the given string to queue output"""

        if len(response) > 0:
            self.out_queue = '{curr}{app}\n'.format(curr=self.out_queue,
                    app=response)
            self.elist[DO_WRITE] = True

    def read( self ):
        """Pull data waiting to be read"""

#        displaymsg( 'dbg:: SocketConn read' )
        self.req = self.sock.recv( MAX_REQ_SIZE )
        if len(self.req) == 0:
            self.close()
        else:
            
            self.inp_queue = '{curr}{app}'.format( curr=self.inp_queue,
                    app=self.req.translate(None, '\r\0') )
        return True

    def write( self ):
        """Send any queue data on the socket"""

#        displaymsg( 'dbg:: SocketConn write' )
        __slen = self.sock.send( self.out_queue )
        if __slen != len( self.out_queue ):
            self.out_queue = self.out_queue[__slen:]
        else:
            self.out_queue = ''
            self.elist[DO_WRITE] = False
        return True

    def accept( self ):
        """Accept a new client, create new socket"""

        __session, __client = self.sock.accept()
#        displaymsg( 'dbg:: SocketConn accept' )
        return True, __session, __client

    def close( self ):
        """Close the socket"""

#        displaymsg( 'dbg:: SocketConn close' )
        self.sock.shutdown( socket.SHUT_RDWR )
        self.sock.close()
        self.sock_open = False
        return True

# ---

class ServerGizmo:
    """Setup a listening port."""

    def __init__( self, port, shell = ShellNull(), status = dummy_status, s_ip = NO_EXT_IP ):
#        displaymsg( 'dbg:: ServerGizmo init' )
        self.server_ip = s_ip
        self.server_port = port
        self.shell = shell
        self.status_callback = status
        self.conn = SocketConn( self.shell, status = status )
        self.conn.server_ip = self.server_ip
        self.conn.server_port = self.server_port
        self.conn.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.conn.sock.setblocking( 0 )
        self.conn.sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self.conn.sock.bind( (self.server_ip, self.server_port) )
        self.conn.sock.listen( 5 )
        self.conn.sock_open = True

# ---

class Engine:
    """Skeleton for a simple server"""

    def __init__( self, server_list = SERVER_SPEC_LIST):
        self.handler = dict()
        self.port2server = dict()
        for __spec in server_list:
            try:
                if len( __spec ) > 1:
                    __port = __spec[0]
                    __ip = __spec[1]
                else:
                    __port = __spec
                    __ip = NO_EXT_IP
            except TypeError:
                __port = __spec
                __ip = NO_EXT_IP
            self.config_server( __port, s_ip = __ip )

    def config_server( self, port, shell = ShellNull(), status = dummy_status, s_ip = NO_EXT_IP ):
        """Add a server or change the shell of one"""

        try:
            __serv = self.port2server[port]
        except KeyError:
            __serv = ServerGizmo( port, shell = shell, status = status, s_ip = s_ip )
            self.port2server[port] = __serv
            self.handler[__serv.conn.sock] = __serv.conn

        __serv.shell = shell
        __serv.conn.shell = __serv.shell
        __serv.status_callback = status
        __serv.conn.status_callback = status

    def run( self ):
        """Run the network packet state machine"""

        __idle_cycles = 0
        __active_sockets = set()
        __current_sockets = set()
        __polling = True

#        displaymsg( "dbg:: Starting the state machine" )

        for __sock in self.handler:
            __conn = self.handler[__sock]
            if __conn.sock_open:
                __active_sockets.add( __conn )

        # ---

        while __polling:

            __event_list = wait_for_sock_event( __active_sockets, self.handler )
#            displaymsg( "dbg:: After WFSE: events {lev}".format(
#                    lev=len(__event_list)) )

            for __event in __event_list:

                if __event.type == DO_TIMEOUT:
                    __idle_cycles += 1
                    if __idle_cycles >= STATUS_INTERVAL:
                        displaymsg( 'Check tunnel status' )
                        for __sock in __active_sockets:
                            if __sock.type == IS_LISTEN:
                                __sock.status_callback( __active_sockets )
                        __idle_cycles = 0
                    else:
                        displaymsg( 'Timeout #{seq}, wait again...'.
                                format(seq=__idle_cycles) )
                    continue

                else:
                    __idle_cycles = 0

                if __event.sock == NO_SOCK:
                    continue

                __sess = self.handler[__event.sock]
#                __dbgmsg = 'dbg:: Socket #{fd} action {act} shell {shn}'
#                displaymsg( __dbgmsg.format(fd=__event.sock.fileno(),
#                        act=ACTION[__event.type],
#                        shn=str(__sess.shell.get_name())) )

                if __event.type == DO_READ:
                    __polling = __sess.read()

                elif __event.type == DO_WRITE:
                    __polling = __sess.write()

                elif __event.type == DO_CLOSE:
                    displaymsg( 'Closing client connection' )
                    __polling = __sess.close()

                elif __event.type == DO_ACCEPT:
                    displaymsg( 'Got a new admin client on port {port}'.format(
                            port=__sess.server_port) )
                    __polling, __sock, __client = __sess.accept()
                    __cli = SocketConn( __sess.shell, status = 
                            __sess.status_callback )
                    __cli.sock = __sock
                    __cli.client = __client
                    __cli.type = IS_SESSION
                    __cli.server_ip = __sess.server_ip
                    __cli.server_port = __sess.server_port
                    __cli.sock_open = True
                    __active_sockets.add( __cli )
                    self.handler[__cli.sock] = __cli

                if not __polling:
                    break

            if not __polling:
                break

            __current_sockets = set()

            for __conn in __active_sockets:
                __sock = __conn.sock

                if not __conn.sock_open:
                    continue

#                __dbgmsg = 'dbg:: run-active fd#{fd} type {stype} shell {shn} \
#inp {lin} out {lout}'
#                displaymsg( __dbgmsg.format(fd=sock.fileno(), stype=conn.type,
#                        shn=conn.shell.get_name(), lin=len(conn.inp_queue),
#                        lout=len(conn.out_queue)) )

                if len(__conn.inp_queue) > 0:
                    __polling = __conn.shell.process_request( __conn )
                    if not __polling:
                        break

                if len(__conn.out_queue) > 0:
                    __conn.elist[DO_WRITE] = True

                if __conn.sock_open:
                    __current_sockets.add( __conn )

            __active_sockets = __current_sockets

        # ---

        displaymsg( 'Done...' )
