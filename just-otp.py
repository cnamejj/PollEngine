#!/usr/bin/env python
"""
Driver for OpenVPN client
"""

import time
import base64
import hashlib
import struct
import hmac
import pollengine

# ---

class OVDriveData:
    """OpenVPN authentication data"""

    def __init__( self ):
        self.otp_secret = NO_SECRET

# ---

class ShellAdmin:
    """Driver for admin shell object"""

    def __init__( self ):
#        PE.displaymsg( 'dbg:: Shell_Admin init' )
        self.ovdata = OVDriveData()

    def set_ovdata( self, ovdata ):
        """Record a data structure"""

        self.ovdata = ovdata

    def process_request( self, conn ):
        """Handle requests received from the client"""

#        PE.displaymsg( 'Received {size} bytes "{req}"'.format(
#                size=len(conn.inp_queue), req=conn.inp_queue) )
        __continue = True

        __lines = conn.inp_queue.split( '\n' )
        for __req in __lines:
            __words = __req.split( ' ' )

#            PE.displaymsg( 'dbg:: line "{line}" words {nw}'.format(line=__req,
#                    nw=len(__words)) )
            if len(__words) > 0:
                __comm = __words[0]

                if __comm == '':
                    continue

                if __comm == ACR_SECRET:
                    if len(__words) == 2:
                        self.ovdata.otp_secret = __words[1]

                        PE.displaymsg( 'Admin: set OTP secret' )
                        conn.queue_response( 'OTP secret' )
                    else:
                        conn.queue_response(
                               'The "secret" command takes one argument' )

                elif __comm == ACR_SHOW:
                    PE.displaymsg( 'Admin: show current settings' )
                    conn.queue_response( SHOW_TEMPLATE.format(
                            secret=self.ovdata.otp_secret) )

                elif __comm == ACR_OTP:
                    __otp = gen_otp(self.ovdata)
                    PE.displaymsg( 'Admin: Generate OTP {otp}'.format(
                            otp=__otp[-6:]) )
                    conn.queue_response( 'OTP for {now} is {otp}'.format(
                            now=time.strftime('%y/%m/%d-%H:%M:%S'),
                            otp=__otp[-6:]) )

                elif __comm == ACR_DROP:
                    PE.displaymsg( 'Admin: drop client connection' )
                    conn.close()

                elif __comm == ACR_QUIT:
                    PE.displaymsg( 'Admin: stop OVDriver' )
                    __continue = False

                else:

                    PE.displaymsg( 'Admin: unrecognized command "{comm}"'.
                            format(comm=__comm) )
                    conn.queue_response( 'Command "{comm}" unrecognized'.
                            format(comm=__comm) )

#        conn.queue_response( 'Got {nl} lines, {size} bytes\n'.format(
#                size=len(conn.inp_queue), nl=len(__lines)) )
        conn.inp_lines = ''
        conn.inp_queue = ''

        return __continue

    def get_name( self ):
        """Return a description of the class"""

        return 'Shell_Admin'

# ---

def gen_otp( ovdata ):
    """Generate the current one-time-password"""

    try:
        __n_interval = time.time() // OTP_INTERVAL
        __key = base64.b32decode( ovdata.otp_secret, casefold=OTP_COLLAPSE )
        __msg = struct.pack( '>Q', __n_interval )
        __hdig = hmac.new( __key, __msg, OTP_DIGEST_METH ).digest()
        __ob_low = ord( __hdig[19] ) & 15
        __fulltoken = struct.unpack( '>I', __hdig[__ob_low:__ob_low + 4])
        __token = (__fulltoken[0] & OTP_TOKEN_MASK) % (10 ** OTP_TOKEN_LEN)

        __result = '{token:06d}'.format(token=__token)
    except TypeError:

        __result = OTP_ERROR


#    PE.displaymsg( 'dbg:: Generate OTP {otp}'.format(otp=__result) )
    return( __result )

# ---

ADMIN_PORT = 8888

NO_SECRET = 'NoOTPSecret'

OTP_INTERVAL = 30
OTP_TOKEN_LEN = 6
OTP_DIGEST_METH = hashlib.sha1
OTP_COLLAPSE = True
OTP_TOKEN_MASK = 0x7fffffff
OTP_ERROR = 'OTP-Failed'

ACR_SECRET = 'secret'
ACR_SHOW = 'show'
ACR_QUIT = 'quit'
ACR_OTP = 'otp'
ACR_DROP = 'drop'

# Comma is needed to make this a tuple
SERVER_SPEC_LIST = ( ADMIN_PORT, )

SHOW_TEMPLATE = 'Secret: {secret}'

# ---

print "Listening on port {port}".format(port=SERVER_SPEC_LIST[0])

PE = pollengine
ENGINE = PE.Engine( server_list = SERVER_SPEC_LIST )

OVDATA = OVDriveData()
OVDATA.otp_secret = NO_SECRET

ADMIN_SHELL = ShellAdmin()
ADMIN_SHELL.set_ovdata( OVDATA )

ENGINE.config_server( ADMIN_PORT, shell = ADMIN_SHELL )

ENGINE.run()
