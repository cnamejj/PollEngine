#!/usr/bin/env python
"""
Sample sever, just echos input plus seq number
"""

import pollengine

# ---

class EchoDriver:
    """Driver to echo back client data"""

    def __init__( self ):
        self.seq = 0
        return

    def process_request( self, conn ):
        """Handle requests received from the client"""

        __continue = True
        __inp = conn.inp_queue
        if __inp[-1:] == '\n':
            __inp = __inp[:-1]

        conn.inp_queue = ''

        if __inp == 'QUIT':
            PE.displaymsg( 'Stopping server.' )
            __continue = False

        elif __inp == 'DROP':
            PE.displaymsg( 'Dropped client.' )
            conn.close()

        else:
            self.seq += 1
            conn.queue_response( 'Msg#{seq} len={ilen} {inp}'.format(
                    seq=self.seq, ilen=len(__inp), inp=__inp) )

        return __continue

    def get_name( self ):
        """Return a description of the class"""

        return 'Echo-Driver'

# ---

ECHO_PORT = 8888
SERVER_PORTS = set()
SERVER_PORTS.add( ECHO_PORT )

# ---

PE = pollengine

ECHO_SHELL = EchoDriver()

ENGINE = PE.Engine( port_list = SERVER_PORTS )
ENGINE.config_server( ECHO_PORT, shell = ECHO_SHELL )
ENGINE.run()
