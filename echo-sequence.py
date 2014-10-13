#!/usr/bin/env python
"""
Sample server, just echos input plus seq number
"""

import pollengine
PE = pollengine

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

ECHO_PORT1 = 8888
ECHO_PORT2 = 8889
ANY_IP = '0.0.0.0'
SERVER1 = (ECHO_PORT1, ANY_IP)
SERVER2 = (ECHO_PORT2, ANY_IP)

ENGINE = PE.Engine( server_list = [ SERVER1, SERVER2 ] )
ENGINE.config_server( SERVER1, shell = EchoDriver() )
ENGINE.config_server( SERVER2, shell = EchoDriver() )
ENGINE.run()
